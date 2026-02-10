# Flight Price Scraper

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![Playwright](https://img.shields.io/badge/playwright-1.55-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Application de scraping pour rechercher les prix de vols les moins chers entre deux destinations sur Kayak.fr

## 🚀 Features

✨ **Web Scraping** - Playwright automation for Kayak.fr
📊 **Data Export** - CSV format with flight details
🔒 **Secure** - Environment variables for credentials
🎯 **Smart Extraction** - Support for multiple Kayak layouts (A/B testing)

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

3. Configurer les variables d'environnement (optionnel) :

Créer un fichier `.env` à la racine du projet :

```bash
# BrightData Configuration (optionnel - pour proxy)
BRIGHTDATA_WS_CDP=wss://brd-customer-YOUR_ID-zone-YOUR_ZONE:YOUR_PASSWORD@brd.superproxy.io:9222

# Price Alert Configuration
PRICE_ALERT_THRESHOLD=150
```

**Note:** Le fichier `.env` est ignoré par git pour protéger vos credentials.

## Utilisation

### Exemple de base
```bash
python scraping_vols_playwright.py
```

### Personnalisation dans le code
```python
from playwright.sync_api import sync_playwright
from datetime import datetime

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
```

## Paramètres

- `depart` (str): Ville de départ (ex: "Paris")
- `arrive` (str): Ville d'arrivée (ex: "Malaga")
- `start_date` (datetime): Date de départ (ex: datetime(2026, 7, 1))
- `end_date` (datetime): Date de retour (ex: datetime(2026, 7, 31))
- `bright_data` (bool): Utiliser BrightData proxy (défaut: False)
- `headless` (bool): Lancer le navigateur en mode headless (défaut: False)

## Configuration

Les variables d'environnement sont gérées via un fichier `.env` (voir Installation).

**Variables disponibles :**
- `PRICE_ALERT_THRESHOLD` - Seuil de prix pour les alertes (défaut: 150 EUR)
- `BRIGHTDATA_WS_CDP` - URL de connexion BrightData (optionnel)
- `DEBUG_SCREENSHOTS` - Activer les screenshots de débogage (défaut: false)

## Sorties générées

L'application génère automatiquement deux types de fichiers :

### 📄 CSV (données brutes) → `data/`
- `data/vols_DEPART_ARRIVE_YYYYMMDD_HHMMSS.csv`
- Format Excel-compatible avec toutes les données
- Colonnes : rang, prix, compagnie, horaires, escales, durées, URL

### 📑 HTML (rapports visuels) → `reports/`
- `reports/vols_DEPART_ARRIVE_YYYYMMDD_HHMMSS.html`
- Rapport élégant avec design moderne
- S'ouvre automatiquement dans le navigateur
- Statistiques, meilleure offre, tableau interactif

### 📊 Affichage console
- Tableau récapitulatif des 5 meilleurs vols
- Logs détaillés du processus de scraping

## Structure du projet

```
scraping_advanced/
├── scraping_vols_playwright.py  # Script principal
├── price.py                     # Extraction des vols
├── generate_report.py           # Générateur HTML standalone (optionnel)
├── requirements.txt             # Dépendances
├── .env                         # Configuration (à créer)
├── README.md                    # Documentation
│
├── data/                        # 📊 Données CSV (ignoré par git)
│   ├── README.md
│   └── vols_*.csv
│
├── reports/                     # 📑 Rapports HTML (ignoré par git)
│   ├── README.md
│   └── vols_*.html
│
└── old_archives/                # Archives (ignoré par git)
    ├── data_export.py
    ├── visualizations.py
    ├── notifications.py
    └── example_usage.py
```

## Fonctionnalités

### 🔒 Sécurité & Qualité
- ✅ Credentials sécurisés (variables d'environnement)
- ✅ Gestion d'erreurs robuste avec logging détaillé
- ✅ Timeouts configurables et documentés
- ✅ Code modulaire et maintenable

### 🎯 Scraping intelligent
- ✅ Support multi-layout (Kayak Layout A/B testing)
- ✅ Détection automatique du layout de la page
- ✅ Extraction robuste avec sélecteurs data-testid
- ✅ Gestion des popups (cookies, publicités)
- ✅ Configuration des passagers (adultes + enfants)
- ✅ Sélection de dates personnalisables

### 📊 Export de données
- ✅ Export CSV avec toutes les informations de vol
- ✅ Horodatage automatique des fichiers
- ✅ URL de réservation incluse
- ✅ Affichage console formaté

## Notes

- Le scraping peut échouer si Kayak modifie sa structure HTML
- Les timeouts peuvent nécessiter ajustement selon votre connexion
- Les sélecteurs CSS sont optimisés mais peuvent nécessiter maintenance
