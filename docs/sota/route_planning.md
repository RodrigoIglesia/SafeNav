# Route Planning
La planificación de rutas es el proceso de determinar el trayecto óptimo entre un origen y un destino dentro de una red de transporte, considerando restricciones y objetivos específicos.

* Objetivos tradicionales: Minimizar la distancia y el tiempo de viaje (Dijkstra, 1959).
* Líneas recientes - optimización multiobjetivo: Necesidad de integrar múltiples criterios en la planificación, como coste, seguridad o factores ambientales, (Bast et al., 2016)


## Sistemas clásicos de planificación de rutas
### Google maps
Sistema de navegación de Google Inc.
Permite encontrar la ruta más rápida y conveniente entre los puntos A y B.
Las versiones más recientes han incorporado vista de calle (Street view), y posicionamiento de lugares de interés en el mapa, como hospitales, cafés, monumentos, etc.
Google maps calcula varias rutas "candidatas" y sugiere la "mejor" en función de varios criterios.

El sistema modela la **red vial como un grafo dirigido y ponderado*** en el que los nodos son las intersecciones, y las aristas son segmentos con pesos asociados a tiempo y distancia.

El sistema usa los siguientes algoritmos de planificación de rutas:
* Dijikstra: Emplea estructuras de grafos para encontrar el camino más corto entre dos puntos.
* A*: Añade heurísticas para acelerar la búsqueda.

Problema de los algoritmos clásicos: El coste computacional es extremadamente alto debido a los millones de nodos y aristas en los grafos. Se emplean técnicas de **Aceleración Algorítmica**:
* **Contraction Hirearchies, Geisberger et al. (2008)**: Procesa el grafo, elimina nodos y añade atajos. Reduce el tiempo de consulta.
* **ALT**: Añade landmarks y desigualdades triangulares para mejorar la heurística.
* **Transit Node Routing (TNR)**: Preprocesamiento que identifica “nodos de tránsito” clave en viajes largos, acelerando consultas interurbanas.
* **Combinaciones híbridas**: En la práctica, motores como Google Maps combinan varias de estas técnicas para balancear rapidez de consulta y memoria.

El algoritmo de Google Maps no solo busca la ruta más corta, selecciona rutas candidatas en función de distintos objetivos mediante **Selección Multiobjetivo**:
* **Objetivo Primario**: Minimizar ETA
* **Objetivos Secundarios**: Minimización de giros, seguridad, eficiencia energética.

Para Google, si dos rutas tienen ETAs similares, **se prioriza el objetivo secundario**.

### OpenStreetMap

## Algoritmos de planificación de rutas
A*
Dijkstra
## Limitaciones
Sistemas actuales no consideran factores ambientales

## Fuentes de datos
### Open Street Maps
API para obtener datos: https://overpass-turbo.eu/


## Algoritmos de planificación inteligentes


## Referencias
[1] Dijkstra, E. W. (1959). A note on two problems in connexion with graphs.

[2] Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A Formal Basis for the Heuristic Determination of Minimum Cost Paths.

[3] Bellman, R. (1958). On a routing problem.
Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. Numerische Mathematik, 1, 269–271.

[4] Delling, D., Pajor, T., Sanders, P., & Wagner, D. (2009). Engineering Route Planning Algorithms. In Algorithmics of Large and Complex Networks (pp. 117–139). Springer.

[5] Bast, H., Delling, D., Goldberg, A., Müller-Hannemann, M., Pajor, T., Sanders, P., Wagner, D., & Werneck, R. F. (2016). Route Planning in Transportation Networks. In Algorithm Engineering: Selected Results and Surveys (pp. 19–80). Springer.

[6] Zheng, Y., Capra, L., Wolfson, O., & Yang, H. (2014). Urban Computing: Concepts, Methodologies, and Applications. ACM Transactions on Intelligent Systems and Technology (TIST), 5(3), 38.

[7] Geisberger, R., Sanders, P., Schultes, D., & Delling, D. (2008). Contraction Hierarchies: Faster and Simpler Hierarchical Routing in Road Networks.

[8] Bast, H., Delling, D., Goldberg, A., Müller-Hannemann, M., Pajor, T., Sanders, P., Wagner, D., & Werneck, R. F. (2016). Route Planning in Transportation Networks. Algorithm Engineering.