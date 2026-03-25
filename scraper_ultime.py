import json, time, random, unicodedata, os, re, sys
from datetime import datetime
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

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

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.linkedin.com/",
    })
    return s

# ═══ SOURCE 1 : LINKEDIN (requests) ═══

def scrape_linkedin(session, angle, nom, aliases, vues, date):
    offres = []
    for start in [0, 25]:
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote_plus(angle + ' ' + nom)}"
            f"&location=France&f_TPR=r2592000&f_JT=I&sortBy=DD&start={start}"
        )
        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                print(f"    LinkedIn {r.status_code} pour {nom}")
                break
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.find_all("li")
            if not cards:
                break
            for card in cards:
                try:
                    titre_el = card.find("h3", class_="base-search-card__title") or card.find("h3")
                    ent_el   = card.find("h4", class_="base-search-card__subtitle") or card.find("h4")
                    loc_el   = card.find("span", class_="job-search-card__location")
                    lien_el  = card.find("a", class_="base-card__full-link") or card.find("a")

                    titre = titre_el.get_text(strip=True) if titre_el else ""
                    ent   = ent_el.get_text(strip=True) if ent_el else ""
                    loc   = loc_el.get_text(strip=True).split(',')[0] if loc_el else ""
                    lien  = (lien_el.get("href") or "").split("?")[0] if lien_el else ""

                    if not (titre and ent and "linkedin.com/jobs" in lien):
                        continue
                    if not any(a in norm(ent) for a in aliases):
                        continue

                    score, matches = scorer(titre)
                    if score < SCORE_MIN:
                        continue

                    k = cle(titre, ent, loc)
                    if k in vues:
                        continue
                    vues.add(k)
                    offres.append({
                        "entreprise": ent, "titre": titre,
                        "localisation": loc, "lien": lien,
                        "score": score, "mots_cles_matches": matches,
                        "source": "LinkedIn", "first_seen": date, "last_seen": date,
                        "is_priority": any(p in norm(titre) for p in METIERSPRIORITAIRES),
                    })
                except Exception:
                    continue
            time.sleep(random.uniform(1.5, 2.5))
        except Exception as e:
            print(f"    ⚠️ LinkedIn requests: {e}")
            break
    return offres

# ═══ SOURCE 2 : APEC ═══

def scrape_apec(session, mots, aliases_toutes, vues, date):
    offres = []
    url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles={quote_plus(mots)}&typeContrat=148990&nbResultats=50"
    try:
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select(".card-offer, article.job"):
            try:
                titre_el = card.select_one("h2.card-title, .card-offer__title, h2")
                ent_el   = card.select_one(".card-offer__company, .company-name")
                loc_el   = card.select_one(".card-offer__location, .location")
                lien_el  = card.select_one("a[href*='apec.fr']")

                titre = titre_el.get_text(strip=True) if titre_el else ""
                ent   = ent_el.get_text(strip=True) if ent_el else ""
                loc   = loc_el.get_text(strip=True).split(',')[0] if loc_el else ""
                lien  = lien_el.get("href", "").split("?")[0] if lien_el else ""

                if not (titre and lien and any(a in norm(ent) for a in aliases_toutes)):
                    continue

                score, matches = scorer(titre)
                if score < SCORE_MIN:
                    continue

                k = cle(titre, ent, loc)
                if k in vues:
                    continue
                vues.add(k)
                offres.append({
                    "entreprise": ent, "titre": titre,
                    "localisation": loc, "lien": lien,
                    "score": score, "mots_cles_matches": matches,
                    "source": "APEC", "first_seen": date, "last_seen": date,
                    "is_priority": any(p in norm(titre) for p in METIERSPRIORITAIRES),
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  ⚠️ APEC: {e}")
    return offres

# ═══ SOURCE 3 : FRANCE TRAVAIL (API officielle) ═══

FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
FT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
FT_CLIENT_ID  = os.environ.get("FT_CLIENT_ID", "")
FT_CLIENT_SECRET = os.environ.get("FT_CLIENT_SECRET", "")

_ft_token = None

def get_ft_token(session):
    global _ft_token
    if _ft_token:
        return _ft_token
    if not FT_CLIENT_ID or not FT_CLIENT_SECRET:
        return None
    try:
        r = session.post(FT_TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": FT_CLIENT_ID,
            "client_secret": FT_CLIENT_SECRET,
            "scope": "api_offresdemploiv2 o2dsoffre",
        }, timeout=10)
        _ft_token = r.json().get("access_token")
        return _ft_token
    except Exception as e:
        print(f"  ⚠️ France Travail token: {e}")
        return None

def scrape_france_travail(session, mot_cle, aliases, vues, date):
    offres = []
    token = get_ft_token(session)
    if not token:
        return offres
    try:
        r = session.get(FT_SEARCH_URL, headers={"Authorization": f"Bearer {token}"},
            params={
                "motsCles": mot_cle,
                "typeContrat": "AL",  # Alternance
                "lieux": "75,77,78,91,92,93,94,95",  # Ile-de-France
                "range": "0-49",
                "sort": "1",
            }, timeout=15)
        data = r.json()
        for item in data.get("resultats", []):
            try:
                titre = item.get("intitule", "")
                ent   = item.get("entreprise", {}).get("nom", "")
                loc   = item.get("lieuTravail", {}).get("libelle", "").split("-")[0].strip()
                lien  = item.get("origineOffre", {}).get("urlOrigine") or \
                        f"https://candidat.francetravail.fr/offres/recherche/detail/{item.get('id','')}"

                if not any(a in norm(ent) for a in aliases):
                    continue

                score, matches = scorer(titre)
                if score < SCORE_MIN:
                    continue

                k = cle(titre, ent, loc)
                if k in vues:
                    continue
                vues.add(k)
                offres.append({
                    "entreprise": ent, "titre": titre,
                    "localisation": loc, "lien": lien,
                    "score": score, "mots_cles_matches": matches,
                    "source": "France Travail", "first_seen": date, "last_seen": date,
                    "is_priority": any(p in norm(titre) for p in METIERSPRIORITAIRES),
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  ⚠️ France Travail search: {e}")
    return offres

# ═══ MAIN ═══

def main():
    batch = "A"
    if "--batch" in sys.argv:
        i = sys.argv.index("--batch")
        batch = sys.argv[i + 1].upper() if i + 1 < len(sys.argv) else "A"

    entreprises = BATCHS.get(batch, BATCHS["A"])
    fichier = f"offres_batch_{batch}.json"
    aliases_toutes = [a for _, als in ENTREPRISES for a in als]
    date = datetime.now().strftime("%d/%m/%Y")

    print(f"🚀 Batch {batch} — {len(entreprises)} entreprises")

    offres = []
    vues = set()
    session = make_session()

    # ——— LinkedIn (requests) ———
    print(f"\n🔵 LinkedIn ({len(ANGLES)} angles × {len(entreprises)} entreprises)")
    for nom, aliases in entreprises:
        print(f"  → {nom}")
        for angle in ANGLES:
            nouveaux = scrape_linkedin(session, angle, nom, aliases, vues, date)
            offres.extend(nouveaux)
            time.sleep(random.uniform(1.0, 2.0))
        time.sleep(random.uniform(1.0, 2.0))
    print(f"  ✓ LinkedIn : {len(offres)} offres")

    # ——— APEC (batch A seulement) ———
    if batch == "A":
        print(f"\n🟡 APEC ({len(ANGLES_APEC)} requêtes)")
        n_avant = len(offres)
        for mots in ANGLES_APEC:
            print(f"  → {mots}")
            offres.extend(scrape_apec(session, mots, aliases_toutes, vues, date))
            time.sleep(random.uniform(1.5, 2.5))
        print(f"  ✓ APEC : +{len(offres) - n_avant} offres")

    # ——— France Travail (si credentials dispos) ———
    if FT_CLIENT_ID and FT_CLIENT_SECRET:
        print(f"\n🟢 France Travail")
        n_avant = len(offres)
        for nom, aliases in entreprises:
            for angle in ["alternance ingenieur affaires", "alternance avant-vente", "alternance technico-commercial"]:
                offres.extend(scrape_france_travail(session, f"{angle} {nom}", aliases, vues, date))
                time.sleep(random.uniform(0.5, 1.0))
        print(f"  ✓ France Travail : +{len(offres) - n_avant} offres")
    else:
        print("\n⚠️ France Travail ignoré (FT_CLIENT_ID / FT_CLIENT_SECRET non définis)")

    offres.sort(key=lambda x: (not x.get("is_priority", False), -x.get("score", 0)))

    print(f"\n✅ Batch {batch} : {len(offres)} offres → {fichier}")
    if offres:
        print("🏆 Top 5 :")
        for o in offres[:5]:
            flag = "⭐" if o.get("is_priority") else "  "
            print(f"  {flag}[{o['score']}pts] {o['titre']} — {o['entreprise']}")

    json.dump(offres, open(fichier, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
    print(f"💾 {fichier} écrit.")

if __name__ == "__main__":
    main()
