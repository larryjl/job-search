#!/usr/bin/env python3
"""
Save a job posting as a PDF or DOCX file.

Usage:
    python save_job_posting.py --input-type [pasted|pdf|docx] \
        --company "Company Name" --title "Job Title" \
        [--input-path /path/to/file | --input-text "..."]

    For URL inputs: the agent fetches HTML via web_fetch (MCP tool) and converts
    it to PDF using url_to_pdf() from the shared lib. This script handles
    pasted text, uploaded PDF files, and uploaded DOCX files only.

    For LinkedIn URLs: use save_linkedin_posting.py instead.

Output:
    SAVED:/path/to/saved/file
    FILENAME:filename.ext
"""

import sys
import os
import argparse
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../.claude/lib'))

from project_paths import get_postings_dir, get_project_root
from filename_builder import make_filename
from docx_helpers import set_metadata


def save_pasted_text(company, title, text, output_path):
    """
    Save pasted text as a DOCX file.

    Args:
        company (str): Company name
        title (str): Job title
        text (str): Job posting text
        output_path (str): Path to save the DOCX file

    Returns:
        bool: True if successful
    """
    try:
        from docx import Document

        doc = Document()
        set_metadata(doc)

        # Title heading
        doc.add_heading(f"{title} — {company}", level=1)

        # Body: preserve text as-is
        for line in text.strip().split("\n"):
            doc.add_paragraph(line)

        doc.save(output_path)
        return True
    except ImportError:
        import subprocess
        subprocess.run(
            ["pip", "install", "python-docx", "--break-system-packages", "-q"],
            check=False,
        )
        return save_pasted_text(company, title, text, output_path)
    except Exception as e:
        print(f"Error saving pasted text: {e}", file=sys.stderr)
        return False


def copy_file(source_path, output_path):
    """
    Copy a file to the postings directory with normalized filename.

    Args:
        source_path (str): Path to the source file
        output_path (str): Destination path

    Returns:
        bool: True if successful
    """
    try:
        shutil.copy(source_path, output_path)
        return True
    except Exception as e:
        print(f"Error copying file: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Save a job posting as PDF or DOCX"
    )
    parser.add_argument(
        "--input-type",
        required=True,
        choices=["pasted", "pdf", "docx"],
        help="Type of input (url inputs are handled agent-side; LinkedIn uses save_linkedin_posting.py)",
    )
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--title", required=True, help="Job title")
    parser.add_argument(
        "--input-path", help="Path to input file (for pdf/docx)"
    )
    parser.add_argument("--input-text", help="Pasted text (for pasted)")

    args = parser.parse_args()

    # Determine file extension
    ext = "docx" if args.input_type in ["pasted", "docx"] else "pdf"

    # Build filename and output path
    filename = make_filename(args.company, args.title, ext=ext)
    postings_dir = get_postings_dir()
    output_path = os.path.join(postings_dir, filename)

    # Handle filename collision
    counter = 2
    base_path = output_path
    while os.path.exists(output_path):
        name_parts = base_path.rsplit(".", 1)
        output_path = f"{name_parts[0]}_{counter}.{name_parts[1]}"
        counter += 1
        filename = os.path.basename(output_path)

    # Save based on input type
    success = False
    if args.input_type == "pasted":
        success = save_pasted_text(args.company, args.title, args.input_text, output_path)
    elif args.input_type in ["pdf", "docx"]:
        success = copy_file(args.input_path, output_path)

    if success:
        print(f"SAVED:{output_path}")
        print(f"FILENAME:{filename}")
        sys.exit(0)
    else:
        print(f"ERROR: Failed to save job posting", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
