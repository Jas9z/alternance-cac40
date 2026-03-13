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
from selenium.common.exceptions import StaleElementReferenceException

# ─────────────────────────────
# ENTREPRISES
# ─────────────────────────────

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

# ─────────────────────────────
# ANGLES DE RECHERCHE (15 angles couvrant tous les métiers cibles)
# ─────────────────────────────

ANGLES = [
    # Métiers commerciaux & affaires
    "Alternance ingénieur affaires",
    "Alternance chargé affaires",
    "Alternance business developer",
    "Alternance commercial IT",
    "Alternance technico-commercial",
    "Alternance account manager",
    "Alternance key account manager",
    # Avant-vente & pre-sales
    "Alternance avant-vente",
    "Alternance pre-sales engineer",
    "Alternance ingenieur avant-vente",
    # Projet & déploiement
    "Alternance chef de projet digital",
    "Alternance chargé de déploiement",
    "Alternance chef de projet PPO",
    "Alternance business manager",
    # Conseil & digital
    "Alternance consultant digital",
]

# ─────────────────────────────
# SCORING (poids par mot-clé dans le titre)
# ─────────────────────────────

MOTS_POSITIFS = {
    # ★ Avant-vente / pre-sales (poids maximum = métier exact de Jasim)
    "avant-vente": 6, "avant vente": 6, "avante vente": 6,
    "pre-sales": 6, "presales": 6, "pre sales": 6,
    "ingenieur avant": 6, "solution engineer": 6, "solution architect": 5,

    # ★ Technico-commercial (métier exact)
    "technico-commercial": 6, "technico commercial": 6,
    "ingenieur commercial": 5, "ingenieur d affaires": 5,
    "ingenieur affaires": 5, "charge d affaires": 5, "charge affaires": 5,

    # ★ Business / vente (poids fort)
    "business": 4, "account": 4, "commercial": 4,
    "sales": 4, "vente": 4, "b2b": 4, "kam": 4,
    "business manager": 5, "business developer": 5,
    "key account": 5, "account manager": 5,
    "business development": 4, "developpement commercial": 4,

    # ★ Déploiement & projet (métier exact)
    "deploiement": 5, "deployment": 5, "charge de deploiement": 6,
    "chef de projet": 4, "project manager": 4, "ppo": 5,
    "pilotage": 3, "coordination": 3, "delivery": 3,

    # ★ Conseil / digital (poids moyen)
    "consultant": 3, "consulting": 3,
    "digital": 2, "transformation": 2, "innovation": 2,
    "strategy": 3, "strategie": 3, "partenariat": 3,

    # ★ Tech / IT (poids moyen — pertinent si combiné à autre chose)
    "data": 2, "cloud": 2, "ia": 2, "ai": 2,
    "cyber": 2, "tech": 2, "it": 2, "erp": 2, "crm": 2,
    "saas": 2, "telecom": 2, "reseau": 2, "si": 2,

    # ★ Management / responsabilité (poids faible)
    "manager": 2, "responsable": 1, "charge": 1, "ingenieur": 1,
    "management": 2, "pilote": 2,
}

# Score minimum pour retenir une offre
SCORE_MIN = 3

# ─────────────────────────────
# MOTS INTERDITS (blocage absolu)
# ─────────────────────────────

MOTS_INTERDITS = [
    # RH
    "ressources humaines", "recrutement", "talent acquisition", "paie", "payroll",
    # Finance / compta
    "comptabilite", "comptable", "controleur", "audit", "fiscal", "tresorerie",
    # Support technique (pas commercial)
    "helpdesk", "technicien", "support technique", "hotline",
    # Production / industrie
    "maintenance", "mecanique", "usine", "soudeur", "fraiseur",
    "electrotechni", "industriel", "production", "operateur",
    # Supply chain / achats
    "logistique", "supply chain", "acheteur", "approvisionnement", "entrepot",
    # Communication / design
    "graphiste", "communication externe", "relations presse", "redacteur",
    # Juridique
    "juridique", "droit", "notaire", "paralegal",
    # Qualité
    "qualite", "qhse", "hse",
    # Stage explicitement (on veut alternance)
    "stage ",   # espace pour ne pas bloquer "Dassault Systèmes"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# ─────────────────────────────
# DRIVER
# ─────────────────────────────

def init_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    prefs = {"profile.managed_default_content_settings.images": 2}
    opts.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

# ─────────────────────────────
# UTILITAIRES
# ─────────────────────────────

def normaliser(texte):
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8').lower().strip()

def scorer_offre(titre):
    t = normaliser(titre)
    for mot in MOTS_INTERDITS:
        if mot in t:
            return 0
    score = 0
    for mot, poids in MOTS_POSITIFS.items():
        if mot in t:
            score += poids
    return score

def cle_dedup(titre, entreprise, localisation):
    return normaliser(titre)[:60] + "|" + normaliser(entreprise)[:20] + "|" + normaliser(localisation)[:15]

def charger_json_existant(chemin):
    if os.path.exists(chemin):
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

# ─────────────────────────────
# SCROLL & EXTRACTION
# ─────────────────────────────

def scroll_et_charger(driver, nb_scrolls=5):
    for _ in range(nb_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.2, 2.2))
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
    offres = []
    cards = []
    for sel in [".base-card", ".job-search-card", "li.jobs-search-results__list-item"]:
        cards = driver.find_elements(By.CSS_SELECTOR, sel)
        if cards:
            break

    for card in cards:
        try:
            titre, entreprise, localisation, lien = "", "", "", ""

            for t_sel in [".base-search-card__title", "h3.base-search-card__title", ".job-search-card__title"]:
                try:
                    titre = card.find_element(By.CSS_SELECTOR, t_sel).text.strip()
                    if titre: break
                except Exception:
                    pass

            for e_sel in [".base-search-card__subtitle", "h4.base-search-card__subtitle"]:
                try:
                    entreprise = card.find_element(By.CSS_SELECTOR, e_sel).text.strip()
                    if entreprise: break
                except Exception:
                    pass

            for l_sel in [".job-search-card__location", ".base-search-card__metadata"]:
                try:
                    localisation = card.find_element(By.CSS_SELECTOR, l_sel).text.strip().split(',')[0].strip()
                    if localisation: break
                except Exception:
                    pass

            for a_sel in ["a.base-card__full-link", "a.job-search-card__list-date--new", "a"]:
                try:
                    href = card.find_element(By.CSS_SELECTOR, a_sel).get_attribute("href")
                    if href and "linkedin.com/jobs" in href:
                        lien = href.split("?")[0]
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

# ─────────────────────────────
# MAIN
# ─────────────────────────────

def main():
    total_requetes = len(GEANTS) * len(ANGLES)
    print(f"🚀 Scraper V12 — {len(GEANTS)} entreprises × {len(ANGLES)} angles = {total_requetes} requêtes")
    print(f"   Métiers cibles : avant-vente, technico-commercial, chargé déploiement, PPO, business manager, pre-sales")
    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    chemin_json = "offres_cac40.json"

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
                    f"&f_TPR=r2592000"
                    f"&f_JT=I"
                    f"&sortBy=DD"
                )

                try:
                    driver.get(url)
                    time.sleep(random.uniform(2.0, 3.5))
                    scroll_et_charger(driver, nb_scrolls=5)

                    resultats = extraire_cards(driver)
                    stats["total_scrappe"] += len(resultats)

                    for titre, nom_ent, localisation, lien in resultats:
                        if ent_norm not in normaliser(nom_ent):
                            continue

                        score = scorer_offre(titre)
                        if score == 0:
                            stats["refuses_interdit"] += 1
                            continue
                        if score < SCORE_MIN:
                            stats["refuses_score"] += 1
                            continue

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
                            "score": score,
                            "date_ajout": date_du_jour
                        })

                except Exception as e:
                    print(f"    ⚠️ Erreur : {e}")
                    continue

                time.sleep(random.uniform(1.5, 3.0))

            time.sleep(random.uniform(2.0, 4.0))

    finally:
        driver.quit()

    nouvelles_offres.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n📊 Stats du run :")
    print(f"   Offres scrapées brutes   : {stats['total_scrappe']}")
    print(f"   Refusées (mot interdit)  : {stats['refuses_interdit']}")
    print(f"   Refusées (score < {SCORE_MIN})    : {stats['refuses_score']}")
    print(f"   Refusées (doublon)       : {stats['refuses_dedup']}")
    print(f"   Nouvelles offres valides : {len(nouvelles_offres)}")

    # Affiche le top 10 pour vérifier la qualité
    if nouvelles_offres:
        print(f"\n🏆 Top 10 offres les plus pertinentes :")
        for o in nouvelles_offres[:10]:
            print(f"   [{o['score']} pts] {o['titre']} — {o['entreprise']} ({o['localisation']})")

    if len(nouvelles_offres) >= 5:
        with open(chemin_json, 'w', encoding='utf-8') as f:
            json.dump(nouvelles_offres, f, ensure_ascii=False, indent=4)
        print(f"\n✅ {len(nouvelles_offres)} offres enregistrées dans {chemin_json}")
    elif len(offres_existantes) > 0:
        print(f"⚠️ Moins de 5 nouvelles offres. Conservation de l'existant ({len(offres_existantes)} offres).")
    else:
        print("❌ Aucune offre — vérifier manuellement.")

if __name__ == "__main__":
    main()
