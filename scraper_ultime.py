import json
import time
import random
import unicodedata
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Noms simplifiés pour attraper plus de variations (ex: "Dassault" au lieu de "Dassault Systèmes")
CAC40 = [
    "Air Liquide", "Airbus", "Alstom", "ArcelorMittal", "AXA", "BNP", 
    "Bouygues", "Capgemini", "Carrefour", "Crédit Agricole", "Danone", 
    "Dassault", "Edenred", "Engie", "Essilor", "Hermès", 
    "Kering", "L'Oréal", "Legrand", "LVMH", "Michelin", "Orange", "Pernod", 
    "Publicis", "Renault", "Safran", "Sanofi", "Schneider", 
    "Société Générale", "Stellantis", "STMicroelectronics", "Teleperformance", 
    "Thales", "TotalEnergies", "Unibail", "Veolia", "Vinci", "Vivendi"
]

# Les mots clés (sans accents pour éviter de rater des offres mal écrites)
MOTS_CLES_VALIDES = [
    "affaire", "business", "developer", "commercial", "sales", "account", "vente", "developpement", 
    "it", "developpeur", "dev", "software", "informatique", "tech", "web", "fullstack",
    "data", "cloud", "cyber", "securite", "systeme", "reseau", "ia", "intelligence",
    "projet", "ingenieur", "consultant", "management", "product", "agile"
]

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# Fonction pour enlever les accents et mettre en minuscules pour comparer
def nettoyer_texte(texte):
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode("utf-8")
    return texte.lower()

def offre_est_pertinente(titre):
    titre_clean = nettoyer_texte(titre)
    return any(mot in titre_clean for mot in MOTS_CLES_VALIDES)

def main():
    print("🚀 Lancement du Scraper V4 (Anti-blocage + Scrolling)...")
    driver = init_driver()
    toutes_les_offres = []
    urls_deja_vues = set()

    try:
        for entreprise in CAC40:
            print(f"🏢 Recherche globale pour : {entreprise}...")
            
            # UNE SEULE requête large par entreprise pour éviter le blocage : "Alternance [Entreprise]"
            mots_cles = f"Alternance {entreprise}".replace(" ", "%20")
            url = f"https://fr.linkedin.com/jobs/search?keywords={mots_cles}&location=France&f_TPR=r2592000"
            
            driver.get(url)
            time.sleep(random.uniform(3.0, 5.0))
            
            try:
                # SCROLLING MAGIQUE : On descend 3 fois pour forcer LinkedIn à charger plus d'offres
                for _ in range(3):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1.0, 2.0))

                job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
                
                for card in job_cards:
                    titre = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                    nom_entreprise = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                    localisation = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text.strip()
                    lien = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
                    
                    # On vérifie si c'est la bonne entreprise ET si notre filtre accepte le titre
                    if lien not in urls_deja_vues and nettoyer_texte(entreprise) in nettoyer_texte(nom_entreprise):
                        if offre_est_pertinente(titre):
                            urls_deja_vues.add(lien)
                            toutes_les_offres.append({
                                "entreprise": nom_entreprise,
                                "titre": titre,
                                "localisation": localisation,
                                "lien": lien
                            })
            except Exception as e:
                print(f"Erreur sur {entreprise}")
                    
    finally:
        driver.quit()

    with open('offres_cac40.json', 'w', encoding='utf-8') as f:
        json.dump(toutes_les_offres, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Mission accomplie ! {len(toutes_les_offres)} offres trouvées.")

if __name__ == "__main__":
    main()
