# Flujo de Datos - ADK News Scorer

## Diagrama de Flujo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    INICIO: main.py                              │
│                    (ETLPipeline.run())                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1: EXTRACCIÓN DE NOTICIAS                                 │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ HybridApifyExtractor (extractors_apify_simple.py)      │     │
│  │                                                         │     │
│  │  ┌─────────────────┐                                   │     │
│  │  │ APIFY_API_TOKEN │                                   │     │
│  │  │    existe?      │                                   │     │
│  │  └────┬────────────┘                                   │     │
│  │       │                                                 │     │
│  │  ┌────▼────┐         ┌──────────────────┐            │     │
│  │  │   SÍ    │         │       NO         │            │     │
│  │  └────┬────┘         └────────┬─────────┘            │     │
│  │       │                       │                       │     │
│  │       ▼                       ▼                       │     │
│  │  SimpleApifyExtractor    NewsExtractor               │     │
│  │  (Apify Web Crawler)     (extractors.py)             │     │
│  │                                                         │     │
│  │  Fuentes:                                              │     │
│  │  • Metro de Medellín                                   │     │
│  │  • Alcaldía de Medellín                                │     │
│  │  • El Colombiano                                       │     │
│  │  • Minuto30                                            │     │
│  └────────────────────────┬───────────────────────────────┘     │
│                           │                                     │
│                    Retorna: List[Dict]                         │
│                    [{source, url, title, body, published_at}]  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2: DEDUPLICACIÓN                                          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ NewsDatabase o SupabaseNewsDatabase                    │     │
│  │ (db.py o db_supabase.py)                               │     │
│  │                                                         │     │
│  │  Para cada noticia:                                    │     │
│  │    hash_url = SHA256(url)                              │     │
│  │    if hash_url existe en DB:                           │     │
│  │       ⚠️  DUPLICADO - Descartar                        │     │
│  │    else:                                                │     │
│  │       ✓ ÚNICO - Continuar                              │     │
│  └────────────────────────┬───────────────────────────────┘     │
│                           │                                     │
│                    Retorna: unique_news[]                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 3: SCORING CON ADK                                        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ USE_MOCK_ADK?                                          │     │
│  └────┬───────────────────────────────────────────────────┘     │
│       │                                                         │
│  ┌────▼────┐         ┌──────────────────┐                     │
│  │   NO    │         │       SÍ         │                     │
│  └────┬────┘         └────────┬─────────┘                     │
│       │                       │                               │
│       ▼                       ▼                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ ADKScorerV3              MockADKScorer              │     │
│  │ (adk_scorer_v3.py)       (adk_scorer.py)            │     │
│  │                                                       │     │
│  │ ┌───────────────────┐    ┌──────────────────────┐   │     │
│  │ │ Google ADK        │    │ Heurísticas simples  │   │     │
│  │ │ + Gemini 2.0      │    │ (keywords en título) │   │     │
│  │ │                   │    │                      │   │     │
│  │ │ 1. system_prompt  │    │ Retorna:             │   │     │
│  │ │    (prompts/)     │    │ - keep: true/false   │   │     │
│  │ │                   │    │ - severity: medium   │   │     │
│  │ │ 2. build_user_    │    │ - tags: [mock]       │   │     │
│  │ │    prompt()       │    │ - score: 0.75        │   │     │
│  │ │                   │    │                      │   │     │
│  │ │ 3. Gemini API     │    └──────────────────────┘   │     │
│  │ │                   │                              │     │
│  │ │ 4. Valida con     │                              │     │
│  │ │    ScoringResponse│                              │     │
│  │ │    (schemas/)     │                              │     │
│  │ └───────────────────┘                              │     │
│  │                                                       │     │
│  │ Enriquece cada noticia con:                          │     │
│  │ • keep: bool - ¿Es relevante?                        │     │
│  │ • severity: low|medium|high|critical                 │     │
│  │ • tags: [lista de etiquetas]                         │     │
│  │ • area: Zona geográfica afectada                     │     │
│  │ • entities: [instituciones, lugares]                 │     │
│  │ • summary: Resumen del impacto                       │     │
│  │ • relevance_score: 0.0 - 1.0                         │     │
│  │ • reasoning: Justificación                           │     │
│  └───────────────────────┬───────────────────────────────┘     │
│                          │                                     │
│                  Filtra: keep == true                         │
│                  Retorna: scored_news[]                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 4: ALMACENAMIENTO EN BASE DE DATOS                        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ USE_SUPABASE?                                          │     │
│  └────┬───────────────────────────────────────────────────┘     │
│       │                                                         │
│  ┌────▼────┐         ┌──────────────────┐                     │
│  │   NO    │         │       SÍ         │                     │
│  └────┬────┘         └────────┬─────────┘                     │
│       │                       │                               │
│       ▼                       ▼                               │
│  ┌──────────────┐    ┌─────────────────────┐                 │
│  │ NewsDatabase │    │ SupabaseNewsDatabase│                 │
│  │ (db.py)      │    │ (db_supabase.py)    │                 │
│  │              │    │                     │                 │
│  │ SQLite local │    │ PostgreSQL Cloud    │                 │
│  │ data/        │    │ Supabase            │                 │
│  │ etl_movilidad│    │                     │                 │
│  │ .db          │    │                     │                 │
│  └──────┬───────┘    └──────────┬──────────┘                 │
│         │                       │                            │
│         └───────────┬───────────┘                            │
│                     │                                        │
│              INSERT INTO news_item                           │
│              Retorna: news_id                                │
└─────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 5: SISTEMA DE ALERTAS                                     │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ AlertManager / ConsoleOnlyAlertManager                 │     │
│  │ (alert_manager.py)                                     │     │
│  │                                                         │     │
│  │ Filtra: severity IN ('high', 'critical')               │     │
│  │                                                         │     │
│  │ Para cada alerta:                                      │     │
│  │  ┌──────────────────────────────────────────────┐     │     │
│  │  │ 1. Consola (siempre)                         │     │     │
│  │  │    Muestra: Emoji + Título + Área + Tags     │     │     │
│  │  │                                               │     │     │
│  │  │ 2. Archivo JSON (logs/alerts.json)           │     │     │
│  │  │    Append al archivo de alertas              │     │     │
│  │  │                                               │     │     │
│  │  │ 3. Email (si ENABLE_EMAIL_ALERTS=true)       │     │     │
│  │  │    SMTP: HTML + Plain Text                   │     │     │
│  │  └──────────────────────────────────────────────┘     │     │
│  │                                                         │     │
│  │ Marca en DB: UPDATE alerted = 1                        │     │
│  └────────────────────────┬───────────────────────────────┘     │
│                           │                                     │
│                    Retorna: alert_count                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 6: LOG DE EJECUCIÓN                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ db.log_execution(stats)                                │     │
│  │                                                         │     │
│  │ INSERT INTO execution_log:                             │     │
│  │  - execution_time                                      │     │
│  │  - news_extracted                                      │     │
│  │  - news_deduplicated                                   │     │
│  │  - news_scored                                         │     │
│  │  - news_kept                                           │     │
│  │  - news_discarded                                      │     │
│  │  - errors (si hay)                                     │     │
│  │  - duration_seconds                                    │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                      ┌──────────┐
                      │  FIN     │
                      │          │
                      │ Retorna: │
                      │  stats{} │
                      └──────────┘
```

## Componentes Clave

### 1. Extractores (Capa de Datos)
- **HybridApifyExtractor**: Usa Apify si token disponible, sino fallback
- **SimpleApifyExtractor**: Web scraping con Apify Website Content Crawler
- **NewsExtractor**: Scraping directo con BeautifulSoup + Requests

### 2. Base de Datos (Capa de Persistencia)
- **NewsDatabase**: SQLite local (por defecto)
- **SupabaseNewsDatabase**: PostgreSQL cloud (opcional)

### 3. Scorer ADK (Capa de Inteligencia)
- **ADKScorerV3**: Google ADK + Gemini 2.0 Flash (producción)
- **MockADKScorer**: Clasificador simple para testing

### 4. Alertas (Capa de Notificaciones)
- **AlertManager**: Consola + JSON + Email
- **ConsoleOnlyAlertManager**: Solo consola + JSON

### 5. Configuración
- **system_prompt.py**: Instrucciones para el agente ADK
- **scoring_schema.py**: Validación Pydantic del output

## Variables de Entorno Importantes

```bash
# Modo de operación
USE_MOCK_ADK=false          # true = testing sin Google Cloud
USE_SUPABASE=false          # true = usa Supabase, false = SQLite

# Google Cloud (obligatorio si USE_MOCK_ADK=false)
GOOGLE_CLOUD_PROJECT=tu-proyecto
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash

# Apify (opcional, mejora scraping)
APIFY_API_TOKEN=tu-token

# Email (opcional)
ENABLE_EMAIL_ALERTS=false
```

## Flujo de Decisiones

### ¿Qué extractor usar?
```
if APIFY_API_TOKEN existe:
    try: SimpleApifyExtractor
    except: NewsExtractor (fallback)
else:
    NewsExtractor
```

### ¿Qué scorer usar?
```
if USE_MOCK_ADK == true:
    MockADKScorer
else:
    ADKScorerV3
```

### ¿Qué base de datos?
```
if USE_SUPABASE == true:
    SupabaseNewsDatabase
else:
    NewsDatabase (SQLite)
```

### ¿Enviar alertas?
```
if ENABLE_EMAIL_ALERTS == true:
    AlertManager (consola + JSON + email)
else:
    ConsoleOnlyAlertManager (consola + JSON)
```

## Salida del Pipeline

### Console Output
```
==========================================
PIPELINE EXECUTION SUMMARY
==========================================
Extracted:      45
Deduplicated:   12
Scored:         33
Kept:           8
Discarded:      25
Alerted:        2
Duration:       12.34s
==========================================
```

### Archivos Generados
```
logs/
├── etl_pipeline.log        # Log completo del pipeline
└── alerts.json             # Alertas de alta severidad

data/
└── etl_movilidad.db        # Base de datos SQLite (si USE_SUPABASE=false)
```

### Base de Datos

**Tabla: news_item**
- Noticias procesadas y clasificadas como relevantes (keep=true)

**Tabla: execution_log**
- Historial de ejecuciones del pipeline con estadísticas
