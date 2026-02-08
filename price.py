from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)

def get_average_price(html: str, month: str, depart: str, arrive:str) -> dict:
    prices = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # Encuentra todos los divs con la clase que contiene el precio
    divs = soup.find_all('div', class_="f8F1-price-text")

    for div in divs:
        # Extrae el texto del div que contiene el precio
        price = re.sub(r"\D", "", div.text)  # Remover caracteres no numéricos
        if price.isdigit():
            logger.debug(f"Price found: {price}")
            prices.append(int(price))
        else:
            logger.warning(f"Price is not a digit: {price}")

    
    # Calculate average, min and max if prices were found
    if prices:
        price_data = {
            'average': round(sum(prices) / len(prices)),
            'min': min(prices),
            'max': max(prices),
            'count': len(prices),
            'currency': 'EUR',
            'available': True
        }
    else:
        price_data = {
            'average': 0,
            'min': 0,
            'max': 0,
            'count': 0,
            'currency': 'EUR',
            'available': False
        }

    save_prices_to_html(month, price_data, depart, arrive)

    return price_data
def save_prices_to_html(month: str, price_data: dict, depart: str, arrive: str):
    """Save price data to HTML file with proper formatting"""
    import os

    # Use absolute path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, 'flight_prices.html')

    # Create or read existing HTML
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
    except FileNotFoundError:
        soup = BeautifulSoup("<html><head></head><body></body></html>", 'html.parser')
        title = soup.new_tag('title')
        title.string = f'Flight Prices from {depart} to {arrive}'
        soup.head.append(title)

        # Add basic CSS
        style = soup.new_tag('style')
        style.string = """
            body { font-family: Arial, sans-serif; margin: 20px; }
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            table { border-collapse: collapse; margin-bottom: 20px; width: 400px; }
            td { padding: 8px; border: 1px solid #ddd; }
            td:first-child { font-weight: bold; background-color: #f8f9fa; }
        """
        soup.head.append(style)

    # Create month header
    h2 = soup.new_tag('h2')
    h2.string = f"Prices for {month.capitalize()}"
    soup.body.append(h2)

    # Create table with formatted values
    table = soup.new_tag('table')

    if price_data.get('available', True):
        # Display formatted prices
        rows_data = [
            ('Average', f"{price_data['average']} {price_data['currency']}"),
            ('Minimum', f"{price_data['min']} {price_data['currency']}"),
            ('Maximum', f"{price_data['max']} {price_data['currency']}"),
            ('Count', f"{price_data['count']} flights found")
        ]
    else:
        rows_data = [('Status', 'No flights available')]

    for label, value in rows_data:
        row = soup.new_tag('tr')
        td_key = soup.new_tag('td')
        td_key.string = label
        row.append(td_key)
        td_value = soup.new_tag('td')
        td_value.string = value
        row.append(td_value)
        table.append(row)

    soup.body.append(table)

    # Save HTML file
    try:
        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(str(soup.prettify()))
        logger.debug(f"Saved prices to {html_path}")
    except IOError as e:
        logger.error(f"Failed to save HTML file: {e}")