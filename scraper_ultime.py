import json
import time
import random
import unicodedata
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

GEANTS_MONDIAUX = [
    "Air Liquide", "Airbus", "Alstom", "ArcelorMittal", "AXA", "BNP", 
    "Bouygues", "Capgemini", "Carrefour", "Crédit Agricole", "Danone", 
    "Dassault", "Edenred", "Engie", "Essilor", "Hermès", 
    "Kering", "L'Oréal", "Legrand", "LVMH", "Michelin", "Orange", "Pernod", 
    "Publicis", "Renault", "Safran", "Sanofi", "Schneider", 
    "Société Générale", "Stellantis", "STMicroelectronics", "Teleperformance", 
    "Thales", "TotalEnergies", "Unibail", "Veolia", "Vinci", "Vivendi",
    "Microsoft", "Amazon", "Google", "Salesforce", "SAP", "Oracle", "IBM", "Cisco",
    "Accenture", "Deloitte", "EY", "PwC", "KPMG", "Sopra Steria", "CGI", "Wavestone",
    "EDF", "SNCF", "CMA CGM", "La Poste", "Naval Group", "Siemens", "Nestlé", "Unilever"
]

# Les angles d'attaque pour contourner la limite de LinkedIn
ANGLES_RECHERCHE = ["Alternance Business", "Alternance Tech", "Alternance Projet"]

MOTS_CLES_VALIDES = [
    "affaire", "business", "sales", "account", "vente", "b2b", "key", "kam", "commercial", "avant-vente", "presales",
    "produit", "product", "strategy", "strategie", "partenariat",
    "developpeur", "data", "cyber", "ia", "cloud", "it",
    "projet", "consultant", "management", "agile"
]

MOTS_INTERDITS = [
    "rh", "ressources humaines", "recrutement", "talent", 
    "finance", "comptabilite", "comptable", "controleur", "audit",
    "support", "technicien", "helpdesk", "maintenance", "mecanique", "usine",
    "logistique", "supply chain", "achat", "acheteur",
    "communication", "design", "graphiste", "juridique", "droit", "stage"
]

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def nettoyer_texte(texte):
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode("utf-8")
    return texte.lower()

def offre_est_pertinente(titre):
    titre_clean = nettoyer_texte(titre)
    if any(mot_interdit in titre_clean for mot_interdit in MOTS_INTERDITS):
        return False
    return any(mot_valide in titre_clean for mot_valide in MOTS_CLES_VALIDES)

def main():
    print(f"🚀 Lancement du Scraper V10 (Quantité Max) pour {len(GEANTS_MONDIAUX)} entreprises...")
    driver = init_driver()
    toutes_les_offres = []
    urls_deja_vues = set()
    date_du_jour = datetime.now().strftime("%d/%m/%Y")

    try:
        for entreprise in GEANTS_MONDIAUX:
            print(f"🏢 Extraction massive pour : {entreprise}...")
            
            # On attaque chaque entreprise sous 3 angles différents
            for angle in ANGLES_RECHERCHE:
                mots_cles = f"{angle} {entreprise}".replace(" ", "%20")
                url = f"https://fr.linkedin.com/jobs/search?keywords={mots_cles}&location=France&f_TPR=r2592000"
                
                driver.get(url)
                time.sleep(random.uniform(2.5, 4.0))
                
                try:
                    # On scroll plus profondément (4 fois au lieu de 3)
                    for _ in range(4):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        try:
                            bouton = driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
                            if bouton.is_displayed():
                                bouton.click()
                                time.sleep(random.uniform(1.0, 1.5))
                        except:
                            pass

                    job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
                    
                    for card in job_cards:
                        titre = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                        nom_entreprise = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                        localisation = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text.strip().split(',')[0]
                        lien = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
                        
                        # Si l'offre est nouvelle et pertinente, on l'ajoute !
                        if lien not in urls_deja_vues and nettoyer_texte(entreprise) in nettoyer_texte(nom_entreprise):
                            if offre_est_pertinente(titre):
                                urls_deja_vues.add(lien)
                                toutes_les_offres.append({
                                    "entreprise": nom_entreprise,
                                    "titre": titre,
                                    "localisation": localisation,
                                    "lien": lien,
                                    "date_ajout": date_du_jour
                                })
                except Exception:
                    pass 
                    
    finally:
        driver.quit()

    if len(toutes_les_offres) > 5:
        with open('offres_cac40.json', 'w', encoding='utf-8') as f:
            json.dump(toutes_les_offres, f, ensure_ascii=False, indent=4)
        print(f"✅ BINGO ! {len(toutes_les_offres)} offres récupérées.")
    else:
        print(f"❌ Sécurité anti-vide activée.")

if __name__ == "__main__":
    main()
