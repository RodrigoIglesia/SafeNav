[ ] TODO: Change design and interfaces for new city change functionality.
[ ] The system must be multi-city. when city changes in the UI, the system must know it and load a graph for the entire new cities.
[ ] For each route request, the city will be sent to the system
[ ] For performance porpouses, the system must know when a city has been loaded before, by searching in a cached memory

# 1. Descripción del Sistema
El sistema **SafeNav** (en su versión 1.0 - prototipo) tiene como objetivo proporcionar a los peatones rutas **seguras o confortables** en entornos urbanos.

**SafeNav** integra **datos espaciales y ambientales abiertos (fuentes de datos abiertas)** para calcular y recomendar rutas óptimas basadas en el contexto en tiempo real y las preferencias del usuario.

**SafeNav** consiste en los siguientes módulos:
- **Interfaz de Usuario (UI)**: Proporciona la interacción entre el usuario y el sistema. Gestiona las solicitudes de rutas, muestra los caminos recomendados y comunica retroalimentación sobre confort/seguridad.
- **Motor de Enrutamiento (RE)**: Genera rutas candidatas y las envía al analizador de contexto. Utiliza datos cartográficos para calcular rutas y optimizarlas en función del tiempo estimado de llegada (ETA) y la distancia.
- **Motor de representación Geoespacial**: Obtiene una representación contextual de las rutas, de modo que puedan ser evaluadas en base al estado de su contexto (sombras, puntos de agua, zonas seguras, etc.)
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
| **F6** | **Priorización y recomendación de rutas** | SafeNav puede priorizar las rutas candidatas combinando tiempo estimado, distancia y puntuaciones de confort/seguridad, devolviendo una o varias rutas ordenadas según las preferencias del usuario. |
| **F7** | **Visualización de rutas y resultados** | La interfaz de usuario (**UI**) muestra las rutas recomendadas en un mapa, indicando puntuaciones, alertas y elementos relevantes (zonas sombreadas, puntos de agua, etc.). |
---

# 2. Arquitectura del sistema
## Sistemas Externos
Se consideran los siguientes sistemas externos:

| ID | Sistema Externo | Tipo / Naturaleza | Descripción | Datos o Servicios Proporcionados | Mecanismo de Intercambio | Formato de Datos Esperado |
|----|------------------|------------------|--------------|----------------------------------|--------------------------|---------------------------|
| **ES1** | **Map Services (MapAPI)** | Servicio cartográfico | Proporciona datos geoespaciales base: red vial, geometrías de calles, polígonos de zonas urbanas y metadatos asociados. Utilizado por el sistema SafeNav (a través del componente **Data Management**) para proporcionar datos cartográficos tanto para la generación de rutas como para la visualización del mapa. | - Calles y red vial<br>- Capas de mapa (tiles)<br>- Información geográfica y topológica | Peticiones HTTP/REST | GeoJSON, JSON |
| **ES2** | **Meteo Sources (MeteoAPI)** | Servicio meteorológico | Ofrece información meteorológica en tiempo real y alertas. Utilizado por el **Context Analyzer (CA)** (a través del **DM**) para obtener condiciones de temperatura, radiación y eventos extremos. | - Temperatura actual<br>- Radiación UV<br>- Alertas de calor / tormenta | Peticiones HTTP/REST | JSON |
| **ES3** | **Local Open Data (OpenDataAPI)** | Servicio de datos abiertos urbanos | Fuente de datos abierta mantenida por autoridades locales o entidades públicas. Proporciona información sobre infraestructura y entorno urbano relevante para la seguridad y el confort peatonal. | - Árboles y zonas de sombra<br>- Fuentes de agua y mobiliario urbano<br>- Puntos de interés (POIs) | Peticiones HTTP/REST o descarga periódica | JSON, CSV, GeoJSON |
---

## Subsistemas Internos
SafeNav se compone de los siguientes subsistemas:
| ID | Subsistema | Descripción General | Responsabilidades Principales | Entradas | Salidas |
|----|-------------|---------------------|-------------------------------|-----------|----------|
| **S1** | **User Interface (UI)** | Subsistema cliente que permite la interacción entre el usuario y el sistema SafeNav. Puede implementarse como aplicación web, móvil o de escritorio. | - Renderizar rutas calculadas, putos de origen, destino y otros puntos de interés en la ruta, y mapa. Actúa como interfaz entre el usuario y el sistema backend, capturando los parámetros de entrada y configuración introducidos y mostrando los resultados. | Datos introducidos por el usuario. | Rutas, puntuaciones y alertas mostradas al usuario. |
| **S2** | **SafeNav Core** | Subsistema principal que contiene toda la lógica de negocio del sistema. Se encarga de procesar las solicitudes de ruta, generar recomendaciones y obtener la información contextual necesaria. | - Recibir solicitudes desde la UI.<br>- Calcular rutas y evaluar su confort y seguridad.<br>- Integrar información proveniente de datos externos (grafos, clima, open data).<br>- Devolver resultados listos para presentación. | Solicitudes de la UI.<br>Datos externos de fuentes abiertas. | Rutas optimizadas con evaluación contextual. |
---

# 3. Arquitectura Lógica
## Subsistema S1: User Interface (UI)
| ID | Componente | Descripción General | Responsabilidades Principales | Entradas | Salidas |
|----|-------------|--------------------|-------------------------------|-----------|----------|
| **C1** | **User Interface (UI)** | Gestiona toda la interacción entre el usuario y el sistema SafeNav. Proporciona las vistas y controles para definir rutas, mostrar resultados y emitir alertas contextuales. | - Renderiza el mapa en función de la ciudad seleccionada por el usuario y los puntos de origen y destino introducidos. UI implementa una interfaz directa con el servicio de provisionamiento de ´tiles´ (externo) <br>- Recibir entradas del usuario (origen, destino, preferencias).<br>- Enviar solicitudes al sistema SafeNav Core.<br>- Mostrar al usuario las rutas sugeridas, puntuaciones de confort y alertas contextuales.<br>- Gestionar la experiencia visual e interacción.<br>- Enviar solicitudes al subsistema **SafeNav Core** a través de la API REST. | Datos introducidos por el usuario (origen, destino, preferencias). | Solicitudes HTTP/JSON a API Layer (SafeNav Core).<br>Visualización de rutas, puntuaciones y alertas. |

---

## Subsistema S2: SafeNav Core

El **SafeNav Core** contiene los componentes funcionales y de integración del sistema.  
Cada componente cumple un rol específico dentro del flujo de procesamiento de una solicitud de ruta.

| ID | Componente | Descripción General | Responsabilidades Principales | Entradas | Salidas |
|----|-------------|--------------------|-------------------------------|-----------|----------|
| **C2** | **API Layer (HTTP Controller)** | Capa de entrada del núcleo SafeNav. Expone los servicios del sistema mediante una API REST para la UI. API actúa como orquestrador del sistema, gestionando la secuencia de llamadas a los servicios backend. | - Recibir solicitudes HTTP desde la UI.<br>- Validar datos y convertirlos en objetos internos (`RouteRequest`, `Preferences`).<br>- Orquestar la ejecución de los módulos internos (`RE`, `CA`, `DM`).<br>- Devolver resultados en formato JSON. | Solicitudes REST desde la UI. | Respuestas JSON con rutas y puntuaciones. |
| **C3** | **Routing Engine (RE)** | Núcleo de cálculo de rutas. Genera y optimiza rutas posibles utilizando los datos cartográficos y las condiciones actuales. | - Generar rutas candidatas a partir de los datos del mapa.<br>- Calcular ETA, distancia y costo de trayecto.<br>- (Opcionalmente) Solicitar evaluación contextual al `CA` cuando el flujo lo requiera.<br>- Devuelve rutas candidatas o rutas enriquecidas con puntuaciones. | Datos del mapa (desde `DM`).<br>Solicitudes internas (desde `API Layer`). | Rutas optimizadas con puntuaciones. |
| **C4** | **Geospatial Engine (GE)** | Obtiene una representacißon geoespacial del contexto de las rutas candidatas, de modo que puedan ser evaluadas en función de ese contexto. | - Solicitar datos procesados al `DM` (clima, sombra, POIs).<br>- Calcular la representación contextual de las rutas. | Datos contextuales (desde `DM`).<br>Rutas candidatas (desde `RE`). | Representación contextual. |
| **C5** | **Context Analyzer (CA)** | Evalúa las rutas candidatas con base en datos ambientales y contextuales. Combina información meteorológica y urbana para determinar su confort y seguridad. | - Obtiene representación contextual de `GE`.<br>- Calcular puntuaciones de confort/seguridad por ruta o segmento.<br>- Devolver puntuaciones al `RE`. | Representación contextuales (desde `GE`).<br>Rutas candidatas (desde `RE`). | Puntuaciones de confort y seguridad.<br>Alertas contextuales. |
| **C6** | **Data Management (DM)** | Capa de gestión e integración de datos externos. Se encarga de conectar el sistema con las fuentes abiertas (`MapAPI`, `MeteoAPI`, `OpenDataAPI`), procesar los datos y entregarlos en formato interno. | - Obtener y actualizar datos externos.<br>- Preprocesar, normalizar y cachear información.<br>- Proveer datos consistentes a `RE` y `CA`.<br>- Mantener coherencia temporal y semántica de los datos. | Peticiones de datos desde `RE` y `CA`.<br>Datos de servicios externos. | Datos preparados (Grafos de mapas, clima, contexto urbano). |
---

# 4. Especificación de Interfaces
[ ] TBD: Analizar fuentes externas de datos y definir el modelo de datos

## Interfaces Internas (SafeNav Core)

| ID | Nombre de Interfaz | Descripción | Datos Principales |
|----|--------------------|-------------|-------------------|
| **I_HTTP_Routes** | Interfaz HTTP de Rutas | Expone los endpoints HTTP/JSON que permiten a la interfaz de usuario solicitar rutas, consultar resultados y recibir puntuaciones o alertas. No se define en Pydantic, ya que es una llamada API. | `RouteRequest`, `RouteResponse` |
| **I_RoutingService** | Servicio de Generación de Rutas | Proporciona servicios internos para calcular rutas candidatas basadas en origen, destino y configuración de usuario. | `Area`, `RouteCandidates` |
| **I_ContextService** | Servicio de Evaluación Contextual | Evalúa las rutas según factores ambientales (temperatura, sombra, alertas) y devuelve puntuaciones agregadas de confort y seguridad. | `RouteCandidates`, `RouteScores` |
| **I_RoadGraphAccess** | Acceso a grafos de representación de rutas de mapas (nodos y aristas) | Proporciona acceso a estructuras de datos en formato de grafo para representar mapas. | `Area`, `GraphData` |
| **I_ContextDataAccess** | Acceso a Datos obtenidos de fuentes externas (urbanos y meteorológicos) | Proporciona acceso estructurado a datos cartográficos, meteorológicos y urbanos ya procesados o en caché dentro del sistema. | `WeatherData`, `UrbanData` |
---

## Interfaces Externas (Fuentes de Datos)

| ID | Nombre de Interfaz | Descripción | Datos Principales |
|----|--------------------|-------------|-------------------|
| **I_MapDataAccess** | Interfaz HTTP para visualizar mapas | Expone los endpoints HTTP/JSON que permiten a la interfaz de usuario solicitar un mapa para mostrar. No se define en Pydantic, ya que es una llamada API | `mapRequest`, `MapDataResponse` |
| **I_MeteoDataAccess** | Interfaz de Datos Meteorológicos | Permite recuperar condiciones meteorológicas actuales, temperatura, radiación UV y alertas climáticas. | `WeatherRequest`, `WeatherResponse` |
| **I_OpenDataAccess** | Interfaz de Datos Abiertos Urbanos | Solicita datos abiertos municipales: zonas de sombra, árboles, fuentes, parques y puntos de interés urbano. | `OpenDataRequest`, `OpenDataResponse` |
---

## Relación entre Componentes e Interfaces

| Componente | Interfaces Implementadas | Interfaces Utilizadas |
|-------------|--------------------------|------------------------|
| **User Interface (UI)** | — | `I_HTTP_Routes`, `I_MapDataAccess_`, `I_MapView`|
| **API Layer** | `I_HTTP_Routes` | `I_RoutingService`, `I_RoutingService` |
| **Routing Engine (RE)** | `I_RoutingService` | `I_RoadGraphAccess` |
| **Context Analyzer (CA)** | `I_ContextService` | `I_ContextDataAccess` |
| **Data Management (DM)** | `I_ContextDataAccess`, `I_RoadGraphAccess`, `I_MeteoDataAccess`, `I_OpenDataAccess` | — |

---

## Descripción de Datos Principales

| Tipo de Dato | Descripción | Campos Relevantes |
|---------------|--------------|-------------------|
| **RouteRequest** | Solicitud de cálculo de ruta enviada por el usuario. | `origin: GeoPoint`, `destination: GeoPoint`, `preferences: RoutePreferences` |
| **RouteResponse** | Respuesta de rutas con puntuaciones y metadatos. | `routes: RouteCandidates`, `scores: Optional[RouteScores]`, `metadata: ResponseMetadata` |
| **RouteCandidates** | Conjunto de rutas candidatas generadas por el motor de rutas. | `route_id`, `geometry`, `eta`, `distance` |
| **RouteScores** | Puntuaciones de seguridad y confort asignadas por el analizador contextual. | `comfort_score`, `safety_score`, `segment_scores` |
| **GraphData** | Datos cartográficos convertidos en estructura de grafo para planificación. | `Graph`, `metadata` |
| **WeatherData** | Datos meteorológicos procesados. | `temperature`, `uv_index`, `alert_level` |
| **UrbanData** | Datos urbanos relevantes para confort y seguridad. | `shadow_zones`, `water_points`, `POIs` |

---

# 5. Escenarios Operacionales

Esta sección describe los principales escenarios operacionales del sistema **SafeNav**.  

Cada escenario representa una secuencia concreta de interacciones entre los componentes del sistema durante su ejecución. Los escenarios permiten comprender cómo se materializan las funcionalidades descritas anteriormente y cómo colaboran los distintos módulos del sistema.

Los escenarios se organizan según el ciclo de vida típico de uso del sistema:

0. Visualización inicial del mapa.
1. Solicitud y generación de rutas candidatas.
2. Evaluación contextual (opcional).
3. Ajuste dinámico del mapa.
4. Visualización de rutas sobre el mapa.

---

## Escenario 0 – Visualización Inicial del Mapa

### Propósito

Mostrar un mapa base por defecto cuando la aplicación se inicia, incluso antes de que el usuario seleccione un origen o un destino.

### Condición de Activación

El usuario abre la aplicación SafeNav.

### Componentes Involucrados

- User Interface (UI)  
- Map Services (MapAPI)

### Descripción del Flujo

1. El usuario abre la aplicación.
2. La UI envía una solicitud de mapa (`mapDataAccess`) a la API externa de mapas. Esta solicitud se ejecuta a través de la librería Leaflet
3. Map API devuelve la imagen OSM del mapa a la UI.
4. La UI renderiza el mapa base al usuario.

### Resultado

El usuario visualiza un mapa inicial de la ciudad configurada, sin rutas activas ni elementos superpuestos.

---

## Escenario 1 – Recentrado del Mapa tras Selección de Origen y Destino

### Propósito

Ajustar dinámicamente el área visible del mapa cuando el usuario selecciona un origen y un destino.

### Condición de Activación

El usuario selecciona origen y destino en la interfaz.

### Componentes Involucrados

- User Interface (UI)
- Map Services (MapAPI)

### Descripción del Flujo

1. El usuario selecciona origen y destino.
2. La UI determina el área de interés que contiene ambos puntos.
3. La UI envía una nueva solicitud de Tile, `fetchMapData` a través de la interfaz `I_MapDataAccess` a MapAPI (OpenStreetMap o similar).
4. MapAPI devuelve `MapData` actualizado a la UI.
5. La UI renderiza el mapa centrado en el área seleccionada.
6. La UI muestra los puntos de inicio y destino en la UI.

### Resultado

El mapa se ajusta dinámicamente al contexto espacial del trayecto solicitado.

---


## Escenario 2 – Solicitud y Generación de Rutas Candidatas

### Propósito

Generar rutas candidatas entre un origen y un destino definidos por el usuario.

### Condición de Activación

El usuario selecciona un destino e introduce sus preferencias de ruta.

### Componentes Involucrados

- User Interface (UI)  
- API Layer  
- Routing Engine (RE)  
- Data Management (DM)  
- Map Services (MapAPI)

### Descripción del Flujo

1. El usuario solicita una ruta.
2. La UI envía a la API una solicitud `RouteRequest` que incluye origen, destino y preferencias.
3. La API delega en el Routing Engine el cálculo de rutas candidatas.
4. El Routing Engine solicita a Data Management los datos cartográficos en formato de grafo (`GraphData`).
5. Data Management obtiene los datos cartográficos desde MapAPI y los transforma en una representación topológica.
6. El Routing Engine calcula las rutas candidatas (ETA, distancia). En caso de evaluar varios candidatos, la estimación de dichas rutas se realizarán en procesos paralelos sin impacto acumulado en el tiempo de procesado.
7. El Routing Engine devuelve a la API un conjunto de `RouteCandidates`.

En este punto, el sistema puede activar el Escenario 3 para evaluación contextual -Implementando la interfaz I_routing_service::get_route_scores- o devolver directamente las rutas candidatas.

UI renderizará tantas rutas candidatas como sean retornadas en este escenario.

### Resultado

Se generan rutas candidatas basadas en datos cartográficos y métricas básicas (tiempo estimado y distancia).

---

## Escenario 3 - Descripción Contextual de Rutas (Opcional)

### Propósito
Generar una representación contextual del espacio por el que transcurren las rutas en un momento dado, representando datos meteorológicos y urbanísticos con los que poder evaluar el comfort y seguridad de la ruta más adelante.

### Condición de activación
Este escenario se activa automáticamente desde la API tras recibir las rutas candidatas.  
Su ejecución puede depender de la configuración del sistema o de la disponibilidad de datos externos.

### Componentes Involucrados

- API Layer  
- Geospatial Engine (GE)
- Data Management (DM)  
- Meteo Data Source (MeteoAPI)  
- Open Data Source (OpenDataAPI)

### Descripción del Flujo

1. La API solicita a GE la obtención de la representación de contexto, enviando las rutas para que GE pueda adaptar el contexto a su área.
2. GE solicita datos climáticos a `Meteo Source`.
3. GE solicita datos urbanísticos a `Open Data Source`.
4. GE procesa los datos obtenidos para cada ruta e instante de tiempo, generando una representación en datos estructurados para cada ruta.


### Resultado

GE obtiene una representación estructurada de los elementos contextuales en la ruta.
Si el escenario no se ejecuta, la representación contextual estará vacía y CA no lo tendrá en cuenta.

---

## Escenario 4 – Evaluación Contextual de Rutas (Opcional)

### Propósito

Evaluar las rutas candidatas utilizando información contextual (meteorológica y urbana) para asignar puntuaciones de seguridad y confort.

### Condición de Activación

Este escenario se activa automáticamente desde la API tras la obtención de la representación contextual de las rutas
Su ejecución puede depender de la configuración del sistema o de la disponibilidad de datos externos.

### Componentes Involucrados

- API Layer  
- Context Analyzer (CA)

### Descripción del Flujo

1. La API solicita al Context Analizer la evaluación contextual de las rutas. La solicitud incluye las rutas a evaluar y la descripción contextual de cada ruta.
2. El Context Analyzer calcula puntuaciones de confort y seguridad para cada ruta o segmento --> **Analyze Data and Puntuate route**
3. Las puntuaciones (`RouteScores`) se devuelven a la API.
4. La API enriquece el `RouteResponse` con los scores.

### Resultado

Las rutas candidatas se enriquecen con puntuaciones de seguridad y confort.  
Si este escenario no se ejecuta, el sistema devuelve rutas sin evaluación contextual.

---


## Escenario 4 – Superposición de Rutas sobre el Mapa

### Propósito

Visualizar las rutas calculadas y sus puntuaciones sobre el mapa actualmente mostrado.

### Condición de Activación

La API devuelve un `RouteResponse` con rutas candidatas y, opcionalmente, puntuaciones de contexto.

### Componentes Involucrados

- API Layer  
- User Interface (UI)

### Descripción del Flujo

1. La API devuelve a la UI un `RouteResponse` que contiene rutas candidatas y, si procede, puntuaciones.
2. La UI renderiza las geometrías de las rutas como superposición sobre el mapa ya cargado.
3. La UI muestra indicadores visuales asociados a las puntuaciones.

No se solicita un nuevo mapa en este escenario; se reutiliza el mapa actualmente visualizado.

### Resultado

El usuario visualiza las rutas recomendadas superpuestas sobre el mapa, junto con sus indicadores de seguridad y confort.

---

## Trazabilidad entre Escenarios y Funcionalidades

| Escenario | Funcionalidades Relacionadas |
|------------|------------------------------|
| Escenario 0 – Visualización Inicial del Mapa | F7, F8 |
| Escenario 1 – Recentrado del Mapa | F7, F9 |
| Escenario 2 – Generación de Rutas Candidatas | F1, F2 |
| Escenario 3 – Evaluación Contextual | F3, F4, F5 |
| Escenario 4 – Superposición de Rutas | F6, F7 |

---

# 6. Especificación Lógica
[ ] TODO: En este capítulo se debe explicar la lógica de las funcionalidades implementadas por cada módulo para generar la respuesta. Ahora hay que disenar CA, pero hay que documentar RE y DM
Los siguientes módulos de SafeNav Core aplican una lógica específica para cubrir las funcionalidades del sistema.
## Routing Engine
RE es el encargado de implementar la lógica de enrutamiento, cubriendo así la funcionalidad **F2** - **Cálculo de rutas candidatas**
[ ] Desarrollar más

## Geospatial Engine
Módulo encargado de construir una descripción contextual de cada ruta candidata a partir de los datos meteorológicos y urbanos obtenidos mediante `Data Management`.

Cubre las siguientes funcionalidades:
* **F4** - **Fusión de datos ambientales y urbanos**

El módulo procesa cada RouteCandidate independiéntemente, generando un contexto por candidato.

### Entradas
RouteCandidates: Respuesta de RE enviada a través de API.
WeatherData: GE hace uso de la interfaz `I_ContextService` implementada por DM para obtener los datos meteorológicos.
UrbanData: GE hace uso de la interfaz `I_ContextService` implementada por DM para obtener los datos urbanos.

### Salida
ContextDescription

### Analyze Data to obtain Context Representation
Esta función implementa la lógica central del módulo.

[ ] TBC

    FOR EACH RouteCandidate

        1. Sample route geometry

        2. Associate meteorological observations to sampled route points

        3. Select urban elements relevant to the route according to spatial criteria

            - shadow zone intersections
            - nearby water points
            - nearby police offices
            - nearby parks
            - nearby benches

        4. Build WeatherContext

        5. Build UrbanContext

        6. Build RouteContext

    Aggregate all RouteContext objects into a ContextDescription response

## Data Management
DM implementa las interfaces externas con servicios de datos abiertos. Estas interfaces son usadas por los distintos servicios SafeNav core para:
* Obtener grafos para calcular rutas entre dos puntos
* Obtener datos climáticos para analizar la seguridad y comfort de las rutas
* Obtener datos de vías públicas para analizar la seguridad y comfort de las rutas.
DM es una capa gateway que adapta datos de entrada al modelo de datos SafeNav, actúa como interfaz entre los módulos core y datos externos:
---
    API
    ↓
    RE
    ↓
    DM
---
    API
    ↓
    GE
    ↓
    DM

### Get graph data
[ ] Explicar la lógica implementada
Implementa la interfaz I_RoadGraphAccess.

### Get open data
Implementa la interfaz I_OpenDataAccess para obtener datos metereológicos y de vías públicas.
#### Fetch Weather Data
Obtiene los datos meteorológicos de interés de una plataforma de datos abiertos.
SafeNav v1.0 hace uso de Open-Meteo [ ] referencia.

#### Aggregate Weather Data
Convierte los datos meteorológicos obtenidos en un modelo de impacto meteorológico en la ruta.
Este módulo debe ser:
* stateless
* cacheable
* determinista
* independiente del routing
* optimizado para múltiples rutas en una sola request

La entrada del módulo es una región Area, solicitada por CA en I_OpenDataAccess.

#### Fetch Urban Data

## Context Analyzer
CA es el encargado de aplicar la lógica de evaluación de rutas y selección de la mejor. Cubre las siguientes funcionalidades:
* **F3** - **Evaluación contextual de rutas** 
* **F5** - **Asignación de puntuaciones de seguridad y confort**
* **F6** - **Priorización y recomendación de rutas**
