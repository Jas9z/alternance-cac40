# alternance-cac40

Projet personnel pour repérer des offres d’alternance liées à l’ingénierie d’affaires dans les entreprises du CAC40.

## Scraper LinkedIn 100% alternance

Le fichier `scraper_linkedin_alternance.py` scrape uniquement LinkedIn et filtre strictement sur les offres d’alternance.

### Lancer le scraper

```bash
pip install -r requirements.txt
python scraper_linkedin_alternance.py
```

### Ce que fait le script

- Scrape uniquement LinkedIn (pas Apec, pas les sites carrières).
- Utilise uniquement des requêtes du type `alternance + ingénieur d’affaires / business developer / ingénieur commercial`.
- Rejette toute offre dont le titre ne contient pas `alternance`, `apprentissage` ou `alternant`.
- Rejette les offres de type stage, CDI, CDD, freelance ou intérim.
- Filtre sur les entreprises du CAC40 déjà listées dans le repo.
- Enregistre les résultats dans `data/offres_linkedin_alternance.json`.

### Remarque

LinkedIn interdit le scraping automatisé dans ses CGU. Ce script est à usage strictement personnel et à faible volume.
