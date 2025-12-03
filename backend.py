import json
import os
import base64
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})

try:
    geolocator = Nominatim(user_agent="Zeta_Navigation_App_v1")
except Exception:
    geolocator = None

def generate_risk_zones():
    return [
        {"name": "Zona Dorada", "lat": 28.6500, "lon": -106.1100, "radius_km": 1.2, "level": "low", "color": "#10b981"},
        {"name": "San Felipe", "lat": 28.6700, "lon": -106.1000, "radius_km": 1.0, "level": "low", "color": "#10b981"},
        {"name": "Campestre", "lat": 28.6600, "lon": -106.0500, "radius_km": 1.5, "level": "low", "color": "#10b981"},
        {"name": "Valle del Sol", "lat": 28.6200, "lon": -106.0400, "radius_km": 1.0, "level": "low", "color": "#10b981"},
        {"name": "Quintas del Sol", "lat": 28.6900, "lon": -106.0700, "radius_km": 0.8, "level": "low", "color": "#10b981"},
        {"name": "Privadas del Bosque", "lat": 28.6650, "lon": -106.0600, "radius_km": 0.7, "level": "low", "color": "#10b981"},
        {"name": "Centro Histórico", "lat": 28.6353, "lon": -106.0886, "radius_km": 0.8, "level": "medium", "color": "#f59e0b"},
        {"name": "Nombre de Dios", "lat": 28.6100, "lon": -106.0800, "radius_km": 1.0, "level": "medium", "color": "#f59e0b"},
        {"name": "Las Haciendas", "lat": 28.7000, "lon": -106.1300, "radius_km": 0.9, "level": "medium", "color": "#f59e0b"},
        {"name": "Industrial", "lat": 28.6000, "lon": -106.1500, "radius_km": 1.2, "level": "medium", "color": "#f59e0b"},
        {"name": "Altavista", "lat": 28.6800, "lon": -106.1200, "radius_km": 0.7, "level": "medium", "color": "#f59e0b"},
        {"name": "Mirador", "lat": 28.6450, "lon": -106.1050, "radius_km": 0.6, "level": "medium", "color": "#f59e0b"},
        {"name": "División del Norte", "lat": 28.5900, "lon": -106.1200, "radius_km": 1.0, "level": "high", "color": "#ef4444"},
        {"name": "Pacífico", "lat": 28.6800, "lon": -106.1500, "radius_km": 0.8, "level": "high", "color": "#ef4444"},
        {"name": "Infonavit Nacional", "lat": 28.5700, "lon": -106.1000, "radius_km": 0.9, "level": "high", "color": "#ef4444"},
        {"name": "Cerro Grande", "lat": 28.7200, "lon": -106.1100, "radius_km": 1.1, "level": "high", "color": "#ef4444"},
        {"name": "Ávalos", "lat": 28.5950, "lon": -106.0950, "radius_km": 0.7, "level": "high", "color": "#ef4444"},
        {"name": "Riberas del Sacramento", "lat": 28.5500, "lon": -106.1300, "radius_km": 0.7, "level": "critical", "color": "#000000"},
        {"name": "Dale", "lat": 28.7400, "lon": -106.1200, "radius_km": 0.6, "level": "critical", "color": "#000000"},
        {"name": "Tierra Nueva", "lat": 28.5800, "lon": -106.1600, "radius_km": 0.8, "level": "critical", "color": "#000000"},
    ]

def generate_places_database():
    return [
        {"name": "Catedral de Chihuahua", "coords": [28.6355, -106.0747], "type": "Turismo", "category": "Religioso"},
        {"name": "Museo Casa Chihuahua", "coords": [28.6370, -106.0760], "type": "Cultura", "category": "Museo"},
        {"name": "Palacio de Gobierno", "coords": [28.6358, -106.0889], "type": "Turismo", "category": "Histórico"},
        {"name": "Quinta Gameros", "coords": [28.6385, -106.0820], "type": "Cultura", "category": "Museo"},
        {"name": "Museo Histórico de la Revolución", "coords": [28.6280, -106.0750], "type": "Cultura", "category": "Museo"},
        {"name": "Teatro de los Héroes", "coords": [28.6365, -106.0885], "type": "Cultura", "category": "Teatro"},
        {"name": "Acueducto Colonial", "coords": [28.6320, -106.0895], "type": "Turismo", "category": "Histórico"},
        {"name": "Parque Metropolitano El Rejón", "coords": [28.6150, -106.1150], "type": "Recreación", "category": "Parque"},
        {"name": "Parque Central", "coords": [28.6360, -106.0880], "type": "Recreación", "category": "Parque"},
        {"name": "Parque Lerdo", "coords": [28.6350, -106.0900], "type": "Recreación", "category": "Parque"},
        {"name": "Bosque La Primavera", "coords": [28.6550, -106.0650], "type": "Recreación", "category": "Parque"},
        {"name": "Parque Las Américas", "coords": [28.6800, -106.1100], "type": "Recreación", "category": "Parque"},
        {"name": "Fashion Mall", "coords": [28.6450, -106.1200], "type": "Compras", "category": "Mall"},
        {"name": "Plaza del Sol", "coords": [28.6400, -106.0800], "type": "Compras", "category": "Plaza"},
        {"name": "Galerías Chihuahua", "coords": [28.6580, -106.0920], "type": "Compras", "category": "Mall"},
        {"name": "Plaza Universidad", "coords": [28.6950, -106.1250], "type": "Compras", "category": "Plaza"},
        {"name": "Distrito 1", "coords": [28.6550, -106.0900], "type": "Comercial", "category": "Mall"},
        {"name": "Plaza Cumbres", "coords": [28.6720, -106.1050], "type": "Compras", "category": "Plaza"},
        {"name": "Universidad Autónoma de Chihuahua", "coords": [28.6380, -106.0950], "type": "Educación", "category": "Universidad"},
        {"name": "Campus UACH II", "coords": [28.7000, -106.1300], "type": "Educación", "category": "Universidad"},
        {"name": "Tecnológico de Chihuahua", "coords": [28.6850, -106.1380], "type": "Educación", "category": "Universidad"},
        {"name": "Universidad La Salle", "coords": [28.6620, -106.0880], "type": "Educación", "category": "Universidad"},
        {"name": "Hospital Ángeles", "coords": [28.6500, -106.1000], "type": "Salud", "category": "Hospital"},
        {"name": "Hospital Central", "coords": [28.6320, -106.0920], "type": "Salud", "category": "Hospital"},
        {"name": "Hospital Star Médica", "coords": [28.6650, -106.1050], "type": "Salud", "category": "Hospital"},
        {"name": "IMSS Clínica 1", "coords": [28.6250, -106.0950], "type": "Salud", "category": "Hospital"},
        {"name": "Restaurante La Casona", "coords": [28.6360, -106.0790], "type": "Restaurante", "category": "Comida"},
        {"name": "Rincón Mexicano", "coords": [28.6340, -106.0870], "type": "Restaurante", "category": "Comida"},
        {"name": "La Mansion", "coords": [28.6380, -106.0810], "type": "Restaurante", "category": "Comida"},
        {"name": "Los Parados", "coords": [28.6420, -106.0890], "type": "Restaurante", "category": "Comida"},
        {"name": "Hotel San Francisco", "coords": [28.6365, -106.0875], "type": "Hotel", "category": "Hospedaje"},
        {"name": "Hotel Soberano", "coords": [28.6350, -106.0895], "type": "Hotel", "category": "Hospedaje"},
        {"name": "Hampton Inn", "coords": [28.6520, -106.1120], "type": "Hotel", "category": "Hospedaje"},
        {"name": "Central de Autobuses", "coords": [28.6080, -106.0920], "type": "Transporte", "category": "Terminal"},
        {"name": "Aeropuerto Internacional", "coords": [28.7029, -105.9646], "type": "Transporte", "category": "Aeropuerto"},
        {"name": "Banco Santander Centro", "coords": [28.6358, -106.0882], "type": "Servicios", "category": "Banco"},
        {"name": "BBVA Av. Independencia", "coords": [28.6365, -106.0895], "type": "Servicios", "category": "Banco"},
        {"name": "Banamex Plaza Mayor", "coords": [28.6352, -106.0878], "type": "Servicios", "category": "Banco"},
        {"name": "Presidencia Municipal", "coords": [28.6355, -106.0892], "type": "Gobierno", "category": "Oficina"},
        {"name": "Congreso del Estado", "coords": [28.6348, -106.0868], "type": "Gobierno", "category": "Oficina"},
    ]

RISK_ZONES = generate_risk_zones()
PLACES_DB = generate_places_database()
users_db = {}
reports_db = []

def get_coordinates(location_name):
    if not location_name: return None, None
    if ',' in location_name and len(location_name.split(',')) == 2:
        try:
            parts = location_name.split(',')
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if 28.0 <= lat <= 29.0 and -107.0 <= lon <= -106.0:
                return lat, lon
        except ValueError:
            pass
    for place in PLACES_DB:
        if place["name"].lower() in location_name.lower():
            return place["coords"][0], place["coords"][1]
    try:
        if geolocator:
            location = geolocator.geocode(f"{location_name}, Chihuahua, México", timeout=5)
            if location:
                return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

def calculate_risk(lat, lon):
    point = (lat, lon)
    risks = []
    for zone in RISK_ZONES:
        zone_point = (zone["lat"], zone["lon"])
        distance = geodesic(point, zone_point).kilometers
        if distance <= zone["radius_km"]:
            risks.append(zone["level"])
    if "critical" in risks: return "Crítico"
    if "high" in risks: return "Alto"
    if "medium" in risks: return "Medio"
    return "Bajo"

def get_transport_options(distance_km, duration_min, risk_level):
    risk_factor = {"Bajo": 1.0, "Medio": 1.1, "Alto": 1.2, "Crítico": 1.4}.get(risk_level, 1.0)
    return [
        {"id": "car", "mode": "Automóvil", "time": f"{int(duration_min * risk_factor)} min", "risk": risk_level, "description": "Ruta estándar"},
        {"id": "moto", "mode": "Motocicleta", "time": f"{int(duration_min * 0.8 * risk_factor)} min", "risk": risk_level, "description": "Más rápido"},
        {"id": "bike", "mode": "Bicicleta", "time": f"{int((distance_km / 15) * 60)} min", "risk": "Bajo", "description": "Ciclovía"},
        {"id": "walk", "mode": "Caminando", "time": f"{int((distance_km / 5) * 60)} min", "risk": risk_level, "description": "A pie"}
    ]

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email', '').lower()
    name = data.get('name', '')
    photo = data.get('photo', '')
    accepted_terms = data.get('accepted_terms', False)
    if not email or not name or not accepted_terms:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400
    if email in users_db:
        return jsonify({"status": "error", "message": "Usuario ya existe"}), 400
    user_id = f"user_{len(users_db) + 1}"
    users_db[email] = {"id": user_id, "email": email, "name": name, "photo": photo, "created_at": datetime.now().isoformat(), "accepted_terms": accepted_terms}
    return jsonify({"status": "success", "user": users_db[email]})

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email', '').lower()
    if email not in users_db:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
    return jsonify({"status": "success", "user": users_db[email]})

@app.route('/api/reports/submit', methods=['POST'])
def submit_report():
    data = request.json
    report = {"id": f"report_{len(reports_db) + 1}", "user_email": data.get('user_email'), "description": data.get('description'), 
              "level": data.get('level', 'low'), "lat": data.get('lat'), "lon": data.get('lon'), "photo": data.get('photo', ''), 
              "timestamp": datetime.now().isoformat(), "verified": False, "votes": 0}
    if not report['description'] or len(report['description']) < 10:
        return jsonify({"status": "error", "message": "Descripción muy corta"}), 400
    reports_db.append(report)
    return jsonify({"status": "success", "report_id": report['id']})

@app.route('/api/reports/list', methods=['GET'])
def get_reports():
    return jsonify({"status": "success", "reports": reports_db})

@app.route('/api/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify([])
    suggestions = [{"name": place["name"], "type": place["type"], "category": place.get("category", "")} for place in PLACES_DB if query in place["name"].lower() or query in place["type"].lower()]
    return jsonify(suggestions[:10])

@app.route('/api/search_places', methods=['GET'])
def search_places():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 3:
        return jsonify([])
    try:
        local_results = [{"name": place["name"], "type": place["type"], "category": place.get("category", ""), "coords": place["coords"], "source": "local"} for place in PLACES_DB if query.lower() in place["name"].lower()]
        osm_results = []
        if geolocator:
            try:
                locations = geolocator.geocode(query, exactly_one=False, limit=10, addressdetails=True, bounds=[[28.4, -106.3], [28.8, -105.8]], timeout=3)
                if locations:
                    for loc in locations:
                        address = loc.raw.get('address', {})
                        display_name = loc.raw.get('display_name', '')
                        if 'chihuahua' in display_name.lower():
                            place_type = "Dirección"
                            if address.get('road'):
                                place_type = "Calle"
                            elif address.get('suburb'):
                                place_type = "Colonia"
                            elif address.get('amenity'):
                                place_type = address['amenity'].title()
                            elif address.get('shop'):
                                place_type = address['shop'].title()
                            parts = []
                            if address.get('house_number') and address.get('road'):
                                parts.append(f"{address['road']} #{address['house_number']}")
                            elif address.get('road'):
                                parts.append(address['road'])
                            elif address.get('name'):
                                parts.append(address['name'])
                            if address.get('suburb'):
                                parts.append(address['suburb'])
                            full_name = ", ".join(parts) if parts else display_name
                            osm_results.append({"name": full_name, "type": place_type, "category": address.get('amenity', address.get('shop', '')), "coords": [loc.latitude, loc.longitude], "source": "osm", "display_name": display_name})
            except Exception as e:
                print(f"Error en búsqueda OSM: {e}")
        all_results = local_results + osm_results
        seen = set()
        unique_results = []
        for result in all_results:
            name_key = result['name'].lower()
            if name_key not in seen:
                seen.add(name_key)
                unique_results.append(result)
        return jsonify(unique_results[:15])
    except Exception as e:
        print(f"Error en search_places: {e}")
        return jsonify([])

@app.route('/api/reverse_geocode', methods=['POST'])
def reverse_geocode():
    data = request.json
    lat = data.get('lat')
    lon = data.get('lon')
    if not lat or not lon:
        return jsonify({"status": "error", "message": "Coordenadas inválidas"}), 400
    try:
        if geolocator:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=5, language='es')
            if location:
                address = location.raw.get('address', {})
                parts = []
                if address.get('road'):
                    parts.append(address['road'])
                if address.get('house_number'):
                    parts.append(f"#{address['house_number']}")
                if address.get('suburb'):
                    parts.append(address['suburb'])
                if address.get('city'):
                    parts.append(address['city'])
                readable_address = ", ".join(parts) if parts else location.address
                return jsonify({"status": "success", "address": readable_address, "details": address})
        return jsonify({"status": "success", "address": f"Coordenadas: {lat:.4f}, {lon:.4f}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analyze_route', methods=['POST'])
def analyze_route():
    try:
        data = request.json
        origin = data.get('origin', '').strip()
        destination = data.get('destination', '').strip()
        origin_lat, origin_lon = get_coordinates(origin)
        dest_lat, dest_lon = get_coordinates(destination)
        if not origin_lat: origin_lat, origin_lon = 28.6353, -106.0886
        if not dest_lat: dest_lat, dest_lon = 28.6700, -106.0600
        osrm_url = f"http://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
        route_geometry = None
        duration_min = 15
        distance_km = 5
        try:
            response = requests.get(osrm_url, timeout=5)
            if response.status_code == 200:
                r_data = response.json()
                if r_data.get('routes'):
                    route = r_data['routes'][0]
                    route_geometry = route['geometry']
                    duration_min = route['duration'] / 60
                    distance_km = route['distance'] / 1000
        except Exception as e:
            print(f"OSRM Error: {e}")
        if not route_geometry:
            route_geometry = {"type": "LineString", "coordinates": [[origin_lon, origin_lat], [dest_lon, dest_lat]]}
        mid_lat = (origin_lat + dest_lat) / 2
        mid_lon = (origin_lon + dest_lon) / 2
        risk_level = calculate_risk(mid_lat, mid_lon)
        transport_options = get_transport_options(distance_km, duration_min, risk_level)
        return jsonify({"status": "success", "origin": {"lat": origin_lat, "lon": origin_lon, "name": origin}, "destination": {"lat": dest_lat, "lon": dest_lon, "name": destination}, "risk_level": risk_level, "distance_km": round(distance_km, 2), "transport_options": transport_options, "route_geometry": route_geometry})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/zones', methods=['GET'])
def get_zones():
    return jsonify({"zones": RISK_ZONES})

@app.route('/api/points', methods=['GET'])
def get_points():
    category = request.args.get('category', '')
    if category:
        filtered = [p for p in PLACES_DB if p.get('category', '') == category]
        return jsonify(filtered)
    return jsonify(PLACES_DB)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0", "users": len(users_db), "reports": len(reports_db), "places": len(PLACES_DB)})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)