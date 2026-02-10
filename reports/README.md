# 📑 Rapports HTML

Ce dossier contient les **rapports visuels élégants** générés automatiquement après chaque scraping.

## Format des fichiers

**Nom :** `vols_DEPART_ARRIVE_YYYYMMDD_HHMMSS.html`

## Contenu du rapport

Chaque rapport HTML inclut :

### 📊 Statistiques
- Nombre total de vols analysés
- Prix moyen
- Prix minimum
- Prix maximum

### 🏆 Meilleure offre
- Mise en avant du vol le moins cher
- Prix et compagnie

### 📋 Table détaillée
- Classement avec médailles (🥇 🥈 🥉)
- Toutes les informations de vol
- Badges visuels pour vols directs/escales
- Liens directs vers réservation

## Utilisation

Pour ouvrir un rapport :
```bash
# Ouvrir le dernier rapport
open reports/vols_*.html | tail -1

# Ouvrir un rapport spécifique
open reports/vols_Paris_Malaga_20260210_123456.html
```

## Design

- Design moderne avec dégradé violet/bleu
- Responsive (mobile-friendly)
- Effets hover interactifs
- Impression-friendly

## Nettoyage

Pour supprimer les anciens rapports :
```bash
# Supprimer tous les rapports
rm reports/vols_*.html

# Supprimer les rapports de plus de 30 jours
find reports/ -name "vols_*.html" -mtime +30 -delete
```
