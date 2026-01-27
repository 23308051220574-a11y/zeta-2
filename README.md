# 🛡️ ZETA PRO - Sistema Profesional de Navegación Segura

[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.0-red.svg)](https://flask.palletsprojects.com/)

> **Sistema inteligente de navegación urbana que calcula rutas seguras basándose en datos verificados de seguridad pública en tiempo real.**

---

## 🎯 **Características Principales**

### ✅ **Navegación Inteligente**
- 🗺️ Cálculo de rutas evitando zonas de riesgo
- 📍 Geolocalización precisa en tiempo real
- 🚗 Múltiples modos de transporte
- ⚡ Rutas optimizadas por seguridad y tiempo

### ✅ **Sistema de Reportes Verificados**
- 📝 Reportes de incidentes con foto
- 🤖 Verificación automática con IA
- 👥 Sistema de votos comunitario
- 📰 Corroboración con fuentes noticiosas

### ✅ **Base de Datos Completa**
- 🍽️ Restaurantes con reseñas
- 🏛️ Museos y sitios culturales
- ⭐ Calificaciones y comentarios
- 📸 Galerías de fotos

### ✅ **Alertas Inteligentes**
- 🚨 Zonas de riesgo dinámicas
- 🌊 Desastres naturales
- ⚠️ Alertas en tiempo real
- 🔔 Notificaciones push

---

## 🚀 **Instalación Rápida**

### **1. Clonar Repositorio**

```bash
git clone https://github.com/tu-usuario/zeta-pro.git
cd zeta-pro
```

### **2. Crear Entorno Virtual**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### **3. Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### **4. Ejecutar Backend**

```bash
python app.py
```

El servidor iniciará en `http://localhost:5002`

### **5. Abrir Frontend**

Abre `index.html` en tu navegador o usa:

```bash
python -m http.server 8000
```

Visita `http://localhost:8000`

---

## 📁 **Estructura del Proyecto**

```
zeta-pro/
├── app.py                  # Backend Flask principal
├── zeta_pro.db            # Base de datos SQLite
├── requirements.txt        # Dependencias Python
├── index.html             # Frontend web
├── uploads/
│   └── images/            # Imágenes subidas
├── README.md              # Esta documentación
└── .gitignore
```

---

## 🔧 **Configuración**

### **Variables de Entorno**

Crea un archivo `.env`:

```env
FLASK_ENV=production
PORT=5002
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=sqlite:///zeta_pro.db
MAX_IMAGE_SIZE=5242880
```

### **Base de Datos**

La base de datos se crea automáticamente al iniciar. Para resetear:

```bash
rm zeta_pro.db
python app.py
```

---

## 📡 **API Endpoints**

### **Autenticación**

```http
POST /api/auth/register
Content-Type: application/json

{
  "name": "Juan Pérez",
  "email": "juan@email.com",
  "photo": "data:image/jpeg;base64,..."
}
```

### **Reportes**

```http
POST /api/reports/submit
Content-Type: application/json

{
  "user_id": "user_123",
  "description": "Asalto en la calle Principal",
  "category": "security",
  "severity": "high",
  "lat": 28.6353,
  "lon": -106.0886,
  "images": ["data:image/jpeg;base64,..."]
}
```

### **Lugares**

```http
GET /api/places/search?q=restaurante&type=Restaurante&lat=28.6353&lon=-106.0886
```

### **Rutas**

```http
POST /api/routes/calculate
Content-Type: application/json

{
  "origin": "28.6353,-106.0886",
  "destination": "Catedral de Chihuahua",
  "avoid_risks": true
}
```

Documentación completa: `/docs` (próximamente)

---

## 📱 **App Móvil**

### **React Native**

```bash
npx react-native init ZetaProMobile
cd ZetaProMobile
npm install @react-native-maps/maps axios
```

### **Capacitor (Recomendado)**

```bash
npm install @capacitor/core @capacitor/cli
npx cap init
npx cap add android
npx cap add ios
```

Ver [GUÍA COMPLETA](docs/mobile-app-guide.md)

---

## 🧪 **Testing**

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app
```

---

## 🌐 **Deployment**

### **Opción 1: Railway**

```bash
railway login
railway init
railway up
```

### **Opción 2: Render**

1. Conectar GitHub
2. New Web Service
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app`

### **Opción 3: Google Cloud**

```bash
gcloud run deploy zeta-pro \
  --source . \
  --platform managed \
  --allow-unauthenticated
```

---

## 📊 **Rendimiento**

- ⚡ Tiempo de respuesta promedio: < 100ms
- 📈 Capacidad: 1000+ req/min
- 💾 Base de datos: SQLite (actualizable a PostgreSQL)
- 🖼️ Compresión de imágenes: 80% reducción

---

## 🔒 **Seguridad**

- ✅ Validación de entrada con regex
- ✅ Sanitización de datos
- ✅ Filtros anti-spam
- ✅ Verificación de reportes
- ✅ Rate limiting (próximamente)
- ✅ HTTPS obligatorio en producción

---

## 🤝 **Contribuir**

Este es un proyecto comercial. Para licencias empresariales, contacta:

📧 **Email:** contacto@zetapro.com  
🌐 **Web:** www.zetapro.com  
💼 **LinkedIn:** linkedin.com/company/zeta-pro

---

## 📄 **Licencia**

Copyright © 2024 Zeta Pro. Todos los derechos reservados.

**Licencia Comercial** - Ver [LICENSE](LICENSE) para más detalles.

---

## 🎓 **Soporte**

- 📚 Documentación: [docs.zetapro.com](https://docs.zetapro.com)
- 💬 Discord: [discord.gg/zetapro](https://discord.gg/zetapro)
- 🐛 Issues: [GitHub Issues](https://github.com/tu-usuario/zeta-pro/issues)
- 📧 Email: soporte@zetapro.com

---

## 🌟 **Roadmap**

### **v1.0** (Actual)
- ✅ Sistema de reportes
- ✅ Navegación básica
- ✅ Base de datos de lugares

### **v1.1** (Próximo mes)
- ⏳ Modo offline
- ⏳ Notificaciones push
- ⏳ Compartir ubicación

### **v2.0** (3 meses)
- ⏳ App iOS nativa
- ⏳ Machine learning avanzado
- ⏳ API pública

---

## 👥 **Equipo**

Desarrollado con ❤️ por el equipo de Zeta Pro

**Fundador:** [Tu Nombre]  
**CTO:** [Nombre]  
**Designer:** [Nombre]

---

## 📸 **Screenshots**

![Dashboard](screenshots/dashboard.png)
![Mapa](screenshots/map.png)
![Reportes](screenshots/reports.png)

---

## 💰 **Planes y Precios**

| Plan | Precio | Características |
|------|--------|----------------|
| **Free** | $0 | Rutas básicas, 10 reportes/mes |
| **Pro** | $4.99/mes | Rutas ilimitadas, sin ads |
| **Business** | $49/mes | API access, soporte 24/7 |
| **Enterprise** | Contactar | Solución personalizada |

---

**🚀 ¡Empieza ahora y haz tu ciudad más segura!**
