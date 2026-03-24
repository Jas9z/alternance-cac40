import json, time, random, unicodedata, os, re, sys
from datetime import datetime
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

# ═══ ENTREPRISES + ALIASES ═══

ENTREPRISES = [
    ("Air Liquide",        ["air liquide"]),
    ("Airbus",             ["airbus", "airbus group", "airbus defence", "airbus helicopters"]),
    ("Alstom",             ["alstom"]),
    ("ArcelorMittal",      ["arcelormittal"]),
    ("AXA",                ["axa", "axa france", "axa assurances", "axa partners"]),
    ("BNP Paribas",        ["bnp", "bnp paribas", "bnp paribas cardif"]),
    ("Bouygues",           ["bouygues", "bouygues telecom", "bouygues construction"]),
    ("Capgemini",          ["capgemini", "capgemini invent", "capgemini engineering", "sogeti"]),
    ("Carrefour",          ["carrefour"]),
    ("Credit Agricole",    ["credit agricole", "lcl", "amundi", "indosuez"]),
    ("Danone",             ["danone", "evian", "volvic"]),
    ("Dassault Systemes",  ["dassault", "dassault systemes", "3ds"]),
    ("Edenred",            ["edenred"]),
    ("Engie",              ["engie", "engie solutions", "tractebel"]),
    ("EssilorLuxottica",   ["essilor", "luxottica", "essilorluxottica"]),
    ("Hermes",             ["hermes"]),
    ("Kering",             ["kering", "gucci", "saint laurent", "balenciaga"]),
    ("LOreal",             ["loreal", "l oreal", "lancome", "maybelline", "garnier"]),
    ("Legrand",            ["legrand"]),
    ("LVMH",               ["lvmh", "louis vuitton", "dior", "sephora"]),
    ("Michelin",           ["michelin"]),
    ("Orange",             ["orange", "orange business", "orange cyberdefense"]),
    ("Pernod Ricard",      ["pernod", "pernod ricard"]),
    ("Publicis",           ["publicis", "publicis sapient", "leo burnett"]),
    ("Renault",            ["renault", "renault group", "ampere"]),
    ("Safran",             ["safran", "safran aircraft", "safran electronics"]),
    ("Sanofi",             ["sanofi"]),
    ("Schneider Electric", ["schneider", "schneider electric"]),
    ("Societe Generale",   ["societe generale", "sg", "boursorama", "ayvens"]),
    ("Stellantis",         ["stellantis", "peugeot", "citroen", "fiat"]),
    ("STMicro",            ["st", "stmicroelectronics"]),
    ("Teleperformance",    ["teleperformance"]),
    ("Thales",             ["thales", "thales six", "thales alenia"]),
    ("TotalEnergies",      ["totalenergies", "total"]),
    ("Unibail",            ["unibail", "westfield"]),
    ("Veolia",             ["veolia", "veolia water"]),
    ("Vinci",              ["vinci", "vinci construction", "vinci energies"]),
    ("Vivendi",            ["vivendi", "canal+", "canal plus", "havas"]),
    ("Microsoft",          ["microsoft", "microsoft france"]),
    ("Amazon",             ["amazon", "aws", "amazon web services"]),
    ("Google",             ["google", "google france", "alphabet"]),
    ("Salesforce",         ["salesforce", "tableau", "slack"]),
    ("SAP",                ["sap", "sap france"]),
    ("Oracle",             ["oracle", "oracle france"]),
    ("IBM",                ["ibm", "ibm france"]),
    ("Cisco",              ["cisco"]),
    ("Accenture",          ["accenture"]),
    ("Deloitte",           ["deloitte"]),
    ("EY",                 ["ey", "ernst young", "ernst & young"]),
    ("PwC",                ["pwc", "pricewaterhousecoopers"]),
    ("KPMG",               ["kpmg"]),
    ("Sopra Steria",       ["sopra", "sopra steria", "sopra banking"]),
    ("CGI",                ["cgi", "cgi france"]),
    ("Wavestone",          ["wavestone"]),
    ("EDF",                ["edf", "edf renouvelables"]),
    ("SNCF",               ["sncf", "keolis", "ouigo", "eurostar"]),
    ("CMA CGM",            ["cma cgm", "cma"]),
    ("La Poste",           ["la poste", "docaposte", "chronopost"]),
    ("Naval Group",        ["naval group"]),
    ("Siemens",            ["siemens", "siemens energy"]),
    ("Nestle",             ["nestle", "nespresso"]),
    ("Unilever",           ["unilever"]),
]

N = len(ENTREPRISES)
BATCHS = {
    "A": ENTREPRISES[:N//4],
    "B": ENTREPRISES[N//4:N//2],
    "C": ENTREPRISES[N//2:3*N//4],
    "D": ENTREPRISES[3*N//4:],
}

# ═══ ANGLES ═══

ANGLES = [
    "Alternance ingenieur affaires",
    "Alternance avant-vente",
    "Alternance technico-commercial",
    "Alternance business developer",
    "Alternance chef de projet IT",
    "Alternance account manager",
]

ANGLES_APEC = [
    "ingenieur affaires alternance",
    "avant-vente alternance",
    "technico-commercial alternance",
    "pre-sales alternance",
    "charge deploiement alternance",
    "business developer alternance",
]

# ═══ SCORING ═══

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
    "chef de projet": 5, "project manager": 5, "deploiement": 6,
    "consultant": 4, "strategy": 4, "strategie": 4, "transformation": 3,
    "cloud": 2, "data": 2, "saas": 2, "erp": 2, "crm": 2,
    "telecom": 2, "si": 2, "it": 2, "tech": 2, "cyber": 2,
    "manager": 2, "management": 2, "ingenieur": 1, "charge": 1,
}

SCORE_MIN = 3

METIERS_PRIORITAIRES = [
    "avant-vente", "avant vente", "pre-sales", "presales",
    "technico-commercial", "ingenieur affaires", "ingenieur d affaires",
    "charge affaires", "charge de deploiement", "solution engineer",
    "business manager", "ppo",
]

MOTS_INTERDITS = [
    "ressources humaines", "recrutement", "talent acquisition", "paie", "payroll",
    "comptabilite", "comptable", "controleur de gestion", "audit", "fiscal",
    "helpdesk", "technicien support", "support technique", "hotline",
    "maintenance", "mecanique", "usine", "soudeur", "fraiseur",
    "electrotechni", "production", "operateur",
    "logistique", "supply chain", "acheteur", "approvisionnement",
    "graphiste", "motion design", "ux design", "ui design",
    "communication externe", "relations presse",
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

# ═══ DRIVER ═══

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
    driver.set_page_load_timeout(20)
    return driver

# ═══ UTILITAIRES ═══

def norm(t):
    if not t:
        return ""
    return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode('utf-8').lower().strip()

def scorer(titre):
    t = norm(titre)
    for m in MOTS_INTERDITS:
        if m in t:
            return 0, []
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

def cle(titre, ent, loc):
    return norm(titre)[:55] + "|" + re.sub(r'\s+', '', norm(ent))[:15] + "|" + norm(loc)[:10]

# ═══ SCROLL ═══

def scroll(driver, nb=4):
    for _ in range(nb):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.8, 1.5))
        for sel in ["button.infinite-scroller__show-more-button", "button.see-more-jobs"]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    time.sleep(0.8)
                    break
            except:
                pass

# ═══ EXTRACTION LINKEDIN ═══

def get_text(card, selectors):
    """Essaie plusieurs sélecteurs CSS et retourne le premier texte trouvé."""
    for s in selectors:
        try:
            val = card.find_element(By.CSS_SELECTOR, s).text.strip()
            if val:
                return val
        except:
            pass
    return ""

def get_href(card, selectors, keyword):
    """Essaie plusieurs sélecteurs et retourne le premier href contenant keyword."""
    for s in selectors:
        try:
            href = card.find_element(By.CSS_SELECTOR, s).get_attribute("href") or ""
            if keyword in href:
                return href.split("?")[0]
        except:
            pass
    return ""

def extraire(driver):
    offres = []
    cards = []
    for sel in [".base-card", ".job-search-card"]:
        cards = driver.find_elements(By.CSS_SELECTOR, sel)
        if cards:
            break
    for card in cards:
        try:
            titre = get_text(card, [".base-search-card__title", "h3.base-search-card__title"])
            ent   = get_text(card, [".base-search-card__subtitle", "h4.base-search-card__subtitle"])
            loc   = get_text(card, [".job-search-card__location", ".base-search-card__metadata"]).split(',')[0].strip()
            lien  = get_href(card, ["a.base-card__full-link", "a"], "linkedin.com/jobs")
            if titre and ent and lien:
                offres.append({"titre": titre, "entreprise": ent, "localisation": loc, "lien": lien})
        except StaleElementReferenceException:
            continue
        except:
            continue
    return offres

# ═══ EXTRACTION APEC ═══

def extraire_apec(driver, mots, aliases_toutes):
    offres = []
    url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles={quote_plus(mots)}&typeContrat=148990&nbResultats=50"
    try:
        driver.get(url)
        time.sleep(random.uniform(2.5, 4.0))
        scroll(driver, nb=2)
        for card in driver.find_elements(By.CSS_SELECTOR, ".card-offer, article.job"):
            try:
                titre = get_text(card, ["h2.card-title", ".card-offer__title", "h2"])
                ent   = get_text(card, [".card-offer__company", ".company-name"])
                loc   = get_text(card, [".card-offer__location", ".location"]).split(',')[0]
                lien  = get_href(card, ["a"], "apec.fr")
                if titre and lien and any(a in norm(ent) for a in aliases_toutes):
                    offres.append({"titre": titre, "entreprise": ent, "localisation": loc, "lien": lien})
            except:
                continue
    except Exception as e:
        print(f"  ⚠️ APEC: {e}")
    return offres

# ═══ MAIN ═══

METIERS_PRIORITAIRES = [
    "avant-vente", "avant vente", "pre-sales", "presales",
    "technico-commercial", "ingenieur affaires", "ingenieur d affaires",
    "charge affaires", "charge de deploiement", "solution engineer",
    "business manager", "ppo",
]

def main():
    batch = "A"
    if "--batch" in sys.argv:
        i = sys.argv.index("--batch")
        batch = sys.argv[i + 1].upper() if i + 1 < len(sys.argv) else "A"

    entreprises = BATCHS.get(batch, BATCHS["A"])
    fichier = f"offres_batch_{batch}.json"
    aliases_toutes = [a for _, als in ENTREPRISES for a in als]
    date = datetime.now().strftime("%d/%m/%Y")

    print(f"🚀 Batch {batch} — {len(entreprises)} entreprises × {len(ANGLES)} angles = {len(entreprises) * len(ANGLES)} requêtes")

    offres = []
    vues = set()
    driver = init_driver()

    try:
        for nom, aliases in entreprises:
            print(f"  → {nom}")
            for angle in ANGLES:
                url = (
                    f"https://fr.linkedin.com/jobs/search"
                    f"?keywords={quote_plus(angle + ' ' + nom)}"
                    f"&location=France&f_TPR=r2592000&f_JT=I&sortBy=DD"
                )
                try:
                    driver.get(url)
                    time.sleep(random.uniform(1.5, 2.5))
                    scroll(driver)
                    for r in extraire(driver):
                        en = norm(r["entreprise"])
                        if not any(a in en for a in aliases):
                            continue
                        score, matches = scorer(r["titre"])
                        if score == 0 or score < SCORE_MIN:
                            continue
                        k = cle(r["titre"], r["entreprise"], r["localisation"])
                        if k in vues:
                            continue
                        vues.add(k)
                        offres.append({
                            "entreprise": r["entreprise"],
                            "titre": r["titre"],
                            "localisation": r["localisation"],
                            "lien": r["lien"],
                            "score": score,
                            "mots_cles_matches": matches,
                            "source": "LinkedIn",
                            "first_seen": date,
                            "last_seen": date,
                            "is_priority": any(p in norm(r["titre"]) for p in METIERSPRIORITAIRES),
                        })
                except Exception as e:
                    print(f"    ⚠️ {e}")
                time.sleep(random.uniform(1.0, 2.0))
            time.sleep(random.uniform(1.0, 2.0))

        if batch == "A":
            print(f"\n🟡 APEC ({len(ANGLES_APEC)} requêtes)")
            for mots in ANGLES_APEC:
                print(f"  → {mots}")
                for r in extraire_apec(driver, mots, aliases_toutes):
                    score, matches = scorer(r["titre"])
                    if score == 0 or score < SCORE_MIN:
                        continue
                    k = cle(r["titre"], r["entreprise"], r["localisation"])
                    if k in vues:
                        continue
                    vues.add(k)
                    offres.append({
                        "entreprise": r["entreprise"],
                        "titre": r["titre"],
                        "localisation": r["localisation"],
                        "lien": r["lien"],
                        "score": score,
                        "mots_cles_matches": matches,
                        "source": "APEC",
                        "first_seen": date,
                        "last_seen": date,
                        "is_priority": any(p in norm(r["titre"]) for p in METIERSPRIORITAIRES),
                    })
                time.sleep(random.uniform(2.0, 3.0))
    finally:
        driver.quit()

    offres.sort(key=lambda x: (not x.get("is_priority", False), -x["score"]))
    print(f"\n✅ Batch {batch} : {len(offres)} offres → {fichier}")
    if offres:
        print("🏆 Top 5 :")
        for o in offres[:5]:
            flag = "⭐" if o.get("is_priority") else "  "
            print(f"  {flag}[{o['score']}pts] {o['titre']} — {o['entreprise']}")

    json.dump(offres, open(fichier, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
