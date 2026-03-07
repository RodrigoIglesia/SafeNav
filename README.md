# SafeNav
SafeNav is a intelligent Route Planning system which ensures pedestrians' safety. SafeNav aims to increase pedestrians' safe in urban environments, in zones where infraestructure is limited, or under extremely hot envirnomental conditions -such as spanish cities in summer-. SafeNav combines information from OpenData platfo

# SafeNav – Execution and basic usage guide

This guide describes:

1. How to launch the system (Docker Compose)
2. How container networks are set up 
3. How UI and Backend interact with each other through API endpoints

---

# 🐳 1. Cómo lanzar el sistema

## 📦 Requisitos
Pre-requisitos:
- Docker
- Docker Compose

Verificar instalación:

1. docker --version
docker compose version

## 🚀 Iniciar el sistema
1. Clone the repository from Github.

2. From the project´s root (where docker-compose.yml is located):

   - $docker compose up --build
Este comando:

Construye el servicio safenav-core (backend FastAPI)

Construye el servicio safenav-ui (frontend React + Vite)

Inicia ambos contenedores

Expone los siguientes puertos:

Servicio	URL
- Backend API	http://localhost:8000
- Frontend UI	http://localhost:5173

## 🛑 Detener el sistema
docker compose down
# 🌐 2. Puntos de acceso
## 🔎 Backend – SafeNav Core
Documentación Swagger
http://localhost:8000/docs
Permite probar:

POST /routes/

POST /routes/map

GET /health

Health Check
http://localhost:8000/health
Respuesta esperada:

{
  "status": "ok",
  "service": "SafeNav Core API"
}
## 💻 Frontend – SafeNav UI
http://localhost:5173
Desde la interfaz puedes:

Solicitar una ruta segura

Solicitar datos del mapa

Visualizar la respuesta JSON

# 🌍 3. Funcionamiento de las redes en Docker
Docker Compose crea automáticamente una red interna compartida entre los servicios.

Dentro de esa red:

El backend es accesible como:

http://safenav-core:8000
El frontend es accesible como:

http://safenav-ui:5173
⚠️ Diferencia importante
Aunque los contenedores se comuniquen usando safenav-core,
el navegador NO conoce ese nombre.

Cuando el navegador hace una petición fetch(), debe usar:

http://localhost:8000
📌 Resumen de uso de hostnames
Contexto de la llamada	Hostname correcto
Contenedor → Contenedor	safenav-core
Navegador → Backend	localhost
# 🔄 4. Flujo básico de llamadas
## 🗺 Escenario A – Solicitud de Mapa
El usuario pulsa "Request Map"

La UI ejecuta:

POST http://localhost:8000/routes/map
La API recibe la petición

El API Layer llama a:

I_MapView → DataManagement
DataManagement devuelve un MapData

La API responde con MapDataResponse

La UI muestra el resultado

## 🚶 Escenario B – Solicitud de Ruta
El usuario pulsa "Request Safe Route"

La UI ejecuta:

POST http://localhost:8000/routes/
El API Layer llama a:

I_RoutingService → RoutingEngine
El RoutingEngine:

Solicita el grafo a DataManagement

Genera RouteCandidates

Opcionalmente evalúa contexto

La API construye un RouteResponse

La UI muestra la ruta y sus datos

# 🧠 5. Arquitectura simplificada
Navegador
   │
   ▼
SafeNav UI (React)
   │ HTTP
   ▼
SafeNav Core (FastAPI)
   │
   ├── Routing Engine
   ├── Context Analyzer
   └── Data Management
La API expone endpoints HTTP.

Los módulos internos se comunican mediante interfaces.

DataManagement simula (mock) fuentes externas de datos.

# 🔧 6. Consejos de desarrollo
Ver logs del backend
docker logs safenav-core
Ver logs del frontend
docker logs safenav-ui
Reconstruir tras cambios importantes
docker compose down
docker compose up --build
## ✅ Estado correcto del sistema
El sistema está funcionando correctamente cuando:

/health devuelve "status": "ok"

/routes/ devuelve RouteResponse

/routes/map devuelve MapDataResponse

No hay errores CORS

No hay errores 422

No hay errores 404 inesperados
---