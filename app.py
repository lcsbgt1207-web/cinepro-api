from flask import Flask, jsonify, request
from flask_cors import CORS
from allocineAPI.allocineAPI import allocineAPI
from datetime import datetime
import unicodedata, re

app = Flask(__name__)
CORS(app)
api = allocineAPI()

# Mapping code postal → ID département AlloCiné
# Couvre tous les départements français
DEPT_MAP = {
    '01': 'departement-83191', '02': 'departement-83178', '03': 'departement-83111',
    '04': 'departement-83185', '05': 'departement-83186', '06': 'departement-83187',
    '07': 'departement-83112', '08': 'departement-83179', '09': 'departement-83155',
    '10': 'departement-83180', '11': 'departement-83156', '12': 'departement-83113',
    '13': 'departement-83188', '14': 'departement-83166', '15': 'departement-83114',
    '16': 'departement-83157', '17': 'departement-83158', '18': 'departement-83115',
    '19': 'departement-83116', '21': 'departement-83192', '22': 'departement-83167',
    '23': 'departement-83117', '24': 'departement-83159', '25': 'departement-83193',
    '26': 'departement-83189', '27': 'departement-83168', '28': 'departement-83169',
    '29': 'departement-83170', '30': 'departement-83160', '31': 'departement-83161',
    '32': 'departement-83162', '33': 'departement-83163', '34': 'departement-83164',
    '35': 'departement-83171', '36': 'departement-83118', '37': 'departement-83119',
    '38': 'departement-83190', '39': 'departement-83194', '40': 'departement-83165',
    '41': 'departement-83120', '42': 'departement-83195', '43': 'departement-83121',
    '44': 'departement-83172', '45': 'departement-83122', '46': 'departement-83123',
    '47': 'departement-83124', '48': 'departement-83125', '49': 'departement-83173',
    '50': 'departement-83174', '51': 'departement-83181', '52': 'departement-83182',
    '53': 'departement-83175', '54': 'departement-83196', '55': 'departement-83183',
    '56': 'departement-83176', '57': 'departement-83197', '58': 'departement-83126',
    '59': 'departement-83198', '60': 'departement-83184', '61': 'departement-83177',
    '62': 'departement-83199', '63': 'departement-83127', '64': 'departement-83128',
    '65': 'departement-83129', '66': 'departement-83130', '67': 'departement-83200',
    '68': 'departement-83201', '69': 'departement-83202', '70': 'departement-83203',
    '71': 'departement-83131', '72': 'departement-83132', '73': 'departement-83204',
    '74': 'departement-83205', '75': 'ville-115755',      '76': 'departement-83133',
    '77': 'departement-83206', '78': 'departement-83207', '79': 'departement-83134',
    '80': 'departement-83135', '81': 'departement-83136', '82': 'departement-83137',
    '83': 'departement-83138', '84': 'departement-83139', '85': 'departement-83140',
    '86': 'departement-83141', '87': 'departement-83142', '88': 'departement-83208',
    '89': 'departement-83143', '90': 'departement-83209', '91': 'departement-83210',
    '92': 'departement-83211', '93': 'departement-83212', '94': 'departement-83213',
    '95': 'departement-83214', '971': 'departement-83215', '972': 'departement-83216',
    '973': 'departement-83217', '974': 'departement-83218',
}

def normalize(text):
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def extract_dept(address):
    """Extrait le code département depuis une adresse (cherche un code postal 5 chiffres)."""
    match = re.search(r'\b(\d{5})\b', address or '')
    if match:
        cp = match.group(1)
        if cp.startswith('971'): return '971'
        if cp.startswith('972'): return '972'
        if cp.startswith('973'): return '973'
        if cp.startswith('974'): return '974'
        return cp[:2]
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
    Cherche un cinéma par nom + code postal dans le bon département uniquement.
    Params: name (obligatoire), address (optionnel - adresse Google avec code postal)
    Exemple: /search-cinema?name=Megarama+Chambly&address=1+place+Chamblyrama+60230+Chambly
    """
    name = request.args.get('name', '').strip()
    address = request.args.get('address', '').strip()
    if not name:
        return jsonify({"error": "name manquant"}), 400

    try:
        name_norm = normalize(name)
        addr_norm = normalize(address)
        mots = [w for w in name_norm.split() if len(w) > 2]

        # Déterminer les emplacements à chercher
        dept_code = extract_dept(address)
        locations_to_search = []

        if dept_code and dept_code in DEPT_MAP:
            # On cherche d'abord dans le bon département
            locations_to_search.append(DEPT_MAP[dept_code])

        # Fallback : toutes les villes principales
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
                    if addr_norm:
                        # Bonus si code postal ou ville correspondent
                        if dept_code and dept_code in c_addr: score += 3
                    if score > best_score and score >= len(mots):
                        best_score = score
                        best = {
                            "id": c.get('id'),
                            "name": c.get('name'),
                            "address": c.get('address'),
                            "score": score,
                            "loc_id": loc_id
                        }
                # Si on a un bon résultat dans le bon département, on arrête
                if best and best['loc_id'] == DEPT_MAP.get(dept_code) and best_score >= len(mots) * 2:
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
