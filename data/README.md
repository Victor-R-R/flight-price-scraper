# 📊 Données CSV

Ce dossier contient les **données brutes** des vols scrapés au format CSV.

## Format des fichiers

**Nom :** `vols_DEPART_ARRIVE_YYYYMMDD_HHMMSS.csv`

**Colonnes :**
- `rang` - Classement du vol (1-5)
- `prix_eur` - Prix en euros
- `compagnie` - Nom de la compagnie aérienne
- `aller_depart` - Heure de départ aller
- `aller_arrivee` - Heure d'arrivée aller
- `retour_depart` - Heure de départ retour
- `retour_arrivee` - Heure d'arrivée retour
- `escales_aller` - Nombre d'escales aller
- `escales_retour` - Nombre d'escales retour
- `duree_aller` - Durée du vol aller
- `duree_retour` - Durée du vol retour
- `url_reservation` - Lien vers la réservation

## Utilisation

Ces fichiers peuvent être :
- Importés dans Excel/Google Sheets pour analyse
- Utilisés pour générer des rapports HTML
- Archivés pour suivi historique des prix

## Nettoyage

Pour supprimer les anciens fichiers :
```bash
# Supprimer tous les fichiers CSV
rm data/vols_*.csv

# Supprimer les fichiers de plus de 30 jours
find data/ -name "vols_*.csv" -mtime +30 -delete
```
