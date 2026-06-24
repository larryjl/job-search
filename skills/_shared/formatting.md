# Shared Document Formatting — Job Search

All document-generating skills (tailor-resume, cover-letter-generator) must
follow these rules exactly. This is the single source of truth for fonts, colours, sizes,
and margins. Do not redefine these values inside individual skill files.

---

## Colours

```python
from docx.shared import RGBColor

NAVY  = RGBColor(0x1F, 0x37, 0x65)  # #1F3765 — headings, name, accent elements
BLACK = RGBColor(0x1A, 0x1A, 0x1A)  # #1A1A1A — body text, dates, contact line
```

| Use | Hex | RGBColor |
|-----|-----|----------|
| Candidate name | `#1F3765` | `NAVY` |
| Section headings (resume) | `#1F3765` | `NAVY` |
| Company name (resume) | `#1A1A1A` | `BLACK` |
| "Re:" line (cover letter) | `#1F3765` | `NAVY` |
| Body text | `#1A1A1A` | `BLACK` |
| Contact line | `#1A1A1A` | `BLACK` |
| Date ranges (resume) | `#1A1A1A` | `BLACK` |
| Sign-off (cover letter) | `#1A1A1A` | `BLACK` |

---

## Font Family

**Arial** for all body text, bullets, section headings, and contact lines — no exceptions.

**Georgia** for the candidate name only (header line). This is the sole exception to Arial.

```python
# Body text, headings, bullets, contact line:
run.font.name = FONT        # "Arial"

# Candidate name header only:
run.font.name = FONT_NAME   # "Georgia"
```

Do not use Calibri, Times New Roman, or any other font.

---

## Font Sizes

| Element | Size | Weight |
|---------|------|--------|
| Candidate name (header) | 16pt | Bold |
| Section headings (resume only) | 12pt | Bold |
| "Re:" line (cover letter) | 11pt | Bold |
| Body text / bullet points | 11pt | Regular |
| Contact line / metadata | 10pt | Regular |
| **Minimum anywhere** | **10pt** | — |

```python
from docx.shared import Pt

# Always use Pt() — never multiply manually.
# Correct:  run.font.size = Pt(11)
# Wrong:    run.font.size = 11 * 20  # that's twips, not points
```

---

## Page Margins

**0.85 inches** on all sides for resumes. Cover letters use 1 inch.

Use `set_margins(doc)` — the default is `MARGIN_IN = 0.85`. Pass `inches=1` explicitly for cover letters.

```python
set_margins(doc)           # resumes — 0.85"
set_margins(doc, inches=1) # cover letters — 1"
```

---

## Paragraph Spacing

Default spacing to suppress Word's built-in gap between paragraphs:

```python
from docx.shared import Pt

def set_spacing(paragraph, before=0, after=0, line=None):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)
    if line:
        pf.line_spacing = Pt(line)
```

Standard spacing values:

| Context | space_before | space_after |
|---------|-------------|-------------|
| Candidate name | 4 | 4 |
| Contact line | 0 | 12 |
| Date / address block | 0 | 8 |
| "Re:" line (cover letter) | 0 | 12 |
| Salutation | 0 | 8 |
| Body paragraph | 0 | 10 |
| Sign-off ("Sincerely,") | 12 | 0 |
| Closing name | 24 | 0 |
| Section heading (resume) | 10 | 3 |
| Bullet point (resume) | 0 | 2 |

---

## Shared Helper Functions

These are implemented in `skills/lib/docx_helpers.py`. **Import them — do not copy-paste.**

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from docx_helpers import (
    NAVY, BLACK, FONT, FONT_NAME, MARGIN_IN,
    set_spacing, add_run, set_margins, keep_with_next,
    add_section_heading, add_company_date_row, add_rule, add_bullet,
    add_prof_dev_item, set_metadata,
)
```

Available functions:
- `set_spacing(paragraph, before, after, line)` — paragraph spacing in pt
- `add_run(paragraph, text, bold, size, color)` — styled run with Arial font
- `set_margins(doc)` — 0.85" margins on all sides (pass `inches=1` for cover letters)
- `add_section_heading(doc, text)` — ALL-CAPS 12pt bold NAVY heading with 2pt navy left border
- `keep_with_next(paragraph)` — prevent page break after heading/company row
- `add_company_date_row(doc, company, date_range)` — flush-right date tab
- `add_rule(doc, color, size)` — horizontal rule via paragraph border
- `add_bullet(doc, text, indent=0.25)` — hanging-indent bullet
- `add_prof_dev_item(doc, credential, description)` — two-paragraph PD entry
- `set_metadata(doc, project_root)` — sets author/last_modified_by from master-resume.md

---

## Document Metadata

Always set on every `.docx` generated. Use `set_metadata(doc)` from `docx_helpers` — it reads
`profile/master-resume.md` and sets `author`, `last_modified_by`, and clears `comments`.

```python
from docx_helpers import set_metadata
set_metadata(doc)   # project_root resolved automatically
```

---

## Resume-Specific Rules

These apply only to `tailor-resume` and are not relevant to cover letters.

### Company/date row layout

Company name and date range on the same line, date flush right:

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_company_date_row(doc, company, date_range):
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=0)

    pPr = p._p.get_or_add_pPr()
    tabs = OxmlElement('w:tabs')
    tab  = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'right')
    tab.set(qn('w:pos'), str(int(6.5 * 1440)))  # 6.5 inches in twips
    tabs.append(tab)
    pPr.append(tabs)

    run_co = p.add_run(company)
    run_co.bold           = True
    run_co.font.color.rgb = BLACK  # Black for ATS safety — headings stay navy
    run_co.font.name      = FONT

    p.add_run('\t')

    run_date = p.add_run(date_range)
    run_date.bold           = False
    run_date.font.color.rgb = BLACK
    run_date.font.name      = FONT

    return p
```

### Page break control

- Set `paragraph_format.keep_with_next = True` on every section heading
- Set `keep_with_next = True` on every company/date row and job title row
- Do NOT set it on bullet points — only on heading rows of each job entry

```python
def keep_with_next(paragraph):
    paragraph.paragraph_format.keep_with_next = True
```

### Length limit

Resumes must stay under 2 pages. Minimum font size is 10pt — never reduce below this to fit content.

---

## Cover-Letter-Specific Rules

These apply only to `cover-letter-generator` and are not relevant to resumes.

### Length limit

Cover letters must fit on 1 page. If content is too long, tighten paragraphs. Do not reduce font size below 11pt.

### Structure

Candidate name (16pt, bold, NAVY) → contact line (10pt, BLACK) → date → Re: line (11pt, bold, NAVY) → salutation → 3 body paragraphs → sign-off.

