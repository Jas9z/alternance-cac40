import json
import time
import random
import unicodedata
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

MOTS_CLES_VALIDES = [
    "affaire", "business", "developer", "commercial", "sales", "account", "vente", "b2b", "key", "kam", "partenariat",
    "marketing", "produit", "product", "achat", "acheteur", "strategy", "strategie", "digital", "offre",
    "it", "developpeur", "dev", "software", "informatique", "tech", "web", "data", "cloud", "cyber", "securite", "ia", "intelligence",
    "projet", "ingenieur", "consultant", "management", "agile", "transformation", "innovation"
]

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox") # Sécurité supplémentaire pour les serveurs GitHub
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def nettoyer_texte(texte):
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode("utf-8")
    return texte.lower()

def offre_est_pertinente(titre):
    titre_clean = nettoyer_texte(titre)
    return any(mot in titre_clean for mot in MOTS_CLES_VALIDES)

def main():
    print(f"🚀 Lancement du Scraper V7 (Cadre Pro) pour {len(GEANTS_MONDIAUX)} entreprises...")
    driver = init_driver()
    toutes_les_offres = []
    urls_deja_vues = set()
    date_du_jour = datetime.now().strftime("%d/%m/%Y")

    try:
        for entreprise in GEANTS_MONDIAUX:
            print(f"🏢 Analyse de : {entreprise}...")
            
            mots_cles = f"Alternance {entreprise}".replace(" ", "%20")
            url = f"https://fr.linkedin.com/jobs/search?keywords={mots_cles}&location=France&f_TPR=r2592000"
            
            driver.get(url)
            time.sleep(random.uniform(3.0, 5.0))
            
            try:
                # SCROLL ET CLIC INTELLIGENT
                for _ in range(4):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1.5, 2.5))
                    
                    # On cherche si LinkedIn affiche le bouton "Voir plus d'offres" et on clique
                    try:
                        bouton = driver.find_element(By.CSS_SELECTOR, "button.infinite-scroller__show-more-button")
                        if bouton.is_displayed():
                            bouton.click()
                            time.sleep(random.uniform(1.0, 2.0))
                    except:
                        pass # S'il n'y a pas de bouton, on continue le scroll

                job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
                
                for card in job_cards:
                    titre = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                    nom_entreprise = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                    localisation = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text.strip()
                    lien = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
                    
                    # Filtres croisés
                    if lien not in urls_deja_vues and nettoyer_texte(entreprise) in nettoyer_texte(nom_entreprise):
                        if offre_est_pertinente(titre):
                            urls_deja_vues.add(lien)
                            toutes_les_offres.append({
                                "entreprise": nom_entreprise,
                                "titre": titre,
                                "localisation": localisation,
                                "lien": lien,
                                "date_ajout": date_du_jour # Ajout de la traçabilité
                            })
            except Exception as e:
                print(f"⚠️ Avertissement sur {entreprise} - On passe à la suivante.")
                    
    finally:
        driver.quit()

    # SÉCURITÉ ANTI-VIDE : On sauvegarde UNIQUEMENT si on a trouvé des offres
    if len(toutes_les_offres) > 5:
        with open('offres_cac40.json', 'w', encoding='utf-8') as f:
            json.dump(toutes_les_offres, f, ensure_ascii=False, indent=4)
        print(f"✅ Succès ! {len(toutes_les_offres)} offres enregistrées en toute sécurité.")
    else:
        print(f"❌ Échec de la récolte (seulement {len(toutes_les_offres)} offres). Par sécurité, l'ancien fichier n'a pas été écrasé.")

if __name__ == "__main__":
    main()
