from flask import Flask, jsonify, request
from flask_cors import CORS
from allocineAPI.allocineAPI import allocineAPI
from datetime import datetime
import unicodedata, re

app = Flask(__name__)
CORS(app)
api = allocineAPI()

def normalize(text):
    """Minuscules, sans accents, sans ponctuation"""
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

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
    Cherche un cinéma par nom dans toutes les villes ET départements.
    Params: name (obligatoire), city (optionnel)
    Exemple: /search-cinema?name=Megarama+Chambly&city=Chambly
    """
    name = request.args.get('name', '').strip()
    city = request.args.get('city', '').strip()
    if not name:
        return jsonify({"error": "name manquant"}), 400

    try:
        # Récupère toutes les villes ET tous les départements
        villes_data = api.get_top_villes()
        dept_data = api.get_departements()

        all_locations = []
        if isinstance(villes_data, list):
            all_locations += [v['id'] for v in villes_data if 'id' in v]
        if isinstance(dept_data, list):
            all_locations += [d['id'] for d in dept_data if 'id' in d]

        name_norm = normalize(name)
        city_norm = normalize(city) if city else ''
        mots = [w for w in name_norm.split() if len(w) > 2]

        best = None
        best_score = 0

        for loc_id in all_locations:
            try:
                data = api.get_cinema(loc_id)
                cinemas_list = data if isinstance(data, list) else data.get('cinemas', [])
                for c in cinemas_list:
                    c_name = normalize(c.get('name', ''))
                    c_addr = normalize(c.get('address', ''))

                    score = 0
                    for mot in mots:
                        if mot in c_name:
                            score += 2
                        elif mot in c_addr:
                            score += 1
                    if city_norm and city_norm in c_addr:
                        score += 3
                    if city_norm and city_norm in c_name:
                        score += 2

                    if score > best_score and score >= len(mots):
                        best_score = score
                        best = {
                            "id": c.get('id'),
                            "name": c.get('name'),
                            "address": c.get('address'),
                            "score": score,
                            "loc_id": loc_id
                        }
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
