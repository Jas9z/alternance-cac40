import json
import time
import random
import unicodedata
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

GEANTS = [
    "Air Liquide", "Airbus", "Alstom", "ArcelorMittal", "AXA", "BNP Paribas",
    "Bouygues", "Capgemini", "Carrefour", "Crédit Agricole", "Danone",
    "Dassault Systèmes", "Edenred", "Engie", "EssilorLuxottica", "Hermès",
    "Kering", "L'Oréal", "Legrand", "LVMH", "Michelin", "Orange", "Pernod Ricard",
    "Publicis", "Renault", "Safran", "Sanofi", "Schneider Electric",
    "Société Générale", "Stellantis", "STMicroelectronics", "Teleperformance",
    "Thales", "TotalEnergies", "Unibail-Rodamco", "Veolia", "Vinci", "Vivendi",
    "Microsoft", "Amazon", "Google", "Salesforce", "SAP", "Oracle", "IBM", "Cisco",
    "Accenture", "Deloitte", "EY", "PwC", "KPMG", "Sopra Steria", "CGI", "Wavestone",
    "EDF", "Groupe SNCF", "CMA CGM", "La Poste Groupe", "Naval Group",
    "Siemens", "Nestlé", "Unilever"
]

# 9 angles d'attaque = 3x plus de couverture qu'avant
ANGLES = [
    "Alternance ingénieur affaires",
    "Alternance chargé affaires",
    "Alternance business developer",
    "Alternance commercial IT",
    "Alternance chef de projet digital",
    "Alternance consultant digital",
    "Alternance sales tech",
    "Alternance account manager",
    "Alternance data project",
]

# Scoring positif — plus il y a de mots matchés, plus le score est élevé
MOTS_POSITIFS = {
    # Business / commercial (poids fort)
    "affaire": 4, "business": 4, "account": 4, "commercial": 4,
    "sales": 4, "vente": 4, "b2b": 4, "key account": 4, "kam": 4,
    "avant-vente": 4, "presales": 4, "pre-sales": 4,
    # Projet / stratégie (poids fort)
    "projet": 3, "product": 3, "strategy": 3, "strategie": 3,
    "partenariat": 3, "developpement": 3, "business development": 3,
    # Tech / IT (poids moyen)
    "digital": 2, "data": 2, "cloud": 2, "ia": 2, "ai": 2,
    "cyber": 2, "tech": 2, "it": 2, "si": 2, "erp": 2, "crm": 2,
    # Conseil / management (poids moyen)
    "consultant": 2, "management": 2, "agile": 2, "transformation": 2,
    "innovation": 2, "scrum": 2, "product manager": 2,
    # Mots neutres positifs (poids faible)
    "manager": 1, "responsable": 1, "charge": 1, "ingenieur": 1,
}

SCORE_MIN = 2   # Score minimum pour qu'une offre soit conservée

MOTS_INTERDITS = [
    "ressources humaines", "recrutement", "talent acquisition", "paie",
    "comptabilite", "comptable", "controleur", "audit", "fiscal",
    "helpdesk", "maintenance", "mecanique", "usine", "soudeur", "fraiseur",
    "logistique", "supply chain", "acheteur", "approvisionnement",
    "graphiste", "communication externe", "relations presse",
    "juridique", "droit", "notaire",
    "electrotechni", "industriel", "production", "qualite",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# ─────────────────────────────────────────────
# DRIVER
# ─────────────────────────────────────────────

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")          # nouveau mode headless Chrome 112+
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    # Désactiver les images pour aller plus vite
    prefs = {"profile.managed_default_content_settings.images": 2}
    opts.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    # Masquer webdriver flag
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

def normaliser(texte):
    """Supprime accents + lowercase"""
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8').lower().strip()

def scorer_offre(titre):
    """
    Retourne un score de pertinence.
    0 = interdit, positif = pertinent, plus c'est élevé mieux c'est.
    """
    t = normaliser(titre)
    # Blocage absolu
    for mot in MOTS_INTERDITS:
        if mot in t:
            return 0
    # Calcul du score
    score = 0
    for mot, poids in MOTS_POSITIFS.items():
        if mot in t:
            score += poids
    return score

def cle_dedup(titre, entreprise, localisation):
    """Clé de déduplication normalisée (ignore majuscules/accents/espaces)"""
    return normaliser(titre)[:60] + "|" + normaliser(entreprise)[:20] + "|" + normaliser(localisation)[:15]

def charger_json_existant(chemin):
    """Charge le JSON existant pour ne pas perdre les données si le run échoue partiellement"""
    if os.path.exists(chemin):
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

# ─────────────────────────────────────────────
# SCROLL & EXTRACTION
# ─────────────────────────────────────────────

def scroll_et_charger(driver, nb_scrolls=5):
    """Scroll la page pour charger les offres en lazy loading"""
    for _ in range(nb_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.2, 2.2))
        # Cliquer sur "Afficher plus" si présent
        for selector in [
            "button.infinite-scroller__show-more-button",
            "button[aria-label*='plus']",
            "button.see-more-jobs",
        ]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    time.sleep(random.uniform(0.8, 1.5))
                    break
            except Exception:
                pass

def extraire_cards(driver):
    """Extrait les données de toutes les job cards visibles, avec fallback sélecteurs"""
    offres = []
    # Essaie plusieurs sélecteurs CSS (LinkedIn change parfois)
    CARD_SELECTORS = [".base-card", ".job-search-card", "li.jobs-search-results__list-item"]
    cards = []
    for sel in CARD_SELECTORS:
        cards = driver.find_elements(By.CSS_SELECTOR, sel)
        if cards:
            break

    for card in cards:
        try:
            titre = ""
            entreprise = ""
            localisation = ""
            lien = ""

            # Titre — plusieurs sélecteurs de secours
            for t_sel in [".base-search-card__title", "h3.base-search-card__title", ".job-search-card__title"]:
                try:
                    titre = card.find_element(By.CSS_SELECTOR, t_sel).text.strip()
                    if titre: break
                except Exception:
                    pass

            # Entreprise
            for e_sel in [".base-search-card__subtitle", "h4.base-search-card__subtitle"]:
                try:
                    entreprise = card.find_element(By.CSS_SELECTOR, e_sel).text.strip()
                    if entreprise: break
                except Exception:
                    pass

            # Localisation
            for l_sel in [".job-search-card__location", ".base-search-card__metadata"]:
                try:
                    loc = card.find_element(By.CSS_SELECTOR, l_sel).text.strip()
                    localisation = loc.split(',')[0].strip()
                    if localisation: break
                except Exception:
                    pass

            # Lien
            for a_sel in ["a.base-card__full-link", "a.job-search-card__list-date--new", "a"]:
                try:
                    href = card.find_element(By.CSS_SELECTOR, a_sel).get_attribute("href")
                    if href and "linkedin.com/jobs" in href:
                        lien = href.split("?")[0]  # Nettoie les params de tracking
                        break
                except Exception:
                    pass

            if titre and entreprise and lien:
                offres.append((titre, entreprise, localisation, lien))
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return offres

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"🚀 Scraper V11 — {len(GEANTS)} entreprises × {len(ANGLES)} angles = {len(GEANTS)*len(ANGLES)} requêtes")
    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    chemin_json = "offres_cac40.json"

    # Charge l'existant comme filet de sécurité
    offres_existantes = charger_json_existant(chemin_json)
    cles_existantes = {cle_dedup(o["titre"], o["entreprise"], o["localisation"]) for o in offres_existantes}

    nouvelles_offres = []
    cles_nouvelles = set()
    stats = {"total_scrappe": 0, "refuses_interdit": 0, "refuses_score": 0, "refuses_dedup": 0}

    driver = init_driver()

    try:
        for entreprise in GEANTS:
            print(f"  → {entreprise}")
            ent_norm = normaliser(entreprise)

            for angle in ANGLES:
                mots = f"{angle} {entreprise}".replace(" ", "%20")
                url = (
                    f"https://fr.linkedin.com/jobs/search"
                    f"?keywords={mots}"
                    f"&location=France"
                    f"&f_TPR=r2592000"   # 30 derniers jours
                    f"&f_JT=I"            # Type : Internship / Alternance
                    f"&sortBy=DD"         # Tri : les plus récentes d'abord
                )

                try:
                    driver.get(url)
                    time.sleep(random.uniform(2.0, 3.5))
                    scroll_et_charger(driver, nb_scrolls=5)

                    resultats = extraire_cards(driver)
                    stats["total_scrappe"] += len(resultats)

                    for titre, nom_ent, localisation, lien in resultats:
                        # 1. Vérifier que c'est la bonne entreprise
                        if ent_norm not in normaliser(nom_ent):
                            continue

                        # 2. Scorer l'offre
                        score = scorer_offre(titre)
                        if score == 0:
                            stats["refuses_interdit"] += 1
                            continue
                        if score < SCORE_MIN:
                            stats["refuses_score"] += 1
                            continue

                        # 3. Déduplication
                        cle = cle_dedup(titre, nom_ent, localisation)
                        if cle in cles_nouvelles or cle in cles_existantes:
                            stats["refuses_dedup"] += 1
                            continue

                        cles_nouvelles.add(cle)
                        nouvelles_offres.append({
                            "entreprise": nom_ent,
                            "titre": titre,
                            "localisation": localisation,
                            "lien": lien,
                            "score": score,          # Utile pour debug
                            "date_ajout": date_du_jour
                        })

                except Exception as e:
                    print(f"    ⚠️ Erreur sur '{angle} {entreprise}' : {e}")
                    continue

                # Pause anti-ban aléatoire entre les requêtes
                time.sleep(random.uniform(1.5, 3.0))

            # Pause plus longue entre entreprises
            time.sleep(random.uniform(2.0, 4.0))

    finally:
        driver.quit()

    # ─── Tri final par score décroissant ───
    nouvelles_offres.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n📊 Stats du run :")
    print(f"   Offres scrapées brutes   : {stats['total_scrappe']}")
    print(f"   Refusées (mot interdit)  : {stats['refuses_interdit']}")
    print(f"   Refusées (score < {SCORE_MIN})    : {stats['refuses_score']}")
    print(f"   Refusées (doublon)       : {stats['refuses_dedup']}")
    print(f"   Nouvelles offres valides : {len(nouvelles_offres)}")

    if len(nouvelles_offres) >= 5:
        with open(chemin_json, 'w', encoding='utf-8') as f:
            json.dump(nouvelles_offres, f, ensure_ascii=False, indent=4)
        print(f"✅ {chemin_json} mis à jour avec {len(nouvelles_offres)} offres triées par pertinence.")
    elif len(offres_existantes) > 0:
        print(f"⚠️ Moins de 5 nouvelles offres. Conservation du JSON existant ({len(offres_existantes)} offres).")
    else:
        print("❌ Aucune offre et pas de JSON existant — vérifier le scraper manuellement.")

if __name__ == "__main__":
    main()
