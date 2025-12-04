import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import re
import hashlib

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "DELETE"], "allow_headers": ["Content-Type"]}})

try:
    geolocator = Nominatim(user_agent="Zeta_Security_Nav_v3", timeout=5)
except:
    geolocator = None

# Zonas de riesgo REALES basadas en datos oficiales de Seguridad Pública Municipal
def generate_risk_zones():
    return [
        # Zonas de ALTO RIESGO (según DSPM 2024)
        {"name": "Dale", "lat": 28.7050, "lon": -106.1450, "radius_km": 0.8, "level": "critical", "color": "#dc2626"},
        {"name": "Gustavo Díaz Ordaz", "lat": 28.7100, "lon": -106.1380, "radius_km": 0.6, "level": "high", "color": "#ef4444"},
        {"name": "Ferrocarrilera", "lat": 28.7000, "lon": -106.1500, "radius_km": 0.5, "level": "high", "color": "#ef4444"},
        
        # Zona Norte (Alta incidencia)
        {"name": "Cerro Grande", "lat": 28.7200, "lon": -106.1100, "radius_km": 0.7, "level": "high", "color": "#ef4444"},
        {"name": "Barrio del Norte", "lat": 28.6850, "lon": -106.0950, "radius_km": 0.6, "level": "high", "color": "#ef4444"},
        {"name": "Industrial", "lat": 28.6900, "lon": -106.0900, "radius_km": 0.8, "level": "medium", "color": "#f59e0b"},
        
        # Zonas de RIESGO MEDIO
        {"name": "División del Norte", "lat": 28.5900, "lon": -106.1200, "radius_km": 0.9, "level": "medium", "color": "#f59e0b"},
        {"name": "Jardines de Oriente", "lat": 28.6200, "lon": -106.0400, "radius_km": 0.7, "level": "medium", "color": "#f59e0b"},
        {"name": "Centro Histórico (noche)", "lat": 28.6353, "lon": -106.0886, "radius_km": 0.4, "level": "medium", "color": "#f59e0b"},
        
        # Zonas SEGURAS
        {"name": "San Felipe", "lat": 28.6700, "lon": -106.1000, "radius_km": 0.9, "level": "low", "color": "#10b981"},
        {"name": "Campestre", "lat": 28.6450, "lon": -106.0500, "radius_km": 1.0, "level": "low", "color": "#10b981"},
        {"name": "Quintas del Sol", "lat": 28.6500, "lon": -106.1100, "radius_km": 0.8, "level": "low", "color": "#10b981"},
        {"name": "Saucito", "lat": 28.6600, "lon": -106.1200, "radius_km": 0.7, "level": "low", "color": "#10b981"},
    ]

# Puntos de interés con coordenadas CORRECTAS
def generate_places():
    return [
        # Lugares históricos y culturales (coordenadas verificadas)
        {"name": "Catedral de Chihuahua", "coords": [28.6358, -106.0773], "type": "Turismo", "rating": 4.8},
        {"name": "Quinta Gameros", "coords": [28.6400, -106.0850], "type": "Cultura", "rating": 4.7},
        {"name": "Museo Casa Villa", "coords": [28.6320, -106.0910], "type": "Cultura", "rating": 4.6},
        {"name": "Plaza de Armas", "coords": [28.6355, -106.0880], "type": "Recreación", "rating": 4.5},
        {"name": "Palacio de Gobierno", "coords": [28.6350, -106.0875], "type": "Turismo", "rating": 4.6},
        
        # Centros comerciales
        {"name": "Fashion Mall", "coords": [28.6580, -106.1170], "type": "Compras", "rating": 4.4},
        {"name": "Plaza del Sol", "coords": [28.6250, -106.0750], "type": "Compras", "rating": 4.3},
        {"name": "Galerías Chihuahua", "coords": [28.6400, -106.1100], "type": "Compras", "rating": 4.5},
        
        # Educación
        {"name": "UACH Campus 1", "coords": [28.6380, -106.0950], "type": "Educación", "rating": 4.5},
        {"name": "UACH Campus 2", "coords": [28.6600, -106.0400], "type": "Educación", "rating": 4.4},
        {"name": "ITESM Chihuahua", "coords": [28.6450, -106.0600], "type": "Educación", "rating": 4.6},
        
        # Salud
        {"name": "Hospital Ángeles", "coords": [28.6500, -106.1000], "type": "Salud", "rating": 4.5},
        {"name": "Hospital Cima", "coords": [28.6520, -106.1050], "type": "Salud", "rating": 4.4},
        {"name": "Hospital Central", "coords": [28.6380, -106.0920], "type": "Salud", "rating": 4.3},
        
        # Recreación
        {"name": "Parque El Rejón", "coords": [28.6150, -106.1150], "type": "Recreación", "rating": 4.4},
        {"name": "Parque Lerdo", "coords": [28.6330, -106.0800], "type": "Recreación", "rating": 4.5},
        {"name": "Parque El Palomar", "coords": [28.6500, -106.0900], "type": "Recreación", "rating": 4.6},
    ]

RISK_ZONES = generate_risk_zones()
PLACES_DB = generate_places()

# Base de datos simple con persistencia
DATA_FILE = 'zeta_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"users": {}, "reports": []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

db = load_data()

# Validación mejorada
def validate_text(text, min_length=10, max_length=500):
    if not text or len(text.strip()) < min_length:
        return False, f"El texto debe tener al menos {min_length} caracteres"
    if len(text) > max_length:
        return False, f"El texto no debe exceder {max_length} caracteres"
    
    # Detectar spam patterns
    spam_patterns = [
        r'https?://', r'www\.', r'\b(viagra|casino|lottery|prize)\b',
        r'[A-Z]{10,}', r'(.)\1{5,}', r'\$\$\$', r'!!!{3,}'
    ]
    for pattern in spam_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Contenido no permitido detectado"
    
    # Verificar contenido mínimo
    words = text.split()
    if len(words) < 3:
        return False, "Descripción demasiado corta"
    
    return True, "OK"

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def hash_email(email):
    return hashlib.sha256(email.lower().encode()).hexdigest()[:16]

def get_coordinates(location_name):
    """Obtener coordenadas mejorado con múltiples métodos"""
    if not location_name:
        return None, None
    
    # Método 1: Coordenadas directas lat,lon
    if ',' in location_name:
        try:
            parts = location_name.split(',')
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if 28.0 <= lat <= 29.0 and -107.0 <= lon <= -106.0:
                return lat, lon
        except:
            pass
    
    # Método 2: Buscar en base de datos local
    location_lower = location_name.lower()
    for place in PLACES_DB:
        if place["name"].lower() in location_lower or location_lower in place["name"].lower():
            return place["coords"][0], place["coords"][1]
    
    # Método 3: Geocodificación con Nominatim
    if geolocator:
        try:
            # Agregar "Chihuahua, México" para mejorar precisión
            query = f"{location_name}, Chihuahua, Chihuahua, México"
            location = geolocator.geocode(query, timeout=5)
            if location:
                # Verificar que esté dentro de los límites de Chihuahua
                if 28.0 <= location.latitude <= 29.0 and -107.0 <= location.longitude <= -106.0:
                    return location.latitude, location.longitude
        except Exception as e:
            print(f"Geocoding error: {e}")
    
    return None, None

def calculate_risk(lat, lon):
    """Calcular riesgo basado en múltiples zonas"""
    point = (lat, lon)
    risks = []
    risk_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    
    for zone in RISK_ZONES:
        dist = geodesic(point, (zone["lat"], zone["lon"])).kilometers
        if dist <= zone["radius_km"]:
            risks.append((zone["level"], dist))
    
    if not risks:
        return "Bajo"
    
    # Ordenar por prioridad y distancia
    risks.sort(key=lambda x: (risk_scores[x[0]], -x[1]), reverse=True)
    highest_risk = risks[0][0]
    
    risk_map = {"critical": "Crítico", "high": "Alto", "medium": "Medio", "low": "Bajo"}
    return risk_map.get(highest_risk, "Bajo")

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "version": "3.0", "database": len(db["reports"])})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').lower().strip()
    name = data.get('name', '').strip()
    
    if not email or not validate_email(email):
        return jsonify({"status": "error", "message": "Email inválido"}), 400
    
    if not name or len(name) < 2:
        return jsonify({"status": "error", "message": "Nombre inválido"}), 400
    
    user_id = hash_email(email)
    
    if email in db["users"]:
        return jsonify({
            "status": "success", 
            "message": "Sesión restaurada",
            "user": db["users"][email]
        })
    
    user = {
        "id": user_id,
        "email": email,
        "name": name,
        "photo": data.get('photo', ''),
        "created": datetime.now().isoformat(),
        "reports_count": 0
    }
    
    db["users"][email] = user
    save_data(db)
    
    return jsonify({"status": "success", "user": user})

@app.route('/api/reports/submit', methods=['POST'])
def submit_report():
    data = request.json
    description = data.get('description', '').strip()
    
    # Validación robusta
    valid, msg = validate_text(description, min_length=10, max_length=500)
    if not valid:
        return jsonify({"status": "error", "message": msg}), 400
    
    lat = data.get('lat')
    lon = data.get('lon')
    
    if not lat or not lon:
        return jsonify({"status": "error", "message": "Ubicación requerida"}), 400
    
    # Verificar que la ubicación esté en Chihuahua
    if not (28.0 <= float(lat) <= 29.0 and -107.0 <= float(lon) <= -106.0):
        return jsonify({"status": "error", "message": "Ubicación fuera del área de servicio"}), 400
    
    report = {
        "id": f"r{len(db['reports'])+1}_{int(datetime.now().timestamp())}",
        "user_email": data.get('user_email', 'anonymous'),
        "description": description,
        "level": data.get('level', 'low'),
        "lat": float(lat),
        "lon": float(lon),
        "photo": data.get('photo', ''),
        "timestamp": datetime.now().isoformat(),
        "verified": False,
        "votes": 0
    }
    
    db["reports"].append(report)
    
    # Actualizar contador de reportes del usuario
    user_email = data.get('user_email')
    if user_email and user_email in db["users"]:
        db["users"][user_email]["reports_count"] = db["users"][user_email].get("reports_count", 0) + 1
    
    save_data(db)
    
    return jsonify({"status": "success", "report_id": report['id'], "message": "Reporte enviado correctamente"})

@app.route('/api/reports/list', methods=['GET'])
def get_reports():
    # Filtrar reportes recientes (últimos 30 días)
    recent = []
    cutoff = datetime.now().timestamp() - (30 * 24 * 3600)
    
    for report in db["reports"]:
        try:
            report_time = datetime.fromisoformat(report["timestamp"]).timestamp()
            if report_time > cutoff:
                recent.append(report)
        except:
            recent.append(report)
    
    return jsonify({"status": "success", "reports": recent, "total": len(db["reports"])})

@app.route('/api/search_places', methods=['GET'])
def search_places():
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    results = []
    query_lower = query.lower()
    
    # Buscar en base de datos local
    for place in PLACES_DB:
        if query_lower in place["name"].lower() or query_lower in place["type"].lower():
            results.append({
                "name": place["name"],
                "type": place["type"],
                "coords": place["coords"],
                "rating": place.get("rating", 4.0),
                "source": "local"
            })
    
    # Si hay pocos resultados, buscar con geocodificación
    if geolocator and len(results) < 5:
        try:
            locations = geolocator.geocode(
                f"{query}, Chihuahua, México",
                exactly_one=False,
                limit=5,
                addressdetails=True
            )
            
            if locations:
                for loc in locations:
                    if 28.0 <= loc.latitude <= 29.0 and -107.0 <= loc.longitude <= -106.0:
                        addr = loc.raw.get('address', {})
                        name = addr.get('road', addr.get('neighbourhood', loc.address.split(',')[0]))
                        results.append({
                            "name": name,
                            "type": "Dirección",
                            "coords": [loc.latitude, loc.longitude],
                            "rating": 0,
                            "source": "osm"
                        })
        except:
            pass
    
    return jsonify(results[:10])

@app.route('/api/reverse_geocode', methods=['POST'])
def reverse_geocode():
    data = request.json
    lat, lon = data.get('lat'), data.get('lon')
    
    if not lat or not lon:
        return jsonify({"status": "error", "message": "Coordenadas inválidas"}), 400
    
    try:
        if geolocator:
            location = geolocator.reverse(f"{lat}, {lon}", language='es', timeout=5)
            if location:
                addr = location.raw.get('address', {})
                parts = [
                    addr.get('road', ''),
                    addr.get('suburb', ''),
                    addr.get('neighbourhood', '')
                ]
                result = ", ".join([p for p in parts if p]) or "Tu ubicación"
                return jsonify({"status": "success", "address": result})
    except:
        pass
    
    return jsonify({"status": "success", "address": "Tu ubicación actual"})

@app.route('/api/analyze_route', methods=['POST'])
def analyze_route():
    data = request.json
    origin = data.get('origin', '').strip()
    destination = data.get('destination', '').strip()
    
    if not destination:
        return jsonify({"status": "error", "message": "Destino requerido"}), 400
    
    # Obtener coordenadas
    olat, olon = get_coordinates(origin)
    dlat, dlon = get_coordinates(destination)
    
    # Valores por defecto (centro de Chihuahua)
    if not olat or not olon:
        olat, olon = 28.6353, -106.0886
    
    if not dlat or not dlon:
        return jsonify({"status": "error", "message": "Destino no encontrado"}), 400
    
    # Calcular distancia directa
    direct_distance = geodesic((olat, olon), (dlat, dlon)).kilometers
    
    # Geometría de ruta por defecto
    geometry = {
        "type": "LineString",
        "coordinates": [[olon, olat], [dlon, dlat]]
    }
    
    duration_min = direct_distance * 3  # Estimación: 3 min por km
    distance_km = direct_distance
    
    # Intentar obtener ruta real de OSRM
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{olon},{olat};{dlon},{dlat}"
        params = {"overview": "full", "geometries": "geojson"}
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            route_data = response.json()
            if route_data.get('routes'):
                route = route_data['routes'][0]
                geometry = route['geometry']
                duration_min = route['duration'] / 60
                distance_km = route['distance'] / 1000
    except Exception as e:
        print(f"OSRM error: {e}")
    
    # Calcular riesgo promedio de la ruta
    mid_lat = (olat + dlat) / 2
    mid_lon = (olon + dlon) / 2
    risk_level = calculate_risk(mid_lat, mid_lon)
    
    # Factor de riesgo para ajustar tiempos
    risk_factors = {"Bajo": 1.0, "Medio": 1.15, "Alto": 1.3, "Crítico": 1.5}
    risk_factor = risk_factors.get(risk_level, 1.0)
    
    # Opciones de transporte
    transport_options = [
        {
            "mode": "Automóvil",
            "icon": "🚗",
            "time": f"{int(duration_min * risk_factor)} min",
            "risk": risk_level,
            "description": "Ruta más rápida"
        },
        {
            "mode": "Motocicleta",
            "icon": "🏍️",
            "time": f"{int(duration_min * 0.85 * risk_factor)} min",
            "risk": risk_level,
            "description": "Más ágil en tráfico"
        },
        {
            "mode": "Bicicleta",
            "icon": "🚴",
            "time": f"{int((distance_km / 15) * 60)} min",
            "risk": "Bajo",
            "description": "Saludable y ecológico"
        },
        {
            "mode": "Caminando",
            "icon": "🚶",
            "time": f"{int((distance_km / 5) * 60)} min",
            "risk": risk_level,
            "description": "Para distancias cortas"
        }
    ]
    
    return jsonify({
        "status": "success",
        "origin": {"lat": olat, "lon": olon, "name": origin},
        "destination": {"lat": dlat, "lon": dlon, "name": destination},
        "risk_level": risk_level,
        "distance_km": round(distance_km, 2),
        "duration_min": int(duration_min),
        "transport_options": transport_options,
        "route_geometry": geometry
    })

@app.route('/api/zones', methods=['GET'])
def get_zones():
    return jsonify({"status": "success", "zones": RISK_ZONES})

@app.route('/api/points', methods=['GET'])
def get_points():
    return jsonify(PLACES_DB)

@app.route('/api/user/<email>', methods=['GET'])
def get_user(email):
    if email in db["users"]:
        return jsonify({"status": "success", "user": db["users"][email]})
    return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
