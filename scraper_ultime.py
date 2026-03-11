import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Liste du CAC40
CAC40 = [
    "Air Liquide", "Airbus", "Alstom", "ArcelorMittal", "AXA", "BNP Paribas", 
    "Bouygues", "Capgemini", "Carrefour", "Crédit Agricole", "Danone", 
    "Dassault Systèmes", "Edenred", "Engie", "EssilorLuxottica", "Hermès", 
    "Kering", "L'Oréal", "Legrand", "LVMH", "Michelin", "Orange", "Pernod Ricard", 
    "Publicis", "Renault", "Safran", "Sanofi", "Schneider Electric", 
    "Société Générale", "Stellantis", "STMicroelectronics", "Teleperformance", 
    "Thales", "TotalEnergies", "Unibail-Rodamco", "Veolia", "Vinci", "Vivendi"
]

# 🌍 PALETTE ÉLARGIE : Le robot va faire ces 4 recherches pour chaque entreprise
RECHERCHES = [
    "Alternance Ingénieur d'affaires",
    "Alternance Business Developer",
    "Alternance IT Développeur",
    "Alternance Data et Projet"
]

# 🎯 LE GRAND FILTRE : Si le titre contient au moins l'un de ces mots, on garde l'offre !
MOTS_CLES_VALIDES = [
    # Business & Vente
    "affaire", "affaires", "business", "developer", "commercial", "sales", "account", "vente", "développement", "key",
    # IT, Tech & Dev
    "it", "développeur", "developpeur", "dev", "software", "informatique", "tech", "web", "fullstack",
    # Data & Infrastructure
    "data", "cloud", "cyber", "sécurité", "système", "réseau", "ia", "intelligence",
    # Gestion de projet & Consulting
    "projet", "ingénieur", "consultant", "management", "product", "agile"
]

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def offre_est_pertinente(titre):
    titre_lower = titre.lower()
    return any(mot in titre_lower for mot in MOTS_CLES_VALIDES)

def main():
    print("🚀 Lancement du Scraper V3 (Palette Large : Business, IT, Dev, Projets)...")
    driver = init_driver()
    toutes_les_offres = []
    urls_deja_vues = set()

    try:
        for entreprise in CAC40:
            print(f"🏢 Analyse de : {entreprise}...")
            
            for requete in RECHERCHES:
                mots_cles = f"{requete} {entreprise}".replace(" ", "%20")
                url = f"https://fr.linkedin.com/jobs/search?keywords={mots_cles}&location=France&f_TPR=r2592000"
                
                driver.get(url)
                time.sleep(random.uniform(2.5, 4.0)) # Pause anti-blocage
                
                try:
                    job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
                    
                    for card in job_cards:
                        titre = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                        nom_entreprise = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                        localisation = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text.strip()
                        lien = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
                        
                        if lien not in urls_deja_vues and entreprise.lower() in nom_entreprise.lower() and offre_est_pertinente(titre):
                            urls_deja_vues.add(lien)
                            toutes_les_offres.append({
                                "entreprise": nom_entreprise,
                                "titre": titre,
                                "localisation": localisation,
                                "lien": lien
                            })
                except Exception:
                    pass
                    
    finally:
        driver.quit()

    with open('offres_cac40.json', 'w', encoding='utf-8') as f:
        json.dump(toutes_les_offres, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Mission accomplie ! {len(toutes_les_offres)} offres variées (IT, Business, Data...) trouvées.")

if __name__ == "__main__":
    main()
