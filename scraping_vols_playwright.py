from playwright.sync_api import sync_playwright
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from price import get_average_price
from data_export import PriceDataExporter, create_export_data
from visualizations import PriceVisualizer
from notifications import PriceAlertSystem, create_alert_summary
import logging

# Load environment variables
load_dotenv()

# Configuration
SBR_WS_CDP = os.getenv('BRIGHTDATA_WS_CDP')
PRICE_ALERT_THRESHOLD = float(os.getenv('PRICE_ALERT_THRESHOLD', 150))

# Timeouts configuration (in milliseconds)
TIMEOUT_DEFAULT = 10000        # Default timeout for page operations
TIMEOUT_PAGE_LOAD = 30000      # Page navigation timeout
TIMEOUT_SHORT_WAIT = 500       # Short wait between actions
TIMEOUT_MONTH_SELECT = 2000    # Month selector timeout
TIMEOUT_FLIGHT_LINK = 3000     # Flight results link timeout
TIMEOUT_NEW_PAGE = 5000        # New page opening timeout
TIMEOUT_PRICE_LOAD = 5000      # Price elements loading timeout

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run(pw, depart: str, arrive: str, bright_data: bool = False, headless: bool = False):
    logger.info("Connecting to Scraping Browser")
    if bright_data:
        if not SBR_WS_CDP:
            raise ValueError("BRIGHTDATA_WS_CDP environment variable not set")
        browser = pw.chromium.connect_over_cdp(SBR_WS_CDP)
    else:
        browser = pw.chromium.launch(headless=headless)

    context = browser.new_context()
    context.set_default_timeout(TIMEOUT_DEFAULT)
    page = context.new_page()

    # Initialize variable to avoid scope issues
    html_content = None

    # Store all months data for export
    all_months_data = []

    url = 'https://www.kayak.fr'
    logger.info(f"Navigating to {url}")
    page.goto(url, wait_until='domcontentloaded', timeout=TIMEOUT_PAGE_LOAD)

    # Click on search type selector - use more robust selectors
    try:
        page.locator('[class*="neb-item-value"]').click()
    except Exception as e:
        logger.warning(f"Could not click neb-item-value: {e}, trying alternative")
        page.locator('div[class*="_6"]').first.click()

    # Fill departure
    page.get_by_placeholder("De ?").fill(depart)
    page.wait_for_timeout(TIMEOUT_SHORT_WAIT)
    page.locator("ul[role='listbox'] li").first.click()

    # Click world selector
    page.locator('div:has-text("Monde entier")').click()

    # Fill arrival
    page.get_by_placeholder("À ?").fill(arrive)
    page.wait_for_timeout(TIMEOUT_SHORT_WAIT)
    page.locator("ul[role='listbox']").nth(1).locator('li').first.click()
    page.wait_for_timeout(TIMEOUT_SHORT_WAIT)
    page.locator('span._i5z button[aria-label="Lancer la recherche"]').click()
    page.wait_for_timeout(1000)  # Wait for search results to load
    today = datetime.today()

    month_map = {
        "jan.": "janv.",
        "feb.": "févr.",
        "mar.": "mars",
        "apr.": "avr.",
        "may.": "mai",
        "jun.": "juin",
        "jul.": "juil.",
        "aug.": "août",
        "sep.": "sept.",
        "oct.": "oct.",
        "nov.": "nov.",
        "dec.": "déc.",
    }

    for i in range(1, 13):
        next_month = today + relativedelta(months=i, day=1)
        next_month_str = next_month.strftime("%b.").lower()
        logger.info(f"Processing month {i}/12: {next_month_str}")

        try:
            page.wait_for_selector('[data-placeholder="Aller"]', timeout=TIMEOUT_MONTH_SELECT)
            page.locator('[data-placeholder="Aller"]').click()
            page.get_by_title("Période").click()
            page.wait_for_timeout(TIMEOUT_SHORT_WAIT)

            # Try to find month selector
            try:
                page.wait_for_selector(f'[title="{next_month_str}"]', timeout=TIMEOUT_MONTH_SELECT)
                page.get_by_title(next_month_str).click()
            except Exception:
                # Fallback to month without accent
                next_month_str_no_accent = month_map.get(next_month_str, next_month_str)
                logger.debug(f"Month {next_month_str} not found, trying {next_month_str_no_accent}")
                page.get_by_title(next_month_str_no_accent).click()

        except Exception as e:
            logger.error(f"Failed to select month {next_month_str}: {type(e).__name__}: {e}")
            continue

        try:
            # Wait for flight results link
            page.wait_for_selector('[name="Voir les prix des vols"]', timeout=TIMEOUT_FLIGHT_LINK)
            page.get_by_role("link", name="Voir les prix des vols").click()

            # Wait for new page to open
            new_page = context.wait_for_event("page", timeout=TIMEOUT_NEW_PAGE)
            new_page.wait_for_selector('div.f8F1-price-text', timeout=TIMEOUT_PRICE_LOAD)

            html_content = new_page.content()
            price_data = get_average_price(html_content, next_month_str, depart, arrive)

            # Add month name to data
            price_data['month'] = next_month_str
            all_months_data.append(price_data)

            logger.info(f"✓ {next_month_str}: Average {price_data['average']} {price_data['currency']}")
            new_page.close()

        except TimeoutError as e:
            logger.warning(f"⏱ Timeout waiting for flights for {next_month_str}")
            continue
        except Exception as e:
            logger.error(f"✗ Error getting flights for {next_month_str}: {type(e).__name__}: {e}")
            continue

        # Return to search to continue with next month
        page.wait_for_timeout(TIMEOUT_SHORT_WAIT)
        page.get_by_title("Lancer la recherche").click()
        page.wait_for_timeout(1000)  # Wait for search page to reload

    # Debug: print last page content if available
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        logger.debug(f"Last page content: {soup.prettify()[:200]}...")
    else:
        logger.warning("No HTML content was captured during scraping")

    browser.close()

    # Export data to JSON and CSV
    if all_months_data:
        logger.info(f"\n{'='*50}")
        logger.info(f"Exporting data for {len(all_months_data)} months...")

        # Prepare export data
        export_data = create_export_data(depart, arrive, all_months_data)

        # Export to JSON/CSV
        exporter = PriceDataExporter()
        files = exporter.export_all(export_data)

        logger.info(f"✓ JSON: {files['json']}")
        logger.info(f"✓ CSV: {files['csv']}")

        # Generate visualizations
        logger.info(f"\nGenerating charts...")
        visualizer = PriceVisualizer()
        charts = visualizer.generate_all_charts(export_data)

        for chart_type, path in charts.items():
            if path:
                logger.info(f"✓ {chart_type.upper()}: {path}")

        # Check for price alerts
        logger.info(f"\nChecking price alerts (threshold: {PRICE_ALERT_THRESHOLD} EUR)...")
        alert_system = PriceAlertSystem(PRICE_ALERT_THRESHOLD)
        alerts = alert_system.check_prices(export_data)

        if alerts:
            alert_file = alert_system.save_alerts()
            logger.info(f"✓ ALERTS: {alert_file}")

        # Print summary
        summary = create_alert_summary(export_data, PRICE_ALERT_THRESHOLD)
        print(summary)

        logger.info(f"{'='*50}\n")

    logger.info("Scraping completed successfully")

    return all_months_data

if __name__ == '__main__':
    with sync_playwright() as p:
        run(pw=p, 
            depart= "Madrid",
            arrive= "Paris",
            bright_data=False,
            headless=False)

