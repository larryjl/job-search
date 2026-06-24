"""
PDF conversion utilities for web pages.

Two conversion methods are provided, used in a primary/fallback strategy:

Primary — url_to_pdf_weasyprint:
    Converts raw HTML text to PDF using the weasyprint library. Fast and
    reliable for static or server-rendered pages. Does not execute JavaScript.
    If weasyprint is not installed, it is auto-installed via pip and retried.

Fallback — url_to_pdf_playwright:
    Drives a real Chromium browser (via Playwright) to load a URL and print
    it to PDF. Handles JavaScript-rendered content that weasyprint cannot see.
    Slower and heavier; used only when weasyprint fails or produces an
    undersized file. If Playwright is not installed, it is auto-installed.

Orchestrator — url_to_pdf:
    Calls weasyprint first (when HTML is available). If the resulting PDF is
    suspiciously small (< 5 KB — typically a blank or near-empty page caused
    by a JS-rendered layout that weasyprint couldn't render), it falls back to
    Playwright against the original URL. Returns True on success, False if
    both methods fail.
"""

import asyncio
import subprocess
import os


def url_to_pdf_weasyprint(html_text: str, base_url: str, output_path: str) -> bool:
    """
    Convert HTML to PDF using weasyprint (primary method).

    weasyprint renders HTML/CSS to PDF without a browser. It does not execute
    JavaScript, so it works well for static pages and ATS job postings that
    are server-rendered. The base_url is used to resolve relative URLs in the
    HTML (e.g. stylesheets or images referenced with a relative path).

    If weasyprint is not installed, this function attempts to install it
    automatically via pip and then retries the conversion. This auto-install
    fallback lets skill scripts work in fresh environments without requiring
    the user to pre-install dependencies.

    Args:
        html_text (str): Raw HTML content to convert
        base_url (str): Base URL for resolving relative assets in the HTML
        output_path (str): Filesystem path where the PDF should be saved

    Returns:
        bool: True if the PDF was written successfully, False otherwise
    """
    try:
        from weasyprint import HTML

        # weasyprint parses the HTML string and renders it using the provided
        # base_url to resolve any relative hrefs, src attributes, etc.
        HTML(string=html_text, base_url=base_url).write_pdf(output_path)
        return True

    except ImportError:
        # weasyprint is not installed — try to install it silently, then retry.
        # --break-system-packages is needed on systems with externally-managed
        # Python environments (e.g. Debian/Ubuntu with system pip).
        subprocess.run(
            ["pip", "install", "weasyprint", "--break-system-packages", "-q"],
            check=False,  # don't raise if pip itself fails — we'll catch it below
        )
        try:
            # Re-import after installation; this will succeed if pip worked.
            from weasyprint import HTML
            HTML(string=html_text, base_url=base_url).write_pdf(output_path)
            return True
        except Exception:
            # Installation or conversion still failed — signal failure to caller.
            return False

    except Exception:
        # Catch weasyprint rendering errors (e.g. malformed HTML, CSS errors).
        return False


async def url_to_pdf_playwright(url: str, output_path: str) -> bool:
    """
    Convert a live URL to PDF using Playwright / Chromium (fallback method).

    Playwright launches a real Chromium browser, navigates to the URL, waits
    for the page to fully load, and prints it to PDF. This handles pages that
    rely on JavaScript to render their content — something weasyprint cannot do.

    wait_until="networkidle" tells Playwright to wait until there are no more
    than 2 in-flight network requests for at least 500ms. This ensures that
    JS-driven content (e.g. React or Vue apps) has finished fetching data and
    rendering before the PDF is captured.

    format="A4" is used instead of "Letter" because Playwright's PDF output
    defaults to A4 in headless Chromium, and A4 (210×297mm) produces consistent
    margins across platforms. Using a consistent format prevents layout shifts
    when the same PDF is opened on different systems.

    If Playwright is not installed, this function installs it (along with the
    Chromium browser binary) and retries — same auto-install pattern as
    url_to_pdf_weasyprint.

    Args:
        url (str): The full URL to load in the browser
        output_path (str): Filesystem path where the PDF should be saved

    Returns:
        bool: True if the PDF was written successfully, False otherwise
    """
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            # Launch headless Chromium (no visible browser window)
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # Navigate and wait until the page is network-idle (JS has finished
            # loading dynamic content). timeout=60000ms = 60s hard cap.
            await page.goto(url, wait_until="networkidle", timeout=60000)

            # Print to PDF in A4 format with background colours/images included.
            # print_background=True is required to capture coloured headers and
            # company branding that use CSS background-color or background-image.
            await page.pdf(path=output_path, format="A4", print_background=True)

            await browser.close()
        return True

    except ImportError:
        # Playwright Python package not installed — install it along with the
        # Chromium browser binary that it manages.
        subprocess.run(
            ["pip", "install", "playwright", "--break-system-packages", "-q"],
            check=False,
        )
        # Install the Chromium browser binary (separate step required by Playwright).
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


def url_to_pdf(
    html_text: str = None,
    url: str = None,
    base_url: str = None,
    output_path: str = "/tmp/job_raw.pdf",
) -> bool:
    """
    Convert HTML or a URL to PDF, trying weasyprint first and Playwright as fallback.

    Strategy:
        1. If html_text is provided, try weasyprint (fast, no browser required).
        2. Check the output file size. A PDF smaller than 5 000 bytes is almost
           certainly a blank or near-blank page — this happens when the page's
           visible content is rendered by JavaScript and weasyprint (which does
           not run JS) captured only an empty shell. In that case, fall through
           to Playwright even if weasyprint reported success.
        3. If weasyprint failed, produced an undersized file, or no html_text was
           provided, try Playwright against the original URL (runs JS, so it sees
           the fully-rendered page).

    The 5 000-byte threshold (5 KB) was chosen empirically: a minimal PDF with
    one line of text is roughly 1–2 KB, while a real job posting with content is
    typically 50 KB or more. Any file under 5 KB almost always indicates a
    rendering failure rather than a genuinely short document.

    Args:
        html_text (str, optional): Raw HTML content for weasyprint
        url (str, optional): Live URL for Playwright fallback
        base_url (str, optional): Base URL for resolving relative assets in HTML
        output_path (str): Destination path for the PDF (default: /tmp/job_raw.pdf)

    Returns:
        bool: True if a PDF was successfully produced, False if both methods failed
    """
    # --- Primary path: weasyprint from HTML string ---
    if html_text:
        if url_to_pdf_weasyprint(html_text, base_url or "https://example.com", output_path):
            # Sanity-check the output size. A PDF under 5 KB almost always means
            # weasyprint rendered a blank page (JS-dependent content was invisible
            # to it). Fall through to Playwright if this is the case.
            if os.path.getsize(output_path) > 5000:
                return True
            # File is suspiciously small — fall through to Playwright below.

    # --- Fallback path: Playwright (full browser, runs JavaScript) ---
    if url:
        try:
            return asyncio.run(url_to_pdf_playwright(url, output_path))
        except Exception:
            return False

    # No html_text and no url — nothing to convert.
    return False
