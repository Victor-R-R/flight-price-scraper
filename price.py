from playwright.sync_api import Page
import re
import logging

logger = logging.getLogger(__name__)


def extract_flights(page: Page, count: int = 5) -> list[dict]:
    """
    Extrait les vols depuis le DOM live via Playwright.
    Support de 2 layouts Kayak (A/B testing):
    - Layout A (Kayak classique): classes CSS .yuAt.yuAt-pres-rounded
    - Layout B (Booking.com): data-testid="searchresults_card"

    Args:
        page: Page Playwright active
        count: Nombre de vols à extraire (défaut: 5)

    Returns:
        Liste de dictionnaires avec les données de vols:
        {
            'price': int,
            'airline': str,
            'dep_time_out': str,
            'arr_time_out': str,
            'dep_time_ret': str,
            'arr_time_ret': str,
            'stops_out': str,
            'stops_ret': str,
            'duration_out': str,
            'duration_ret': str
        }
    """
    flights = []

    # Détecter le layout
    layout_b_cards = page.locator('[data-testid="searchresults_card"]')
    layout_a_cards = page.locator('.yuAt.yuAt-pres-rounded')

    if layout_b_cards.count() > 0:
        logger.info(f"Layout détecté: Booking.com (data-testid) - {layout_b_cards.count()} vols trouvés")
        flights = _extract_layout_b(page, layout_b_cards, count)
    elif layout_a_cards.count() > 0:
        logger.info(f"Layout détecté: Kayak classique (CSS) - {layout_a_cards.count()} vols trouvés")
        flights = _extract_layout_a(page, layout_a_cards, count)
    else:
        logger.error("Aucun layout reconnu - sélecteurs obsolètes")
        return []

    logger.info(f"✓ {len(flights)} vols extraits avec succès")
    return flights


def _extract_layout_b(page: Page, cards_locator, count: int) -> list[dict]:
    """Extraction pour Layout B (Booking.com avec data-testid)"""
    flights = []
    total_cards = cards_locator.count()

    for i in range(min(count, total_cards)):
        try:
            card = cards_locator.nth(i)

            # Compagnie
            airline_elem = card.locator('[data-testid="flight_card_carriers"]')
            airline = airline_elem.text_content().strip() if airline_elem.count() > 0 else "N/A"

            # Prix (extraire uniquement les chiffres consécutifs avant le symbole €)
            price_elem = card.locator('[data-testid="upt_price"]')
            price_text = price_elem.text_content().strip() if price_elem.count() > 0 else "0"

            # Chercher le pattern : chiffres (avec espaces éventuels) suivis de €
            price_match = re.search(r'(\d[\d\s\xa0]*)\s*€', price_text)
            if price_match:
                # Supprimer tous les espaces (normaux et insécables) et convertir
                price_str = price_match.group(1).replace(' ', '').replace('\xa0', '').replace('\u202f', '')
                price = int(price_str)
            else:
                # Fallback: extraire tous les chiffres
                price_clean = re.sub(r"[^\d]", "", price_text)
                price = int(price_clean) if price_clean else 0

            # Horaires aller (segment 0)
            dep_time_out_elem = card.locator('[data-testid="flight_card_segment_departure_time_0"]')
            dep_time_out = dep_time_out_elem.text_content().strip() if dep_time_out_elem.count() > 0 else "N/A"

            arr_time_out_elem = card.locator('[data-testid="flight_card_segment_destination_time_0"]')
            arr_time_out = arr_time_out_elem.text_content().strip() if arr_time_out_elem.count() > 0 else "N/A"

            # Horaires retour (segment 1)
            dep_time_ret_elem = card.locator('[data-testid="flight_card_segment_departure_time_1"]')
            dep_time_ret = dep_time_ret_elem.text_content().strip() if dep_time_ret_elem.count() > 0 else "N/A"

            arr_time_ret_elem = card.locator('[data-testid="flight_card_segment_destination_time_1"]')
            arr_time_ret = arr_time_ret_elem.text_content().strip() if arr_time_ret_elem.count() > 0 else "N/A"

            # Escales
            stops_out_elem = card.locator('[data-testid="flight_card_segment_stops_0"]')
            stops_out = stops_out_elem.text_content().strip() if stops_out_elem.count() > 0 else "N/A"

            stops_ret_elem = card.locator('[data-testid="flight_card_segment_stops_1"]')
            stops_ret = stops_ret_elem.text_content().strip() if stops_ret_elem.count() > 0 else "N/A"

            # Durée
            duration_out_elem = card.locator('[data-testid="flight_card_segment_duration_0"]')
            duration_out = duration_out_elem.text_content().strip() if duration_out_elem.count() > 0 else "N/A"

            duration_ret_elem = card.locator('[data-testid="flight_card_segment_duration_1"]')
            duration_ret = duration_ret_elem.text_content().strip() if duration_ret_elem.count() > 0 else "N/A"

            flights.append({
                'price': price,
                'airline': airline,
                'dep_time_out': dep_time_out,
                'arr_time_out': arr_time_out,
                'dep_time_ret': dep_time_ret,
                'arr_time_ret': arr_time_ret,
                'stops_out': stops_out,
                'stops_ret': stops_ret,
                'duration_out': duration_out,
                'duration_ret': duration_ret
            })

            logger.debug(f"Vol {i+1}: {airline} - {price}€ - {dep_time_out}->{arr_time_out}")

        except Exception as e:
            logger.error(f"Erreur extraction vol {i+1} (Layout B): {e}")
            continue

    return flights


def _extract_layout_a(page: Page, cards_locator, count: int) -> list[dict]:
    """Extraction pour Layout A (Kayak classique avec classes CSS)"""
    flights = []
    total_cards = cards_locator.count()

    logger.warning("Layout A détecté - extraction à implémenter si nécessaire")
    logger.warning("Actuellement, seul Layout B (Booking.com) est supporté")

    # Placeholder pour Layout A - à implémenter si rencontré
    # Les sélecteurs CSS changent fréquemment sur Kayak classique
    # Il faudrait inspecter le DOM live pour identifier les bons sélecteurs

    for i in range(min(count, total_cards)):
        flights.append({
            'price': 0,
            'airline': "Layout A non supporté",
            'dep_time_out': "N/A",
            'arr_time_out': "N/A",
            'dep_time_ret': "N/A",
            'arr_time_ret': "N/A",
            'stops_out': "N/A",
            'stops_ret': "N/A",
            'duration_out': "N/A",
            'duration_ret': "N/A"
        })

    return flights
