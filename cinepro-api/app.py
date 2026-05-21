from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'fr-FR,fr;q=0.9',
}

@app.route('/')
def index():
    return jsonify({"status": "ok", "message": "CinéProche API"})

@app.route('/seances')
def seances():
    cinema_id = request.args.get('id', '')
    if not cinema_id:
        return jsonify({"error": "id manquant"}), 400
    
    url = f"https://www.allocine.fr/seance/salle_gen_csalle={cinema_id}.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        seances = []
        films = soup.select('.item.card')
        
        for film in films:
            titre_el = film.select_one('.meta-title-link')
            if not titre_el:
                continue
            titre = titre_el.text.strip()
            
            horaires = []
            for h in film.select('.showtimes-hour-item'):
                horaires.append(h.text.strip())
            
            if horaires:
                seances.append({
                    "titre": titre,
                    "horaires": horaires
                })
        
        return jsonify({"cinema_id": cinema_id, "seances": seances})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recherche')
def recherche():
    nom = request.args.get('q', '')
    if not nom:
        return jsonify({"error": "q manquant"}), 400
    
    url = f"https://www.allocine.fr/recherche/?q={requests.utils.quote(nom)}&lang=fr"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        cinemas = []
        for item in soup.select('.card.entity-card')[:10]:
            nom_el = item.select_one('.meta-title-link')
            addr_el = item.select_one('.address')
            link_el = item.select_one('a.meta-title-link')
            if nom_el:
                cinema_id = ''
                if link_el:
                    href = link_el.get('href', '')
                    m = re.search(r'csalle=(\d+)', href)
                    if m:
                        cinema_id = m.group(1)
                cinemas.append({
                    "nom": nom_el.text.strip(),
                    "adresse": addr_el.text.strip() if addr_el else '',
                    "id": cinema_id
                })
        
        return jsonify({"resultats": cinemas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
