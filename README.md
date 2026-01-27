# 🛡️ ZETA PRO - Sistema Profesional de Navegación Segura

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.0-red.svg)](https://flask.palletsprojects.com/)

> **Sistema inteligente de navegación urbana que calcula rutas seguras basándose en datos verificados de seguridad pública en tiempo real.**

**🌐 Demo en vivo:** [Próximamente]  
**📱 App móvil:** En desarrollo

---

## 🎯 Características Principales

### ✅ Navegación Inteligente
- 🗺️ Cálculo de rutas evitando zonas de riesgo
- 📍 Geolocalización precisa en tiempo real
- 🚗 Múltiples modos de transporte (auto, moto, bici, caminando)
- ⚡ Rutas optimizadas por seguridad y tiempo

### ✅ Sistema de Reportes Verificados
- 📝 Reportes de incidentes con fotos
- 🤖 Verificación automática con IA
- 👥 Sistema de votos comunitario (upvote/downvote)
- 📰 Corroboración con fuentes noticiosas confiables

### ✅ Base de Datos Completa
- 🍽️ Restaurantes con reseñas verificadas
- 🏛️ Museos y sitios culturales
- ⭐ Sistema de calificaciones (1-5 estrellas)
- 📸 Galerías de fotos de cada lugar

### ✅ Alertas Inteligentes
- 🚨 Zonas de riesgo dinámicas (actualizadas en tiempo real)
- 🌊 Alertas de desastres naturales
- ⚠️ Notificaciones de incidentes cercanos
- 🔔 Sistema de alertas push (próximamente)

---

## 🚀 Instalación Rápida

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno (Chrome, Firefox, Safari, Edge)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/TU-USUARIO/zeta-pro.git
cd zeta-pro
```

### 2. Configurar el Backend

```bash
# Navegar a la carpeta del backend
cd backend

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
python app.py
```

El backend estará corriendo en: `http://localhost:5002`

### 3. Abrir el Frontend

**Opción A - Directamente:**
- Abre el archivo `frontend/index.html` en tu navegador

**Opción B - Con servidor local (recomendado):**
```bash
# Desde la carpeta raíz
cd frontend

# Python 3
python -m http.server 8000

# O con Node.js
npx serve
```

Luego abre: `http://localhost:8000`

---

## 📁 Estructura del Proyecto

```
zeta-pro/
├── backend/
│   ├── app.py                 # Backend Flask con API REST
│   ├── requirements.txt       # Dependencias Python
│   ├── zeta_pro.db           # Base de datos SQLite (generada automáticamente)
│   └── uploads/              # Imágenes subidas (generada automáticamente)
│
├── frontend/
│   ├── index.html            # Aplicación web completa (SPA)
│   └── assets/               # Recursos estáticos
│
├── docs/
│   ├── MOBILE_APP_GUIDE.md   # Guía para crear apps iOS/Android
│   └── DEPLOYMENT.md         # Guía de deployment
│
├── .gitignore                # Archivos ignorados por Git
├── README.md                 # Esta documentación
└── LICENSE                   # Licencia MIT
```

---

## 🔧 Configuración

### Variables de Entorno (Opcional)

Crea un archivo `.env` en la carpeta `backend/`:

```env
FLASK_ENV=production
PORT=5002
SECRET_KEY=tu-clave-secreta-super-segura
MAX_IMAGE_SIZE=5242880
```

### Configurar API URL en Frontend

Si despliegas el backend en un servidor externo, actualiza la URL en `frontend/index.html`:

```javascript
const CONFIG = {
    API_URL: 'https://tu-backend.onrender.com/api',  // Cambia esto
    // ...
};
```

---

## 📡 API Endpoints

### Autenticación

**POST** `/api/auth/register`
```json
{
  "name": "Juan Pérez",
  "email": "juan@email.com",
  "photo": "data:image/jpeg;base64,..."
}
```

### Reportes

**POST** `/api/reports/submit`
```json
{
  "user_id": "user_123",
  "description": "Incidente en Av. Universidad",
  "category": "security",
  "severity": "high",
  "lat": 28.6353,
  "lon": -106.0886,
  "images": ["data:image/jpeg;base64,..."]
}
```

**GET** `/api/reports/list?verified=true&days=30`

### Lugares

**GET** `/api/places/search?q=restaurante&type=Restaurante`

**POST** `/api/places/{place_id}/reviews`
```json
{
  "user_id": "user_123",
  "rating": 5,
  "comment": "Excelente lugar",
  "images": ["data:image/jpeg;base64,..."]
}
```

### Rutas

**POST** `/api/routes/calculate`
```json
{
  "origin": "28.6353,-106.0886",
  "destination": "Fashion Mall",
  "avoid_risks": true
}
```

📖 **Documentación completa:** [En desarrollo]

---

## 📱 App Móvil

### Crear Apps iOS y Android

Este proyecto puede convertirse en apps nativas usando **Capacitor**:

```bash
npm install @capacitor/core @capacitor/cli
npx cap init "Zeta Pro" "com.zetapro.app"
npx cap add android
npx cap add ios
```

📱 **Guía completa:** Ver [`docs/MOBILE_APP_GUIDE.md`](docs/MOBILE_APP_GUIDE.md)

---

## 🌐 Deployment

### Backend - Render (Gratis)

1. Conecta tu repositorio de GitHub a [Render](https://render.com)
2. Crea un nuevo Web Service
3. Configuración:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Deploy

### Frontend - Netlify (Gratis)

1. Conecta tu repositorio a [Netlify](https://netlify.com)
2. Configuración:
   - **Base directory:** `frontend`
   - **Build command:** (vacío)
   - **Publish directory:** `.`
3. Deploy

🚀 **Guía detallada:** Ver [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

---

## 🧪 Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov

# Ejecutar tests
pytest

# Con coverage
pytest --cov=backend
```

---

## 🔒 Seguridad

- ✅ Validación de entrada con regex y sanitización
- ✅ Filtros anti-spam multicapa
- ✅ Verificación de reportes con IA
- ✅ Encriptación de datos sensibles
- ✅ Rate limiting (próximamente)
- ✅ HTTPS obligatorio en producción

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guía de Estilo de Commits

- ✨ `feat:` Nueva característica
- 🐛 `fix:` Corrección de bug
- 📝 `docs:` Cambios en documentación
- 🎨 `style:` Cambios de formato/estilo
- ⚡ `perf:` Mejoras de rendimiento
- 🧪 `test:` Agregar tests
- 🔧 `chore:` Tareas de mantenimiento

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👥 Equipo

**Creador y Desarrollador Principal:**  
📧 Email: felitzx00@gmail.com

---

## 🙏 Agradecimientos

- [OpenStreetMap](https://www.openstreetmap.org/) - Datos cartográficos
- [Nominatim](https://nominatim.org/) - Geocodificación
- [OSRM](http://project-osrm.org/) - Cálculo de rutas
- [Leaflet](https://leafletjs.com/) - Librería de mapas
- [Flask](https://flask.palletsprojects.com/) - Framework web
- [Tailwind CSS](https://tailwindcss.com/) - Framework CSS
- Dirección de Seguridad Pública Municipal de Chihuahua

---

## 📞 Soporte

¿Necesitas ayuda?

- 📧 **Email:** soporte@zetapro.com
- 💬 **Issues:** [GitHub Issues](https://github.com/TU-USUARIO/zeta-pro/issues)
- 📖 **Documentación:** [Wiki del proyecto](https://github.com/TU-USUARIO/zeta-pro/wiki)

---

## 🌟 Roadmap

### v1.0 ✅ (Actual)
- [x] Sistema de reportes con verificación
- [x] Navegación con zonas de riesgo
- [x] Base de datos de lugares
- [x] Reseñas con fotos

### v1.1 🔄 (En desarrollo)
- [ ] Modo offline
- [ ] Notificaciones push
- [ ] Compartir ubicación con contactos
- [ ] Historial de rutas

### v2.0 📅 (Planeado)
- [ ] Apps nativas iOS y Android
- [ ] Machine Learning avanzado
- [ ] API pública para desarrolladores
- [ ] Panel de administración
- [ ] Sistema de suscripciones

---

## 📊 Estado del Proyecto

![GitHub last commit](https://img.shields.io/github/last-commit/TU-USUARIO/zeta-pro)
![GitHub issues](https://img.shields.io/github/issues/TU-USUARIO/zeta-pro)
![GitHub pull requests](https://img.shields.io/github/issues-pr/TU-USUARIO/zeta-pro)
![GitHub stars](https://img.shields.io/github/stars/TU-USUARIO/zeta-pro?style=social)

---

## 💡 FAQ

**P: ¿Es gratis?**  
R: Sí, Zeta Pro es completamente gratuito y de código abierto.

**P: ¿Funciona en otras ciudades?**  
R: Actualmente está optimizado para Chihuahua, México. Puedes adaptarlo para otras ciudades modificando las coordenadas y zonas de riesgo.

**P: ¿Necesito saber programar para usarlo?**  
R: No para usar la app. Sí para instalar/modificar el código.

**P: ¿Puedo usar esto comercialmente?**  
R: Sí, bajo la Licencia MIT puedes usar, modificar y distribuir este proyecto, incluso comercialmente.

---

<div align="center">

**Hecho con ❤️ en Chihuahua, México**

⭐ **Si te gusta este proyecto, dale una estrella en GitHub** ⭐

[⬆ Volver arriba](#-zeta-pro---sistema-profesional-de-navegación-segura)

</div>
