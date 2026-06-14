#!/usr/bin/env python3
"""
save_linkedin_posting.py — Save a LinkedIn job posting from extracted JD text.

Usage:
    python3 save_linkedin_posting.py \
        --company "ShyftLabs" \
        --title "Data Engineer" \
        --url "https://www.linkedin.com/jobs/view/4385828168/" \
        --jd-file /tmp/jd_text.txt

Or pipe JD text via stdin:
    echo "JD text..." | python3 save_linkedin_posting.py \
        --company "ShyftLabs" --title "Data Engineer" \
        --url "https://www.linkedin.com/jobs/view/4385828168/"

Saves a clean DOCX to job-outputs/postings/ — avoids LinkedIn nav chrome
that appears when converting the raw URL HTML.
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../lib'))
from project_paths import get_project_root, get_postings_dir
from filename_builder import make_filename
from docx_helpers import set_metadata

def save_linkedin_posting(company, title, url, jd_text):
    try:
        from docx import Document
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "python-docx",
             "--break-system-packages", "-q"],
            check=True
        )
        from docx import Document

    POSTINGS_DIR = get_postings_dir()

    doc = Document()
    set_metadata(doc)

    # Title heading
    heading = doc.add_heading(f"{title} — {company}", level=1)

    # Source URL
    if url:
        meta = doc.add_paragraph()
        meta.add_run(f"Source: {url}").bold = False
        meta.style = doc.styles['Normal']

    doc.add_paragraph()  # spacer

    # JD body — preserve structure, split on double newlines for paragraphs
    sections = jd_text.strip().split("\n\n")
    for section in sections:
        lines = section.strip().split("\n")
        if not lines:
            continue
        # Detect section headers (short lines, no punctuation at end, or all-caps)
        first_line = lines[0].strip()
        is_header = (
            len(first_line) < 80 and
            not first_line.endswith('.') and
            len(lines) >= 1 and
            any(c.isupper() for c in first_line)
        )
        if is_header and len(lines) == 1:
            p = doc.add_heading(first_line, level=2)
        else:
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Bullet lines
                if line.startswith(('- ', '• ', '* ')):
                    p = doc.add_paragraph(style='List Bullet')
                    p.add_run(line[2:])
                else:
                    p = doc.add_paragraph(line)

    filename = make_filename(company, title, ext="docx")
    output_path = os.path.join(POSTINGS_DIR, filename)

    # Handle existing file
    if os.path.exists(output_path):
        base = filename.rsplit('.', 1)[0]
        ext = filename.rsplit('.', 1)[1]
        for i in range(2, 10):
            candidate = os.path.join(POSTINGS_DIR, f"{base}_{i}.{ext}")
            if not os.path.exists(candidate):
                output_path = candidate
                filename = f"{base}_{i}.{ext}"
                break

    doc.save(output_path)
    return output_path, filename

def main():
    parser = argparse.ArgumentParser(description="Save a LinkedIn job posting as a clean DOCX")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--title", required=True, help="Job title")
    parser.add_argument("--url", default="", help="LinkedIn job URL")
    parser.add_argument("--jd-file", help="Path to file containing JD text (or use stdin)")
    args = parser.parse_args()

    if args.jd_file:
        with open(args.jd_file) as f:
            jd_text = f.read()
    else:
        jd_text = sys.stdin.read()

    if not jd_text.strip():
        print("ERROR: No JD text provided", file=sys.stderr)
        sys.exit(1)

    output_path, filename = save_linkedin_posting(args.company, args.title, args.url, jd_text)
    print(f"SAVED:{output_path}")
    print(f"FILENAME:{filename}")

if __name__ == "__main__":
    main()
