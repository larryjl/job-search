#!/usr/bin/env python3
"""
Generate a cover letter .docx (and .pdf) from a structured content dict.

Usage:
    python3 skills/cover-letter-generator/generate_cover_letter.py \
        --company "shopify" \
        --role "senior-analytics-engineer" \
        --content-file /tmp/cover_content.py \
        --output-dir job-outputs/cover-letters/

Content file format (/tmp/cover_content.py):
    content = {
        "re_line": "Senior Analytics Engineer — Shopify",
        "hiring_manager": "Hiring Team",      # or a real name
        "opening": "...",
        "middle": "...",
        "closing": "...",
        # Optional — read from master resume if omitted:
        "contact_line": "Calgary, AB | email | phone | linkedin",
    }

Output:
    Prints SAVED:/path/to/file.docx and SAVED:/path/to/file.pdf on success.
    Prints ERROR:... and exits with code 1 on failure.
"""

import argparse
import importlib.util
import os
import subprocess
import sys
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _setup_lib_path():
    lib_path = os.path.normpath(os.path.join(SCRIPT_DIR, '../lib'))
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)


_setup_lib_path()

from project_paths import get_project_root   # noqa: E402
from docx_helpers import (                   # noqa: E402
    NAVY, BLACK,
    set_spacing, add_run, set_margins, set_metadata,
)
from docx import Document                    # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_content(content_file):
    spec   = importlib.util.spec_from_file_location("cover_content", content_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, 'content'):
        raise ValueError(f"content_file must define a variable named 'content': {content_file}")
    return module.content


def convert_to_pdf(docx_path, output_dir):
    """Convert docx to PDF using soffice. Returns pdf_path or None.

    soffice writes temp/lock files alongside the output. To keep those out of
    the cover-letters folder, we convert into /tmp and move only the final .pdf over.
    """
    import shutil
    import tempfile

    tmp_dir = tempfile.mkdtemp(prefix="cover_pdf_")
    try:
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", docx_path, "--outdir", tmp_dir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return None
        tmp_pdf = os.path.join(tmp_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
        if not os.path.exists(tmp_pdf):
            return None
        dest_pdf = os.path.join(output_dir, os.path.basename(tmp_pdf))
        shutil.move(tmp_pdf, dest_pdf)
        return dest_pdf
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def read_contact_line_from_resume(project_root):
    """Attempt to read contact info from master resume (second non-empty line after name)."""
    resume_path = os.path.join(project_root, "profile", "master-resume.md")
    try:
        with open(resume_path) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        # First line is "# Name", second is typically contact
        return lines[1] if len(lines) > 1 else ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Document builder
# ---------------------------------------------------------------------------

def build_cover_letter(doc, content, project_root):
    """Populate doc with cover letter content."""
    candidate_name = set_metadata(doc, project_root)

    # Header — candidate name
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=2)
    add_run(p, candidate_name, bold=True, size=16, color=NAVY)

    # Contact line
    contact_line = content.get("contact_line") or read_contact_line_from_resume(project_root)
    if contact_line:
        # Strip markdown formatting if present
        contact_line = contact_line.lstrip("#| ").strip()
        p = doc.add_paragraph()
        set_spacing(p, before=0, after=12)
        add_run(p, contact_line, size=10)

    # Date
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=8)
    add_run(p, date.today().strftime("%B %-d, %Y"))

    # Re: line
    re_line = content.get("re_line", "")
    if re_line:
        p = doc.add_paragraph()
        set_spacing(p, before=0, after=12)
        add_run(p, "Re: ", bold=True, color=NAVY)
        add_run(p, re_line, bold=True, color=NAVY)

    # Salutation
    hiring_manager = content.get("hiring_manager", "Hiring Team")
    p = doc.add_paragraph()
    set_spacing(p, before=0, after=8)
    add_run(p, f"Dear {hiring_manager},")

    # Body paragraphs
    for body_key in ("opening", "middle", "closing"):
        body_text = content.get(body_key, "")
        if body_text:
            p = doc.add_paragraph()
            set_spacing(p, before=0, after=10)
            add_run(p, body_text)

    # Sign-off
    p = doc.add_paragraph()
    set_spacing(p, before=12, after=0)
    add_run(p, "Sincerely,")

    p = doc.add_paragraph()
    set_spacing(p, before=24, after=0)
    add_run(p, candidate_name, bold=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate cover letter docx + pdf")
    parser.add_argument("--company",      required=True)
    parser.add_argument("--role",         required=True)
    parser.add_argument("--content-file", required=True)
    parser.add_argument("--output-dir",   required=False)
    args = parser.parse_args()

    try:
        project_root = get_project_root()
    except RuntimeError as e:
        print(f"ERROR:{e}", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(project_root, "job-outputs", "cover-letters")
    os.makedirs(output_dir, exist_ok=True)

    today     = date.today().strftime("%Y-%m-%d")
    filename  = f"cover_{args.company}_{args.role}_{today}"
    docx_path = os.path.join(output_dir, filename + ".docx")
    pdf_path  = os.path.join(output_dir, filename + ".pdf")

    try:
        content = load_content(args.content_file)
    except Exception as e:
        print(f"ERROR:Failed to load content file: {e}", file=sys.stderr)
        sys.exit(1)

    doc = Document()
    set_margins(doc)

    try:
        build_cover_letter(doc, content, project_root)
    except Exception as e:
        print(f"ERROR:Document build failed: {e}", file=sys.stderr)
        sys.exit(1)

    doc.save(docx_path)

    try:
        Document(docx_path)
    except Exception as e:
        print(f"ERROR:Generated docx failed validation: {e}", file=sys.stderr)
        sys.exit(1)

    result_pdf = convert_to_pdf(docx_path, output_dir)
    if not result_pdf:
        print("ERROR:PDF conversion failed (soffice). docx saved but no pdf.", file=sys.stderr)
        print(f"SAVED:{docx_path}")
        sys.exit(1)

    print(f"SAVED:{docx_path}")
    if os.path.exists(pdf_path):
        print(f"SAVED:{pdf_path}")


if __name__ == "__main__":
    main()
