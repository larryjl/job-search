#!/usr/bin/env python3
"""
Generate a tailored resume .docx (and .pdf) from a structured content dict.

Usage:
    python3 skills/tailor-resume/generate_resume.py \
        --company "telus" \
        --role "data-strategist" \
        --content-file /tmp/resume_content.py \
        --output-dir job-outputs/resumes/

Content file format (/tmp/resume_content.py):
    content = {
        "summary": "...",
        "skills": [
            {"category": "Analytics Engineering", "items": ["dbt", "Snowflake"]},
        ],
        "experience": [
            {
                "title": "Senior Data Analyst",
                "company": "ACME Corp",
                "location": "Calgary, AB",
                "dates": "Jan 2022 – Present",
                "bullets": ["Led...", "Built..."],
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Commerce",
                "institution": "University of Calgary",
                "location": "Calgary, AB",
                "dates": "2012 – 2016",
                "details": [],   # optional: list of strings
            }
        ],
        "prof_dev": [
            {"credential": "dbt Analytics Engineering | 2024", "description": "Data modeling"},
            {"credential": "AWS Solutions Architect | 2023", "description": None},
        ],
        "optional_sections": [],  # list of {"heading": "...", "items": [...str]}
    }

Output:
    Prints SAVED:/path/to/file.docx and SAVED:/path/to/file.pdf on success.
    Prints ERROR:... and exits with code 1 on failure.
    Prints PAGE_COUNT:N after PDF conversion.
"""

import argparse
import importlib.util
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# Path setup — works when run from any cwd
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = None  # resolved lazily via get_project_root()


def _setup_lib_path():
    lib_path = os.path.join(SCRIPT_DIR, '../../.claude/lib')
    lib_path = os.path.normpath(lib_path)
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)


_setup_lib_path()

from project_paths import get_project_root  # noqa: E402
from docx_helpers import (                  # noqa: E402
    NAVY, BLACK, FONT,
    set_spacing, add_run, set_margins, keep_with_next,
    add_company_date_row, add_prof_dev_item, set_metadata,
)
from docx import Document                   # noqa: E402
from docx.shared import Pt                  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_content(content_file):
    """Load the content dict from a Python file."""
    spec   = importlib.util.spec_from_file_location("resume_content", content_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'content'):
        raise ValueError(f"content_file must define a variable named 'content': {content_file}")
    return module.content


def get_pdf_page_count(pdf_path):
    """Return page count of a PDF using pdfinfo, or None on error."""
    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path],
            capture_output=True, text=True, timeout=15,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                return int(line.split(":")[1].strip())
    except Exception:
        pass
    return None


def convert_to_pdf(docx_path, output_dir):
    """Convert docx to PDF using soffice. Returns pdf_path or None."""
    result = subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", docx_path, "--outdir", output_dir],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        return None
    pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
    return pdf_path if os.path.exists(pdf_path) else None


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def add_section_heading(doc, text):
    """Add an ALL-CAPS section heading (12pt bold NAVY)."""
    p = doc.add_paragraph()
    set_spacing(p, before=8, after=2)
    keep_with_next(p)
    add_run(p, text.upper(), bold=True, size=12, color=NAVY)
    return p


def build_resume(doc, content, project_root):
    """Populate doc with resume content from the content dict."""
    candidate_name = set_metadata(doc, project_root)

    # --- Header ---
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=2)
    add_run(p, candidate_name, bold=True, size=16, color=NAVY)

    # Contact line — read from master resume first line block
    # (Skills that call this script should include contact_line in content if needed)
    contact_line = content.get("contact_line", "")
    if contact_line:
        p = doc.add_paragraph()
        set_spacing(p, before=0, after=12)
        add_run(p, contact_line, size=10)

    # --- Summary ---
    summary = content.get("summary", "")
    if summary:
        add_section_heading(doc, "Professional Summary")
        p = doc.add_paragraph()
        set_spacing(p, before=0, after=6)
        add_run(p, summary)

    # --- Skills ---
    skills = content.get("skills", [])
    if skills:
        add_section_heading(doc, "Skills")
        for skill_group in skills:
            p = doc.add_paragraph()
            set_spacing(p, before=0, after=2)
            add_run(p, skill_group["category"] + ": ", bold=True)
            add_run(p, ", ".join(skill_group["items"]))

    # --- Experience ---
    experience = content.get("experience", [])
    if experience:
        add_section_heading(doc, "Professional Experience")
        for job in experience:
            # Job title
            p = doc.add_paragraph()
            set_spacing(p, before=6, after=0)
            keep_with_next(p)
            add_run(p, job["title"], bold=True)

            # Company + date row
            company_loc = job["company"]
            if job.get("location"):
                company_loc += f", {job['location']}"
            row = add_company_date_row(doc, company_loc, job.get("dates", ""))
            keep_with_next(row)

            # Bullets
            for bullet in job.get("bullets", []):
                p = doc.add_paragraph()
                set_spacing(p, before=0, after=2)
                p.paragraph_format.left_indent       = Pt(18)   # ~0.25in
                p.paragraph_format.first_line_indent = Pt(-18)
                add_run(p, "•  " + bullet)

    # --- Education ---
    education = content.get("education", [])
    if education:
        add_section_heading(doc, "Education")
        for edu in education:
            row = add_company_date_row(doc, edu["institution"] + (f", {edu['location']}" if edu.get("location") else ""), edu.get("dates", ""))
            keep_with_next(row)
            p = doc.add_paragraph()
            set_spacing(p, before=0, after=2)
            add_run(p, edu["degree"], bold=True)
            for detail in edu.get("details", []):
                p2 = doc.add_paragraph()
                set_spacing(p2, before=0, after=2)
                add_run(p2, "•  " + detail)

    # --- Professional Development ---
    prof_dev = content.get("prof_dev", [])
    if prof_dev:
        add_section_heading(doc, "Professional Development")
        for item in prof_dev:
            add_prof_dev_item(doc, item["credential"], item.get("description"))

    # --- Optional sections ---
    for section in content.get("optional_sections", []):
        add_section_heading(doc, section["heading"])
        for item in section.get("items", []):
            p = doc.add_paragraph()
            set_spacing(p, before=0, after=2)
            add_run(p, item)


def trim_one_bullet(content):
    """
    Drop the weakest bullet from the oldest non-current role.
    Returns True if a bullet was removed, False if nothing left to trim.
    Weakest = last bullet in the list (caller should order bullets best-to-worst).
    Never removes the only bullet in a role.
    Never trims from the most recent role (index 0) unless all others are at 1 bullet.
    """
    experience = content.get("experience", [])
    if not experience:
        return False

    # Try oldest role first, then work toward most recent
    for job in reversed(experience[1:]):   # skip index 0 (most recent)
        if len(job.get("bullets", [])) > 1:
            job["bullets"].pop()
            return True

    # If every older role is at 1 bullet, trim from most recent as last resort
    if len(experience[0].get("bullets", [])) > 1:
        experience[0]["bullets"].pop()
        return True

    return False


def trim_summary(content):
    """Shorten summary by one sentence (removes last sentence)."""
    summary = content.get("summary", "")
    sentences = [s.strip() for s in summary.split(".") if s.strip()]
    if len(sentences) > 1:
        content["summary"] = ". ".join(sentences[:-1]) + "."
        return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate tailored resume docx + pdf")
    parser.add_argument("--company",      required=True,  help="Normalized company name (e.g. 'telus')")
    parser.add_argument("--role",         required=True,  help="Normalized role slug (e.g. 'data-strategist')")
    parser.add_argument("--content-file", required=True,  help="Path to Python file defining 'content' dict")
    parser.add_argument("--output-dir",   required=False, help="Output directory (default: job-outputs/resumes/)")
    parser.add_argument("--max-pages",    type=int, default=2, help="Maximum page count (default: 2)")
    args = parser.parse_args()

    try:
        project_root = get_project_root()
    except RuntimeError as e:
        print(f"ERROR:{e}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(project_root, "job-outputs", "resumes")
    os.makedirs(output_dir, exist_ok=True)

    from datetime import date
    today     = date.today().strftime("%Y-%m-%d")
    filename  = f"resume_{args.company}_{args.role}_{today}"
    docx_path = os.path.join(output_dir, filename + ".docx")
    pdf_path  = os.path.join(output_dir, filename + ".pdf")

    try:
        content = load_content(args.content_file)
    except Exception as e:
        print(f"ERROR:Failed to load content file: {e}", file=sys.stderr)
        sys.exit(1)

    # Build and save docx
    max_passes = 10
    for attempt in range(max_passes):
        doc = Document()
        set_margins(doc)
        try:
            build_resume(doc, content, project_root)
        except Exception as e:
            print(f"ERROR:Document build failed: {e}", file=sys.stderr)
            sys.exit(1)

        # Validate
        doc.save(docx_path)
        try:
            Document(docx_path)
        except Exception as e:
            print(f"ERROR:Generated docx failed validation: {e}", file=sys.stderr)
            sys.exit(1)

        # Convert to PDF
        result_pdf = convert_to_pdf(docx_path, output_dir)
        if not result_pdf:
            print("ERROR:PDF conversion failed (soffice). docx saved but no pdf.", file=sys.stderr)
            print(f"SAVED:{docx_path}")
            sys.exit(1)

        # Page count check
        pages = get_pdf_page_count(result_pdf)
        if pages is not None:
            print(f"PAGE_COUNT:{pages}")
        else:
            pages = 0  # can't determine — assume ok

        if pages <= args.max_pages or pages == 0:
            break

        # Over page limit — trim and retry
        print(f"INFO:Resume is {pages} pages — trimming (pass {attempt + 1})", file=sys.stderr)
        trimmed = trim_one_bullet(content)
        if not trimmed:
            trimmed = trim_summary(content)
        if not trimmed:
            print(f"INFO:Nothing left to trim — accepting {pages} pages", file=sys.stderr)
            break

    print(f"SAVED:{docx_path}")
    if os.path.exists(pdf_path):
        print(f"SAVED:{pdf_path}")


if __name__ == "__main__":
    main()
