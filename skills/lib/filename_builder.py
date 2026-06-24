"""
Filename normalisation for job-search output files.

This module is the single source of truth for how output filenames are built.
Every skill that saves a file (postings, resumes, cover letters, reports, etc.)
must call make_filename() rather than constructing paths inline.  This ensures
consistent naming across the entire project and makes files easy to glob.

Convention (from CLAUDE.md):
    <company>_<role>_<YYYY-MM-DD>.<ext>

where company and role are lowercase with words joined by hyphens, and special
characters are stripped.  Example:

    make_filename("Acme Corp", "Senior Data Engineer", "docx")
    → "acme-corp_senior-data-engineer_2026-06-22.docx"
"""

from datetime import date
import re


def make_filename(company: str, title: str, ext: str = "pdf") -> str:  # ext defaults to "pdf" — postings are the most common output format and are always PDFs
    """
    Build a normalised job output filename from company, role, and extension.

    The filename encodes today's date so that files from different scouting
    sessions don't collide.  Both company and title are scrubbed to lowercase
    hyphenated slugs, stripping punctuation that would break filesystem paths.

    Args:
        company (str): Company name as it appears in the job posting
                       (e.g. "Acme Corp.", "TD Bank").
        title   (str): Job title from the posting
                       (e.g. "Senior Data Engineer").
        ext     (str): File extension without the leading dot, defaults to "pdf".
                       Common values: "pdf", "docx", "md".

    Returns:
        str: Normalised filename ready to be joined with a directory path.
             Example: "acme-corp_senior-data-engineer_2026-06-22.pdf"
    """
    # Stamp today's date in ISO format; included in every filename so that
    # multiple runs on different days produce distinct files.
    today = date.today().strftime("%Y-%m-%d")

    # Private helper: only serves make_filename and doesn't need to be
    # accessible anywhere else, so it's defined as a nested function here.
    def clean(s: str) -> str:
        """
        Normalise a free-form string into a lowercase hyphenated slug.

        Steps:
          1. Strip leading/trailing whitespace.
          2. Lowercase everything.
          3. Replace spaces with hyphens (so "Data Engineer" → "data-engineer").
          4. Remove any character that is not a word character (\w) or hyphen,
             so punctuation like ".", ",", "&", "/" is dropped.

        Args:
            s (str): Raw string to normalise.

        Returns:
            str: Slug suitable for use in a filename.
        """
        s = s.strip().lower().replace(" ", "-")
        # `^` inside [...] negates the character class — so [^\w\-] matches
        # everything that is NOT a word character (\w = [a-zA-Z0-9_]) or a
        # hyphen. re.sub removes all those characters.
        # Example: "Hello World!" → after replace(" ","-") → "Hello-World!"
        #          → after re.sub → "Hello-World"  (the "!" is stripped)
        s = re.sub(r"[^\w\-]", "", s)
        return s

    # Pattern: <company-slug>_<role-slug>_<date>.<ext>
    # Example: "td-bank_senior-analyst_2026-06-22.pdf"
    return f"{clean(company)}_{clean(title)}_{today}.{ext}"
