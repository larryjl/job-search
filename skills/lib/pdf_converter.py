"""PDF conversion utilities for web pages."""

import asyncio
import subprocess
import os


def url_to_pdf_weasyprint(html_text, base_url, output_path):
    """
    Convert HTML to PDF using weasyprint (primary method).

    Args:
        html_text (str): Raw HTML content
        base_url (str): Base URL for resolving relative assets
        output_path (str): Path to save the PDF

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from weasyprint import HTML

        HTML(string=html_text, base_url=base_url).write_pdf(output_path)
        return True
    except ImportError:
        subprocess.run(
            ["pip", "install", "weasyprint", "--break-system-packages", "-q"],
            check=False,
        )
        try:
            from weasyprint import HTML
            HTML(string=html_text, base_url=base_url).write_pdf(output_path)
            return True
        except Exception:
            return False
    except Exception:
        return False


async def url_to_pdf_playwright(url, output_path):
    """
    Convert a URL to PDF using Playwright (fallback method).

    Args:
        url (str): URL to convert
        output_path (str): Path to save the PDF

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await page.pdf(path=output_path, format="A4", print_background=True)
            await browser.close()
        return True
    except ImportError:
        subprocess.run(
            ["pip", "install", "playwright", "--break-system-packages", "-q"],
            check=False,
        )
        subprocess.run(
            ["python", "-m", "playwright", "install", "chromium"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.pdf(path=output_path, format="A4", print_background=True)
                await browser.close()
            return True
        except Exception:
            return False
    except Exception:
        return False


def url_to_pdf(html_text=None, url=None, base_url=None, output_path="/tmp/job_raw.pdf"):
    """
    Convert HTML or URL to PDF, with fallback strategy.

    Primary: weasyprint (fast, HTML-based)
    Fallback: Playwright (handles JS-heavy pages)

    Args:
        html_text (str, optional): Raw HTML content (for weasyprint)
        url (str, optional): URL to convert (for Playwright fallback)
        base_url (str, optional): Base URL for resolving relative assets
        output_path (str): Path to save the PDF, defaults to /tmp/job_raw.pdf

    Returns:
        bool: True if conversion successful, False otherwise
    """
    # Try weasyprint first if HTML is provided
    if html_text:
        if url_to_pdf_weasyprint(html_text, base_url or "https://example.com", output_path):
            # Check if file is not empty (< 5KB might indicate blank page)
            if os.path.getsize(output_path) > 5000:
                return True

    # Fallback to Playwright if weasyprint failed or HTML not provided
    if url:
        try:
            return asyncio.run(url_to_pdf_playwright(url, output_path))
        except Exception:
            return False

    return False
