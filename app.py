from flask import Flask, jsonify, request
from flask_cors import CORS
from allocineAPI.allocineAPI import allocineAPI
from datetime import datetime
import unicodedata, re

app = Flask(__name__)
CORS(app)
api = allocineAPI()

# Mapping code département → ID AlloCiné (vrais IDs récupérés depuis /departements)
DEPT_MAP = {
    'Ain': 'departement-83191',
    'Aisne': 'departement-83178',
    'Allier': 'departement-83111',
    'Alpes-de-Haute-Provence': 'departement-83185',
    'Alpes-Maritimes': 'departement-83187',
    'Ardeche': 'departement-83112',
    'Ardennes': 'departement-83129',
    'Ariege': 'departement-83155',
    'Aube': 'departement-83130',
    'Aude': 'departement-83138',
    'Aveyron': 'departement-83151',
    'Bas-Rhin': 'departement-83104',
    'Bouches-du-Rhone': 'departement-83188',
    'Calvados': 'departement-83160',
    'Cantal': 'departement-83112',
    'Charente': 'departement-83181',
    'Charente-Maritime': 'departement-83182',
    'Cher': 'departement-83123',
    'Correze': 'departement-83143',
    'Corse-du-Sud': 'departement-265496',
    'Cote-dOr': 'departement-83115',
    'Cotes-dArmor': 'departement-83119',
    'Creuse': 'departement-83144',
    'Deux-Sevres': 'departement-83183',
    'Dordogne': 'departement-83106',
    'Doubs': 'departement-83193',
    'Drome': 'departement-83189',
    'Essonne': 'departement-83168',
    'Eure': 'departement-83163',
    'Eure-et-Loir': 'departement-83120',
    'Finistere': 'departement-83120',
    'Gard': 'departement-83139',
    'Gers': 'departement-83153',
    'Gironde': 'departement-83107',
    'Guadeloupe': 'departement-83199',
    'Guyane': 'departement-83201',
    'Haut-Rhin': 'departement-83105',
    'Haute-Corse': 'departement-83133',
    'Haute-Garonne': 'departement-83152',
    'Haute-Loire': 'departement-83113',
    'Haute-Marne': 'departement-83132',
    'Haute-Saone': 'departement-83136',
    'Haute-Savoie': 'departement-83198',
    'Haute-Vienne': 'departement-83145',
    'Hautes-Alpes': 'departement-83186',
    'Hautes-Pyrenees': 'departement-83155',
    'Hauts-de-Seine': 'departement-83169',
    'Herault': 'departement-83140',
    'Ille-et-Vilaine': 'departement-83121',
    'Indre': 'departement-83125',
    'Indre-et-Loire': 'departement-83126',
    'Isere': 'departement-83194',
    'Jura': 'departement-83135',
    'Landes': 'departement-83108',
    'Loir-et-Cher': 'departement-83127',
    'Loire': 'departement-83195',
    'Loire-Atlantique': 'departement-83173',
    'Loiret': 'departement-83128',
    'Lot': 'departement-83154',
    'Lot-et-Garonne': 'departement-83109',
    'Lozere': 'departement-83141',
    'Maine-et-Loire': 'departement-83174',
    'Manche': 'departement-83161',
    'Marne': 'departement-83131',
    'Martinique': 'departement-83200',
    'Mayenne': 'departement-83175',
    'Meurthe-et-Moselle': 'departement-83146',
    'Meuse': 'departement-83147',
    'Morbihan': 'departement-83122',
    'Moselle': 'departement-83148',
    'Nievre': 'departement-83116',
    'Nord': 'departement-83158',
    'Oise': 'departement-83179',
    'Orne': 'departement-83162',
    'Paris': 'ville-115755',
    'Pas-de-Calais': 'departement-83159',
    'Puy-de-Dome': 'departement-83114',
    'Pyrenees-Atlantiques': 'departement-83110',
    'Pyrenees-Orientales': 'departement-83142',
    'Reunion': 'departement-83189',
    'Rhone': 'departement-83202',
    'Saone-et-Loire': 'departement-83196',
    'Sarthe': 'departement-83117',
    'Savoie': 'departement-83197',
    'Seine-et-Marne': 'departement-83166',
    'Seine-Maritime': 'departement-83164',
    'Seine-Saint-Denis': 'departement-83170',
    'Somme': 'departement-83180',
    'Tarn': 'departement-83156',
    'Tarn-et-Garonne': 'departement-83157',
    'Val-dOise': 'departement-83172',
    'Val-de-Marne': 'departement-83171',
    'Var': 'departement-83189',
    'Vaucluse': 'departement-83190',
    'Vendee': 'departement-83177',
    'Vienne': 'departement-83184',
    'Vosges': 'departement-83149',
    'Yonne': 'departement-83118',
    'Yvelines': 'departement-83167',
}

# Mapping code postal (2 premiers chiffres) → nom département
CP_TO_DEPT = {
    '01':'Ain','02':'Aisne','03':'Allier','04':'Alpes-de-Haute-Provence',
    '05':'Hautes-Alpes','06':'Alpes-Maritimes','07':'Ardeche','08':'Ardennes',
    '09':'Ariege','10':'Aube','11':'Aude','12':'Aveyron','13':'Bouches-du-Rhone',
    '14':'Calvados','15':'Cantal','16':'Charente','17':'Charente-Maritime',
    '18':'Cher','19':'Correze','20':'Corse-du-Sud','21':'Cote-dOr',
    '22':'Cotes-dArmor','23':'Creuse','24':'Dordogne','25':'Doubs',
    '26':'Drome','27':'Eure','28':'Eure-et-Loir','29':'Finistere',
    '30':'Gard','31':'Haute-Garonne','32':'Gers','33':'Gironde',
    '34':'Herault','35':'Ille-et-Vilaine','36':'Indre','37':'Indre-et-Loire',
    '38':'Isere','39':'Jura','40':'Landes','41':'Loir-et-Cher',
    '42':'Loire','43':'Haute-Loire','44':'Loire-Atlantique','45':'Loiret',
    '46':'Lot','47':'Lot-et-Garonne','48':'Lozere','49':'Maine-et-Loire',
    '50':'Manche','51':'Marne','52':'Haute-Marne','53':'Mayenne',
    '54':'Meurthe-et-Moselle','55':'Meuse','56':'Morbihan','57':'Moselle',
    '58':'Nievre','59':'Nord','60':'Oise','61':'Orne',
    '62':'Pas-de-Calais','63':'Puy-de-Dome','64':'Pyrenees-Atlantiques',
    '65':'Hautes-Pyrenees','66':'Pyrenees-Orientales','67':'Bas-Rhin',
    '68':'Haut-Rhin','69':'Rhone','70':'Haute-Saone','71':'Saone-et-Loire',
    '72':'Sarthe','73':'Savoie','74':'Haute-Savoie','75':'Paris',
    '76':'Seine-Maritime','77':'Seine-et-Marne','78':'Yvelines',
    '79':'Deux-Sevres','80':'Somme','81':'Tarn','82':'Tarn-et-Garonne',
    '83':'Var','84':'Vaucluse','85':'Vendee','86':'Vienne',
    '87':'Haute-Vienne','88':'Vosges','89':'Yonne','90':'Territoire-de-Belfort',
    '91':'Essonne','92':'Hauts-de-Seine','93':'Seine-Saint-Denis',
    '94':'Val-de-Marne','95':'Val-dOise',
    '971':'Guadeloupe','972':'Martinique','973':'Guyane','974':'Reunion',
}

def normalize(text):
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_dept_id(address):
    """Extrait l'ID département AlloCiné depuis une adresse contenant un code postal."""
    match = re.search(r'\b(\d{5})\b', address or '')
    if match:
        cp = match.group(1)
        code = cp[:3] if cp.startswith(('971','972','973','974')) else cp[:2]
        dept_name = CP_TO_DEPT.get(code)
        if dept_name:
            return DEPT_MAP.get(dept_name)
    return None

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "CinéProche API"})

@app.route('/seances')
def seances():
    cinema_id = request.args.get('id', '')
    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    if not cinema_id:
        return jsonify({"error": "id manquant"}), 400
    try:
        data = api.get_showtime(cinema_id, date_str)
        return jsonify({"cinema_id": cinema_id, "date": date_str, "seances": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cinemas')
def cinemas():
    location_id = request.args.get('loc', '')
    if not location_id:
        return jsonify({"error": "loc manquant"}), 400
    try:
        data = api.get_cinema(location_id)
        return jsonify({"cinemas": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/villes')
def villes():
    try:
        data = api.get_top_villes()
        return jsonify({"villes": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/departements')
def departements():
    try:
        data = api.get_departements()
        return jsonify({"departements": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search-cinema')
def search_cinema():
    """
    Cherche un cinéma par nom dans le bon département via le code postal.
    Params: name (obligatoire), address (avec code postal, ex: 60230)
    """
    name = request.args.get('name', '').strip()
    address = request.args.get('address', '').strip()
    if not name:
        return jsonify({"error": "name manquant"}), 400

    try:
        name_norm = normalize(name)
        mots = [w for w in name_norm.split() if len(w) > 2]

        # Construire la liste des emplacements à chercher
        locations_to_search = []

        # 1. Département ciblé via code postal (prioritaire)
        dept_id = extract_dept_id(address)
        if dept_id:
            locations_to_search.append(dept_id)

        # 2. Fallback : villes principales
        villes_data = api.get_top_villes()
        if isinstance(villes_data, list):
            for v in villes_data:
                if v['id'] not in locations_to_search:
                    locations_to_search.append(v['id'])

        best = None
        best_score = 0

        for loc_id in locations_to_search:
            try:
                data = api.get_cinema(loc_id)
                cinemas_list = data if isinstance(data, list) else data.get('cinemas', [])
                for c in cinemas_list:
                    c_name = normalize(c.get('name', ''))
                    c_addr = normalize(c.get('address', ''))
                    score = 0
                    for mot in mots:
                        if mot in c_name: score += 2
                        elif mot in c_addr: score += 1
                    if score > best_score and score >= len(mots):
                        best_score = score
                        best = {
                            "id": c.get('id'),
                            "name": c.get('name'),
                            "address": c.get('address'),
                            "score": score,
                            "loc_id": loc_id
                        }
                # Bon résultat dans le département ciblé → on arrête
                if best and loc_id == dept_id and best_score >= len(mots) * 2:
                    break
            except:
                continue

        if best:
            return jsonify(best)
        else:
            return jsonify({"id": None, "message": "Cinéma non trouvé"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
