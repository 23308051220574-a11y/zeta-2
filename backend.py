
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import re
import hashlib
import base64
from PIL import Image
from io import BytesIO
import sqlite3

app = Flask(__name__)
CORS(app, resources={r"/api/*": {
    "origins": "*", 
    "methods": ["GET", "POST", "PUT", "DELETE"], 
    "allow_headers": ["Content-Type", "Authorization"]
}})

# Configuración
NOMINATIM_USER_AGENT = "ZetaPro_v1.0_Navigation"
DB_FILE = 'zeta_pro.db'
IMAGES_DIR = 'uploads/images'
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Crear directorio de imágenes
os.makedirs(IMAGES_DIR, exist_ok=True)

try:
    geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT, timeout=10)
except:
    geolocator = None

# ==================== BASE DE DATOS SQL ====================
def init_database():
    """Inicializar base de datos SQLite profesional"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            photo TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            reports_count INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT 0,
            rating REAL DEFAULT 5.0
        )
    ''')
    
    # Tabla de reportes con sistema de verificación
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            address TEXT,
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verified BOOLEAN DEFAULT 0,
            verified_by TEXT,
            verified_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            news_source TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabla de lugares (restaurantes, museos, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            address TEXT,
            phone TEXT,
            website TEXT,
            description TEXT,
            images TEXT,
            rating REAL DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            price_level INTEGER DEFAULT 2,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de reseñas de lugares
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            place_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            helpful_count INTEGER DEFAULT 0,
            FOREIGN KEY (place_id) REFERENCES places(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabla de zonas de riesgo dinámicas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            radius_km REAL NOT NULL,
            level TEXT NOT NULL,
            type TEXT NOT NULL,
            color TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT,
            description TEXT
        )
    ''')
    
    # Tabla de desastres naturales
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS natural_disasters (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            radius_km REAL NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            source TEXT
        )
    ''')
    
    # Tabla de votos en reportes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS report_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            vote_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(report_id, user_id),
            FOREIGN KEY (report_id) REFERENCES reports(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar DB al arrancar
init_database()

# ==================== DATOS INICIALES ====================
def seed_initial_data():
    """Poblar datos iniciales de restaurantes y museos de Chihuahua"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Verificar si ya hay datos
    cursor.execute("SELECT COUNT(*) FROM places")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    initial_places = [
        # MUSEOS Y CULTURA
        {
            "id": "p_catedral_001",
            "name": "Catedral Metropolitana de Chihuahua",
            "type": "Museo/Cultura",
            "lat": 28.6358,
            "lon": -106.0773,
            "address": "Plaza de Armas, Centro",
            "phone": "+52 614 410 3858",
            "description": "Catedral barroca del siglo XVIII, principal templo católico de Chihuahua",
            "rating": 4.8,
            "total_reviews": 1247
        },
        {
            "id": "p_quinta_gameros_002",
            "name": "Quinta Gameros - Museo Regional",
            "type": "Museo/Cultura",
            "lat": 28.6400,
            "lon": -106.0850,
            "address": "Paseo Bolívar 401, Centro",
            "phone": "+52 614 416 6684",
            "description": "Mansión art nouveau convertida en museo, joya arquitectónica de Chihuahua",
            "rating": 4.7,
            "total_reviews": 892
        },
        {
            "id": "p_casa_villa_003",
            "name": "Museo Histórico de la Revolución - Casa Villa",
            "type": "Museo/Cultura",
            "lat": 28.6320,
            "lon": -106.0910,
            "address": "Calle 10a 3010, Centro",
            "phone": "+52 614 416 2958",
            "description": "Casa donde vivió Pancho Villa, convertida en museo sobre la Revolución Mexicana",
            "rating": 4.6,
            "total_reviews": 654
        },
        {
            "id": "p_museo_mamut_004",
            "name": "Museo del Mamut",
            "type": "Museo/Cultura",
            "lat": 28.6280,
            "lon": -106.0795,
            "description": "Museo paleontológico con restos de mamuts encontrados en Chihuahua",
            "rating": 4.5,
            "total_reviews": 423
        },
        
        # RESTAURANTES RECONOCIDOS
        {
            "id": "p_la_casona_005",
            "name": "La Casona",
            "type": "Restaurante",
            "lat": 28.6350,
            "lon": -106.0880,
            "address": "Av. Juárez 3300, Centro",
            "phone": "+52 614 410 2828",
            "description": "Restaurante de cocina tradicional mexicana en una casona histórica",
            "rating": 4.6,
            "total_reviews": 1891,
            "price_level": 3
        },
        {
            "id": "p_la_parrilla_006",
            "name": "La Parrilla Suiza",
            "type": "Restaurante",
            "lat": 28.6420,
            "lon": -106.0920,
            "address": "Av. Independencia 1300",
            "phone": "+52 614 415 7777",
            "description": "Especialidad en cortes de carne y parrilladas",
            "rating": 4.5,
            "total_reviews": 2156,
            "price_level": 3
        },
        {
            "id": "p_vips_007",
            "name": "VIPS Chihuahua Centro",
            "type": "Restaurante",
            "lat": 28.6365,
            "lon": -106.0865,
            "description": "Restaurante familiar con variedad de platillos mexicanos e internacionales",
            "rating": 4.3,
            "total_reviews": 987,
            "price_level": 2
        },
        {
            "id": "p_rincon_mexicano_008",
            "name": "Rincón Mexicano",
            "type": "Restaurante",
            "lat": 28.6340,
            "lon": -106.0895,
            "description": "Comida tradicional mexicana y regional",
            "rating": 4.4,
            "total_reviews": 756,
            "price_level": 2
        },
        {
            "id": "p_dorichangos_009",
            "name": "Dorichangos",
            "type": "Restaurante",
            "lat": 28.6450,
            "lon": -106.0950,
            "description": "Restaurante de comida rápida local, famoso por sus burritos",
            "rating": 4.2,
            "total_reviews": 1234,
            "price_level": 1
        },
        
        # CENTROS COMERCIALES Y RECREACIÓN
        {
            "id": "p_fashion_mall_010",
            "name": "Fashion Mall",
            "type": "Centro Comercial",
            "lat": 28.6580,
            "lon": -106.1170,
            "address": "Blvd. Teófilo Borunda 8401",
            "description": "Centro comercial moderno con tiendas departamentales y restaurantes",
            "rating": 4.4,
            "total_reviews": 3421
        },
        {
            "id": "p_plaza_sol_011",
            "name": "Plaza del Sol",
            "type": "Centro Comercial",
            "lat": 28.6250,
            "lon": -106.0750,
            "description": "Centro comercial con variedad de tiendas y zona de comidas",
            "rating": 4.3,
            "total_reviews": 2134
        },
        {
            "id": "p_parque_rejon_012",
            "name": "Parque El Rejón",
            "type": "Recreación",
            "lat": 28.6150,
            "lon": -106.1150,
            "description": "Parque público con áreas verdes, juegos infantiles y pista para correr",
            "rating": 4.4,
            "total_reviews": 892
        },
        {
            "id": "p_parque_lerdo_013",
            "name": "Parque Lerdo",
            "type": "Recreación",
            "lat": 28.6330,
            "lon": -106.0800,
            "description": "Parque histórico en el centro de la ciudad",
            "rating": 4.5,
            "total_reviews": 1045
        }
    ]
    
    for place in initial_places:
        cursor.execute('''
            INSERT OR IGNORE INTO places 
            (id, name, type, lat, lon, address, phone, description, rating, total_reviews, price_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            place['id'], place['name'], place['type'], place['lat'], place['lon'],
            place.get('address', ''), place.get('phone', ''), place.get('description', ''),
            place.get('rating', 0), place.get('total_reviews', 0), place.get('price_level', 2)
        ))
    
    conn.commit()
    conn.close()

# Poblar datos iniciales
seed_initial_data()

# ==================== UTILIDADES ====================
def generate_id(prefix=''):
    """Generar ID único"""
    timestamp = str(int(datetime.now().timestamp() * 1000))
    return f"{prefix}{timestamp}_{hashlib.md5(os.urandom(16)).hexdigest()[:8]}"

def validate_email(email):
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_text(text, min_length=10, max_length=1000):
    """Validar texto con filtros anti-spam mejorados"""
    if not text or len(text.strip()) < min_length:
        return False, f"El texto debe tener al menos {min_length} caracteres"
    
    if len(text) > max_length:
        return False, f"El texto no debe exceder {max_length} caracteres"
    
    # Patrones de spam mejorados
    spam_patterns = [
        r'https?://',
        r'www\.',
        r'\b(viagra|casino|lottery|prize|winner|congratulations)\b',
        r'[A-Z]{15,}',
        r'(.)\1{7,}',
        r'\$\$\$',
        r'!!!{5,}',
        r'\b(click|here|now)\b.*\b(buy|win|free)\b'
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Contenido sospechoso detectado"
    
    words = text.split()
    if len(words) < 3:
        return False, "Descripción demasiado corta"
    
    return True, "OK"

def compress_image(base64_string, max_size=(800, 800), quality=85):
    """Comprimir imagen base64"""
    try:
        if not base64_string or not base64_string.startswith('data:image'):
            return base64_string
        
        # Extraer datos de la imagen
        header, data = base64_string.split(',', 1)
        image_data = base64.b64decode(data)
        
        # Abrir y comprimir
        img = Image.open(BytesIO(image_data))
        
        # Convertir a RGB si es necesario
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Redimensionar manteniendo aspecto
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Guardar comprimida
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_data = output.getvalue()
        
        # Convertir de vuelta a base64
        compressed_base64 = base64.b64encode(compressed_data).decode()
        return f"data:image/jpeg;base64,{compressed_base64}"
    
    except Exception as e:
        print(f"Error comprimiendo imagen: {e}")
        return base64_string

def get_coordinates(location_name):
    """Geocodificación mejorada"""
    if not location_name:
        return None, None
    
    # Método 1: Coordenadas directas
    if ',' in location_name and location_name.count(',') == 1:
        try:
            parts = location_name.split(',')
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            if 28.0 <= lat <= 29.0 and -107.0 <= lon <= -106.0:
                return lat, lon
        except:
            pass
    
    # Método 2: Buscar en base de datos local
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    location_lower = location_name.lower()
    cursor.execute('''
        SELECT lat, lon FROM places 
        WHERE LOWER(name) LIKE ? OR LOWER(address) LIKE ?
        LIMIT 1
    ''', (f'%{location_lower}%', f'%{location_lower}%'))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0], result[1]
    
    # Método 3: Nominatim
    if geolocator:
        try:
            query = f"{location_name}, Chihuahua, Chihuahua, México"
            location = geolocator.geocode(query, timeout=10)
            if location:
                if 28.0 <= location.latitude <= 29.0 and -107.0 <= location.longitude <= -106.0:
                    return location.latitude, location.longitude
        except Exception as e:
            print(f"Geocoding error: {e}")
    
    return None, None

def calculate_risk(lat, lon):
    """Calcular nivel de riesgo basado en reportes y zonas"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    point = (lat, lon)
    max_risk = "Bajo"
    risk_scores = {"Crítico": 4, "Alto": 3, "Medio": 2, "Bajo": 1}
    
    # Verificar zonas de riesgo activas
    cursor.execute('''
        SELECT lat, lon, radius_km, level 
        FROM risk_zones 
        WHERE active = 1 AND (expires_at IS NULL OR expires_at > ?)
    ''', (datetime.now(),))
    
    for zone_lat, zone_lon, radius, level in cursor.fetchall():
        dist = geodesic(point, (zone_lat, zone_lon)).kilometers
        if dist <= radius:
            level_spanish = {"critical": "Crítico", "high": "Alto", "medium": "Medio", "low": "Bajo"}
            zone_level = level_spanish.get(level, "Bajo")
            if risk_scores[zone_level] > risk_scores[max_risk]:
                max_risk = zone_level
    
    # Verificar reportes recientes cercanos
    one_week_ago = datetime.now() - timedelta(days=7)
    cursor.execute('''
        SELECT lat, lon, severity FROM reports 
        WHERE verified = 1 AND created_at > ? AND status = 'active'
    ''', (one_week_ago,))
    
    nearby_reports = 0
    for report_lat, report_lon, severity in cursor.fetchall():
        dist = geodesic(point, (report_lat, report_lon)).kilometers
        if dist <= 0.5:  # 500 metros
            nearby_reports += 1
            if severity == 'high' and risk_scores["Alto"] > risk_scores[max_risk]:
                max_risk = "Alto"
    
    conn.close()
    
    # Ajustar por densidad de reportes
    if nearby_reports >= 5 and max_risk == "Bajo":
        max_risk = "Medio"
    
    return max_risk

# ==================== ENDPOINTS DE AUTENTICACIÓN ====================
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Registro de usuario profesional"""
    try:
        data = request.json
        email = data.get('email', '').lower().strip()
        name = data.get('name', '').strip()
        photo = data.get('photo', '')
        phone = data.get('phone', '').strip()
        
        # Validaciones
        if not email or not validate_email(email):
            return jsonify({"status": "error", "message": "Email inválido"}), 400
        
        if not name or len(name) < 2:
            return jsonify({"status": "error", "message": "Nombre inválido"}), 400
        
        # Comprimir foto si existe
        if photo:
            photo = compress_image(photo, max_size=(400, 400), quality=80)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute("SELECT id, name, email, photo, reports_count, rating FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        
        if existing:
            user = {
                "id": existing[0],
                "name": existing[1],
                "email": existing[2],
                "photo": existing[3],
                "reports_count": existing[4],
                "rating": existing[5]
            }
            conn.close()
            return jsonify({
                "status": "success",
                "message": "Sesión restaurada",
                "user": user
            })
        
        # Crear nuevo usuario
        user_id = generate_id('user_')
        cursor.execute('''
            INSERT INTO users (id, email, name, photo, phone, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, email, name, photo, phone, datetime.now()))
        
        conn.commit()
        
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "photo": photo,
            "phone": phone,
            "reports_count": 0,
            "rating": 5.0,
            "verified": False
        }
        
        conn.close()
        
        return jsonify({"status": "success", "user": user})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== ENDPOINTS DE REPORTES ====================
@app.route('/api/reports/submit', methods=['POST'])
def submit_report():
    """Enviar reporte con sistema de verificación mejorado"""
    try:
        data = request.json
        user_id = data.get('user_id')
        description = data.get('description', '').strip()
        category = data.get('category', 'general')
        severity = data.get('severity', 'low')
        lat = data.get('lat')
        lon = data.get('lon')
        images = data.get('images', [])
        
        # Validaciones
        valid, msg = validate_text(description, min_length=15, max_length=1000)
        if not valid:
            return jsonify({"status": "error", "message": msg}), 400
        
        if not lat or not lon:
            return jsonify({"status": "error", "message": "Ubicación requerida"}), 400
        
        if not (28.0 <= float(lat) <= 29.0 and -107.0 <= float(lon) <= -106.0):
            return jsonify({"status": "error", "message": "Ubicación fuera del área de servicio"}), 400
        
        # Comprimir imágenes
        compressed_images = []
        for img in images[:3]:  # Máximo 3 imágenes
            compressed = compress_image(img, max_size=(1200, 1200), quality=85)
            compressed_images.append(compressed)
        
        # Geocodificación inversa para dirección
        address = "Ubicación reportada"
        if geolocator:
            try:
                location = geolocator.reverse(f"{lat}, {lon}", language='es', timeout=5)
                if location:
                    addr = location.raw.get('address', {})
                    parts = [addr.get('road', ''), addr.get('suburb', '')]
                    address = ", ".join([p for p in parts if p]) or address
            except:
                pass
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Crear reporte
        report_id = generate_id('report_')
        cursor.execute('''
            INSERT INTO reports 
            (id, user_id, description, category, severity, lat, lon, address, images, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (report_id, user_id, description, category, severity, 
              float(lat), float(lon), address, json.dumps(compressed_images)))
        
        # Actualizar contador de reportes del usuario
        if user_id:
            cursor.execute('''
                UPDATE users SET reports_count = reports_count + 1 
                WHERE id = ?
            ''', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Auto-verificación básica con IA (simulada)
        verification_score = verify_report_with_ai(description, category, severity)
        
        return jsonify({
            "status": "success",
            "report_id": report_id,
            "message": "Reporte enviado. Será verificado en breve.",
            "verification_score": verification_score,
            "requires_review": verification_score < 0.7
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def verify_report_with_ai(description, category, severity):
    """
    Verificación automática con IA (simulada)
    En producción: integrar con GPT-4, Claude API o modelo local
    """
    score = 0.5
    
    # Factores que incrementan confianza
    keywords_credible = [
        'policía', 'patrulla', 'ambulancia', 'bomberos', 
        'accidente', 'choque', 'incendio', 'robo', 'asalto',
        'inundación', 'bloqueo', 'manifestación'
    ]
    
    # Factores que reducen confianza
    keywords_suspicious = [
        'creo', 'tal vez', 'parece', 'supongo', 'dicen que',
        'me contaron', 'escuché', 'alguien dijo'
    ]
    
    desc_lower = description.lower()
    
    for keyword in keywords_credible:
        if keyword in desc_lower:
            score += 0.1
    
    for keyword in keywords_suspicious:
        if keyword in desc_lower:
            score -= 0.15
    
    # Longitud detallada aumenta credibilidad
    if len(description) > 100:
        score += 0.1
    
    # Severidad consistente
    severe_keywords = ['peligro', 'grave', 'urgente', 'rápido']
    if severity == 'high' and any(k in desc_lower for k in severe_keywords):
        score += 0.15
    
    return min(1.0, max(0.0, score))

@app.route('/api/reports/verify/<report_id>', methods=['POST'])
def verify_report(report_id):
    """Verificar reporte manualmente (admin)"""
    try:
        data = request.json
        verified_by = data.get('verified_by')
        news_source = data.get('news_source', '')
        approved = data.get('approved', True)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if approved:
            cursor.execute('''
                UPDATE reports 
                SET verified = 1, verified_by = ?, verified_at = ?, 
                    news_source = ?, status = 'active'
                WHERE id = ?
            ''', (verified_by, datetime.now(), news_source, report_id))
            
            # Crear zona de riesgo temporal si es necesario
            cursor.execute('''
                SELECT lat, lon, severity, description FROM reports WHERE id = ?
            ''', (report_id,))
            
            report = cursor.fetchone()
            if report and report[2] in ['high', 'medium']:
                zone_id = generate_id('zone_')
                expires = datetime.now() + timedelta(hours=24)
                
                cursor.execute('''
                    INSERT INTO risk_zones 
                    (id, name, lat, lon, radius_km, level, type, color, expires_at, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (zone_id, report[3][:50], report[0], report[1], 0.5, 
                      report[2], 'incident', '#ef4444', expires, f'report_{report_id}'))
        else:
            cursor.execute('''
                UPDATE reports SET status = 'rejected' WHERE id = ?
            ''', (report_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "Reporte verificado" if approved else "Reporte rechazado"
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reports/list', methods=['GET'])
def get_reports():
    """Obtener reportes con filtros"""
    try:
        verified_only = request.args.get('verified', 'true').lower() == 'true'
        category = request.args.get('category', None)
        days = int(request.args.get('days', 7))
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        query = '''
            SELECT r.id, r.user_id, r.description, r.category, r.severity,
                   r.lat, r.lon, r.address, r.images, r.created_at,
                   r.verified, r.status, r.upvotes, r.downvotes,
                   u.name as user_name, u.photo as user_photo
            FROM reports r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.created_at > ?
        '''
        
        params = [cutoff]
        
        if verified_only:
            query += " AND r.verified = 1"
        
        if category:
            query += " AND r.category = ?"
            params.append(category)
        
        query += " ORDER BY r.created_at DESC LIMIT 100"
        
        cursor.execute(query, params)
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                "id": row[0],
                "user_id": row[1],
                "description": row[2],
                "category": row[3],
                "severity": row[4],
                "lat": row[5],
                "lon": row[6],
                "address": row[7],
                "images": json.loads(row[8]) if row[8] else [],
                "created_at": row[9],
                "verified": bool(row[10]),
                "status": row[11],
                "upvotes": row[12],
                "downvotes": row[13],
                "user_name": row[14],
                "user_photo": row[15]
            })
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "reports": reports,
            "total": len(reports)
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reports/vote/<report_id>', methods=['POST'])
def vote_report(report_id):
    """Votar por un reporte (upvote/downvote)"""
    try:
        data = request.json
        user_id = data.get('user_id')
        vote_type = data.get('vote_type')  # 'up' o 'down'
        
        if vote_type not in ['up', 'down']:
            return jsonify({"status": "error", "message": "Tipo de voto inválido"}), 400
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si ya votó
        cursor.execute('''
            SELECT vote_type FROM report_votes 
            WHERE report_id = ? AND user_id = ?
        ''', (report_id, user_id))
        
        existing_vote = cursor.fetchone()
        
        if existing_vote:
            # Cambiar voto
            old_vote = existing_vote[0]
            cursor.execute('''
                UPDATE report_votes SET vote_type = ? 
                WHERE report_id = ? AND user_id = ?
            ''', (vote_type, report_id, user_id))
            
            # Actualizar contadores
            if old_vote == 'up':
                cursor.execute('UPDATE reports SET upvotes = upvotes - 1 WHERE id = ?', (report_id,))
            else:
                cursor.execute('UPDATE reports SET downvotes = downvotes - 1 WHERE id = ?', (report_id,))
        else:
            # Nuevo voto
            cursor.execute('''
                INSERT INTO report_votes (report_id, user_id, vote_type)
                VALUES (?, ?, ?)
            ''', (report_id, user_id, vote_type))
        
        # Incrementar contador correspondiente
        if vote_type == 'up':
            cursor.execute('UPDATE reports SET upvotes = upvotes + 1 WHERE id = ?', (report_id,))
        else:
            cursor.execute('UPDATE reports SET downvotes = downvotes + 1 WHERE id = ?', (report_id,))
        
        conn.commit()
        
        # Obtener contadores actualizados
        cursor.execute('SELECT upvotes, downvotes FROM reports WHERE id = ?', (report_id,))
        upvotes, downvotes = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "upvotes": upvotes,
            "downvotes": downvotes
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== ENDPOINTS DE LUGARES ====================
@app.route('/api/places/search', methods=['GET'])
def search_places():
    """Buscar lugares (restaurantes, museos, etc.)"""
    try:
        query = request.args.get('q', '').strip()
        place_type = request.args.get('type', None)
        lat = request.args.get('lat', None)
        lon = request.args.get('lon', None)
        radius = float(request.args.get('radius', 10))  # km
        
        if len(query) < 2:
            return jsonify([])
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        sql = '''
            SELECT id, name, type, lat, lon, address, phone, 
                   description, rating, total_reviews, price_level
            FROM places
            WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(address) LIKE ?
        '''
        
        params = [f'%{query.lower()}%', f'%{query.lower()}%', f'%{query.lower()}%']
        
        if place_type:
            sql += " AND LOWER(type) LIKE ?"
            params.append(f'%{place_type.lower()}%')
        
        sql += " ORDER BY rating DESC, total_reviews DESC LIMIT 20"
        
        cursor.execute(sql, params)
        
        places = []
        for row in cursor.fetchall():
            place = {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "coords": [row[3], row[4]],
                "lat": row[3],
                "lon": row[4],
                "address": row[5],
                "phone": row[6],
                "description": row[7],
                "rating": row[8],
                "total_reviews": row[9],
                "price_level": row[10],
                "source": "local"
            }
            
            # Si hay coordenadas, calcular distancia
            if lat and lon:
                try:
                    dist = geodesic((float(lat), float(lon)), (row[3], row[4])).kilometers
                    if dist <= radius:
                        place['distance_km'] = round(dist, 2)
                        places.append(place)
                except:
                    places.append(place)
            else:
                places.append(place)
        
        conn.close()
        
        # Si hay pocos resultados, buscar con Nominatim
        if geolocator and len(places) < 5:
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
                            places.append({
                                "id": f"osm_{loc.osm_id}",
                                "name": name,
                                "type": "Dirección",
                                "coords": [loc.latitude, loc.longitude],
                                "lat": loc.latitude,
                                "lon": loc.longitude,
                                "address": loc.address,
                                "rating": 0,
                                "total_reviews": 0,
                                "source": "osm"
                            })
            except:
                pass
        
        return jsonify(places[:15])
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/places/<place_id>', methods=['GET'])
def get_place_details(place_id):
    """Obtener detalles completos de un lugar"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, type, lat, lon, address, phone, website,
                   description, rating, total_reviews, price_level
            FROM places WHERE id = ?
        ''', (place_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"status": "error", "message": "Lugar no encontrado"}), 404
        
        place = {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "coords": [row[3], row[4]],
            "address": row[5],
            "phone": row[6],
            "website": row[7],
            "description": row[8],
            "rating": row[9],
            "total_reviews": row[10],
            "price_level": row[11]
        }
        
        # Obtener reseñas
        cursor.execute('''
            SELECT r.id, r.rating, r.comment, r.images, r.created_at, r.helpful_count,
                   u.name, u.photo
            FROM reviews r
            LEFT JOIN users u ON r.user_id = u.id
            WHERE r.place_id = ?
            ORDER BY r.created_at DESC
            LIMIT 50
        ''', (place_id,))
        
        reviews = []
        for rev_row in cursor.fetchall():
            reviews.append({
                "id": rev_row[0],
                "rating": rev_row[1],
                "comment": rev_row[2],
                "images": json.loads(rev_row[3]) if rev_row[3] else [],
                "created_at": rev_row[4],
                "helpful_count": rev_row[5],
                "user_name": rev_row[6],
                "user_photo": rev_row[7]
            })
        
        place['reviews'] = reviews
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "place": place
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/places/<place_id>/reviews', methods=['POST'])
def add_review():
    """Agregar reseña a un lugar"""
    try:
        place_id = request.view_args['place_id']
        data = request.json
        user_id = data.get('user_id')
        rating = data.get('rating')
        comment = data.get('comment', '').strip()
        images = data.get('images', [])
        
        # Validaciones
        if not rating or not (1 <= int(rating) <= 5):
            return jsonify({"status": "error", "message": "Calificación inválida"}), 400
        
        if comment:
            valid, msg = validate_text(comment, min_length=10, max_length=500)
            if not valid:
                return jsonify({"status": "error", "message": msg}), 400
        
        # Comprimir imágenes
        compressed_images = []
        for img in images[:3]:
            compressed = compress_image(img, max_size=(1200, 1200), quality=85)
            compressed_images.append(compressed)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar que el lugar existe
        cursor.execute("SELECT id FROM places WHERE id = ?", (place_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"status": "error", "message": "Lugar no encontrado"}), 404
        
        # Crear reseña
        review_id = generate_id('review_')
        cursor.execute('''
            INSERT INTO reviews (id, place_id, user_id, rating, comment, images)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (review_id, place_id, user_id, int(rating), comment, json.dumps(compressed_images)))
        
        # Actualizar rating del lugar
        cursor.execute('''
            SELECT AVG(rating), COUNT(*) FROM reviews WHERE place_id = ?
        ''', (place_id,))
        avg_rating, total_reviews = cursor.fetchone()
        
        cursor.execute('''
            UPDATE places SET rating = ?, total_reviews = ? WHERE id = ?
        ''', (round(avg_rating, 1), total_reviews, place_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "review_id": review_id,
            "message": "Reseña publicada exitosamente",
            "new_rating": round(avg_rating, 1),
            "total_reviews": total_reviews
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== DESASTRES NATURALES ====================
@app.route('/api/disasters/list', methods=['GET'])
def get_disasters():
    """Obtener desastres naturales activos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, type, lat, lon, radius_km, severity, description, created_at, expires_at
            FROM natural_disasters
            WHERE active = 1 AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY created_at DESC
        ''', (datetime.now(),))
        
        disasters = []
        for row in cursor.fetchall():
            disasters.append({
                "id": row[0],
                "type": row[1],
                "lat": row[2],
                "lon": row[3],
                "radius_km": row[4],
                "severity": row[5],
                "description": row[6],
                "created_at": row[7],
                "expires_at": row[8]
            })
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "disasters": disasters
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/disasters/report', methods=['POST'])
def report_disaster():
    """Reportar desastre natural"""
    try:
        data = request.json
        disaster_type = data.get('type')  # flood, fire, earthquake, etc.
        lat = data.get('lat')
        lon = data.get('lon')
        severity = data.get('severity', 'medium')
        description = data.get('description', '')
        
        valid_types = ['flood', 'fire', 'earthquake', 'storm', 'landslide']
        if disaster_type not in valid_types:
            return jsonify({"status": "error", "message": "Tipo de desastre inválido"}), 400
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        disaster_id = generate_id('disaster_')
        expires = datetime.now() + timedelta(hours=48)
        
        cursor.execute('''
            INSERT INTO natural_disasters 
            (id, type, lat, lon, radius_km, severity, description, expires_at, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'user_report')
        ''', (disaster_id, disaster_type, float(lat), float(lon), 
              2.0, severity, description, expires))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "disaster_id": disaster_id,
            "message": "Desastre natural reportado. Será verificado."
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== RUTAS AVANZADAS ====================
@app.route('/api/routes/calculate', methods=['POST'])
def calculate_route():
    """Calcular ruta óptima evitando zonas de riesgo"""
    try:
        data = request.json
        origin = data.get('origin', '').strip()
        destination = data.get('destination', '').strip()
        avoid_risks = data.get('avoid_risks', True)
        
        if not destination:
            return jsonify({"status": "error", "message": "Destino requerido"}), 400
        
        # Obtener coordenadas
        olat, olon = get_coordinates(origin)
        dlat, dlon = get_coordinates(destination)
        
        if not olat or not olon:
            olat, olon = 28.6353, -106.0886  # Centro por defecto
        
        if not dlat or not dlon:
            return jsonify({"status": "error", "message": "Destino no encontrado"}), 400
        
        # Calcular ruta con OSRM
        direct_distance = geodesic((olat, olon), (dlat, dlon)).kilometers
        geometry = {"type": "LineString", "coordinates": [[olon, olat], [dlon, dlat]]}
        duration_min = direct_distance * 3
        distance_km = direct_distance
        
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{olon},{olat};{dlon},{dlat}"
            params = {"overview": "full", "geometries": "geojson", "alternatives": "true"}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                route_data = response.json()
                if route_data.get('routes'):
                    best_route = None
                    min_risk_score = float('inf')
                    
                    # Evaluar cada ruta alternativa
                    for route in route_data['routes'][:3]:
                        geometry_coords = route['geometry']['coordinates']
                        risk_score = 0
                        
                        if avoid_risks:
                            # Calcular riesgo de la ruta
                            for coord in geometry_coords[::10]:  # Muestrear cada 10 puntos
                                risk_level = calculate_risk(coord[1], coord[0])
                                risk_scores_map = {"Crítico": 4, "Alto": 3, "Medio": 2, "Bajo": 1}
                                risk_score += risk_scores_map.get(risk_level, 1)
                        
                        if risk_score < min_risk_score:
                            min_risk_score = risk_score
                            best_route = route
                    
                    if best_route:
                        geometry = best_route['geometry']
                        duration_min = best_route['duration'] / 60
                        distance_km = best_route['distance'] / 1000
        
        except Exception as e:
            print(f"OSRM error: {e}")
        
        # Calcular riesgo promedio
        mid_lat, mid_lon = (olat + dlat) / 2, (olon + dlon) / 2
        risk_level = calculate_risk(mid_lat, mid_lon)
        
        # Factor de ajuste por riesgo
        risk_factors = {"Bajo": 1.0, "Medio": 1.2, "Alto": 1.4, "Crítico": 1.6}
        risk_factor = risk_factors.get(risk_level, 1.0)
        
        # Opciones de transporte
        transport_options = [
            {
                "mode": "Automóvil",
                "icon": "🚗",
                "time": f"{int(duration_min * risk_factor)} min",
                "distance": f"{round(distance_km, 1)} km",
                "risk": risk_level,
                "description": "Ruta más rápida",
                "eco_friendly": False
            },
            {
                "mode": "Motocicleta",
                "icon": "🏍️",
                "time": f"{int(duration_min * 0.85 * risk_factor)} min",
                "distance": f"{round(distance_km, 1)} km",
                "risk": risk_level,
                "description": "Ágil en tráfico",
                "eco_friendly": False
            },
            {
                "mode": "Bicicleta",
                "icon": "🚴",
                "time": f"{int((distance_km / 15) * 60)} min",
                "distance": f"{round(distance_km, 1)} km",
                "risk": "Bajo",
                "description": "Saludable y ecológico",
                "eco_friendly": True
            },
            {
                "mode": "Caminando",
                "icon": "🚶",
                "time": f"{int((distance_km / 5) * 60)} min",
                "distance": f"{round(distance_km, 1)} km",
                "risk": risk_level,
                "description": "Para distancias cortas",
                "eco_friendly": True
            }
        ]
        
        # Advertencias de ruta
        warnings = []
        if risk_level in ["Alto", "Crítico"]:
            warnings.append({
                "type": "risk",
                "message": f"Esta ruta pasa por una zona de riesgo {risk_level.lower()}",
                "severity": "high"
            })
        
        # Verificar desastres naturales en la ruta
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT type, description FROM natural_disasters 
            WHERE active = 1 AND expires_at > ?
        ''', (datetime.now(),))
        
        for disaster_type, desc in cursor.fetchall():
            warnings.append({
                "type": "disaster",
                "message": f"⚠️ {disaster_type.title()}: {desc}",
                "severity": "critical"
            })
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "origin": {"lat": olat, "lon": olon, "name": origin},
            "destination": {"lat": dlat, "lon": dlon, "name": destination},
            "risk_level": risk_level,
            "distance_km": round(distance_km, 2),
            "duration_min": int(duration_min),
            "transport_options": transport_options,
            "route_geometry": geometry,
            "warnings": warnings,
            "avoid_risks": avoid_risks
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== GEOCODIFICACIÓN ====================
@app.route('/api/geocode/reverse', methods=['POST'])
def reverse_geocode():
    """Geocodificación inversa mejorada"""
    try:
        data = request.json
        lat, lon = data.get('lat'), data.get('lon')
        
        if not lat or not lon:
            return jsonify({"status": "error", "message": "Coordenadas inválidas"}), 400
        
        address = "Ubicación desconocida"
        
        if geolocator:
            try:
                location = geolocator.reverse(f"{lat}, {lon}", language='es', timeout=10)
                if location:
                    addr = location.raw.get('address', {})
                    parts = [
                        addr.get('road', ''),
                        addr.get('suburb', ''),
                        addr.get('neighbourhood', ''),
                        addr.get('city', 'Chihuahua')
                    ]
                    address = ", ".join([p for p in parts if p]) or location.address
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
        
        return jsonify({
            "status": "success",
            "address": address,
            "lat": lat,
            "lon": lon
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== ENDPOINTS DE ZONAS ====================
@app.route('/api/zones/risk', methods=['GET'])
def get_risk_zones():
    """Obtener zonas de riesgo activas"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, lat, lon, radius_km, level, type, color, description
            FROM risk_zones
            WHERE active = 1 AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY level DESC
        ''', (datetime.now(),))
        
        zones = []
        for row in cursor.fetchall():
            zones.append({
                "id": row[0],
                "name": row[1],
                "lat": row[2],
                "lon": row[3],
                "radius_km": row[4],
                "level": row[5],
                "type": row[6],
                "color": row[7],
                "description": row[8]
            })
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "zones": zones
        })
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== HEALTH CHECK ====================
@app.route('/api/health', methods=['GET'])
def health():
    """Estado del sistema"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reports WHERE verified = 1")
        verified_reports = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM places")
        total_places = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "stats": {
                "users": total_users,
                "verified_reports": verified_reports,
                "places": total_places,
                "reviews": total_reviews
            },
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ==================== EJECUTAR APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print(f"""
    ╔══════════════════════════════════════╗
    ║   ZETA PRO - Backend v1.0            ║
    ║   Sistema de Navegación Segura       ║
    ║   Puerto: {port}                         ║
    ╚══════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=False)
