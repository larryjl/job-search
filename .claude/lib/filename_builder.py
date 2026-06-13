"""Filename normalization for job postings."""

from datetime import date
import re


def make_filename(company, title, ext="pdf"):
    """
    Build a normalized job posting filename.

    Args:
        company (str): Company name
        title (str): Job title
        ext (str): File extension ('pdf' or 'docx'), defaults to 'pdf'

    Returns:
        str: Normalized filename (e.g., 'acme-corp_senior-software-engineer_2026-04-21.pdf')
    """
    today = date.today().strftime("%Y-%m-%d")

    def clean(s):
        """Normalize string: lowercase, replace spaces with hyphens, remove special chars."""
        s = s.strip().lower().replace(" ", "-")
        # Keep word chars and hyphens only
        s = re.sub(r'[^\w\-]', '', s)
        return s

    return f"{clean(company)}_{clean(title)}_{today}.{ext}"
