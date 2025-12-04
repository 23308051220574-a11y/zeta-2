import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import re

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST"], "allow_headers": ["Content-Type"]}})

try:
    geolocator = Nominatim(user_agent="Zeta_Nav_v2", timeout=3)
except:
    geolocator = None

def generate_risk_zones():
    return [
        {"name": "Zona Dorada", "lat": 28.6500, "lon": -106.1100, "radius_km": 1.0, "level": "low", "color": "#10b981"},
        {"name": "San Felipe", "lat": 28.6700, "lon": -106.1000, "radius_km": 0.8, "level": "low", "color": "#10b981"},
        {"name": "Campestre", "lat": 28.6600, "lon": -106.0500, "radius_km": 1.2, "level": "low", "color": "#10b981"},
        {"name": "Centro Histórico", "lat": 28.6353, "lon": -106.0886, "radius_km": 0.6, "level": "medium", "color": "#f59e0b"},
        {"name": "Industrial", "lat": 28.6000, "lon": -106.1500, "radius_km": 0.9, "level": "medium", "color": "#f59e0b"},
        {"name": "División del Norte", "lat": 28.5900, "lon": -106.1200, "radius_km": 0.8, "level": "high", "color": "#ef4444"},
        {"name": "Pacífico", "lat": 28.6800, "lon": -106.1500, "radius_km": 0.7, "level": "high", "color": "#ef4444"},
        {"name": "Cerro Grande", "lat": 28.7200, "lon": -106.1100, "radius_km": 0.6, "level": "high", "color": "#ef4444"},
        {"name": "Dale", "lat": 28.7450, "lon": -106.1450, "radius_km": 0.5, "level": "critical", "color": "#000000"},
        {"name": "Riberas del Sacramento", "lat": 28.5500, "lon": -106.1300, "radius_km": 0.6, "level": "critical", "color": "#000000"},
    ]

def generate_places():
    return [
        {"name": "Catedral de Chihuahua", "coords": [28.6355, -106.0747], "type": "Turismo"},
        {"name": "Fashion Mall", "coords": [28.6450, -106.1200], "type": "Compras"},
        {"name": "Plaza del Sol", "coords": [28.6400, -106.0800], "type": "Compras"},
        {"name": "UACH Campus 1", "coords": [28.6380, -106.0950], "type": "Educación"},
        {"name": "Hospital Ángeles", "coords": [28.6500, -106.1000], "type": "Salud"},
        {"name": "Parque El Rejón", "coords": [28.6150, -106.1150], "type": "Recreación"},
    ]

RISK_ZONES = generate_risk_zones()
PLACES_DB = generate_places()
users_db = {}
reports_db = []

def validate_text(text):
    if not text or len(text.strip()) < 10:
        return False, "Texto muy corto"
    bad_words = ['spam', 'fake', 'test123']
    if any(word in text.lower() for word in bad_words):
        return False, "Contenido no permitido"
    if len(re.findall(r'[A-Z]{5,}', text)) > 0:
        return False, "Evita mayúsculas excesivas"
    return True, "OK"

def get_coordinates(location_name):
    if not location_name:
        return None, None
    if ',' in location_name and len(location_name.split(',')) == 2:
        try:
            parts = location_name.split(',')
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if 28.0 <= lat <= 29.0 and -107.0 <= lon <= -106.0:
                return lat, lon
        except:
            pass
    for place in PLACES_DB:
        if place["name"].lower() in location_name.lower():
            return place["coords"][0], place["coords"][1]
    try:
        if geolocator:
            loc = geolocator.geocode(f"{location_name}, Chihuahua, México")
            if loc:
                return loc.latitude, loc.longitude
    except:
        pass
    return None, None

def calculate_risk(lat, lon):
    point = (lat, lon)
    risks = []
    for zone in RISK_ZONES:
        dist = geodesic(point, (zone["lat"], zone["lon"])).kilometers
        if dist <= zone["radius_km"]:
            risks.append(zone["level"])
    if "critical" in risks: return "Crítico"
    if "high" in risks: return "Alto"
    if "medium" in risks: return "Medio"
    return "Bajo"

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').lower().strip()
    name = data.get('name', '').strip()
    if not email or '@' not in email or not name:
        return jsonify({"status": "error", "message": "Datos inválidos"}), 400
    if email in users_db:
        return jsonify({"status": "error", "message": "Usuario existe"}), 400
    users_db[email] = {"id": f"u{len(users_db)+1}", "email": email, "name": name, "photo": data.get('photo', ''), "created": datetime.now().isoformat()}
    return jsonify({"status": "success", "user": users_db[email]})

@app.route('/api/reports/submit', methods=['POST'])
def submit_report():
    data = request.json
    desc = data.get('description', '').strip()
    valid, msg = validate_text(desc)
    if not valid:
        return jsonify({"status": "error", "message": msg}), 400
    report = {"id": f"r{len(reports_db)+1}", "user": data.get('user_email'), "desc": desc, "level": data.get('level', 'low'), 
              "lat": data.get('lat'), "lon": data.get('lon'), "photo": data.get('photo', ''), "time": datetime.now().isoformat(), "verified": False}
    reports_db.append(report)
    return jsonify({"status": "success", "report_id": report['id']})

@app.route('/api/reports/list', methods=['GET'])
def get_reports():
    return jsonify({"status": "success", "reports": reports_db})

@app.route('/api/search_places', methods=['GET'])
def search_places():
    q = request.args.get('q', '').strip()
    if len(q) < 3:
        return jsonify([])
    results = []
    for p in PLACES_DB:
        if q.lower() in p["name"].lower():
            results.append({"name": p["name"], "type": p["type"], "coords": p["coords"], "source": "local"})
    if geolocator and len(results) < 5:
        try:
            locs = geolocator.geocode(q, exactly_one=False, limit=5, addressdetails=True, bounds=[[28.4, -106.3], [28.8, -105.8]])
            if locs:
                for loc in locs:
                    addr = loc.raw.get('address', {})
                    if 'chihuahua' in loc.address.lower():
                        name = addr.get('road', loc.address.split(',')[0])
                        results.append({"name": name, "type": "Calle", "coords": [loc.latitude, loc.longitude], "source": "osm"})
        except:
            pass
    return jsonify(results[:10])

@app.route('/api/reverse_geocode', methods=['POST'])
def reverse_geocode():
    data = request.json
    lat, lon = data.get('lat'), data.get('lon')
    if not lat or not lon:
        return jsonify({"status": "error"}), 400
    try:
        if geolocator:
            loc = geolocator.reverse(f"{lat}, {lon}", language='es')
            if loc:
                addr = loc.raw.get('address', {})
                parts = [addr.get('road', ''), addr.get('suburb', '')]
                result = ", ".join([p for p in parts if p]) or loc.address
                return jsonify({"status": "success", "address": result})
    except:
        pass
    return jsonify({"status": "success", "address": "Tu ubicación"})

@app.route('/api/analyze_route', methods=['POST'])
def analyze_route():
    data = request.json
    orig, dest = data.get('origin', '').strip(), data.get('destination', '').strip()
    olat, olon = get_coordinates(orig)
    dlat, dlon = get_coordinates(dest)
    if not olat: olat, olon = 28.6353, -106.0886
    if not dlat: dlat, dlon = 28.6700, -106.0600
    geom = {"type": "LineString", "coordinates": [[olon, olat], [dlon, dlat]]}
    dur, dist = 15, 5
    try:
        r = requests.get(f"http://router.project-osrm.org/route/v1/driving/{olon},{olat};{dlon},{dlat}?overview=full&geometries=geojson", timeout=3)
        if r.status_code == 200:
            rd = r.json()
            if rd.get('routes'):
                rt = rd['routes'][0]
                geom, dur, dist = rt['geometry'], rt['duration']/60, rt['distance']/1000
    except:
        pass
    risk = calculate_risk((olat+dlat)/2, (olon+dlon)/2)
    rf = {"Bajo": 1.0, "Medio": 1.1, "Alto": 1.2, "Crítico": 1.4}.get(risk, 1.0)
    opts = [
        {"mode": "Automóvil", "time": f"{int(dur*rf)} min", "risk": risk},
        {"mode": "Motocicleta", "time": f"{int(dur*0.8*rf)} min", "risk": risk},
        {"mode": "Bicicleta", "time": f"{int((dist/15)*60)} min", "risk": "Bajo"},
        {"mode": "Caminando", "time": f"{int((dist/5)*60)} min", "risk": risk}
    ]
    return jsonify({"status": "success", "origin": {"lat": olat, "lon": olon}, "destination": {"lat": dlat, "lon": dlon}, 
                    "risk_level": risk, "distance_km": round(dist, 1), "transport_options": opts, "route_geometry": geom})

@app.route('/api/zones', methods=['GET'])
def get_zones():
    return jsonify({"zones": RISK_ZONES})

@app.route('/api/points', methods=['GET'])
def get_points():
    return jsonify(PLACES_DB)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "v": "2.0"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5002)), debug=False)
