"""
Data export module for flight price scraper
Handles JSON and CSV export of scraped data
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PriceDataExporter:
    """Export flight price data to various formats"""

    def __init__(self, output_dir: str = None):
        """
        Initialize exporter

        Args:
            output_dir: Directory for output files (default: script directory)
        """
        if output_dir is None:
            self.output_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def export_to_json(self, data: Dict, filename: str = None) -> str:
        """
        Export price data to JSON file

        Args:
            data: Flight price data dictionary
            filename: Output filename (default: flight_prices_YYYYMMDD_HHMMSS.json)

        Returns:
            Path to created file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flight_prices_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ JSON exported to: {filepath}")
            return filepath
        except IOError as e:
            logger.error(f"Failed to export JSON: {e}")
            raise

    def export_to_csv(self, data: Dict, filename: str = None) -> str:
        """
        Export price data to CSV file

        Args:
            data: Flight price data dictionary
            filename: Output filename (default: flight_prices_YYYYMMDD_HHMMSS.csv)

        Returns:
            Path to created file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flight_prices_{timestamp}.csv"

        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                # Define CSV columns
                fieldnames = [
                    'scrape_date',
                    'origin',
                    'destination',
                    'month',
                    'average_price',
                    'min_price',
                    'max_price',
                    'flights_count',
                    'currency',
                    'available'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                # Write each month's data
                scrape_date = data.get('scrape_date', datetime.now().isoformat())
                origin = data.get('origin', 'Unknown')
                destination = data.get('destination', 'Unknown')

                for month_data in data.get('months', []):
                    row = {
                        'scrape_date': scrape_date,
                        'origin': origin,
                        'destination': destination,
                        'month': month_data.get('month', ''),
                        'average_price': month_data.get('average', 0),
                        'min_price': month_data.get('min', 0),
                        'max_price': month_data.get('max', 0),
                        'flights_count': month_data.get('count', 0),
                        'currency': month_data.get('currency', 'EUR'),
                        'available': month_data.get('available', False)
                    }
                    writer.writerow(row)

            logger.info(f"✓ CSV exported to: {filepath}")
            return filepath
        except IOError as e:
            logger.error(f"Failed to export CSV: {e}")
            raise

    def export_all(self, data: Dict) -> Dict[str, str]:
        """
        Export to both JSON and CSV formats

        Args:
            data: Flight price data dictionary

        Returns:
            Dictionary with paths to created files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"flight_prices_{timestamp}.json"
        csv_file = f"flight_prices_{timestamp}.csv"

        return {
            'json': self.export_to_json(data, json_file),
            'csv': self.export_to_csv(data, csv_file)
        }


def create_export_data(origin: str, destination: str, months_data: List[Dict]) -> Dict:
    """
    Create standardized data structure for export

    Args:
        origin: Departure city
        destination: Arrival city
        months_data: List of price data per month

    Returns:
        Formatted data dictionary ready for export
    """
    return {
        'scrape_date': datetime.now().isoformat(),
        'origin': origin,
        'destination': destination,
        'total_months': len(months_data),
        'months': months_data,
        'metadata': {
            'scraper_version': '1.0',
            'source': 'kayak.fr'
        }
    }
