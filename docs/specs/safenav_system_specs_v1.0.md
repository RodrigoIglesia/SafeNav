# 1. Descripción del Sistema
El sistema **SafeNav** (en su versión 1.0 - prototipo) tiene como objetivo proporcionar a los peatones rutas **seguras o confortables** en entornos urbanos.

**SafeNav** integra **datos espaciales y ambientales abiertos (fuentes de datos abiertas)** para calcular y recomendar rutas óptimas basadas en el contexto en tiempo real y las preferencias del usuario.

**SafeNav** consiste en los siguientes módulos:
- **Interfaz de Usuario (UI)**: Proporciona la interacción entre el usuario y el sistema. Gestiona las solicitudes de rutas, muestra los caminos recomendados y comunica retroalimentación sobre confort/seguridad.
- **Motor de Enrutamiento (RE)**: Genera rutas candidatas y las envía al analizador de contexto. Utiliza datos cartográficos para calcular rutas y optimizarlas en función del tiempo estimado de llegada (ETA) y la distancia.
- **Analizador de Contexto (CA)**: Procesa y fusiona datos ambientales externos con las rutas candidatas para evaluar su seguridad y confort. El componente asigna una “puntuación” a cada ruta (la puntuación puede aplicarse a toda la ruta o a partes de ella) y devuelve las rutas con sus respectivas puntuaciones.
- **Gestión de Datos (DM)**: Implementa las interfaces con las fuentes de datos externas. Preprocesa y prepara los datos para alimentar al RE y al CA.
---

## Especificación de Funcionalidades
En este capítulo se listan las funcionalidades llevadas a cabo por el sistema.

| ID | Funcionalidad | Descripción |
|----|----------------|-------------|
| **F1** | **Gestión de solicitudes de ruta** | El sistema permite al usuario definir una ruta, especificando origen, destino y preferencias (por ejemplo: minimizar exposición al sol, evitar zonas peligrosas, priorizar rapidez). |
| **F2** | **Cálculo de rutas candidatas** | El componente **Routing Engine (RE)** genera múltiples trayectorias posibles entre los puntos de origen y destino, basadas en datos cartográficos proporcionados por el **Data Management (DM)**. |
| **F3** | **Evaluación contextual de rutas** | El componente **Context Analyzer (CA)** analiza cada ruta candidata considerando factores meteorológicos, sombra y elementos urbanos para determinar su nivel de confort y seguridad. |
| **F4** | **Fusión de datos ambientales y urbanos** | El sistema integra información procedente de diferentes fuentes (clima, datos abiertos urbanos, topología vial) para ofrecer una visión contextual unificada de las condiciones actuales. |
| **F5** | **Asignación de puntuaciones de seguridad y confort** | Cada ruta se evalúa y se le asigna un “score” que representa su nivel de exposición al calor, disponibilidad de sombra, fuentes de agua, etc. |
| **F6** | **Selección y recomendación de la mejor ruta** | SafeNav combina tiempo estimado, distancia y puntuaciones de confort para recomendar la ruta más adecuada a las preferencias del usuario. |
| **F7** | **Visualización de rutas y resultados** | La interfaz de usuario (**UI**) muestra las rutas recomendadas en un mapa, indicando puntuaciones, alertas y elementos relevantes (zonas sombreadas, puntos de agua, etc.). |
---

# 2. Arquitectura del sistema
![alt text](system_architecture.png)
## Sistemas Externos
Se consideran los siguientes sistemas externos:

| ID | Sistema Externo | Tipo / Naturaleza | Descripción | Datos o Servicios Proporcionados | Mecanismo de Intercambio | Formato de Datos Esperado |
|----|------------------|------------------|--------------|----------------------------------|--------------------------|---------------------------|
| **ES1** | **Map Services (MapAPI)** | Servicio cartográfico | Proporciona datos geoespaciales base: red vial, geometrías de calles, polígonos de zonas urbanas y metadatos asociados. Utilizado por el componente **Routing Engine (RE)** para la generación de rutas. | - Calles y red vial<br>- Capas de mapa (tiles)<br>- Información geográfica y topológica | Peticiones HTTP/REST | GeoJSON, JSON |
| **ES2** | **Meteo Sources (MeteoAPI)** | Servicio meteorológico | Ofrece información meteorológica en tiempo real y alertas. Utilizado por el **Context Analyzer (CA)** (a través del **DM**) para obtener condiciones de temperatura, radiación y eventos extremos. | - Temperatura actual<br>- Radiación UV<br>- Alertas de calor / tormenta | Peticiones HTTP/REST | JSON |
| **ES3** | **Local Open Data (OpenDataAPI)** | Servicio de datos abiertos urbanos | Fuente de datos abierta mantenida por autoridades locales o entidades públicas. Proporciona información sobre infraestructura y entorno urbano relevante para la seguridad y el confort peatonal. | - Árboles y zonas de sombra<br>- Fuentes de agua y mobiliario urbano<br>- Puntos de interés (POIs) | Peticiones HTTP/REST o descarga periódica | JSON, CSV, GeoJSON |
---

## Subsistemas Internos
SafeNav se compone de los siguientes subsistemas:
| ID | Subsistema | Descripción General | Responsabilidades Principales | Entradas | Salidas |
|----|-------------|---------------------|-------------------------------|-----------|----------|
| **S1** | **User Interface (UI)** | Subsistema cliente que permite la interacción entre el usuario y el sistema SafeNav. Puede implementarse como aplicación web, móvil o de escritorio. | - Recibir entradas del usuario (origen, destino, preferencias).<br>- Enviar solicitudes al sistema SafeNav Core.<br>- Mostrar al usuario las rutas sugeridas, puntuaciones de confort y alertas contextuales.<br>- Gestionar la experiencia visual e interacción. | Datos introducidos por el usuario. | Rutas, puntuaciones y alertas mostradas al usuario. |
| **S2** | **SafeNav Core** | Subsistema principal que contiene toda la lógica de negocio del sistema. Se encarga de procesar las solicitudes de ruta, generar recomendaciones y obtener la información contextual necesaria. | - Recibir solicitudes desde la UI.<br>- Calcular rutas y evaluar su confort y seguridad.<br>- Integrar información proveniente de datos externos (mapas, clima, open data).<br>- Devolver resultados listos para presentación. | Solicitudes de la UI.<br>Datos externos de fuentes abiertas. | Rutas optimizadas con evaluación contextual. |
---

# 3. Arquitectura Lógica
![alt text](logical_architecture.png)
## Subsistema S1: User Interface (UI)

| ID | Componente | Descripción General | Responsabilidades Principales | Entradas | Salidas |
|----|-------------|--------------------|-------------------------------|-----------|----------|
| **C1** | **User Interface (UI)** | Gestiona toda la interacción entre el usuario y el sistema SafeNav. Proporciona las vistas y controles para definir rutas, mostrar resultados y emitir alertas contextuales. | - Capturar solicitudes del usuario (“Go Home”, destino, preferencias).<br>- Mostrar rutas, puntuaciones de seguridad/confort y alertas.<br>- Gestionar parámetros de usuario y configuración de preferencias.<br>- Enviar solicitudes al subsistema **SafeNav Core** a través de la API REST. | Datos introducidos por el usuario (origen, destino, preferencias). | Solicitudes HTTP/JSON a API Layer (SafeNav Core).<br>Visualización de rutas, puntuaciones y alertas. |

---

## Subsistema S2: SafeNav Core

El **SafeNav Core** contiene los componentes funcionales y de integración del sistema.  
Cada componente cumple un rol específico dentro del flujo de procesamiento de una solicitud de ruta.

| ID | Componente | Descripción General | Responsabilidades Principales | Entradas | Salidas |
|----|-------------|--------------------|-------------------------------|-----------|----------|
| **C2** | **API Layer (HTTP Controller)** | Capa de entrada del núcleo SafeNav. Expone los servicios del sistema mediante una API REST para la UI. | - Recibir solicitudes HTTP desde la UI.<br>- Validar datos y convertirlos en objetos internos (`RouteRequest`, `Preferences`).<br>- Orquestar la ejecución de los módulos internos (`RE`, `CA`, `DM`).<br>- Devolver resultados en formato JSON. | Solicitudes REST desde la UI. | Respuestas JSON con rutas y puntuaciones. |
| **C3** | **Routing Engine (RE)** | Núcleo de cálculo de rutas. Genera y optimiza rutas posibles utilizando los datos cartográficos y las condiciones actuales. | - Generar rutas candidatas a partir de los datos del mapa.<br>- Calcular ETA, distancia y costo de trayecto.<br>- Solicitar evaluación contextual al `CA`.<br>- Integrar puntuaciones y devolver rutas finales. | Datos del mapa (desde `DM`).<br>Solicitudes internas (desde `API Layer`). | Rutas optimizadas con puntuaciones. |
| **C4** | **Context Analyzer (CA)** | Evalúa las rutas candidatas con base en datos ambientales y contextuales. Combina información meteorológica y urbana para determinar su confort y seguridad. | - Solicitar datos procesados al `DM` (clima, sombra, POIs).<br>- Calcular puntuaciones de confort/seguridad por ruta o segmento.<br>- Devolver puntuaciones al `RE` y alertas al `API Layer`. | Datos contextuales (desde `DM`).<br>Rutas candidatas (desde `RE`). | Puntuaciones de confort y seguridad.<br>Alertas contextuales. |
| **C5** | **Data Management (DM)** | Capa de gestión e integración de datos externos. Se encarga de conectar el sistema con las fuentes abiertas (`MapAPI`, `MeteoAPI`, `OpenDataAPI`), procesar los datos y entregarlos en formato interno. | - Obtener y actualizar datos externos.<br>- Preprocesar, normalizar y cachear información.<br>- Proveer datos consistentes a `RE` y `CA`.<br>- Mantener coherencia temporal y semántica de los datos. | Peticiones de datos desde `RE` y `CA`.<br>Datos de servicios externos. | Datos preparados (mapas, clima, contexto urbano). |
---

# 3. Especificación de Interfaces

## Especificación de Interfaces Externas
[ ] TBD: Analizar fuentes externas de datos y definir el modelo de datos

En esta sección se describen las **interfaces externas** entre el sistema y sistemas externos.

| ID | Fuente → Destino | Descripción | Datos Principales Intercambiados |
|----|------------------|-------------|----------------------------------|
| **E1 – Interfaz de Datos Cartográficos** | **DM → MapAPI** | Solicita y obtiene información de calles, geometrías y capas de mapa necesarias para el cálculo de rutas. | `MapDataRequest` { área, nivel_zoom } → `MapDataResponse` { red_vial, polígonos, metadata } |
| **E2 – Interfaz de Datos Meteorológicos** | **DM → MeteoAPI** | Recupera condiciones climáticas actuales, temperatura, radiación solar y alertas. | `WeatherRequest` { área, hora_actual } → `WeatherResponse` { temperatura, UV, alerta } |
| **E3 – Interfaz de Datos Abiertos Urbanos** | **DM → OpenDataAPI** | Solicita datos urbanos relevantes: zonas de sombra, árboles, fuentes, mobiliario urbano, etc. | `OpenDataRequest` { área, tipo_dato } → `OpenDataResponse` { puntos_sombra, fuentes, parques } |
---


## Especificación de Interfaces Internas
En esta sección se describen las **interfaces internas** entre los componentes del sistema.  


| ID | Fuente → Destino | Descripción | Datos Principales Intercambiados |
|----|------------------|-------------|----------------------------------|
| **I1 – Interfaz de Solicitud de Ruta** | **UI → RE** | Transfiere la solicitud de navegación del usuario, incluyendo origen, destino y preferencias (comodidad, tiempo, evitar calor, etc.). | `RouteRequest` { origen, destino, preferencias } |
| **I2 – Interfaz de Visualización de Ruta** | **RE → UI** | Envía las rutas calculadas (con sus puntuaciones y metadatos) al componente UI para su visualización y selección por el usuario. | `RouteSet` { geometría, ETA, distancia, puntuación, alertas } |
| **I3 – Interfaz de Evaluación de Rutas** | **RE → CA** | Proporciona una lista de rutas candidatas para su evaluación contextual (seguridad, sombra, confort). | `RouteCandidates` { route_id, geometría, ETA, distancia } |
| **I4 – Interfaz de Puntuación de Rutas** | **CA → UI** | Devuelve las rutas (o segmentos) con sus valores de seguridad y confort. | `RouteScores` { route_id, comfort_score, segment_scores } |
| **I5 – Interfaz de Acceso a Datos Contextuales** | **CA → DM** | Solicita datos ambientales procesados (clima, sombra, puntos de interés) para apoyar la evaluación de contexto. | `ContextData` { temperatura, alertas, zonas_sombra, POIs } |
| **I6 – Interfaz de Datos Cartográficos** | **RE → DM** | Solicita datos de mapas o topología vial preprocesados o en caché necesarios para la generación de rutas. | `MapData` { grafo_vial, metadatos, info_tiles } |
| **I7 – Interfaz de Estado y Alertas** *(opcional)* | **UI ↔ CA** | Permite que el UI consulte condiciones ambientales actuales o alertas antes de calcular rutas (p. ej., “alerta de calor activa”). | `ContextSummary` { temperatura, nivel_alerta } |
---



