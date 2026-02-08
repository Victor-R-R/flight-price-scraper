"""
Example usage of the flight price scraper with all features
"""

from playwright.sync_api import sync_playwright
from scraping_vols_playwright import run

# Example 1: Basic scraping with all features enabled (default)
def example_basic():
    """Run basic scraping with automatic exports and visualizations"""
    print("="*70)
    print("EXAMPLE 1: Basic scraping (headless mode with all features)")
    print("="*70)

    with sync_playwright() as p:
        data = run(
            pw=p,
            depart="Madrid",
            arrive="Paris",
            bright_data=False,  # Use local browser
            headless=True       # Run without UI
        )

    print(f"\n✓ Scraped {len(data)} months of data")
    print("✓ Generated: JSON, CSV, HTML, Charts, Alerts")


# Example 2: Interactive scraping (see browser in action)
def example_interactive():
    """Run scraping with visible browser for debugging"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Interactive scraping (visible browser)")
    print("="*70)

    with sync_playwright() as p:
        data = run(
            pw=p,
            depart="Barcelona",
            arrive="London",
            bright_data=False,
            headless=False  # Show browser window
        )

    print(f"\n✓ Scraped {len(data)} months of data")


# Example 3: Using individual modules
def example_individual_modules():
    """Use export and visualization modules separately"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Using individual modules")
    print("="*70)

    # Sample data (normally from scraping)
    sample_data = {
        'scrape_date': '2024-01-15T10:30:00',
        'origin': 'Madrid',
        'destination': 'Paris',
        'total_months': 3,
        'months': [
            {
                'month': 'feb.',
                'average': 120,
                'min': 89,
                'max': 180,
                'count': 15,
                'currency': 'EUR',
                'available': True
            },
            {
                'month': 'mar.',
                'average': 98,
                'min': 75,
                'max': 145,
                'count': 22,
                'currency': 'EUR',
                'available': True
            },
            {
                'month': 'apr.',
                'average': 165,
                'min': 120,
                'max': 210,
                'count': 18,
                'currency': 'EUR',
                'available': True
            }
        ],
        'metadata': {
            'scraper_version': '1.0',
            'source': 'kayak.fr'
        }
    }

    # Export to JSON/CSV
    from data_export import PriceDataExporter
    exporter = PriceDataExporter()
    files = exporter.export_all(sample_data)
    print(f"✓ Exported to: {files['json']}")
    print(f"✓ Exported to: {files['csv']}")

    # Generate visualizations
    from visualizations import PriceVisualizer
    visualizer = PriceVisualizer()
    charts = visualizer.generate_all_charts(sample_data)
    print(f"✓ Chart created: {charts['trends']}")
    print(f"✓ Chart created: {charts['best_deals']}")

    # Check price alerts
    from notifications import PriceAlertSystem
    alert_system = PriceAlertSystem(threshold=100)
    alerts = alert_system.check_prices(sample_data)
    print(f"✓ Found {len(alerts)} price alerts")

    if alerts:
        alert_file = alert_system.save_alerts()
        print(f"✓ Alerts saved to: {alert_file}")

    # Print summary
    alert_system.print_summary()


# Example 4: Custom alert threshold
def example_custom_threshold():
    """Set custom price alert threshold"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom alert threshold (200 EUR)")
    print("="*70)

    # Override environment variable
    import os
    os.environ['PRICE_ALERT_THRESHOLD'] = '200'

    with sync_playwright() as p:
        data = run(
            pw=p,
            depart="Madrid",
            arrive="Tokyo",
            bright_data=False,
            headless=True
        )

    print(f"\n✓ Will alert for prices below 200 EUR")


if __name__ == '__main__':
    # Choose which example to run
    print("\n🚀 Flight Price Scraper - Example Usage\n")

    # Uncomment the example you want to run:

    # example_basic()
    # example_interactive()
    example_individual_modules()  # Safe to run without scraping
    # example_custom_threshold()

    print("\n✅ Example completed!\n")
