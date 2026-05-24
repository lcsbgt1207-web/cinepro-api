from flask import Flask, jsonify, request
from flask_cors import CORS
from allocineAPI.allocineAPI import allocineAPI
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import unicodedata, re, math, time, json, os

app = Flask(__name__)
CORS(app)
api = allocineAPI()

# Cache des coordonnées pour éviter de géocoder plusieurs fois la même adresse
COORDS_CACHE = {}
CACHE_FILE = '/tmp/coords_cache.json'

# Cache des séances (clé: cinema_id|date, valeur: {data, timestamp})
SEANCES_CACHE = {}
SEANCES_CACHE_TTL = 3600  # 1 heure

# Cache search-cinema (clé: nom normalisé, valeur: {data, timestamp})
SEARCH_CACHE = {}
SEARCH_CACHE_TTL = 86400  # 24 heures

# Charger le cache depuis le disque si disponible
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r') as f:
            COORDS_CACHE = json.load(f)
    except:
        COORDS_CACHE = {}

geolocator = Nominatim(user_agent="cinepro-app", timeout=5)

def save_cache():
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(COORDS_CACHE, f)
    except:
        pass

def geocode_address(address):
    """Géocode une adresse française et retourne (lat, lng) ou None."""
    if address in COORDS_CACHE:
        return COORDS_CACHE[address]
    try:
        time.sleep(0.5)  # Respecter le rate limit Nominatim
        location = geolocator.geocode(address + ', France')
        if location:
            coords = (location.latitude, location.longitude)
            COORDS_CACHE[address] = coords
            save_cache()
            return coords
    except GeocoderTimedOut:
        pass
    except Exception:
        pass
    COORDS_CACHE[address] = None
    return None

def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# Coordonnées GPS des départements (centroïdes)
DEPT_COORDS = {
    'departement-83191': (46.20, 5.35),
    'departement-83178': (49.57, 3.62),
    'departement-83111': (46.35, 3.03),
    'departement-83185': (44.12, 6.24),
    'departement-83186': (44.67, 6.27),
    'departement-83187': (43.92, 7.25),
    'departement-83112': (44.75, 4.60),
    'departement-83129': (49.70, 4.70),
    'departement-83155': (43.00, 1.60),
    'departement-83130': (48.30, 4.07),
    'departement-83138': (43.10, 2.35),
    'departement-83151': (44.35, 2.57),
    'departement-83104': (48.50, 7.75),
    'departement-83188': (43.50, 5.40),
    'departement-83160': (49.10, -0.37),
    'departement-83181': (45.70, 0.16),
    'departement-83182': (45.75, -0.68),
    'departement-83123': (47.07, 2.40),
    'departement-83143': (45.37, 1.88),
    'departement-265496': (41.87, 9.00),
    'departement-83115': (47.32, 4.83),
    'departement-83119': (48.45, -3.00),
    'departement-83144': (46.00, 2.02),
    'departement-83106': (45.15, 0.73),
    'departement-83193': (47.13, 6.23),
    'departement-83189': (44.73, 5.25),
    'departement-83168': (48.53, 2.27),
    'departement-83163': (49.12, 1.17),
    'departement-83120': (48.45, 1.37),
    'departement-83139': (43.95, 4.42),
    'departement-83152': (43.60, 1.44),
    'departement-83153': (43.65, 0.57),
    'departement-83107': (44.84, -0.58),
    'departement-83199': (16.25, -61.58),
    'departement-83201': (4.00, -53.00),
    'departement-83105': (47.75, 7.33),
    'departement-83133': (42.35, 9.18),
    'departement-83113': (45.25, 3.88),
    'departement-83132': (48.10, 5.13),
    'departement-83136': (47.63, 6.08),
    'departement-83198': (45.92, 6.47),
    'departement-83145': (45.88, 1.28),
    'departement-83169': (48.83, 2.23),
    'departement-83140': (43.62, 3.88),
    'departement-83121': (48.15, -1.68),
    'departement-83125': (46.82, 1.58),
    'departement-83126': (47.25, 0.68),
    'departement-83194': (45.28, 5.72),
    'departement-83135': (46.68, 5.55),
    'departement-83108': (43.93, -0.50),
    'departement-83127': (47.60, 1.33),
    'departement-83195': (45.75, 4.12),
    'departement-83173': (47.37, -1.55),
    'departement-83128': (47.90, 2.08),
    'departement-83154': (44.62, 1.67),
    'departement-83109': (44.37, 0.47),
    'departement-83141': (44.43, 3.50),
    'departement-83174': (47.38, -0.55),
    'departement-83161': (49.08, -1.30),
    'departement-83131': (49.05, 4.03),
    'departement-83200': (14.67, -61.00),
    'departement-83175': (48.08, -0.77),
    'departement-83146': (48.70, 6.18),
    'departement-83147': (49.00, 5.38),
    'departement-83122': (47.87, -2.83),
    'departement-83148': (49.00, 6.55),
    'departement-83116': (47.12, 3.50),
    'departement-83158': (50.42, 3.08),
    'departement-83179': (49.25, 2.50),
    'departement-83162': (48.63, 0.10),
    'ville-115755':      (48.86, 2.35),
    'ville-83172':       (49.08, 2.08),  # Val-d'Oise (L'Isle-Adam, Cergy...)
    'ville-83166':       (48.75, 2.92),  # Val-de-Marne
    'ville-83170':       (48.92, 2.40),  # Seine-Saint-Denis
    'ville-83171':       (48.78, 2.48),  # Seine-et-Marne ouest
    'ville-83179':       (49.25, 2.50),  # Oise sud
    'departement-83159': (50.45, 2.55),
    'departement-83114': (45.77, 3.08),
    'departement-83110': (43.38, -0.77),
    'departement-83142': (42.70, 2.90),
    'departement-83202': (45.75, 4.85),
    'departement-83196': (46.65, 4.87),
    'departement-83117': (47.98, 0.17),
    'departement-83197': (45.47, 6.43),
    'departement-83166': (48.75, 2.92),
    'departement-83164': (49.65, 1.08),
    'departement-83170': (48.92, 2.40),
    'departement-83180': (49.92, 2.30),
    'departement-83156': (43.93, 2.15),
    'departement-83157': (44.00, 1.35),
    'departement-83171': (48.78, 2.48),
    'departement-83172': (49.08, 2.08),
    'departement-83190': (43.97, 5.35),
    'departement-83177': (46.67, -1.43),
    'departement-83184': (46.52, 0.43),
    'departement-83149': (48.17, 6.45),
    'departement-83118': (47.80, 3.57),
    'departement-83167': (48.78, 1.83),
    'departement-83183': (46.57, -0.38),
    'departement-83206': (48.75, 2.92),
    'departement-83207': (48.78, 1.83),
    'departement-83210': (48.53, 2.27),
    'departement-83211': (48.83, 2.23),
    'departement-83212': (48.92, 2.40),
    'departement-83213': (48.78, 2.48),
    'departement-83214': (49.05, 2.13),
}

def normalize(text):
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def find_nearest_depts(lat, lng, top_n=3):
    distances = []
    seen = set()
    for dept_id, (dlat, dlng) in DEPT_COORDS.items():
        if dept_id not in seen:
            seen.add(dept_id)
            d = haversine(lat, lng, dlat, dlng)
            distances.append((d, dept_id))
    distances.sort()
    return [dept_id for _, dept_id in distances[:top_n]]

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "CinéProche API"})

@app.route('/seances')
def seances():
    cinema_id = request.args.get('id', '')
    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    if not cinema_id:
        return jsonify({"error": "id manquant"}), 400

    # Vérifier le cache séances
    cache_key = f"{cinema_id}|{date_str}"
    now = time.time()
    if cache_key in SEANCES_CACHE:
        entry = SEANCES_CACHE[cache_key]
        if now - entry['ts'] < SEANCES_CACHE_TTL:
            return jsonify({"cinema_id": cinema_id, "date": date_str, "seances": entry['data'], "cached": True})

    try:
        data = api.get_showtime(cinema_id, date_str)
        # Sauvegarder dans le cache
        SEANCES_CACHE[cache_key] = {'data': data, 'ts': now}
        return jsonify({"cinema_id": cinema_id, "date": date_str, "seances": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/seances-auto')
def seances_auto():
    cinema_id = request.args.get('id', '')
    start_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    days = int(request.args.get('days', 7))

    if not cinema_id:
        return jsonify({"error": "id manquant"}), 400

    try:
        base_date = datetime.strptime(start_date, '%Y-%m-%d')
        attempts = []

        for offset in range(days + 1):
            current_date = (base_date + timedelta(days=offset)).strftime('%Y-%m-%d')
            cache_key = f"{cinema_id}|{current_date}"
            now = time.time()

            # Vérifier le cache
            if cache_key in SEANCES_CACHE and now - SEANCES_CACHE[cache_key]['ts'] < SEANCES_CACHE_TTL:
                data = SEANCES_CACHE[cache_key]['data']
                count = len(data) if isinstance(data, list) else 0
                if count > 0:
                    return jsonify({"cinema_id": cinema_id, "requested_date": start_date,
                                    "date": current_date, "auto": True, "cached": True,
                                    "attempts": attempts, "seances": data})
                continue

            try:
                data = api.get_showtime(cinema_id, current_date)
                count = len(data) if isinstance(data, list) else 0
                SEANCES_CACHE[cache_key] = {'data': data, 'ts': now}
                attempts.append({"date": current_date, "count": count})
                if count > 0:
                    return jsonify({"cinema_id": cinema_id, "requested_date": start_date,
                                    "date": current_date, "auto": True,
                                    "attempts": attempts, "seances": data})
            except Exception as inner_error:
                attempts.append({"date": current_date, "error": str(inner_error)})

        return jsonify({"cinema_id": cinema_id, "requested_date": start_date,
                        "date": start_date, "auto": True, "attempts": attempts, "seances": []})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cinemas')
def cinemas():
    location_id = request.args.get('loc', '')
    try:
        user_lat = float(request.args.get('lat', 0))
        user_lng = float(request.args.get('lng', 0))
    except:
        user_lat, user_lng = 0, 0

    if not location_id:
        return jsonify({"error": "loc manquant"}), 400
    try:
        data = api.get_cinema(location_id)
        cinemas_list = data if isinstance(data, list) else data.get('cinemas', [])

        result = []
        for c in cinemas_list:
            address = c.get('address', '')
            coords = geocode_address(address)
            cinema = {
                "id": c.get('id'),
                "name": c.get('name'),
                "address": address,
                "lat": coords[0] if coords else None,
                "lng": coords[1] if coords else None,
            }
            if user_lat and user_lng and coords:
                cinema['distance_km'] = round(haversine(user_lat, user_lng, coords[0], coords[1]), 2)
            result.append(cinema)

        if user_lat and user_lng:
            result.sort(key=lambda x: x.get('distance_km', 9999))

        return jsonify({"cinemas": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cinemas-proches')
def cinemas_proches():
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
        radius_km = float(request.args.get('radius_km', 30))
    except:
        return jsonify({"error": "lat/lng invalides"}), 400

    if not lat or not lng:
        return jsonify({"error": "lat et lng obligatoires"}), 400

    try:
        dept_ids = find_nearest_depts(lat, lng, top_n=2)
        all_cinemas = []
        seen_ids = set()

        for dept_id in dept_ids:
            try:
                data = api.get_cinema(dept_id)
                cinemas_list = data if isinstance(data, list) else data.get('cinemas', [])
                for c in cinemas_list:
                    if c.get('id') in seen_ids:
                        continue
                    seen_ids.add(c.get('id'))
                    address = c.get('address', '')
                    coords = geocode_address(address)
                    if not coords:
                        continue
                    dist = haversine(lat, lng, coords[0], coords[1])
                    if dist > radius_km:
                        continue
                    all_cinemas.append({
                        "id": c.get('id'),
                        "name": c.get('name'),
                        "address": address,
                        "lat": coords[0],
                        "lng": coords[1],
                        "distance_km": round(dist, 2)
                    })
            except:
                continue

        all_cinemas.sort(key=lambda x: x['distance_km'])
        return jsonify({"cinemas": all_cinemas, "count": len(all_cinemas)})

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
    name = request.args.get('name', '').strip()
    try:
        lat = float(request.args.get('lat', 0))
        lng = float(request.args.get('lng', 0))
    except:
        lat, lng = 0, 0

    if not name:
        return jsonify({"error": "name manquant"}), 400

    # Vérifier le cache search
    cache_key = normalize(name)
    now = time.time()
    if cache_key in SEARCH_CACHE:
        entry = SEARCH_CACHE[cache_key]
        if now - entry['ts'] < SEARCH_CACHE_TTL:
            return jsonify({**entry['data'], "cached": True})

    try:
        STOP_WORDS = {'le', 'la', 'les', 'du', 'de', 'des', 'salle', 'theatre', 'cine'}
        name_norm = normalize(name)
        mots = [w for w in name_norm.split() if len(w) > 2 and w not in STOP_WORDS]

        if lat and lng:
            locations_to_search = find_nearest_depts(lat, lng, top_n=5)
        else:
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
                    if loc_id == locations_to_search[0]: score += 1
                    if score > best_score and score >= max(1, len(mots) - 1):
                        best_score = score
                        best = {
                            "id": c.get('id'),
                            "name": c.get('name'),
                            "address": c.get('address'),
                            "score": score,
                            "loc_id": loc_id
                        }
                if best and loc_id == locations_to_search[0] and best_score >= len(mots) * 2:
                    break
            except:
                continue

        if best:
            SEARCH_CACHE[cache_key] = {'data': best, 'ts': now}
            return jsonify(best)
        else:
            return jsonify({"id": None, "message": "Cinéma non trouvé"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
