import json
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Liste complète du CAC40
CAC40 = [
    "Air Liquide", "Airbus", "Alstom", "ArcelorMittal", "AXA", "BNP Paribas", 
    "Bouygues", "Capgemini", "Carrefour", "Crédit Agricole", "Danone", 
    "Dassault Systèmes", "Edenred", "Engie", "EssilorLuxottica", "Hermès", 
    "Kering", "L'Oréal", "Legrand", "LVMH", "Michelin", "Orange", "Pernod Ricard", 
    "Publicis", "Renault", "Safran", "Sanofi", "Schneider Electric", 
    "Société Générale", "Stellantis", "STMicroelectronics", "Teleperformance", 
    "Thales", "TotalEnergies", "Unibail-Rodamco", "Veolia", "Vinci", "Vivendi"
]

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") # Activé : indispensable pour que ça marche sur GitHub
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    # Ajout d'un faux User-Agent pour passer inaperçu
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    print("🚀 Lancement de l'automatisation CAC40...")
    driver = init_driver()
    toutes_les_offres = []

    try:
        for entreprise in CAC40:
            print(f"🔍 Recherche en cours pour : {entreprise}...")
            
            # Construction de l'URL de recherche LinkedIn Jobs (publique, sans connexion)
            mots_cles = f"Alternance Ingénieur d'affaires {entreprise}".replace(" ", "%20")
            url = f"https://fr.linkedin.com/jobs/search?keywords={mots_cles}&location=France&f_TPR=r2592000" # f_TPR = depuis 30 jours
            
            driver.get(url)
            
            # Pause aléatoire pour imiter un humain et éviter de se faire bloquer
            time.sleep(random.uniform(3.5, 6.2)) 
            
            try:
                # Récupération des cartes d'offres
                job_cards = driver.find_elements(By.CSS_SELECTOR, ".base-card")
                
                for card in job_cards:
                    titre = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text.strip()
                    nom_entreprise = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text.strip()
                    localisation = card.find_element(By.CSS_SELECTOR, ".job-search-card__location").text.strip()
                    lien = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link").get_attribute("href")
                    
                    # On vérifie que c'est bien la bonne entreprise (LinkedIn propose parfois des alternatives)
                    if entreprise.lower() in nom_entreprise.lower():
                        toutes_les_offres.append({
                            "entreprise": nom_entreprise,
                            "titre": titre,
                            "localisation": localisation,
                            "lien": lien
                        })
            except Exception as e:
                print(f"⚠️ Aucun résultat ou erreur pour {entreprise}")

    finally:
        driver.quit()

    # Sauvegarde des données
    with open('offres_cac40.json', 'w', encoding='utf-8') as f:
        json.dump(toutes_les_offres, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Terminé ! {len(toutes_les_offres)} offres trouvées et sauvegardées dans 'offres_cac40.json'.")

if __name__ == "__main__":
    main()
