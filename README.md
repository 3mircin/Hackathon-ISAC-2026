# ⚽ Club América Analytics — ISAC 2026 Hackathon

[![Next.js](https://img.shields.io/badge/Web-Next.js-black?style=flat&logo=next.js)](https://jardine-hackathon-isac-2026.vercel.app/)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57?style=flat&logo=sqlite)](https://www.sqlite.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Vercel](https://img.shields.io/badge/Vercel-Deployed-000000?style=flat&logo=vercel)](https://jardine-hackathon-isac-2026.vercel.app/)

Repositorio del proyecto desarrollado para el **ISAC 2026 Sports Analytics Hackathon (Club América)**. Este proyecto integra una **plataforma web interactiva de analítica táctica** alimentada por un **pipeline de ingeniería de datos (ETL)** diseñado para procesar, estructurar y consultar datos de eventos orientados al modelo de juego del director técnico André Jardine[cite: 1, 2, 3].

🌐 **Plataforma Web Interactiva:** [https://jardine-hackathon-isac-2026.vercel.app/](https://jardine-hackathon-isac-2026.vercel.app/)

---

## 📌 Resumen del Proyecto

El objetivo del proyecto fue transformar registros de eventos en métricas tácticas accionables y visualizaciones intuitivas para el análisis de rendimiento deportivo. 

A través de un pipeline personalizado desarrollado en Python, se procesaron encuentros de la Liga MX para extraer patrones tácticos clave[cite: 1, 2, 3]:

* **Generación de Ocasiones y $xG$:** Análisis de la calidad de remates, carril de creación donde se encontraba el jugador al momento de la ocasión/gol (izquierdo, centro, derecho) y contribución de pases clave[cite: 3].
* **Progresión de Balón:** Medición de pases progresivos calculando la reducción de distancia a puerta a través de coordenadas $(x, y)$, cambios de juego, centros y pases filtrados[cite: 3].
* **Fase Defensiva y Presión:** Registro de acciones defensivas por zona (tercio defensivo, área de penal, presión alta) y efectividad en duelos/recuperaciones[cite: 3].
* **Transiciones Ataque-Defensa:** Evaluación del $xG$ generado y velocidad de remate tras recuperaciones tras pérdida o recuperaciones en campo rival[cite: 3].
* **Análisis por Ventanas de Tiempo:** Micro-análisis del rendimiento de jugadores en intervalos de 5 minutos según el estado del partido (ganando, empatando, perdiendo)[cite: 3].

---
## 🏗️ Arquitectura de Ingeniería de Datos & Pipeline ETL

El desarrollo se estructuró en tres capas principales de ingeniería de software y analítica deportiva:

```text
┌─────────────────────────┐
│ Extracción & Filtrado   │ ──► Selección de partidos y eventos del DT objetivo
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Normalización & ETL     │ ──► Limpieza de caracteres, estandarización de campos,
└────────────┬────────────┘     cálculo de coordenadas (x, y) y tiempos de juego
             │
             ▼
┌─────────────────────────┐
│ Modelo Relacional SQL   │ ──► Indexación y estructuración en esquema
└────────────┬────────────┘     multitabla optimizado para analítica
             │
             ▼
┌─────────────────────────┐
│ Plataforma Web Dashboard│ ──► Visualización de métricas tácticas y dashboards
└─────────────────────────┘
```
---

### Principales Funcionalidades del Pipeline:
1. **Atomicidad y Gestión de Descargas:** Guardado atómico de archivos para garantizar la integridad de los datos procesados[cite: 2].
2. **Normalización Lingüística:** Procesamiento de nombres de directores técnicos y equipos mediante normalización Unicode (NFKD) para eliminar tildes y caracteres especiales[cite: 1, 2].
3. **Ubicación en Ocasiones de Gol:** Clasificación espacial por carril (izquierdo, central, derecho) según la posición del jugador al registrarse un remate o gol[cite: 3].

---

## 🗄️ Diseño del Esquema Relacional (`schema.sql`)

Para permitir consultas complejas con tiempos de respuesta óptimos en el dashboard, se diseñó un modelo relacional en SQLite cuya definición de tablas, índices y vistas se encuentra documentada en el archivo [`schema.sql`](./schema.sql):

* **`partidos`**: Información general de los encuentros, fechas y rivales[cite: 3].
* **`eventos`**: Tabla principal con todos los eventos registrados, coordenadas iniciales/finales, indicador de presión y patrón de juego[cite: 3].
* **`pases`**: Atributos analíticos de pase (distancia, ángulo, pase progresivo, *shot assist*, *goal assist*, centros, cambios de juego)[cite: 3].
* **`remates`**: Métricas de tiro, Expected Goals ($xG$), carril de creación del remate, técnica utilizada y parte del cuerpo[cite: 3].
* **`acciones_defensivas`**: Cobertura defensiva, presiones, intercepciones y recuperaciones divididas por tercio de campo[cite: 3].
* **`posesiones`**: Secuencias de posesión, número de pases/conducciones, duración en segundos y detección de recuperaciones en zona alta[cite: 3].
* **`transiciones`**: Evaluación de secuencias de ataque inmediato tras recuperación de balón (tiempo hasta el tiro, pases previos y $xG$ acumulado)[cite: 3].
* **`features_jugador_ventana`**: Agregación de métricas individuales en bloques de 5 minutos cruzados con el estado dinámico del marcador[cite: 3].
* **Vistas Analíticas (`vw_*`)**: Vistas SQL precalculadas (`vw_posesiones_analiticas`, `vw_transiciones`, `vw_jugador_partido`) para simplificar el consumo de datos desde la interfaz web[cite: 3].

---
## 🌐 Aplicación Web
La interfaz gráfica permite consultar de forma dinámica las métricas consolidadas por el pipeline:

Dashboards Interactivos: Gráficos tácticos de rendimiento colectivo e individual.

Mapas y Visualizaciones: Representación gráfica de zonas de influencia, pases y remates.

Filtros por Partido y Rival: Exploración comparativa entre encuentros.

👉 Visita la plataforma: https://jardine-hackathon-isac-2026.vercel.app/
---
## 🔒 Aviso de Privacidad y Términos de la Competencia
Propiedad de los Datos: Los datos utilizados para la construcción de este análisis son propiedad exclusiva de ISAC 2026 y sus proveedores oficiales. No están incluidos en este repositorio ni se distribuyen públicamente en cumplimiento con las políticas de privacidad y uso de la competencia.

Propiedad Intelectual: El código fuente correspondiente a la aplicación web, el diseño del esquema de base de datos (schema.sql) y la arquitectura del pipeline son de la autoría de sus creadores.
---

## 📁 Estructura del Repositorio

```text
├── schema.sql                 # Estructura DDL limpia de la base de datos (Tablas, Índices, Vistas)
├── Db.py                      # Pipeline ETL para procesamiento de eventos y cálculo de métricas
├── Renombrar.py               # Script de ordenamiento y estandarización de archivos
└── README.md                  # Documentación del proyecto

