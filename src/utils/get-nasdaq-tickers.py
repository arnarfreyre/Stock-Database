from playwright.sync_api import sync_playwright
from pathlib import Path
import pandas as pd

""" -------Clean Tickers Directory-------"""
directory = Path('/Users/arnarfreyrerlingsson/Desktop/Afleiður-Working/Src/Data')

# Clean existing files
for file in directory.iterdir():
    file.unlink()

# Create directory if it doesn't exist
directory.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    # Launch browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()

    # Navigate to your website
    page.goto("https://www.nasdaq.com/market-activity/stocks/screener?page=1&rows_per_page=25")

    # Wait for the page to load
    page.wait_for_load_state("networkidle")

    # Handle cookie consent popup
    try:
        # Wait for the cookie banner -> click "I Accept"
        accept_button = page.locator("#onetrust-accept-btn-handler")
        if accept_button.is_visible():
            print("Cookie consent popup found, clicking 'I Accept'...")
            accept_button.click()
    except:
        print("No cookie consent popup found or already accepted")

    # The download button selector
    download_button_selector = "button.jupiter22-c-table__download-csv"

    # Wait for the download button to be visible
    page.wait_for_selector(download_button_selector, state="visible", timeout=1000)

    # Start waiting for download before clicking
    with page.expect_download() as download_info:
        page.click(download_button_selector)

    download = download_info.value

    # Save to specific directory
    download_path = directory / f"nasdaq_screener.csv"
    download.save_as(str(download_path))
    print(f"Downloaded to: {download_path}")

    browser.close()

    # Filter columns to keep only Symbol, Name, Sector, and Industry
    print("Filtering columns...")
    df = pd.read_csv(download_path)

    # Keep only the desired columns
    columns_to_keep = ['Symbol', 'Name', 'Sector', 'Industry']
    df_filtered = df[columns_to_keep]

    # Save the filtered data back to the same file
    df_filtered.to_csv(download_path, index=False)
    print(f"Filtered data saved. Kept columns: {', '.join(columns_to_keep)}")