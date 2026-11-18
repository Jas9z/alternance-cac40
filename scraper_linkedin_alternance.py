import json, time, random, unicodedata, re, os
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# ═══ ENTREPRISES CAC40 + ALIASES ═══

ENTREPRISES = [
    ("Air Liquide", ["air liquide"]),
    ("Airbus", ["airbus"]),
    ("Alstom", ["alstom"]),
    ("ArcelorMittal", ["arcelormittal"]),
    ("AXA", ["axa"]),
    ("BNP Paribas", ["bnp"]),
    ("Bouygues", ["bouygues"]),
    ("Capgemini", ["capgemini"]),
    ("Carrefour", ["carrefour"]),
    ("Credit Agricole", ["credit agricole", "lcl"]),
    ("Danone", ["danone"]),
    ("Dassault Systemes", ["dassault"]),
    ("Edenred", ["edenred"]),
    ("Engie", ["engie"]),
    ("EssilorLuxottica", ["essilor", "luxottica"]),
    ("Hermes", ["hermes"]),
    ("Kering", ["kering"]),
    ("LOreal", ["loreal", "l oreal"]),
    ("Legrand", ["legrand"]),
    ("LVMH", ["lvmh", "louis vuitton"]),
    ("Michelin", ["michelin"]),
    ("Orange", ["orange"]),
    ("Pernod Ricard", ["pernod"]),
    ("Publicis", ["publicis"]),
    ("Renault", ["renault"]),
    ("Safran", ["safran"]),
    ("Sanofi", ["sanofi"]),
    ("Schneider Electric", ["schneider"]),
    ("Societe Generale", ["societe generale", "sg"]),
    ("Stellantis", ["stellantis"]),
    ("STMicro", ["stmicroelectronics"]),
    ("Teleperformance", ["teleperformance"]),
    ("Thales", ["thales"]),
    ("TotalEnergies", ["totalenergies"]),
    ("Unibail", ["unibail"]),
    ("Veolia", ["veolia"]),
    ("Vinci", ["vinci"]),
    ("Vivendi", ["vivendi"]),
]

# ═══ REQUETES STRICTEMENT ALTERNANCE ═══

REQUETES = [
    "alternance ingenieur affaires",
    "alternance ingenieur commercial",
    "alternance business developer",
    "alternance business development",
    "alternance business manager",
    "alternance account manager",
    "alternance account executive",
    "alternance inside sales",
    "alternance technico commercial",
    "alternance avant vente",
    "alternance pre sales",
    "alternance bid manager",
    "alternance ingenieur affaires IT",
    "alternance ingenieur affaires telecoms",
    "alternance charge affaires",
]

# ═══ FILTRES ═══

MOTS_ALTERNANCE = [
    "alternance", "alternant", "alternante", "apprentissage", "apprenti",
]

MOTS_INTERDITS = [
    "stage", "stagiaire", "cdi", "cdd", "freelance", "interim",
]

def norm(t):
    if not t:
        return ""
    return unicodedata.normalize('NFD', t).encode('ascii', 'ignore').decode('utf-8').lower().strip()

def est_alternance(titre):
    t = norm(titre)
    if not any(m in t for m in MOTS_ALTERNANCE):
        return False
    if any(m in t for m in MOTS_INTERDITS):
        return False
    return True

def correspond_entreprise(nom_entreprise, aliases):
    e = norm(nom_entreprise)
    return any(a in e for a in aliases)

def cle(titre, ent, loc):
    return norm(titre)[:60] + "|" + norm(ent)[:20] + "|" + norm(loc)[:15]

# ═══ SELENIUM ═══

def make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=fr-FR,fr")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    return driver

def scrape_linkedin_alternance(driver, requete, nom, aliases, vus, date):
    offres = []

    url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={quote_plus(requete + ' ' + nom)}"
        "&location=France"
        "&f_TPR=r2592000"
        "&f_JT=F"
        "&sortBy=DD"
    )

    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list"))
        )
    except TimeoutException:
        print(f"  Timeout LinkedIn pour {nom} / {requete}")
        return offres

    time.sleep(random.uniform(2, 4))

    if any(k in driver.current_url for k in ["authwall", "login", "uas/authenticate"]):
        print(f"  LinkedIn authwall pour {nom}")
        return offres

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("ul.jobs-search__results-list > li")

    for card in cards:
        try:
            titre_el = card.select_one("h3.base-search-card__title") or card.select_one("h3")
            ent_el = card.select_one("h4.base-search-card__subtitle") or card.select_one("h4")
            loc_el = card.select_one(".job-search-card__location") or card.select_one("span[class*='location']")
            lien_el = card.select_one("a.base-card__full-link") or card.select_one("a[href*='/jobs/view/']")

            titre = titre_el.get_text(strip=True) if titre_el else ""
            ent = ent_el.get_text(strip=True) if ent_el else ""
            loc = loc_el.get_text(strip=True).split(',')[0] if loc_el else ""
            lien = (lien_el.get("href") or "").split("?")[0] if lien_el else ""

            if not (titre and lien and "linkedin.com/jobs" in lien):
                continue

            if not est_alternance(titre):
                continue

            if ent and not correspond_entreprise(ent, aliases):
                continue

            k = cle(titre, ent, loc)
            if k in vus:
                continue
            vus.add(k)

            offres.append({
                "entreprise": ent or nom,
                "titre": titre,
                "localisation": loc,
                "lien": lien,
                "source": "LinkedIn",
                "requete": requete,
                "first_seen": date,
                "last_seen": date,
            })
        except Exception:
            continue

    return offres

def main():
    date = datetime.now().strftime("%Y-%m-%d")
    vus = set()
    toutes = []

    driver = make_driver()

    try:
        for requete in REQUETES:
            print(f"\n=== Requete : {requete} ===")
            for nom, aliases in ENTREPRISES:
                print(f"  - {nom}")
                offres = scrape_linkedin_alternance(driver, requete, nom, aliases, vus, date)
                toutes.extend(offres)
                time.sleep(random.uniform(2, 5))
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    os.makedirs("data", exist_ok=True)
    chemin = os.path.join("data", "offres_linkedin_alternance.json")

    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(toutes, f, ensure_ascii=False, indent=2)

    print(f"\n{len(toutes)} offres LinkedIn alternance enregistrees dans {chemin}")

if __name__ == "__main__":
    main()
