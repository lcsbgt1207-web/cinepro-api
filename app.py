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

@app.route('/search-cinema')
def search_cinema():
    """
    Cherche un cinéma par nom et ville, retourne son ID AlloCiné.
    Params: name (obligatoire), city (optionnel)
    Exemple: /search-cinema?name=Megarama+Chambly&city=Chambly
    """
    name = request.args.get('name', '').strip()
    city = request.args.get('city', '').strip()
    if not name:
        return jsonify({"error": "name manquant"}), 400

    try:
        # Liste des IDs de villes à essayer
        # On utilise get_top_villes() si disponible, sinon liste fixe
        VILLES_IDS = [
            'ville-115755',  # Paris
            'ville-113315',  # Lyon
            'ville-96943',   # Bordeaux
            'ville-98857',   # Grenoble
            'ville-107951',  # Lille
            'ville-87860',   # Aix-en-Provence
            'ville-101187',  # Nantes
            'ville-98024',   # Rennes
            'ville-96373',   # Toulouse
            'ville-112664',  # Strasbourg
            'ville-124868',  # Nice
            'ville-97612',   # Montpellier
            'ville-85268',   # Cannes
            'ville-91241',   # Dijon
            'ville-85327',   # Antibes
            'ville-98662',   # Tours
            'ville-110514',  # Clermont-Ferrand
            'ville-87914',   # Marseille
            'ville-124868',  # Monaco
        ]

        name_norm = normalize(name)
        city_norm = normalize(city) if city else ''

        # Mots clés importants du nom (> 2 lettres)
        mots = [w for w in name_norm.split() if len(w) > 2]

        best = None
        best_score = 0

        for ville_id in VILLES_IDS:
            try:
                data = api.get_cinema(ville_id)
                cinemas_list = data if isinstance(data, list) else data.get('cinemas', [])
                for c in cinemas_list:
                    c_name = normalize(c.get('name', ''))
                    c_addr = normalize(c.get('address', ''))

                    # Score de correspondance
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
                            "ville_id": ville_id
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
