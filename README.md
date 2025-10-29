# ADK News Scorer - Proyecto Limpio

Este proyecto es un agente ADK (Agent Development Kit) de Google que analiza noticias de movilidad en Medellín mediante web scraping y las clasifica por relevancia.

## Estructura del Proyecto

```
etl-movilidad-local/
├── src/
│   ├── main.py                      # Script principal del ETL
│   ├── extractors_apify_simple.py   # Extractor con Apify (prioritario)
│   ├── extractors.py                # Extractor directo (fallback)
│   ├── adk_scorer_v3.py             # Scorer ADK con Google Gemini
│   ├── adk_scorer.py                # Mock scorer para testing
│   ├── alert_manager.py             # Sistema de alertas
│   ├── db.py                        # Base de datos SQLite
│   ├── db_supabase.py               # Base de datos Supabase (opcional)
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system_prompt.py         # Prompts para el ADK
│   └── schemas/
│       ├── __init__.py
│       └── scoring_schema.py        # Schema Pydantic para validación
├── data/                            # Directorio para SQLite DB
├── requirements.txt                 # Dependencias Python
└── .env.example                     # Template de variables de entorno

```

## Flujo de Datos

1. **Extracción** (`extractors_apify_simple.py` o `extractors.py`)
   - Scraping de noticias de múltiples fuentes
   - Normalización de datos

2. **Deduplicación** (`db.py` o `db_supabase.py`)
   - Hash URL para evitar duplicados
   - Consulta a base de datos

3. **Scoring con ADK** (`adk_scorer_v3.py`)
   - Análisis con Google Gemini via ADK
   - Clasificación por relevancia, severidad y área
   - Extracción de entidades y tags

4. **Almacenamiento** (`db.py` o `db_supabase.py`)
   - Guarda noticias relevantes (keep=true)
   - Log de ejecuciones

5. **Alertas** (`alert_manager.py`)
   - Notificaciones para severidad high/critical
   - Consola, archivo JSON y email (opcional)

## Instalación

```bash
cd etl-movilidad-local
pip install -r requirements.txt
```

## Configuración

Copia `.env.example` a `.env` y configura:

```bash
# Google Cloud (para ADK Scorer)
GOOGLE_CLOUD_PROJECT=tu-proyecto
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash

# Apify (para scraping, opcional)
APIFY_API_TOKEN=tu-token

# Base de datos (opcional, por defecto usa SQLite)
USE_SUPABASE=false
SUPABASE_URL=tu-url
SUPABASE_KEY=tu-key

# Testing (sin credenciales de Google Cloud)
USE_MOCK_ADK=false

# Alertas Email (opcional)
ENABLE_EMAIL_ALERTS=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email
SMTP_PASSWORD=tu-password
ALERT_RECIPIENTS=email1@example.com,email2@example.com
```

## Uso

### Modo Producción (con Google Cloud ADK)

```bash
cd etl-movilidad-local/src
python main.py
```

### Modo Testing (sin credenciales)

```bash
cd etl-movilidad-local/src
USE_MOCK_ADK=true python main.py
```

## Dependencias Principales

- `google-adk` - Google Agent Development Kit
- `google-cloud-aiplatform` - Vertex AI
- `pydantic` - Validación de schemas
- `apify-client` - Web scraping (opcional)
- `supabase` - Base de datos cloud (opcional)
- `requests`, `beautifulsoup4`, `feedparser` - Web scraping directo

## Archivos Eliminados

Se removieron archivos innecesarios para el funcionamiento básico:
- Documentación extensa (*.md en raíz)
- Scripts de testing y utilidades
- Migraciones de base de datos
- Terraform para despliegue
- Schedulers y automatización
- Versiones antiguas del código (adk_scorer_v2.py, extractors_apify.py)

## Notas

- El proyecto usa SQLite por defecto (base de datos local en `data/etl_movilidad.db`)
- Para producción se recomienda Supabase (configurar `USE_SUPABASE=true`)
- El extractor intentará usar Apify si `APIFY_API_TOKEN` está configurado, sino usará scraping directo
- Los logs se guardan en `logs/etl_pipeline.log` y `logs/alerts.json`
