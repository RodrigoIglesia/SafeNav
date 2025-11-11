# 1. Descripción del Sistema
El sistema **SafeNav** (en su versión 1.0 - prototipo) tiene como objetivo proporcionar a los peatones rutas **seguras o confortables** en entornos urbanos.

**SafeNav** integra **datos espaciales y ambientales abiertos (fuentes de datos abiertas)** para calcular y recomendar rutas óptimas basadas en el contexto en tiempo real y las preferencias del usuario.

**SafeNav** consiste en los siguientes módulos:

| Componente | Descripción |
|---|---|
| **Interfaz de Usuario (UI)** | Proporciona la interacción entre el usuario y el sistema. Gestiona las solicitudes de rutas, muestra los caminos recomendados y comunica retroalimentación sobre confort/seguridad. |
| **Motor de Enrutamiento (RE)** | Genera rutas candidatas y las envía al analizador de contexto. Utiliza datos cartográficos para calcular rutas y optimizarlas en función del tiempo estimado de llegada (ETA) y la distancia. |
| **Analizador de Contexto (CA)** | Procesa y fusiona datos ambientales externos con las rutas candidatas para evaluar su seguridad y confort. El componente asigna una “puntuación” a cada ruta (la puntuación puede aplicarse a toda la ruta o a partes de ella) y devuelve las rutas con sus respectivas puntuaciones. |
| **Gestión de Datos (DM)** | Implementa las interfaces con las fuentes de datos externas. Preprocesa y prepara los datos para alimentar al RE y al CA. |
---

# 2. Arquitectura del sistema
![alt text](system_architecture.png)
## Sistemas Externos
Se consideran los siguientes sistemas externos:

| ID | Sistema Externo | Tipo / Naturaleza | Descripción | Datos o Servicios Proporcionados | Mecanismo de Intercambio | Formato de Datos Esperado |
|----|------------------|------------------|--------------|----------------------------------|--------------------------|---------------------------|
| **S1** | **Map Services (MapAPI)** | Servicio cartográfico | Proporciona datos geoespaciales base: red vial, geometrías de calles, polígonos de zonas urbanas y metadatos asociados. Utilizado por el componente **Routing Engine (RE)** para la generación de rutas. | - Calles y red vial<br>- Capas de mapa (tiles)<br>- Información geográfica y topológica | Peticiones HTTP/REST | GeoJSON, JSON |
| **S2** | **Meteo Sources (MeteoAPI)** | Servicio meteorológico | Ofrece información meteorológica en tiempo real y alertas. Utilizado por el **Context Analyzer (CA)** (a través del **DM**) para obtener condiciones de temperatura, radiación y eventos extremos. | - Temperatura actual<br>- Radiación UV<br>- Alertas de calor / tormenta | Peticiones HTTP/REST | JSON |
| **S3** | **Local Open Data (OpenDataAPI)** | Servicio de datos abiertos urbanos | Fuente de datos abierta mantenida por autoridades locales o entidades públicas. Proporciona información sobre infraestructura y entorno urbano relevante para la seguridad y el confort peatonal. | - Árboles y zonas de sombra<br>- Fuentes de agua y mobiliario urbano<br>- Puntos de interés (POIs) | Peticiones HTTP/REST o descarga periódica | JSON, CSV, GeoJSON |
---

## Componentes Internos
El sistema SafeNav v1.0 se compone de los siguientes componentes internos:

| ID | Componente | Descripción General | Responsabilidades Principales | Entradas | Salidas | Interfaz(es) Relacionada(s) |
|----|-------------|--------------------|--------------------------------|-----------|-----------|------------------------------|
| **C1** | **User Interface (UI)** | Gestiona toda la interacción entre el usuario y el sistema SafeNav. Proporciona las vistas y controles para definir rutas, mostrar resultados y emitir alertas contextuales. | - Capturar solicitudes del usuario (“Go Home”, destino, preferencias)<br>- Mostrar rutas, puntuaciones de seguridad/confort y alertas<br>- Gestionar parámetros de usuario | Entrada del usuario (origen, destino, preferencias) | Visualización de rutas y alertas | I1, I2, I7 |
| **C2** | **Routing Engine (RE)** | Núcleo de cálculo de rutas. Genera y optimiza rutas posibles utilizando los datos cartográficos. Se comunica con el Context Analyzer para evaluar seguridad y confort. | - Generar rutas candidatas a partir de datos del mapa<br>- Calcular ETA, distancia y costo de trayecto<br>- Solicitar evaluación contextual al CA<br>- Integrar puntuaciones y devolver rutas finales | Datos del mapa (desde DM), solicitud de usuario (desde UI) | Rutas optimizadas con puntuaciones | I1, I2, I3, I4, I6 |
| **C3** | **Context Analyzer (CA)** | Evalúa las rutas candidatas con base en datos ambientales y contextuales. Combina información del clima y de datos urbanos abiertos para calcular puntuaciones de seguridad y confort. | - Solicitar datos procesados al DM (clima, sombra, POIs)<br>- Fusionar datos contextuales<br>- Calcular puntuaciones de confort/seguridad por ruta o segmento<br>- Devolver resultados al RE y alertas al UI | Datos contextuales (desde DM), rutas candidatas (desde RE) | Puntuaciones de rutas y alertas ambientales | I3, I4, I5, I7 |
| **C4** | **Data Management (DM)** | Capa de gestión e integración de datos. Se encarga de conectar el sistema con las fuentes externas (MapAPI, MeteoAPI, OpenDataAPI), procesar los datos y entregarlos a los componentes internos. | - Obtener y actualizar datos externos (mapas, clima, datos urbanos)<br>- Preprocesar, normalizar y cachear datos<br>- Proveer datos consistentes al RE y CA<br>- Gestionar privacidad y almacenamiento temporal | Peticiones de datos (desde RE y CA) | Datos preparados (mapas, clima, contexto urbano) | I5, I6, E1, E2, E3 |
---

# 3. Especificación de
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

## F1 - Gestión de solicitud de ruta


# 4. Especificación de Interfaces

## Especificación de Interfaces Externas
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



