"""
Visualization module for flight price data
Generates charts and graphs using matplotlib and seaborn
"""

import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Set seaborn style for professional-looking plots
sns.set_style("whitegrid")
sns.set_palette("husl")


class PriceVisualizer:
    """Create visualizations from flight price data"""

    def __init__(self, output_dir: str = None):
        """
        Initialize visualizer

        Args:
            output_dir: Directory for output images (default: script directory)
        """
        if output_dir is None:
            self.output_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

    def plot_price_trends(self, data: Dict, filename: str = None) -> str:
        """
        Create comprehensive price trends visualization

        Args:
            data: Flight price data dictionary
            filename: Output filename (default: price_trends_YYYYMMDD.png)

        Returns:
            Path to created image file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"price_trends_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)

        # Extract data
        months = [m['month'] for m in data['months'] if m.get('available', True)]
        averages = [m['average'] for m in data['months'] if m.get('available', True)]
        mins = [m['min'] for m in data['months'] if m.get('available', True)]
        maxs = [m['max'] for m in data['months'] if m.get('available', True)]
        counts = [m['count'] for m in data['months'] if m.get('available', True)]

        if not months:
            logger.warning("No data available to plot")
            return None

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            f"Flight Price Analysis: {data['origin']} → {data['destination']}",
            fontsize=16,
            fontweight='bold',
            y=0.995
        )

        # 1. Price Trends Line Chart
        ax1 = axes[0, 0]
        ax1.plot(months, averages, marker='o', linewidth=2, markersize=8, label='Average', color='#2ecc71')
        ax1.plot(months, mins, marker='s', linewidth=1.5, markersize=6, label='Minimum', color='#3498db', linestyle='--')
        ax1.plot(months, maxs, marker='^', linewidth=1.5, markersize=6, label='Maximum', color='#e74c3c', linestyle='--')
        ax1.fill_between(range(len(months)), mins, maxs, alpha=0.2, color='gray')
        ax1.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Price (EUR)', fontsize=11, fontweight='bold')
        ax1.set_title('Price Trends Over Time', fontsize=13, fontweight='bold', pad=10)
        ax1.legend(loc='best', frameon=True, shadow=True)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # Add value labels on average line
        for i, (month, avg) in enumerate(zip(months, averages)):
            ax1.annotate(f'{avg}€', (i, avg), textcoords="offset points", xytext=(0, 10),
                        ha='center', fontsize=8, color='#2ecc71', fontweight='bold')

        # 2. Bar Chart - Average Prices
        ax2 = axes[0, 1]
        colors = sns.color_palette("coolwarm", len(months))
        bars = ax2.bar(months, averages, color=colors, edgecolor='black', linewidth=1.2)
        ax2.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Average Price (EUR)', fontsize=11, fontweight='bold')
        ax2.set_title('Average Price by Month', fontsize=13, fontweight='bold', pad=10)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height)}€', ha='center', va='bottom', fontsize=9, fontweight='bold')

        # 3. Price Range (Min-Max)
        ax3 = axes[1, 0]
        x_pos = range(len(months))
        ranges = [max_val - min_val for min_val, max_val in zip(mins, maxs)]

        ax3.bar(x_pos, ranges, bottom=mins, color='#95a5a6', alpha=0.7, label='Price Range')
        ax3.scatter(x_pos, averages, color='#e74c3c', s=100, zorder=5, label='Average', edgecolors='black', linewidths=1.5)

        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(months, rotation=45)
        ax3.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Price (EUR)', fontsize=11, fontweight='bold')
        ax3.set_title('Price Range (Min-Max) with Average', fontsize=13, fontweight='bold', pad=10)
        ax3.legend(loc='best', frameon=True, shadow=True)
        ax3.grid(axis='y', alpha=0.3)

        # 4. Flights Availability
        ax4 = axes[1, 1]
        ax4.bar(months, counts, color='#9b59b6', edgecolor='black', linewidth=1.2)
        ax4.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Number of Flights', fontsize=11, fontweight='bold')
        ax4.set_title('Flight Availability by Month', fontsize=13, fontweight='bold', pad=10)
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(axis='y', alpha=0.3)

        # Add value labels
        for i, count in enumerate(counts):
            ax4.text(i, count, str(count), ha='center', va='bottom', fontsize=9, fontweight='bold')

        # Add metadata footer
        scrape_date = datetime.fromisoformat(data['scrape_date']).strftime("%Y-%m-%d %H:%M")
        fig.text(0.5, 0.01, f"Data scraped on {scrape_date} | Source: kayak.fr | {len(months)} months analyzed",
                ha='center', fontsize=9, style='italic', color='gray')

        plt.tight_layout(rect=[0, 0.03, 1, 0.99])

        try:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"✓ Chart saved to: {filepath}")
            plt.close()
            return filepath
        except IOError as e:
            logger.error(f"Failed to save chart: {e}")
            plt.close()
            raise

    def plot_best_deals(self, data: Dict, filename: str = None) -> str:
        """
        Create visualization highlighting best deals

        Args:
            data: Flight price data dictionary
            filename: Output filename (default: best_deals_YYYYMMDD.png)

        Returns:
            Path to created image file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"best_deals_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)

        # Extract data and find best deals
        available_months = [m for m in data['months'] if m.get('available', True)]

        if not available_months:
            logger.warning("No data available to plot best deals")
            return None

        # Sort by average price
        sorted_data = sorted(available_months, key=lambda x: x['average'])

        months = [m['month'] for m in sorted_data]
        averages = [m['average'] for m in sorted_data]

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))

        # Color code: green for best deals, red for expensive
        colors = ['#27ae60' if i < 3 else '#95a5a6' if i < len(months) - 3 else '#e74c3c'
                 for i in range(len(months))]

        bars = ax.barh(months, averages, color=colors, edgecolor='black', linewidth=1.5)

        # Add value labels
        for i, (bar, avg) in enumerate(zip(bars, averages)):
            label = f'{int(avg)}€'
            if i < 3:
                label += ' ⭐ BEST'
            ax.text(avg, bar.get_y() + bar.get_height() / 2, label,
                   ha='left', va='center', fontsize=10, fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=colors[i], edgecolor='black', linewidth=1))

        ax.set_xlabel('Average Price (EUR)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Month', fontsize=12, fontweight='bold')
        ax.set_title(f'Best Deals: {data["origin"]} → {data["destination"]}\nSorted by Price',
                    fontsize=14, fontweight='bold', pad=15)
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        try:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            logger.info(f"✓ Best deals chart saved to: {filepath}")
            plt.close()
            return filepath
        except IOError as e:
            logger.error(f"Failed to save best deals chart: {e}")
            plt.close()
            raise

    def generate_all_charts(self, data: Dict) -> Dict[str, str]:
        """
        Generate all available charts

        Args:
            data: Flight price data dictionary

        Returns:
            Dictionary with paths to created chart files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        charts = {}

        try:
            charts['trends'] = self.plot_price_trends(
                data,
                f"price_trends_{timestamp}.png"
            )
        except Exception as e:
            logger.error(f"Failed to create trends chart: {e}")

        try:
            charts['best_deals'] = self.plot_best_deals(
                data,
                f"best_deals_{timestamp}.png"
            )
        except Exception as e:
            logger.error(f"Failed to create best deals chart: {e}")

        return charts
