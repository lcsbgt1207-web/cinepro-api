from flask import Flask, jsonify, request
from flask_cors import CORS
from allocineAPI.allocineAPI import allocineAPI
from datetime import datetime
import unicodedata, re, math

app = Flask(__name__)
CORS(app)
api = allocineAPI()

# Coordonnées GPS de chaque département (centroïde approximatif)
DEPT_COORDS = {
    'departement-83191': (46.20, 5.35),   # Ain
    'departement-83178': (49.57, 3.62),   # Aisne
    'departement-83111': (46.35, 3.03),   # Allier
    'departement-83185': (44.12, 6.24),   # Alpes-de-Haute-Provence
    'departement-83186': (44.67, 6.27),   # Hautes-Alpes
    'departement-83187': (43.92, 7.25),   # Alpes-Maritimes
    'departement-83112': (44.75, 4.60),   # Ardèche
    'departement-83129': (49.70, 4.70),   # Ardennes
    'departement-83155': (43.00, 1.60),   # Ariège
    'departement-83130': (48.30, 4.07),   # Aube
    'departement-83138': (43.10, 2.35),   # Aude
    'departement-83151': (44.35, 2.57),   # Aveyron
    'departement-83104': (48.50, 7.75),   # Bas-Rhin
    'departement-83188': (43.50, 5.40),   # Bouches-du-Rhône
    'departement-83160': (49.10, -0.37),  # Calvados
    'departement-83112': (45.07, 2.68),   # Cantal
    'departement-83181': (45.70, 0.16),   # Charente
    'departement-83182': (45.75, -0.68),  # Charente-Maritime
    'departement-83123': (47.07, 2.40),   # Cher
    'departement-83143': (45.37, 1.88),   # Corrèze
    'departement-265496': (41.87, 9.00),  # Corse-du-Sud
    'departement-83115': (47.32, 4.83),   # Côte-d'Or
    'departement-83119': (48.45, -3.00),  # Côtes-d'Armor
    'departement-83144': (46.00, 2.02),   # Creuse
    'departement-83106': (45.15, 0.73),   # Dordogne
    'departement-83193': (47.13, 6.23),   # Doubs
    'departement-83189': (44.73, 5.25),   # Drôme
    'departement-83168': (48.53, 2.27),   # Essonne
    'departement-83163': (49.12, 1.17),   # Eure
    'departement-83120': (48.45, 1.37),   # Eure-et-Loir
    'departement-83120': (48.28, -4.03),  # Finistère
    'departement-83139': (43.95, 4.42),   # Gard
    'departement-83152': (43.60, 1.44),   # Haute-Garonne
    'departement-83153': (43.65, 0.57),   # Gers
    'departement-83107': (44.84, -0.58),  # Gironde
    'departement-83199': (16.25, -61.58), # Guadeloupe
    'departement-83201': (4.00, -53.00),  # Guyane
    'departement-83105': (47.75, 7.33),   # Haut-Rhin
    'departement-83133': (42.35, 9.18),   # Haute-Corse
    'departement-83113': (45.25, 3.88),   # Haute-Loire
    'departement-83132': (48.10, 5.13),   # Haute-Marne
    'departement-83136': (47.63, 6.08),   # Haute-Saône
    'departement-83198': (45.92, 6.47),   # Haute-Savoie
    'departement-83145': (45.88, 1.28),   # Haute-Vienne
    'departement-83155': (43.07, 0.17),   # Hautes-Pyrénées
    'departement-83169': (48.83, 2.23),   # Hauts-de-Seine
    'departement-83140': (43.62, 3.88),   # Hérault
    'departement-83121': (48.15, -1.68),  # Ille-et-Vilaine
    'departement-83125': (46.82, 1.58),   # Indre
    'departement-83126': (47.25, 0.68),   # Indre-et-Loire
    'departement-83194': (45.28, 5.72),   # Isère
    'departement-83135': (46.68, 5.55),   # Jura
    'departement-83108': (43.93, -0.50),  # Landes
    'departement-83127': (47.60, 1.33),   # Loir-et-Cher
    'departement-83195': (45.75, 4.12),   # Loire
    'departement-83173': (47.37, -1.55),  # Loire-Atlantique
    'departement-83128': (47.90, 2.08),   # Loiret
    'departement-83154': (44.62, 1.67),   # Lot
    'departement-83109': (44.37, 0.47),   # Lot-et-Garonne
    'departement-83141': (44.43, 3.50),   # Lozère
    'departement-83174': (47.38, -0.55),  # Maine-et-Loire
    'departement-83161': (49.08, -1.30),  # Manche
    'departement-83131': (49.05, 4.03),   # Marne
    'departement-83200': (14.67, -61.00), # Martinique
    'departement-83175': (48.08, -0.77),  # Mayenne
    'departement-83146': (48.70, 6.18),   # Meurthe-et-Moselle
    'departement-83147': (49.00, 5.38),   # Meuse
    'departement-83122': (47.87, -2.83),  # Morbihan
    'departement-83148': (49.00, 6.55),   # Moselle
    'departement-83116': (47.12, 3.50),   # Nièvre
    'departement-83158': (50.42, 3.08),   # Nord
    'departement-83179': (49.42, 2.43),   # Oise ← Chambly !
    'departement-83162': (48.63, 0.10),   # Orne
    'ville-115755':      (48.86, 2.35),   # Paris
    'departement-83159': (50.45, 2.55),   # Pas-de-Calais
    'departement-83114': (45.77, 3.08),   # Puy-de-Dôme
    'departement-83110': (43.38, -0.77),  # Pyrénées-Atlantiques
    'departement-83142': (42.70, 2.90),   # Pyrénées-Orientales
    'departement-83202': (45.75, 4.85),   # Rhône
    'departement-83196': (46.65, 4.87),   # Saône-et-Loire
    'departement-83117': (47.98, 0.17),   # Sarthe
    'departement-83197': (45.47, 6.43),   # Savoie
    'departement-83166': (48.75, 2.92),   # Seine-et-Marne
    'departement-83164': (49.65, 1.08),   # Seine-Maritime
    'departement-83170': (48.92, 2.40),   # Seine-Saint-Denis
    'departement-83180': (49.92, 2.30),   # Somme
    'departement-83156': (43.93, 2.15),   # Tarn
    'departement-83157': (44.00, 1.35),   # Tarn-et-Garonne
    'departement-83171': (48.78, 2.48),   # Val-de-Marne
    'departement-83172': (49.05, 2.13),   # Val-d'Oise
    'departement-83189': (43.40, 6.22),   # Var
    'departement-83190': (43.97, 5.35),   # Vaucluse
    'departement-83177': (46.67, -1.43),  # Vendée
    'departement-83184': (46.52, 0.43),   # Vienne
    'departement-83145': (45.88, 1.28),   # Haute-Vienne
    'departement-83149': (48.17, 6.45),   # Vosges
    'departement-83118': (47.80, 3.57),   # Yonne
    'departement-83167': (48.78, 1.83),   # Yvelines
    'departement-83183': (46.57, -0.38),  # Deux-Sèvres
    'departement-83163': (49.12, 1.17),   # Eure
    'departement-83160': (49.10, -0.37),  # Calvados
    'departement-83206': (48.75, 2.92),   # Seine-et-Marne
    'departement-83207': (48.78, 1.83),   # Yvelines
    'departement-83210': (48.53, 2.27),   # Essonne
    'departement-83211': (48.83, 2.23),   # Hauts-de-Seine
    'departement-83212': (48.92, 2.40),   # Seine-Saint-Denis
    'departement-83213': (48.78, 2.48),   # Val-de-Marne
    'departement-83214': (49.05, 2.13),   # Val-d'Oise
}

def normalize(text):
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def find_nearest_dept(lat, lng, top_n=3):
    """Trouve les N départements les plus proches des coordonnées GPS."""
    distances = []
    for dept_id, (dlat, dlng) in DEPT_COORDS.items():
        d = haversine(lat, lng, dlat, dlng)
        distances.append((d, dept_id))
    distances.sort()
    # Dédupliquer les IDs
    seen = set()
    result = []
    for d, dept_id in distances:
        if dept_id not in seen:
            seen.add(dept_id)
            result.append(dept_id)
        if len(result) >= top_n:
            break
    return result

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
    Cherche un cinéma par nom via coordonnées GPS.
    Params: name (obligatoire), lat, lng (coordonnées du cinéma)
    """
    name = request.args.get('name', '').strip()
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
    except:
        lat, lng = 0, 0

    if not name:
        return jsonify({"error": "name manquant"}), 400

    try:
        name_norm = normalize(name)
        mots = [w for w in name_norm.split() if len(w) > 2]

        # Trouver les 3 départements les plus proches via GPS
        if lat and lng:
            locations_to_search = find_nearest_dept(lat, lng, top_n=3)
        else:
            # Fallback : villes principales
            villes_data = api.get_top_villes()
            locations_to_search = [v['id'] for v in villes_data if 'id' in v] if isinstance(villes_data, list) else []

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
                # Bon résultat dans le 1er département → on arrête
                if best and loc_id == locations_to_search[0] and best_score >= len(mots) * 2:
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
