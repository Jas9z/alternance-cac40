import json
import time
import random
import unicodedata
import os
import re
import sys
from datetime import datetime
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

# ═══════════════════════════════════════════════
# ENTREPRISES + ALIASES
# ═══════════════════════════════════════════════

ENTREPRISES = [
    ("Air Liquide",         ["air liquide"]),
    ("Airbus",              ["airbus", "airbus group", "airbus defence", "airbus helicopters"]),
    ("Alstom",              ["alstom"]),
    ("ArcelorMittal",       ["arcelormittal"]),
    ("AXA",                 ["axa", "axa france", "axa assurances", "axa partners"]),
    ("BNP Paribas",         ["bnp", "bnp paribas", "bnp paribas cardif"]),
    ("Bouygues",            ["bouygues", "bouygues telecom", "bouygues construction"]),
    ("Capgemini",           ["capgemini", "capgemini invent", "capgemini engineering", "sogeti"]),
    ("Carrefour",           ["carrefour"]),
    ("Crédit Agricole",     ["credit agricole", "lcl", "amundi", "indosuez"]),
    ("Danone",              ["danone", "evian", "volvic"]),
    ("Dassault Systèmes",   ["dassault", "dassault systemes", "3ds"]),
    ("Edenred",             ["edenred"]),
    ("Engie",               ["engie", "engie solutions", "tractebel"]),
    ("EssilorLuxottica",    ["essilor", "luxottica", "essilorluxottica"]),
    ("Hermès",              ["hermes"]),
    ("Kering",              ["kering", "gucci", "saint laurent", "balenciaga"]),
    ("L'Oréal",             ["loreal", "l oreal", "lancome", "maybelline", "garnier"]),
    ("Legrand",             ["legrand"]),
    ("LVMH",                ["lvmh", "louis vuitton", "dior", "sephora", "tag heuer"]),
    ("Michelin",            ["michelin"]),
    ("Orange",              ["orange", "orange business", "orange cyberdefense"]),
    ("Pernod Ricard",       ["pernod", "pernod ricard"]),
    ("Publicis",            ["publicis", "publicis sapient", "leo burnett"]),
    ("Renault",             ["renault", "renault group", "ampere"]),
    ("Safran",              ["safran", "safran aircraft", "safran electronics"]),
    ("Sanofi",              ["sanofi"]),
    ("Schneider Electric",  ["schneider", "schneider electric"]),
    ("Société Générale",   ["societe generale", "sg", "boursorama", "ayvens"]),
    ("Stellantis",          ["stellantis", "peugeot", "citroen", "fiat"]),
    ("STMicroelectronics",  ["st", "stmicroelectronics"]),
    ("Teleperformance",     ["teleperformance"]),
    # ─ BATCH B ─
    ("Thales",              ["thales", "thales six", "thales alenia"]),
    ("TotalEnergies",       ["totalenergies", "total"]),
    ("Unibail-Rodamco",     ["unibail", "westfield"]),
    ("Veolia",              ["veolia", "veolia water"]),
    ("Vinci",               ["vinci", "vinci construction", "vinci energies"]),
    ("Vivendi",             ["vivendi", "canal+", "canal plus", "havas"]),
    ("Microsoft",           ["microsoft", "microsoft france"]),
    ("Amazon",              ["amazon", "aws", "amazon web services"]),
    ("Google",              ["google", "google france", "alphabet"]),
    ("Salesforce",          ["salesforce", "tableau", "slack"]),
    ("SAP",                 ["sap", "sap france"]),
    ("Oracle",              ["oracle", "oracle france"]),
    ("IBM",                 ["ibm", "ibm france"]),
    ("Cisco",               ["cisco"]),
    ("Accenture",           ["accenture"]),
    ("Deloitte",            ["deloitte"]),
    ("EY",                  ["ey", "ernst young", "ernst & young"]),
    ("PwC",                 ["pwc", "pricewaterhousecoopers"]),
    ("KPMG",                ["kpmg"]),
    ("Sopra Steria",        ["sopra", "sopra steria", "sopra banking"]),
    ("CGI",                 ["cgi", "cgi france"]),
    ("Wavestone",           ["wavestone"]),
    ("EDF",                 ["edf", "edf renouvelables"]),
    ("Groupe SNCF",         ["sncf", "keolis", "ouigo", "eurostar"]),
    ("CMA CGM",             ["cma cgm", "cma"]),
    ("La Poste Groupe",     ["la poste", "docaposte", "chronopost"]),
    ("Naval Group",         ["naval group"]),
    ("Siemens",             ["siemens", "siemens energy"]),
    ("Nestlé",              ["nestle", "nespresso"]),
    ("Unilever",            ["unilever"]),
]

BATCH_SIZE = len(ENTREPRISES) // 2  # ~32 entreprises par batch
ENTREPRISES_A = ENTREPRISES[:BATCH_SIZE]
ENTREPRISES_B = ENTREPRISES[BATCH_SIZE:]

# ═══════════════════════════════════════════════
# ANGLES
# ═══════════════════════════════════════════════

ANGLES_LINKEDIN = [
    "Alternance ingénieur affaires",
    "Alternance chargé affaires",
    "Alternance business developer",
    "Alternance commercial IT",
    "Alternance technico-commercial",
    "Alternance account manager",
    "Alternance key account manager",
    "Alternance avant-vente",
    "Alternance pre-sales",
    "Alternance solution engineer",
    "Alternance chef de projet digital",
    "Alternance chargé de déploiement",
    "Alternance business manager",
    "Alternance consultant digital",
    "Alternance chef de projet IT",
]

ANGLES_APEC = [
    "ingénieur d'affaires alternance",
    "avant-vente alternance",
    "pre-sales alternance",
    "technico-commercial alternance",
    "chargé de déploiement alternance",
    "business developer alternance",
    "chef de projet IT alternance",
]

# ═══════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════

MOTS_POSITIFS = {
    "avant-vente": 8, "avant vente": 8, "pre-sales": 8, "presales": 8,
    "solution engineer": 8, "solution architect": 7,
    "technico-commercial": 8, "technico commercial": 8,
    "ingenieur d affaires": 8, "ingenieur affaires": 8,
    "charge d affaires": 8, "charge affaires": 8,
    "charge de deploiement": 8, "ppo": 7,
    "business manager": 7, "ingenieur commercial": 7,
    "business developer": 6, "business development": 6,
    "key account": 6, "account manager": 6, "kam": 6,
    "commercial": 5, "business": 5, "sales": 5, "vente": 5, "b2b": 5,
    "developpement commercial": 6,
    "chef de projet": 5, "project manager": 5,
    "deploiement": 6, "delivery": 4, "pilotage": 4,
    "consultant": 4, "strategy": 4, "strategie": 4,
    "transformation": 3, "partenariat": 3, "digital": 2,
    "cloud": 2, "data": 2, "ia": 2, "saas": 2, "erp": 2, "crm": 2,
    "telecom": 2, "si": 2, "it": 2, "tech": 2, "cyber": 2,
    "manager": 2, "management": 2, "responsable": 1, "ingenieur": 1, "charge": 1,
}

SCORE_MIN = 3

METIERS_PRIORITAIRES = [
    "avant-vente", "avant vente", "pre-sales", "presales",
    "technico-commercial", "technico commercial",
    "ingenieur affaires", "ingenieur d affaires",
    "charge affaires", "charge de deploiement",
    "solution engineer", "business manager", "ppo",
]

MOTS_INTERDITS = [
    "ressources humaines", "recrutement", "talent acquisition", "paie", "payroll",
    "comptabilite", "comptable", "controleur de gestion", "audit", "fiscal",
    "helpdesk", "technicien support", "support technique", "hotline",
    "maintenance", "mecanique", "usine", "soudeur", "fraiseur",
    "electrotechni", "production", "operateur",
    "logistique", "supply chain", "acheteur", "approvisionnement",
    "graphiste", "motion design", "ux design", "ui design",
    "communication externe", "relations presse", "redacteur",
    "juridique", "droit", "paralegal",
    "qualite", "qhse", "hse",
    "stage ",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# ═══════════════════════════════════════════════
# DRIVER
# ═══════════════════════════════════════════════

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
    opts.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    driver.set_page_load_timeout(30)
    return driver

# ═══════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════

def normaliser(texte):
    if not texte: return ""
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8').lower().strip()

def scorer_offre(titre):
    t = normaliser(titre)
    for mot in MOTS_INTERDITS:
        if mot in t: return 0, []
    score, matches = 0, []
    for mot, poids in MOTS_POSITIFS.items():
        if mot in t:
            score += poids
            matches.append(mot)
    for p in METIERSPRIORITAIRES:
        if p in t:
            score += 3
            break
    return score, matches

def cle_dedup(titre, entreprise, localisation):
    return normaliser(titre)[:55] + "|" + re.sub(r'\s+','',normaliser(entreprise))[:15] + "|" + normaliser(localisation)[:10]

def charger_json(chemin):
    if os.path.exists(chemin):
        try:
            return json.load(open(chemin, encoding='utf-8'))
        except: pass
    return []

# ═══════════════════════════════════════════════
# SCROLL & EXTRACTION
# ═══════════════════════════════════════════════

def scroll_et_charger(driver, nb=5):
    for _ in range(nb):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.0, 1.8))
        for sel in ["button.infinite-scroller__show-more-button", "button.see-more-jobs"]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    time.sleep(random.uniform(0.7, 1.2))
                    break
            except: pass

def extraire_cards(driver, source="LinkedIn"):
    offres = []
    cards = []
    for sel in [".base-card", ".job-search-card", "li.jobs-search-results__list-item"]:
        cards = driver.find_elements(By.CSS_SELECTOR, sel)
        if cards: break
    for card in cards:
        try:
            titre = entreprise = localisation = lien = ""
            for s in [".base-search-card__title", "h3.base-search-card__title"]:
                try:
                    titre = card.find_element(By.CSS_SELECTOR, s).text.strip()
                    if titre: break
                except: pass
            for s in [".base-search-card__subtitle", "h4.base-search-card__subtitle"]:
                try:
                    entreprise = card.find_element(By.CSS_SELECTOR, s).text.strip()
                    if entreprise: break
                except: pass
            for s in [".job-search-card__location", ".base-search-card__metadata"]:
                try:
                    localisation = card.find_element(By.CSS_SELECTOR, s).text.strip().split(',')[0].strip()
                    if localisation: break
                except: pass
            for s in ["a.base-card__full-link", "a"]:
                try:
                    href = card.find_element(By.CSS_SELECTOR, s).get_attribute("href") or ""
                    if "linkedin.com/jobs" in href:
                        lien = href.split("?")[0]
                        break
                except: pass
            if titre and entreprise and lien:
                offres.append({"titre": titre, "entreprise": entreprise,
                               "localisation": localisation, "lien": lien})
        except StaleElementReferenceException: continue
        except: continue
    return offres

def scraper_apec(driver, mots_cles, aliases_toutes):
    offres = []
    url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles={quote_plus(mots_cles)}&typeContrat=148990&nbResultats=50"
    try:
        driver.get(url)
        time.sleep(random.uniform(3.0, 5.0))
        scroll_et_charger(driver, nb=3)
        cards = driver.find_elements(By.CSS_SELECTOR, ".card-offer, article.job, .result-item")
        for card in cards:
            try:
                titre = entreprise = localisation = lien = ""
                for s in ["h2.card-title", ".card-offer__title", "h2", "h3"]:
                    try:
                        titre = card.find_element(By.CSS_SELECTOR, s).text.strip()
                        if titre: break
                    except: pass
                for s in [".card-offer__company", ".company-name"]:
                    try:
                        entreprise = card.find_element(By.CSS_SELECTOR, s).text.strip()
                        if entreprise: break
                    except: pass
                for s in [".card-offer__location", ".location"]:
                    try:
                        localisation = card.find_element(By.CSS_SELECTOR, s).text.strip().split(',')[0]
                        if localisation: break
                    except: pass
                try:
                    href = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href") or ""
                    if "apec.fr" in href: lien = href.split("?")[0]
                except: pass
                if titre and lien and any(a in normaliser(entreprise) for a in aliases_toutes):
                    offres.append({"titre": titre, "entreprise": entreprise,
                                   "localisation": localisation, "lien": lien})
            except: continue
    except Exception as e:
        print(f"    ⚠️ APEC '{mots_cles}': {e}")
    return offres

# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

METIERS_PRIORITAIRES = [
    "avant-vente", "avant vente", "pre-sales", "presales",
    "technico-commercial", "ingenieur affaires", "ingenieur d affaires",
    "charge affaires", "charge de deploiement", "solution engineer",
    "business manager", "ppo",
]

def traiter_offres(resultats, aliases, cles_vues, date_du_jour, source):
    nouvelles = []
    stats = {"interdit": 0, "score_bas": 0, "dedup": 0, "ok": 0}
    for r in resultats:
        ent_norm = normaliser(r["entreprise"])
        if not any(a in ent_norm for a in aliases): continue
        score, matches = scorer_offre(r["titre"])
        if score == 0: stats["interdit"] += 1; continue
        if score < SCORE_MIN: stats["score_bas"] += 1; continue
        cle = cle_dedup(r["titre"], r["entreprise"], r["localisation"])
        if cle in cles_vues: stats["dedup"] += 1; continue
        cles_vues.add(cle)
        stats["ok"] += 1
        nouvelles.append({
            "entreprise": r["entreprise"], "titre": r["titre"],
            "localisation": r["localisation"], "lien": r["lien"],
            "score": score, "mots_cles_matches": matches, "source": source,
            "first_seen": date_du_jour, "last_seen": date_du_jour,
            "is_priority": any(p in normaliser(r["titre"]) for p in METIERSPRIORITAIRES),
        })
    return nouvelles, stats

def main():
    # Déterminer le batch depuis l'argument CLI
    batch = "A"
    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        batch = sys.argv[idx + 1].upper() if idx + 1 < len(sys.argv) else "A"

    entreprises = ENTREPRISES_A if batch == "A" else ENTREPRISES_B
    fichier_sortie = f"offres_batch_{batch}.json"
    aliases_toutes = [a for _, aliases in ENTREPRISES for a in aliases]

    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    print(f"🚀 Scraper V13 — Batch {batch} ({len(entreprises)} entreprises × {len(ANGLES_LINKEDIN)} angles)")
    if batch == "A":
        print(f"   + APEC : {len(ANGLES_APEC)} requêtes métier")

    toutes_offres = []
    cles_vues = set()
    driver = init_driver()

    try:
        # LinkedIn
        for nom, aliases in entreprises:
            print(f"  → {nom}")
            for angle in ANGLES_LINKEDIN:
                url = (
                    f"https://fr.linkedin.com/jobs/search"
                    f"?keywords={quote_plus(angle + ' ' + nom)}"
                    f"&location=France&f_TPR=r2592000&f_JT=I&sortBy=DD"
                )
                try:
                    driver.get(url)
                    time.sleep(random.uniform(1.8, 3.0))
                    scroll_et_charger(driver)
                    resultats = extraire_cards(driver)
                    nouvelles, _ = traiter_offres(resultats, aliases, cles_vues, date_du_jour, "LinkedIn")
                    toutes_offres.extend(nouvelles)
                except Exception as e:
                    print(f"    ⚠️ {e}")
                time.sleep(random.uniform(1.2, 2.5))
            time.sleep(random.uniform(1.5, 3.0))

        # APEC (seulement dans le batch A pour éviter les doublons)
        if batch == "A":
            print(f"\n🟡 APEC ({len(ANGLES_APEC)} requêtes)")
            for mots in ANGLES_APEC:
                print(f"  → {mots}")
                resultats_apec = scraper_apec(driver, mots, aliases_toutes)
                nouvelles, _ = traiter_offres(resultats_apec, aliases_toutes, cles_vues, date_du_jour, "APEC")
                toutes_offres.extend(nouvelles)
                time.sleep(random.uniform(2.0, 3.5))

    finally:
        driver.quit()

    toutes_offres.sort(key=lambda x: (not x.get("is_priority", False), -x["score"]))

    print(f"\n✅ Batch {batch} : {len(toutes_offres)} offres → {fichier_sortie}")
    if toutes_offres:
        print("🏆 Top 5 :")
        for o in toutes_offres[:5]:
            prio = "⭐" if o.get("is_priority") else "  "
            print(f"   {prio}[{o['score']}pts] {o['titre']} — {o['entreprise']}")

    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        json.dump(toutes_offres, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
