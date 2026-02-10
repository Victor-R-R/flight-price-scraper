from playwright.sync_api import sync_playwright, Page
from datetime import datetime
import os
import csv
from dotenv import load_dotenv
from price import extract_flights
import logging
import subprocess

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


def generate_html_report(flights: list, depart: str, arrive: str, start_date: datetime, end_date: datetime) -> str:
    """
    Generate elegant HTML report from flight data

    Args:
        flights: List of flight dictionaries
        depart: Departure city
        arrive: Arrival city
        start_date: Start date
        end_date: End date

    Returns:
        Path to generated HTML file
    """
    if not flights:
        return None

    # Calculate statistics
    prices = [f['price'] for f in flights if f.get('price', 0) > 0]
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    best_deal = min(flights, key=lambda x: x.get('price', float('inf')))

    # Ensure reports directory exists
    os.makedirs('reports', exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = f"reports/vols_{depart}_{arrive}_{timestamp}.html"

    # Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Vols {depart} → {arrive}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .route {{
            font-size: 1.5em;
            font-weight: 300;
            opacity: 0.95;
        }}
        .period {{
            font-size: 1em;
            margin-top: 10px;
            opacity: 0.9;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-label {{
            font-size: 0.85em;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }}
        .best-deal {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 25px 40px;
            margin: 20px 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
        }}
        .best-deal-label {{
            font-size: 1.2em;
            font-weight: 600;
        }}
        .best-deal-info {{
            text-align: right;
        }}
        .best-deal-price {{
            font-size: 2.5em;
            font-weight: 800;
        }}
        .best-deal-company {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .table-container {{
            padding: 40px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }}
        thead {{
            background: #667eea;
            color: white;
        }}
        th {{
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        tbody tr {{
            border-bottom: 1px solid #e9ecef;
            transition: all 0.2s ease;
        }}
        tbody tr:hover {{
            background: #f8f9fa;
            transform: scale(1.01);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        td {{
            padding: 15px 12px;
        }}
        .rank {{
            font-weight: 700;
            color: #667eea;
            font-size: 1.1em;
        }}
        .price {{
            font-weight: 700;
            font-size: 1.3em;
            color: #11998e;
        }}
        .price::after {{
            content: "€";
            margin-left: 2px;
            font-size: 0.8em;
        }}
        .company {{
            font-weight: 600;
            color: #495057;
        }}
        .time {{
            color: #6c757d;
            font-family: 'Courier New', monospace;
        }}
        .direct {{
            background: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .stops {{
            background: #fff3cd;
            color: #856404;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .duration {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .url {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .url:hover {{
            text-decoration: underline;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
            background: #f8f9fa;
        }}
        .medal {{
            font-size: 1.5em;
            margin-right: 5px;
        }}
        @media (max-width: 768px) {{
            .header h1 {{ font-size: 1.8em; }}
            .stats {{ grid-template-columns: 1fr; }}
            .best-deal {{
                flex-direction: column;
                text-align: center;
                gap: 15px;
            }}
            .best-deal-info {{ text-align: center; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ Rapport de Prix des Vols</h1>
            <div class="route">{depart} → {arrive}</div>
            <div class="period">{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Vols analysés</div>
                <div class="stat-value">{len(flights)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Prix moyen</div>
                <div class="stat-value">{int(avg_price)}€</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Prix minimum</div>
                <div class="stat-value">{min_price}€</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Prix maximum</div>
                <div class="stat-value">{max_price}€</div>
            </div>
        </div>

        <div class="best-deal">
            <div>
                <span class="medal">🏆</span>
                <span class="best-deal-label">Meilleure offre</span>
            </div>
            <div class="best-deal-info">
                <div class="best-deal-price">{best_deal.get('price', 0)}€</div>
                <div class="best-deal-company">{best_deal.get('airline', 'N/A')}</div>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Rang</th>
                        <th>Prix</th>
                        <th>Compagnie</th>
                        <th>Départ Aller</th>
                        <th>Arrivée Aller</th>
                        <th>Départ Retour</th>
                        <th>Arrivée Retour</th>
                        <th>Escales Aller</th>
                        <th>Escales Retour</th>
                        <th>Durée Aller</th>
                        <th>Durée Retour</th>
                        <th>Réservation</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Add flight rows
    for i, flight in enumerate(flights, start=1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else ""

        stops_out = flight.get('stops_out', 'N/A')
        stops_ret = flight.get('stops_ret', 'N/A')
        escales_aller_class = "direct" if "direct" in stops_out.lower() else "stops"
        escales_retour_class = "direct" if "direct" in stops_ret.lower() else "stops"

        html_content += f"""                    <tr>
                        <td class="rank">{medal} {i}</td>
                        <td class="price">{flight.get('price', 0)}</td>
                        <td class="company">{flight.get('airline', 'N/A')}</td>
                        <td class="time">{flight.get('dep_time_out', 'N/A')}</td>
                        <td class="time">{flight.get('arr_time_out', 'N/A')}</td>
                        <td class="time">{flight.get('dep_time_ret', 'N/A')}</td>
                        <td class="time">{flight.get('arr_time_ret', 'N/A')}</td>
                        <td><span class="{escales_aller_class}">{stops_out}</span></td>
                        <td><span class="{escales_retour_class}">{stops_ret}</span></td>
                        <td class="duration">{flight.get('duration_out', 'N/A')}</td>
                        <td class="duration">{flight.get('duration_ret', 'N/A')}</td>
                        <td><a href="{flight.get('url', '#')}" target="_blank" class="url">Réserver →</a></td>
                    </tr>
"""

    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    html_content += f"""                </tbody>
            </table>
        </div>

        <div class="footer">
            Rapport généré le {now} | Données depuis Kayak.fr
        </div>
    </div>
</body>
</html>
"""

    # Save HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"✓ Rapport HTML généré : {html_file}")
    return html_file


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

        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"data/vols_{depart}_{arrive}_{timestamp}.csv"

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

        # Generate HTML report automatically
        logger.info("Generating HTML report...")
        html_file = generate_html_report(all_months_data, depart, arrive, start_date, end_date)

        if html_file:
            logger.info(f"✓ HTML report: {html_file}")
            # Open HTML in browser automatically
            try:
                subprocess.run(['open', html_file], check=False)
                logger.info("🌐 Opening report in browser...")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")

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

