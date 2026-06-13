---
name: save-job-posting
description: >
  Save a job posting as a PDF (for URLs/PDF files), DOCX (for uploaded DOCX files or pasted text) with the filename format
  [CompanyName]_[JobTitle]_[Date].pdf/.docx.
  Trigger this skill whenever the user says "save this job posting", "save this job", "save job", 
  "archive this job", or provides a job posting (as a .docx file, .pdf file, URL, or pasted text) and asks 
  to save it. Also trigger when the user says things like "I want to keep this job posting" or 
  "store this job for later". Always use this skill when a job posting needs to be saved — do 
  not attempt to handle this ad-hoc.
---
 
# Save Job Posting Skill
 
Save a job posting as a consistently named file. Output format depends on input type:
- **LinkedIn URL** (`linkedin.com/jobs/...`) → save as `.docx`; use `save_linkedin_posting.py` with the already-extracted JD text (do NOT fetch the URL via web_fetch). Step 2c.
- **Non-LinkedIn URL** save as `.pdf` (web_fetch → weasyprint)
- **PDF file** → save as `.pdf` (no conversion needed, use standard filename)
- **DOCX file** → save as `.docx` (no conversion needed, use standard filename)
- **Pasted text** → save as `.docx` (Step 2a)

## Output Filename Format
 
```
[company-name]_[job-title]_[YYYY-MM-DD].pdf   ← for non-LinkedIn URLs and PDF files
[company-name]_[job-title]_[YYYY-MM-DD].docx  ← for LinkedIn URLs, uploaded DOCX files, and pasted text
```
 
Use today's actual date. Replace spaces with underscores. All lowercase. Remove special characters that are 
invalid in filenames (e.g. `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`).
 
Example: `acme-corp_senior-software-engineer_2026-04-21.pdf`
Example: `acme-corp_senior-software-engineer_2026-04-21.docx`
 
## Path Resolution (use in every step that writes a file)

The project root must be resolved at runtime — never hardcode a session path. Use this pattern in every script:

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.claude/lib'))
from project_paths import get_project_root, get_postings_dir

PROJECT_ROOT = get_project_root()
JOB_OUTPUTS  = os.path.join(PROJECT_ROOT, "job-outputs")
POSTINGS_DIR = get_postings_dir()
```

Use `POSTINGS_DIR` (or other `JOB_OUTPUTS/...` subpaths) for all file writes and copies. Never substitute a literal `/sessions/...` path.

---
## Step 1: Check if file exists
### Step 1a: Extract Company Name and Job Title
 
After getting the PDF (or from the URL page content), extract the company name and job title.
 
#### From a URL
Use the page `<title>`, `<h1>`, or structured job detail fields. With playwright:
```python
title = await page.title()
h1 = await page.inner_text('h1')
```
With web_fetch content: parse the returned markdown/HTML for the `<h1>` or title tag.
 
#### From a PDF
Extract text using pdfplumber or pdftotext:
```bash
pdftotext /tmp/job_raw.pdf /tmp/job_text.txt
```
Then read the first ~500 characters to find the job title and company name.
 
#### Rules for extraction
- **Job title**: Usually the largest heading / `<h1>` / first prominent text on the page
- **Company name**: Often in the header, logo alt-text, or near "at [Company]" / "About [Company]"
- If either is ambiguous or not found, **ask the user** before proceeding

### Step 1b: Check the folder
Check if a posting already exists in `job-outputs/postings/` for the same Company + Role.
If it already exists skip to step 6 and tell the user it already existed.

### Step 1c: Build the new Filename

Use `make_filename(company, title, ext)` from `.claude/lib/filename_builder.py`:
- `ext="pdf"` for URL or PDF file inputs
- `ext="docx"` for uploaded DOCX, LinkedIn, or pasted text inputs

--

## Step 2a: Pasted Text → Save as DOCX

If the input is text pasted directly into the chat (not a file attachment and not a URL):

Write the text to a temp file, then run:

```bash
python3 <project_root>/skills/save-job-posting/save_job_posting.py \
    --input-type pasted \
    --company "[Company Name]" \
    --title "[Job Title]" \
    --input-text "[pasted text]"
```

The script outputs `SAVED:/path/to/file` and `FILENAME:filename.docx`. Use the filename for CSV logging.

- Preserve the original text exactly — do not summarise

---

## Step 2c: LinkedIn URL → Save as DOCX (from extracted JD text)

**Trigger:** Input URL contains `linkedin.com/jobs/` — do NOT use web_fetch or weasyprint on LinkedIn URLs. LinkedIn's raw HTML contains nav chrome ("Sign in", "Join now", pagination) that pollutes the PDF and the JD content is only fully available after JS renders in a logged-in session.

**Instead, use the JD text already extracted via Chrome** (from `get_page_text` in the scout-link right panel), or navigate to the posting in Chrome and extract it now:

1. If JD text is already in session (scout-link flow) → use it directly
2. If not: `navigate` to the LinkedIn URL in Chrome → expand "… more" button → `get_page_text` → extract the "About the job" section through end of posting

Then run `save_linkedin_posting.py`:

```bash
# Write JD text to temp file
cat > /tmp/jd_text.txt << 'JD'
[paste extracted JD text here]
JD

python3 <project_root>/skills/save-job-posting/save_linkedin_posting.py \
    --company "[Company Name]" \
    --title "[Job Title]" \
    --url "[LinkedIn URL]" \
    --jd-file /tmp/jd_text.txt
```

The script outputs `SAVED:/path/to/file` and `FILENAME:filename.docx`. Use the filename for CSV logging.

**Note:** The canonical posting URL for jobs.csv should be `https://www.linkedin.com/jobs/view/[jobId]/` — not the full search URL with parameters.

---

## Step 2b: Convert to PDF (from web)
 
### If input is a URL
 
Use `url_to_pdf()` from the shared lib — it handles the weasyprint → Playwright fallback chain automatically.

**Always use `web_fetch` first** to retrieve the raw HTML, then pass it to `url_to_pdf()`. Only skip the `web_fetch` step if the fetch fails or returns no usable content, in which case pass `url` only and the lib will use Playwright directly.

**Critical:** Do not reformat, restructure, or rewrite the HTML. The goal is fidelity to the original. Inject only a minimal `<base>` tag so relative URLs resolve correctly.

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.claude/lib'))
from pdf_converter import url_to_pdf

# raw_html = full HTML string from web_fetch (do not alter structure or styling)
# base_url  = "https://original-domain.com"  (for resolving relative assets)
# url       = original URL (used as Playwright fallback if weasyprint produces < 5KB)

success = url_to_pdf(
    html_text=raw_html,
    url=url,
    base_url=base_url,
    output_path="/tmp/job_raw.pdf"
)

if not success:
    # Both methods failed — inform the user and ask them to upload the file instead
    raise RuntimeError("PDF conversion failed for URL: " + url)
```

`url_to_pdf()` tries weasyprint first (fast, HTML-based). If the result is < 5KB it falls back to Playwright (headless Chromium, re-fetches the live URL). Both dependencies are auto-installed by the lib if missing.
 
## Step 2d: If input is already a .docx or .pdf file
 
Copy directly to `job-outputs/postings/` with the normalised filename — no conversion needed.

---
 
## Step 3: Save to Output
 
Save the final file to `job-outputs/postings/`:

Resolve `POSTINGS_DIR` using the runtime pattern from the Path Resolution section above. Then:

**If the source file is already inside `job-outputs/postings/`:** rename it in place — do not copy.
```bash
mv "$POSTINGS_DIR/original_name.pdf" "$POSTINGS_DIR/Acme_Corp_Senior_Software_Engineer_2026-04-21.pdf"
```

**For PDF (URL or uploaded file input from outside `job-outputs/postings/`):**
```bash
cp /tmp/job_raw.pdf "$POSTINGS_DIR/Acme_Corp_Senior_Software_Engineer_2026-04-21.pdf"
```

**For DOCX (uploaded .docx file):** copy directly to `job-outputs/postings/` with the normalised filename — no conversion.
```bash
cp "/path/to/uploaded.docx" "$dest"
```

**For DOCX (pasted text input):** already written directly to `job-outputs/postings/` in Step 2a — no copy needed.
 
Then use `present_files` to share the file with the user.
 
---
 
## Step 4: Update jobs.csv and Confirm

Write the `Posting_File` value (the saved filename, e.g. `acme-corp_senior-software-engineer_2026-04-21.pdf`) into the `Posting_File` column when appending or updating a row in `job-outputs/jobs.csv`.

- If appending a new row (status `pending`): populate `Posting_File` with the filename
- If a row already exists for this Company + Role: update `Posting_File` in that row if it is currently blank
- `Job_ID`: leave blank — save-job-posting does not populate this field (SI Systems portal only)

Tell the user:
> "📎 Saved as `acme-corp_senior-software-engineer_2026-04-21.docx`" (docx or pdf)
 
---
 
## Edge Cases
 
| Situation | Action |
|-----------|--------|
| Company name not found | Ask user |
| Job title not found | Ask user |
| URL requires login / paywalled | Inform user the page couldn't be loaded; ask them to upload the file instead |
| .docx copy fails | Check path and permissions; retry with explicit cp command |
| File already exists in outputs | Append `_2`, `_3`, etc. to avoid overwrite |
| Pasted text but python-docx unavailable | Install with `pip install python-docx --break-system-packages -q` then retry |
