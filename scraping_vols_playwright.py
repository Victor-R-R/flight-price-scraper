from playwright.sync_api import sync_playwright, Page
from datetime import datetime
import os
import csv
from dotenv import load_dotenv
from price import extract_flights
import logging

# Load environment variables
load_dotenv()

# Configuration
SBR_WS_CDP = os.getenv('BRIGHTDATA_WS_CDP')
PRICE_ALERT_THRESHOLD = float(os.getenv('PRICE_ALERT_THRESHOLD', 150))
DEBUG_SCREENSHOTS = os.getenv('DEBUG_SCREENSHOTS', 'false').lower() == 'true'

# Timeouts (milliseconds)
TIMEOUT_DEFAULT = 10000
TIMEOUT_PAGE_LOAD = 30000
TIMEOUT_ACTION = 500

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# === HELPER FUNCTIONS ===

def safe_screenshot(page: Page, name: str):
    """Take screenshot only if DEBUG_SCREENSHOTS enabled"""
    if DEBUG_SCREENSHOTS:
        try:
            page.screenshot(path=f"/tmp/kayak_{name}.png", full_page=True)
            logger.debug(f"Screenshot: /tmp/kayak_{name}.png")
        except Exception:
            pass


def handle_popup(page: Page, selector: str, description: str, timeout: int = 5000):
    """Generic popup handler with error suppression"""
    try:
        page.locator(selector).click(timeout=timeout)
        page.wait_for_timeout(TIMEOUT_ACTION)
        logger.info(f"✓ {description}")
        return True
    except Exception:
        return False


def fill_location(page: Page, location: str, field_type: str):
    """Unified location filling (departure/arrival)"""
    field_map = {
        "departure": ('input[placeholder="De…"], input[aria-label*="départ"]', "Paris (PAR)"),
        "arrival": ('input[placeholder="À\u2026"]', None)
    }

    selector, default_value = field_map[field_type]
    logger.info(f"Filling {field_type}: {location}")

    try:
        # Remove default value if exists
        if default_value:
            try:
                page.locator('div:has-text("Paris (PAR)") button').first.click(timeout=3000)
                page.wait_for_timeout(TIMEOUT_ACTION)
            except Exception:
                pass

        # Fill location
        page.locator(selector).first.click(timeout=5000)
        page.wait_for_timeout(300)
        page.keyboard.type(location)
        page.wait_for_timeout(1500)

        # Select first suggestion
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(200)
        page.keyboard.press("Enter")
        page.wait_for_timeout(TIMEOUT_ACTION)

        logger.info(f"✓ {field_type.capitalize()} set")
        return True

    except Exception as e:
        logger.error(f"Failed to fill {field_type}: {e}")
        safe_screenshot(page, f"{field_type}_error")
        raise

def configure_passengers(page: Page, adults: int = 2, children: int = 1, child_age: int = 7):
    """Configure passenger count and ages"""
    logger.info(f"Configuring passengers: {adults} adults + {children} child(ren)")
    try:
        page.get_by_text("1 adulte, Économique").click(timeout=5000)
        page.wait_for_timeout(1000)

        # Add adults
        for _ in range(adults - 1):
            page.locator('.FkqV-inner:has-text("Adultes")').locator('.T_3c button[aria-label="Plus"]').click(timeout=5000)
            page.wait_for_timeout(300)

        # Add children (2-11 ans)
        # Target the specific FkqV-inner that contains "2-11 ans"
        for _ in range(children):
            page.locator('.FkqV-inner:has-text("2-11 ans")').locator('.T_3c button[aria-label="Plus"]').click(timeout=5000)
            page.wait_for_timeout(300)

        # Set child age if applicable
        if children > 0:
            try:
                page.locator('input[aria-label*="âge"], select[aria-label*="âge"]').first.fill(str(child_age))
                page.wait_for_timeout(TIMEOUT_ACTION)
            except Exception:
                pass

        page.keyboard.press("Escape")
        logger.info(f"✓ Passengers: {adults} adults + {children} child(ren)")
        return True

    except Exception as e:
        logger.warning(f"Could not configure passengers: {e}")
        return False


def select_dates(page: Page, start_date: datetime, end_date: datetime):
    """Select travel dates in calendar"""
    logger.info(f"Selecting dates: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}")
    try:
        page.wait_for_timeout(1500)  # Wait for calendar auto-open

        # Calculate months to navigate forward
        today = datetime.today()
        months_diff = (start_date.year - today.year) * 12 + (start_date.month - today.month)

        # Navigate to target month
        for i in range(months_diff):
            page.locator('div[aria-label="Mois suivant"]').click(timeout=5000)
            page.wait_for_timeout(600)
            logger.info(f"  → Month navigation ({i+1}/{months_diff})")

        # Select days
        page.get_by_text(str(start_date.day), exact=True).first.click(timeout=5000)
        page.wait_for_timeout(800)
        page.get_by_text(str(end_date.day), exact=True).first.click(timeout=5000)
        page.wait_for_timeout(800)

        logger.info("✓ Dates selected")
        return True

    except Exception as e:
        logger.warning(f"Could not select dates: {e}")
        safe_screenshot(page, "date_error")
        return False


def run(pw, depart: str, arrive: str, bright_data: bool = False, headless: bool = False,
        start_date: datetime = None, end_date: datetime = None):
    """Main scraping function"""
    logger.info("Initializing browser...")

    # Default dates if not provided
    if not start_date:
        start_date = datetime(2026, 7, 1)
    if not end_date:
        end_date = datetime(2026, 7, 31)

    # Browser setup
    if bright_data:
        if not SBR_WS_CDP:
            raise ValueError("BRIGHTDATA_WS_CDP not set")
        browser = pw.chromium.connect_over_cdp(SBR_WS_CDP)
    else:
        browser = pw.chromium.launch(headless=headless)

    context = browser.new_context()
    context.set_default_timeout(TIMEOUT_DEFAULT)
    page = context.new_page()
    all_months_data = []

    try:
        # Navigate to Kayak
        url = 'https://www.kayak.fr'
        logger.info(f"Navigating to {url}")
        page.goto(url, wait_until='domcontentloaded', timeout=TIMEOUT_PAGE_LOAD)
        page.wait_for_load_state('load')
        page.wait_for_timeout(1000)

        # Handle cookie popup
        handle_popup(page, 'div.RxNS-button-content:has-text("Tout accepter")', "Cookie consent")
        safe_screenshot(page, "after_cookies")

        # Fill search form
        fill_location(page, depart, "departure")
        fill_location(page, arrive, "arrival")
        select_dates(page, start_date, end_date)
        configure_passengers(page)

        # Launch search
        safe_screenshot(page, "before_search")
        logger.info("Launching search...")
        page.get_by_role("button", name="Rechercher").click()
        page.wait_for_timeout(5000)  # Wait for results

        # Scrape top 5 flights from search results
        logger.info("Extracting top 5 flights...")
        try:
            # Wait for flight results - essayer plusieurs sélecteurs (Layout B ou A)
            logger.info("Waiting for flight results to load...")
            selectors_to_try = [
                '[data-testid="searchresults_card"]',  # Layout B (Booking.com)
                '.yuAt.yuAt-pres-rounded',  # Layout A (Kayak classique)
                '[role="link"]',  # Fallback générique
            ]

            results_loaded = False
            for selector in selectors_to_try:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    logger.info(f"✓ Flight results loaded (selector: {selector})")
                    results_loaded = True
                    break
                except:
                    continue

            if not results_loaded:
                raise TimeoutError("No flight results found with any selector")

            page.wait_for_timeout(3000)  # Let results stabilize
            safe_screenshot(page, "final_results")

            # Debug: sauvegarder le HTML pour inspection si besoin
            if DEBUG_SCREENSHOTS:
                html_content = page.content()
                with open(f"/tmp/kayak_results_{depart}_{arrive}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.debug(f"HTML sauvegardé: /tmp/kayak_results_{depart}_{arrive}.html")

            # Extract top 5 flights via Playwright
            flights = extract_flights(page, count=5)

            if not flights:
                raise ValueError("No flights extracted")

            # Ajouter l'URL de la page de résultats (même URL pour tous les vols)
            # Sur Booking.com, l'URL spécifique de réservation se génère dynamiquement
            # après sélection interactive - on fournit l'URL de recherche
            logger.info("Adding search results URL to flights...")
            search_url = page.url
            for i in range(len(flights)):
                flights[i]['url'] = search_url
            logger.info(f"✓ URL de recherche ajoutée aux {len(flights)} vols")

            all_months_data = flights  # Store for export
            logger.info(f"✓ Extracted {len(flights)} flights with URLs")

        except TimeoutError:
            logger.error("⏱ Timeout waiting for flight results")
            safe_screenshot(page, "price_timeout")
        except Exception as e:
            logger.error(f"✗ Error extracting flights: {e}")
            safe_screenshot(page, "scraping_error")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        safe_screenshot(page, "fatal_error")
        raise
    finally:
        browser.close()

    # Export results to CSV
    if all_months_data:
        logger.info(f"\n{'='*50}")
        logger.info("Exporting flight data to CSV...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"vols_{depart}_{arrive}_{timestamp}.csv"

        # CSV columns
        fieldnames = [
            'rang', 'prix_eur', 'compagnie',
            'aller_depart', 'aller_arrivee',
            'retour_depart', 'retour_arrivee',
            'escales_aller', 'escales_retour',
            'duree_aller', 'duree_retour',
            'url_reservation'
        ]

        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i, flight in enumerate(all_months_data, start=1):
                writer.writerow({
                    'rang': i,
                    'prix_eur': flight.get('price', 0),
                    'compagnie': flight.get('airline', 'N/A'),
                    'aller_depart': flight.get('dep_time_out', 'N/A'),
                    'aller_arrivee': flight.get('arr_time_out', 'N/A'),
                    'retour_depart': flight.get('dep_time_ret', 'N/A'),
                    'retour_arrivee': flight.get('arr_time_ret', 'N/A'),
                    'escales_aller': flight.get('stops_out', 'N/A'),
                    'escales_retour': flight.get('stops_ret', 'N/A'),
                    'duree_aller': flight.get('duration_out', 'N/A'),
                    'duree_retour': flight.get('duration_ret', 'N/A'),
                    'url_reservation': flight.get('url', 'N/A')
                })

        logger.info(f"✓ Saved: {csv_file}")

        # Print summary table
        print(f"\n{'='*100}")
        print(f"TOP 5 FLIGHTS: {depart} → {arrive}")
        print(f"Period: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
        print(f"{'='*100}")
        print(f"{'Rang':<6} {'Prix':<8} {'Compagnie':<20} {'Aller':<15} {'Retour':<15} {'URL':<30}")
        print(f"{'-'*100}")

        for i, flight in enumerate(all_months_data, start=1):
            price = f"{flight.get('price', 0)}€"
            airline = flight.get('airline', 'N/A')[:18]
            dep_out = flight.get('dep_time_out', 'N/A')
            arr_out = flight.get('arr_time_out', 'N/A')
            aller = f"{dep_out}->{arr_out}"
            dep_ret = flight.get('dep_time_ret', 'N/A')
            arr_ret = flight.get('arr_time_ret', 'N/A')
            retour = f"{dep_ret}->{arr_ret}"
            url = flight.get('url', 'N/A')[:28]

            print(f"{i:<6} {price:<8} {airline:<20} {aller:<15} {retour:<15} {url:<30}")

        print(f"{'='*100}\n")
        logger.info(f"{'='*50}\n")

    logger.info("✓ Scraping complete")
    return all_months_data

if __name__ == '__main__':
    with sync_playwright() as p:
        run(
            pw=p,
            depart="Paris",
            arrive="Malaga",
            bright_data=False,
            headless=False,
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2026, 7, 31)
        )

