import json
import time
import random
import unicodedata
import os
import re
from datetime import datetime
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException

# ══════════════════════════════════════════════════
# ENTREPRISES + ALIASES (filiales, marques, noms commerciaux)
# ══════════════════════════════════════════════════

# Chaque entrée : (nom principal, [aliases valides pour le filtre])
# L'alias permet d'accepter des offres de filiales qui portent un nom différent
ENTREPRISES = [
    # CAC40
    ("Air Liquide",         ["air liquide"]),
    ("Airbus",              ["airbus", "airbus group", "airbus defence", "airbus helicopters"]),
    ("Alstom",              ["alstom"]),
    ("ArcelorMittal",       ["arcelormittal"]),
    ("AXA",                 ["axa", "axa france", "axa assurances", "axa partners"]),
    ("BNP Paribas",         ["bnp", "bnp paribas", "bnp paribas cardif", "bnp paribas personal finance"]),
    ("Bouygues",            ["bouygues", "bouygues telecom", "bouygues construction", "bouygues immobilier", "b&you"]),
    ("Capgemini",           ["capgemini", "capgemini invent", "capgemini engineering", "sogeti"]),
    ("Carrefour",           ["carrefour"]),
    ("Crédit Agricole",     ["credit agricole", "ca", "lcl", "amundi", "indosuez"]),
    ("Danone",              ["danone", "evian", "volvic", "bledinasl"]),
    ("Dassault Systèmes",   ["dassault", "dassault systemes", "3ds", "3dexperience"]),
    ("Edenred",             ["edenred"]),
    ("Engie",               ["engie", "engie solutions", "engie impact", "tractebel"]),
    ("EssilorLuxottica",    ["essilor", "luxottica", "essilorluxottica"]),
    ("Hermès",              ["hermes", "hermès"]),
    ("Kering",              ["kering", "gucci", "saint laurent", "balenciaga", "bottega veneta"]),
    ("L'Oréal",             ["loreal", "l oreal", "l'oreal", "lancome", "maybelline", "garnier"]),
    ("Legrand",             ["legrand"]),
    ("LVMH",                ["lvmh", "moet hennessy", "louis vuitton", "dior", "givenchy", "tag heuer", "sephora"]),
    ("Michelin",            ["michelin"]),
    ("Orange",              ["orange", "orange business", "orange cyberdefense", "orange france"]),
    ("Pernod Ricard",       ["pernod", "pernod ricard", "ricard"]),
    ("Publicis",            ["publicis", "publicis sapient", "publicis groupe", "leo burnett", "saatchi"]),
    ("Renault",             ["renault", "renault group", "mobilize", "ampere"]),
    ("Safran",              ["safran", "safran aircraft", "safran electronics", "safran data"]),
    ("Sanofi",              ["sanofi"]),
    ("Schneider Electric",  ["schneider", "schneider electric"]),
    ("Société Générale",   ["societe generale", "sg", "sgcib", "boursorama", "ayvens"]),
    ("Stellantis",          ["stellantis", "peugeot", "citroen", "opel", "fiat", "jeep", "alfa romeo"]),
    ("STMicroelectronics",  ["st", "stmicroelectronics", "stm"]),
    ("Teleperformance",     ["teleperformance"]),
    ("Thales",              ["thales", "thales six", "thales alenia", "thales dis"]),
    ("TotalEnergies",       ["totalenergies", "total", "total energies"]),
    ("Unibail-Rodamco",     ["unibail", "westfield", "unibail rodamco"]),
    ("Veolia",              ["veolia", "veolia water", "veolia environnement"]),
    ("Vinci",               ["vinci", "vinci construction", "vinci energies", "vinci autoroutes", "vinci facilities"]),
    ("Vivendi",             ["vivendi", "canal+", "canal plus", "havas"]),
    # Tech / Conseil
    ("Microsoft",           ["microsoft", "microsoft france"]),
    ("Amazon",              ["amazon", "aws", "amazon web services"]),
    ("Google",              ["google", "google france", "alphabet"]),
    ("Salesforce",          ["salesforce", "tableau", "mulesoft", "slack"]),
    ("SAP",                 ["sap", "sap france"]),
    ("Oracle",              ["oracle", "oracle france"]),
    ("IBM",                 ["ibm", "ibm france"]),
    ("Cisco",               ["cisco", "cisco france"]),
    ("Accenture",           ["accenture", "accenture france"]),
    ("Deloitte",            ["deloitte", "deloitte france"]),
    ("EY",                  ["ey", "ernst young", "ernst & young"]),
    ("PwC",                 ["pwc", "pricewaterhousecoopers"]),
    ("KPMG",                ["kpmg", "kpmg france"]),
    ("Sopra Steria",        ["sopra", "sopra steria", "sopra banking"]),
    ("CGI",                 ["cgi", "cgi france"]),
    ("Wavestone",           ["wavestone"]),
    # Autres grands groupes
    ("EDF",                 ["edf", "edf renouvelables", "electricite de france"]),
    ("Groupe SNCF",         ["sncf", "sncf connect", "sncf reseau", "keolis", "ouigo", "thalys", "eurostar"]),
    ("CMA CGM",             ["cma cgm", "cma", "cgm"]),
    ("La Poste Groupe",     ["la poste", "laposte", "docaposte", "chronopost", "geopost"]),
    ("Naval Group",         ["naval group"]),
    ("Siemens",             ["siemens", "siemens france", "siemens energy"]),
    ("Nestlé",              ["nestle", "nestlé", "nespresso", "purina", "maggi"]),
    ("Unilever",            ["unilever", "dove", "axe"]),
]

# ══════════════════════════════════════════════════
# ANGLES (15 — couvrant TOUS les métiers cibles)
# ══════════════════════════════════════════════════

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

# Métiers cibles pour APEC (recherche directe sans nom d'entreprise)
ANGLES_APEC = [
    "ingénieur d'affaires alternance",
    "avant-vente alternance",
    "pre-sales alternance",
    "technico-commercial alternance",
    "chargé de déploiement alternance",
    "business developer alternance",
    "chef de projet IT alternance",
]

# ══════════════════════════════════════════════════
# SCORING
# ══════════════════════════════════════════════════

MOTS_POSITIFS = {
    # Métiers EXACTEMENT visés (poids max)
    "avant-vente": 8, "avant vente": 8,
    "pre-sales": 8, "presales": 8, "pre sales": 8,
    "solution engineer": 8, "solution architect": 7,
    "technico-commercial": 8, "technico commercial": 8,
    "ingenieur d affaires": 8, "ingenieur affaires": 8,
    "charge d affaires": 8, "charge affaires": 8,
    "charge de deploiement": 8, "chargee de deploiement": 8,
    "ppo": 7, "pilote de projet": 7,
    "business manager": 7,
    "ingenieur commercial": 7,

    # Business & sales (poids fort)
    "business developer": 6, "business development": 6,
    "key account": 6, "account manager": 6, "kam": 6,
    "commercial": 5, "business": 5, "sales": 5, "vente": 5,
    "account": 4, "b2b": 5,
    "developpement commercial": 6,

    # Projet / delivery (poids fort)
    "chef de projet": 5, "project manager": 5,
    "deploiement": 6, "deployment": 6,
    "delivery": 4, "pilotage": 4, "coordination": 3,

    # Conseil / stratégie
    "consultant": 4, "consulting": 4,
    "strategy": 4, "strategie": 4,
    "transformation": 3, "partenariat": 3,
    "digital": 2, "innovation": 2,

    # Tech / IT (utiles en combo)
    "cloud": 2, "data": 2, "ia": 2, "ai": 2,
    "cyber": 2, "saas": 2, "erp": 2, "crm": 2,
    "telecom": 2, "reseau": 2, "si": 2, "it": 2, "tech": 2,

    # Mots neutres
    "manager": 2, "management": 2, "responsable": 1,
    "ingenieur": 1, "charge": 1, "pilote": 2,
}

# Score minimum pour retenir une offre
SCORE_MIN = 3

# Mots-clés prioritaires : si l'un d'eux est dans le titre, score bonus +3
METIERS_PRIORITAIRES = [
    "avant-vente", "avant vente", "pre-sales", "presales",
    "technico-commercial", "technico commercial",
    "ingenieur affaires", "ingenieur d affaires",
    "charge affaires", "charge de deploiement",
    "solution engineer", "business manager", "ppo",
]

MOTS_INTERDITS = [
    "ressources humaines", "recrutement", "talent acquisition", "paie", "payroll",
    "comptabilite", "comptable", "controleur de gestion", "audit", "fiscal", "tresorerie",
    "helpdesk", "technicien support", "support technique", "hotline", "technicien reseau",
    "maintenance", "mecanique", "usine", "soudeur", "fraiseur",
    "electrotechni", "production", "operateur",
    "logistique", "supply chain", "acheteur", "approvisionnement", "entrepot",
    "graphiste", "motion design", "ux design", "ui design",
    "communication externe", "relations presse", "redacteur", "journaliste",
    "juridique", "droit", "paralegal",
    "qualite", "qhse", "hse",
    "stage ",  # espace intentionnel pour ne pas bloquer "Dassault Systemes"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# ══════════════════════════════════════════════════
# DRIVER
# ══════════════════════════════════════════════════

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
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
    }
    opts.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    driver.set_page_load_timeout(30)
    return driver

# ══════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════

def normaliser(texte):
    if not texte:
        return ""
    return unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8').lower().strip()

def scorer_offre(titre, description=""):
    """Score sur titre + snippet de description si disponible."""
    texte = normaliser(titre + " " + description)
    for mot in MOTS_INTERDITS:
        if mot in texte:
            return 0, []
    score = 0
    mots_matches = []
    for mot, poids in MOTS_POSITIFS.items():
        if mot in texte:
            score += poids
            mots_matches.append(mot)
    # Bonus métier prioritaire
    for mot in METIERSPRIORITAIRES:
        if mot in normaliser(titre):  # bonus uniquement sur le titre
            score += 3
            break
    return score, mots_matches

def cle_dedup(titre, entreprise, localisation):
    t = normaliser(titre)[:55]
    e = re.sub(r'\s+', '', normaliser(entreprise))[:15]
    l = normaliser(localisation)[:10]
    return f"{t}|{e}|{l}"

def charger_json_existant(chemin):
    if os.path.exists(chemin):
        try:
            with open(chemin, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def construire_index_existant(offres):
    """Index {cle: offre} pour mise à jour last_seen"""
    return {cle_dedup(o["titre"], o["entreprise"], o["localisation"]): o for o in offres}

# ══════════════════════════════════════════════════
# SCROLL
# ══════════════════════════════════════════════════

def scroll_et_charger(driver, nb_scrolls=5):
    for _ in range(nb_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.2, 2.0))
        for selector in [
            "button.infinite-scroller__show-more-button",
            "button[aria-label*='plus']",
            "button.see-more-jobs",
            "button[data-tracking-control-name*='load_more']",
        ]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed() and btn.is_enabled():
                    btn.click()
                    time.sleep(random.uniform(0.8, 1.4))
                    break
            except Exception:
                pass

# ══════════════════════════════════════════════════
# EXTRACTION LINKEDIN
# ══════════════════════════════════════════════════

def extraire_cards_linkedin(driver):
    offres = []
    cards = []
    for sel in [".base-card", ".job-search-card", "li.jobs-search-results__list-item"]:
        cards = driver.find_elements(By.CSS_SELECTOR, sel)
        if cards:
            break
    for card in cards:
        try:
            titre, entreprise, localisation, lien = "", "", "", ""
            for t_sel in [".base-search-card__title", "h3.base-search-card__title"]:
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
            for a_sel in ["a.base-card__full-link", "a"]:
                try:
                    href = card.find_element(By.CSS_SELECTOR, a_sel).get_attribute("href") or ""
                    if "linkedin.com/jobs" in href:
                        lien = href.split("?")[0]
                        break
                except Exception:
                    pass
            if titre and entreprise and lien:
                offres.append({"titre": titre, "entreprise": entreprise,
                               "localisation": localisation, "lien": lien, "source": "LinkedIn"})
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return offres

# ══════════════════════════════════════════════════
# EXTRACTION APEC
# ══════════════════════════════════════════════════

def scraper_apec(driver, mots_cles, aliases_toutes_entreprises):
    """Scrape APEC pour un mot-clé métier, filtre ensuite sur nos entreprises."""
    offres = []
    url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles={quote_plus(mots_cles)}&typeContrat=148990&nbResultats=50"
    try:
        driver.get(url)
        time.sleep(random.uniform(3.0, 5.0))
        scroll_et_charger(driver, nb_scrolls=3)

        cards = driver.find_elements(By.CSS_SELECTOR, ".card-offer, .result-item, article.job")
        for card in cards:
            try:
                titre = ""
                entreprise = ""
                localisation = ""
                lien = ""
                for t_sel in ["h2.card-title", ".card-offer__title", "h2", "h3"]:
                    try:
                        titre = card.find_element(By.CSS_SELECTOR, t_sel).text.strip()
                        if titre: break
                    except Exception:
                        pass
                for e_sel in [".card-offer__company", ".company-name", ".card-company"]:
                    try:
                        entreprise = card.find_element(By.CSS_SELECTOR, e_sel).text.strip()
                        if entreprise: break
                    except Exception:
                        pass
                for l_sel in [".card-offer__location", ".location", ".city"]:
                    try:
                        localisation = card.find_element(By.CSS_SELECTOR, l_sel).text.strip().split(',')[0]
                        if localisation: break
                    except Exception:
                        pass
                for a_sel in ["a"]:
                    try:
                        href = card.find_element(By.CSS_SELECTOR, a_sel).get_attribute("href") or ""
                        if "apec.fr" in href and "/emploi/" in href:
                            lien = href.split("?")[0]
                            break
                    except Exception:
                        pass
                if titre and lien:
                    # Filtre : vérifier que l'entreprise est dans notre liste
                    ent_norm = normaliser(entreprise)
                    if any(alias in ent_norm for alias in aliases_toutes_entreprises):
                        offres.append({"titre": titre, "entreprise": entreprise,
                                       "localisation": localisation, "lien": lien, "source": "APEC"})
            except Exception:
                continue
    except Exception as e:
        print(f"    ⚠️ APEC erreur sur '{mots_cles}': {e}")
    return offres

# ══════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════

METIERS_PRIORITAIRES = METIERSPRIORITAIRES = [
    "avant-vente", "avant vente", "pre-sales", "presales",
    "technico-commercial", "technico commercial",
    "ingenieur affaires", "ingenieur d affaires",
    "charge affaires", "charge de deploiement",
    "solution engineer", "business manager", "ppo",
]

def main():
    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    chemin_json = "offres_cac40.json"
    nb_requetes_linkedin = len(ENTREPRISES) * len(ANGLES_LINKEDIN)

    print(f"🚀 Scraper V13 ULTIME")
    print(f"   LinkedIn : {len(ENTREPRISES)} entreprises × {len(ANGLES_LINKEDIN)} angles = {nb_requetes_linkedin} requêtes")
    print(f"   APEC     : {len(ANGLES_APEC)} requêtes métier + filtre entreprises")
    print(f"   Métiers prioritaires : {', '.join(METIERSPRIORITAIRES[:5])}...")

    # Charge l'historique existant
    offres_existantes = charger_json_existant(chemin_json)
    index_existant = construire_index_existant(offres_existantes)

    nouvelles_offres = []
    cles_vues = set()
    stats = {"linkedin": 0, "apec": 0, "interdit": 0, "score_bas": 0, "dedup": 0, "ok": 0}

    # Liste flat de tous les aliases pour filtre APEC
    aliases_toutes = [alias for _, aliases in ENTREPRISES for alias in aliases]

    driver = init_driver()

    try:
        # ─────────────────────────
        # PHASE 1 — LINKEDIN
        # ─────────────────────────
        print(f"\n🔵 PHASE 1 — LinkedIn ({nb_requetes_linkedin} requêtes)")
        for nom_principal, aliases in ENTREPRISES:
            print(f"  → {nom_principal}")
            for angle in ANGLES_LINKEDIN:
                # Recherche avec le nom principal
                mots = quote_plus(f"{angle} {nom_principal}")
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
                    resultats = extraire_cards_linkedin(driver)
                    stats["linkedin"] += len(resultats)

                    for r in resultats:
                        ent_norm = normaliser(r["entreprise"])
                        # Accepte si n'importe quel alias de cette entreprise match
                        if not any(alias in ent_norm for alias in aliases):
                            continue
                        score, mots_m = scorer_offre(r["titre"])
                        if score == 0:
                            stats["interdit"] += 1; continue
                        if score < SCORE_MIN:
                            stats["score_bas"] += 1; continue
                        cle = cle_dedup(r["titre"], r["entreprise"], r["localisation"])
                        if cle in cles_vues:
                            stats["dedup"] += 1; continue
                        cles_vues.add(cle)
                        stats["ok"] += 1

                        # Si déjà dans l'historique : met à jour last_seen
                        if cle in index_existant:
                            index_existant[cle]["last_seen"] = date_du_jour
                            index_existant[cle]["score"] = score
                        else:
                            nouvelles_offres.append({
                                "entreprise": r["entreprise"],
                                "titre": r["titre"],
                                "localisation": r["localisation"],
                                "lien": r["lien"],
                                "score": score,
                                "mots_cles_matches": mots_m,
                                "source": r["source"],
                                "first_seen": date_du_jour,
                                "last_seen": date_du_jour,
                                "is_priority": any(p in normaliser(r["titre"]) for p in METIERSPRIORITAIRES),
                            })
                except Exception as e:
                    print(f"    ⚠️ {e}")
                    continue
                time.sleep(random.uniform(1.5, 2.8))
            time.sleep(random.uniform(2.0, 4.0))

        # ─────────────────────────
        # PHASE 2 — APEC
        # ─────────────────────────
        print(f"\n🟡 PHASE 2 — APEC ({len(ANGLES_APEC)} requêtes)")
        for mots_cles in ANGLES_APEC:
            print(f"  → {mots_cles}")
            resultats_apec = scraper_apec(driver, mots_cles, aliases_toutes)
            stats["apec"] += len(resultats_apec)
            for r in resultats_apec:
                score, mots_m = scorer_offre(r["titre"])
                if score == 0:
                    stats["interdit"] += 1; continue
                if score < SCORE_MIN:
                    stats["score_bas"] += 1; continue
                cle = cle_dedup(r["titre"], r["entreprise"], r["localisation"])
                if cle in cles_vues:
                    stats["dedup"] += 1; continue
                cles_vues.add(cle)
                stats["ok"] += 1
                if cle not in index_existant:
                    nouvelles_offres.append({
                        "entreprise": r["entreprise"],
                        "titre": r["titre"],
                        "localisation": r["localisation"],
                        "lien": r["lien"],
                        "score": score,
                        "mots_cles_matches": mots_m,
                        "source": "APEC",
                        "first_seen": date_du_jour,
                        "last_seen": date_du_jour,
                        "is_priority": any(p in normaliser(r["titre"]) for p in METIERSPRIORITAIRES),
                    })
            time.sleep(random.uniform(2.0, 3.5))

    finally:
        driver.quit()

    # Tri : prioritaires d'abord, puis par score
    nouvelles_offres.sort(key=lambda x: (not x.get("is_priority", False), -x["score"]))

    # Fusionne nouvelles + existantes mises à jour
    toutes = nouvelles_offres + list(index_existant.values())
    toutes.sort(key=lambda x: (not x.get("is_priority", False), -x["score"]))

    print(f"\n📊 === STATS DU RUN V13 ===")
    print(f"   Scrapées LinkedIn brutes : {stats['linkedin']}")
    print(f"   Scrapées APEC brutes    : {stats['apec']}")
    print(f"   Refusées (interdit)     : {stats['interdit']}")
    print(f"   Refusées (score bas)    : {stats['score_bas']}")
    print(f"   Refusées (doublon)      : {stats['dedup']}")
    print(f"   Nouvelles offres        : {len(nouvelles_offres)}")
    print(f"   Total JSON final        : {len(toutes)}")

    if nouvelles_offres:
        print(f"\n🏆 Top 10 :")
        for o in nouvelles_offres[:10]:
            prio = "⭐" if o.get("is_priority") else "  "
            print(f"   {prio}[{o['score']}pts] {o['titre']} — {o['entreprise']} ({o['localisation']}) [{o['source']}]")

    if len(nouvelles_offres) >= 3 or len(toutes) >= 5:
        with open(chemin_json, 'w', encoding='utf-8') as f:
            json.dump(toutes, f, ensure_ascii=False, indent=4)
        print(f"\n✅ {chemin_json} mis à jour — {len(toutes)} offres totales")
    elif len(offres_existantes) > 0:
        print(f"⚠️ Pas assez de nouvelles offres. Conservation de l'existant.")
    else:
        print("❌ Aucune offre trouvée.")

if __name__ == "__main__":
    main()
