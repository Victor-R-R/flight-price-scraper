"""
Notification module for flight price alerts
Sends alerts when prices drop below threshold
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PriceAlertSystem:
    """Monitor prices and trigger alerts when below threshold"""

    def __init__(self, threshold: float, output_dir: str = None):
        """
        Initialize alert system

        Args:
            threshold: Price threshold in EUR for triggering alerts
            output_dir: Directory for alert logs (default: script directory)
        """
        self.threshold = threshold
        if output_dir is None:
            self.output_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)
        self.alerts = []

    def check_prices(self, data: Dict) -> List[Dict]:
        """
        Check prices and generate alerts for good deals

        Args:
            data: Flight price data dictionary

        Returns:
            List of alert dictionaries
        """
        alerts = []

        for month_data in data.get('months', []):
            if not month_data.get('available', True):
                continue

            month = month_data.get('month', 'Unknown')
            avg_price = month_data.get('average', 0)
            min_price = month_data.get('min', 0)
            max_price = month_data.get('max', 0)
            currency = month_data.get('currency', 'EUR')

            # Check if average price is below threshold
            if avg_price > 0 and avg_price <= self.threshold:
                alert = {
                    'type': 'average_below_threshold',
                    'severity': 'high',
                    'month': month,
                    'price': avg_price,
                    'threshold': self.threshold,
                    'currency': currency,
                    'message': f"🎯 ALERT: Average price for {month} is {avg_price}{currency} (threshold: {self.threshold}{currency})",
                    'route': f"{data['origin']} → {data['destination']}",
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                logger.warning(alert['message'])

            # Check if minimum price is exceptional (< 50% of threshold)
            exceptional_threshold = self.threshold * 0.5
            if min_price > 0 and min_price <= exceptional_threshold:
                alert = {
                    'type': 'minimum_exceptional',
                    'severity': 'critical',
                    'month': month,
                    'price': min_price,
                    'threshold': exceptional_threshold,
                    'currency': currency,
                    'message': f"⭐ EXCEPTIONAL: Minimum price for {month} is only {min_price}{currency}!",
                    'route': f"{data['origin']} → {data['destination']}",
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert)
                logger.warning(alert['message'])

        self.alerts.extend(alerts)
        return alerts

    def save_alerts(self, filename: str = None) -> Optional[str]:
        """
        Save alerts to JSON file

        Args:
            filename: Output filename (default: price_alerts_YYYYMMDD.json)

        Returns:
            Path to created file or None if no alerts
        """
        if not self.alerts:
            logger.info("No price alerts to save")
            return None

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"price_alerts_{timestamp}.json"

        filepath = os.path.join(self.output_dir, filename)

        alert_data = {
            'total_alerts': len(self.alerts),
            'threshold': self.threshold,
            'generated_at': datetime.now().isoformat(),
            'alerts': self.alerts
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(alert_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ {len(self.alerts)} alerts saved to: {filepath}")
            return filepath
        except IOError as e:
            logger.error(f"Failed to save alerts: {e}")
            raise

    def print_summary(self):
        """Print a summary of all alerts to console"""
        if not self.alerts:
            logger.info("✓ No price alerts - all prices above threshold")
            return

        print("\n" + "=" * 70)
        print(f"🔔 PRICE ALERTS SUMMARY ({len(self.alerts)} alerts)")
        print("=" * 70)

        # Group alerts by severity
        critical_alerts = [a for a in self.alerts if a['severity'] == 'critical']
        high_alerts = [a for a in self.alerts if a['severity'] == 'high']

        if critical_alerts:
            print(f"\n⭐ EXCEPTIONAL DEALS ({len(critical_alerts)}):")
            for alert in critical_alerts:
                print(f"   • {alert['month']}: {alert['price']}{alert['currency']} - {alert['route']}")

        if high_alerts:
            print(f"\n🎯 GOOD DEALS ({len(high_alerts)}):")
            for alert in high_alerts:
                print(f"   • {alert['month']}: {alert['price']}{alert['currency']} - {alert['route']}")

        print("\n" + "=" * 70 + "\n")

    def get_best_month(self, data: Dict) -> Optional[Dict]:
        """
        Find the best month to fly based on average price

        Args:
            data: Flight price data dictionary

        Returns:
            Dictionary with best month information or None
        """
        available_months = [m for m in data.get('months', []) if m.get('available', True) and m.get('average', 0) > 0]

        if not available_months:
            return None

        best_month = min(available_months, key=lambda x: x['average'])

        return {
            'month': best_month['month'],
            'average_price': best_month['average'],
            'min_price': best_month['min'],
            'max_price': best_month['max'],
            'flights_count': best_month['count'],
            'currency': best_month['currency'],
            'route': f"{data['origin']} → {data['destination']}"
        }


def create_alert_summary(data: Dict, threshold: float) -> str:
    """
    Create a human-readable alert summary

    Args:
        data: Flight price data dictionary
        threshold: Price threshold

    Returns:
        Formatted summary string
    """
    alert_system = PriceAlertSystem(threshold)
    alerts = alert_system.check_prices(data)
    best_month = alert_system.get_best_month(data)

    summary = []
    summary.append(f"\n{'='*70}")
    summary.append(f"FLIGHT PRICE ANALYSIS: {data['origin']} → {data['destination']}")
    summary.append(f"{'='*70}")

    if best_month:
        summary.append(f"\n🏆 BEST MONTH TO FLY: {best_month['month']}")
        summary.append(f"   Average: {best_month['average_price']} {best_month['currency']}")
        summary.append(f"   Range: {best_month['min_price']} - {best_month['max_price']} {best_month['currency']}")
        summary.append(f"   Available flights: {best_month['flights_count']}")

    if alerts:
        summary.append(f"\n🔔 PRICE ALERTS ({len(alerts)} months below threshold of {threshold} EUR):")
        for alert in alerts:
            emoji = "⭐" if alert['severity'] == 'critical' else "🎯"
            summary.append(f"   {emoji} {alert['month']}: {alert['price']} {alert['currency']}")
    else:
        summary.append(f"\n✓ No alerts - all prices above {threshold} EUR threshold")

    summary.append(f"\n{'='*70}\n")

    return "\n".join(summary)
