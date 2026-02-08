# Flight Price Scraper

Application de scraping pour rechercher les prix de vols les moins chers entre deux destinations sur Kayak.fr

## Installation

1. Créer un environnement virtuel :
```bash
python3 -m venv env
source env/bin/activate  # Sur macOS/Linux
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Configurer les credentials (optionnel - seulement pour BrightData) :
```bash
cp .env.example .env
# Éditer .env avec vos credentials BrightData
```

## Utilisation

### Basique (sans BrightData)
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    run(
        pw=p,
        depart="Madrid",
        arrive="Paris",
        bright_data=False,
        headless=False
    )
```

### Avec BrightData
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    run(
        pw=p,
        depart="Madrid",
        arrive="Paris",
        bright_data=True,
        headless=True
    )
```

## Paramètres

- `depart` (str): Ville de départ (ex: "Madrid")
- `arrive` (str): Ville d'arrivée (ex: "Paris")
- `bright_data` (bool): Utiliser BrightData proxy (défaut: False)
- `headless` (bool): Lancer le navigateur en mode headless (défaut: False)

## Configuration

Éditer le fichier `.env` pour configurer :

```bash
# Threshold pour les alertes de prix (en EUR)
PRICE_ALERT_THRESHOLD=150

# Credentials BrightData (optionnel)
BRIGHTDATA_WS_CDP=wss://...
```

## Sorties générées

L'application génère automatiquement :

### 📄 Fichiers de données
- `flight_prices.html` - Rapport HTML stylisé avec tableaux
- `flight_prices_YYYYMMDD_HHMMSS.json` - Données structurées en JSON
- `flight_prices_YYYYMMDD_HHMMSS.csv` - Export CSV pour Excel/analyse

### 📊 Visualisations
- `price_trends_YYYYMMDD_HHMMSS.png` - Graphiques complets :
  - Évolution des prix moyens/min/max
  - Prix moyens par mois (barres)
  - Plages de prix (range)
  - Disponibilité des vols

- `best_deals_YYYYMMDD_HHMMSS.png` - Classement des meilleurs prix

### 🔔 Alertes
- `price_alerts_YYYYMMDD_HHMMSS.json` - Alertes de prix bas
- Affichage console des deals exceptionnels

## Structure du code

### Scripts principaux
- `scraping_vols_playwright.py` - Script principal de scraping
- `price.py` - Extraction et sauvegarde des prix en HTML
- `data_export.py` - Export JSON/CSV
- `visualizations.py` - Génération de graphiques matplotlib
- `notifications.py` - Système d'alertes de prix

### Configuration
- `.env` - Configuration et credentials - **NE PAS COMMITTER**
- `.env.example` - Template de configuration
- `requirements.txt` - Dépendances Python

### Sorties (générées automatiquement)
- `flight_prices.html` - Rapport HTML
- `flight_prices_*.json` - Export JSON
- `flight_prices_*.csv` - Export CSV
- `price_trends_*.png` - Graphiques d'analyse
- `best_deals_*.png` - Classement des prix
- `price_alerts_*.json` - Alertes (si seuil atteint)

## Fonctionnalités

### 🔒 Sécurité & Qualité
- ✅ Credentials sécurisés (variables d'environnement)
- ✅ Gestion d'erreurs robuste avec logging détaillé
- ✅ Timeouts configurables et documentés
- ✅ Sélecteurs CSS robustes avec fallback
- ✅ Types de données corrects (nombres exploitables)
- ✅ Code nettoyé et refactorisé

### 📊 Export de données
- ✅ Export JSON avec métadonnées complètes
- ✅ Export CSV compatible Excel
- ✅ Horodatage automatique des fichiers
- ✅ Structure de données standardisée

### 📈 Visualisations
- ✅ Graphiques de tendances (ligne + barres)
- ✅ Visualisation des plages de prix (min-max)
- ✅ Graphique de disponibilité des vols
- ✅ Classement visuel des meilleurs deals
- ✅ Design professionnel avec seaborn
- ✅ Export haute résolution (300 DPI)

### 🔔 Système d'alertes
- ✅ Détection automatique des prix bas
- ✅ Seuil configurable via .env
- ✅ Alertes multi-niveaux (good deal / exceptional)
- ✅ Export JSON des alertes
- ✅ Affichage console avec emojis
- ✅ Identification du meilleur mois

## Notes

- Le scraping peut échouer si Kayak modifie sa structure HTML
- Les timeouts peuvent nécessiter ajustement selon votre connexion
- Les sélecteurs CSS sont optimisés mais peuvent nécessiter maintenance
