# Inicio Rápido - ADK News Scorer

## Instalación en 3 Pasos

### 1. Instalar dependencias
```bash
cd etl-movilidad-local
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
```

Edita `.env` y configura al menos:
```bash
GOOGLE_CLOUD_PROJECT=tu-proyecto-gcp
```

O para testing sin credenciales:
```bash
USE_MOCK_ADK=true
```

### 3. Ejecutar
```bash
cd src
python main.py
```

## Configuraciones Comunes

### Modo 1: Testing Local (sin Google Cloud)
```bash
# .env
USE_MOCK_ADK=true
```

**Características:**
- No requiere credenciales de Google Cloud
- Usa MockADKScorer (clasificación por keywords)
- Base de datos SQLite local
- Sin web scraping avanzado (scraping directo)

### Modo 2: Producción Mínima (con Google Cloud)
```bash
# .env
GOOGLE_CLOUD_PROJECT=tu-proyecto
USE_MOCK_ADK=false
```

**Características:**
- Requiere Google Cloud configurado
- Usa ADKScorerV3 con Gemini 2.0 Flash
- Base de datos SQLite local
- Scraping directo con BeautifulSoup

### Modo 3: Producción Completa (Cloud + Apify + Supabase)
```bash
# .env
GOOGLE_CLOUD_PROJECT=tu-proyecto
USE_MOCK_ADK=false
APIFY_API_TOKEN=tu-token-apify
USE_SUPABASE=true
SUPABASE_URL=tu-url-supabase
SUPABASE_KEY=tu-key-supabase
```

**Características:**
- Google Cloud ADK con Gemini
- Web scraping avanzado con Apify
- Base de datos Supabase (PostgreSQL cloud)
- Alertas configurables

### Modo 4: Producción con Email (todo activado)
```bash
# .env
GOOGLE_CLOUD_PROJECT=tu-proyecto
USE_MOCK_ADK=false
APIFY_API_TOKEN=tu-token-apify
USE_SUPABASE=true
SUPABASE_URL=tu-url-supabase
SUPABASE_KEY=tu-key-supabase
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password
ALERT_RECIPIENTS=dest1@example.com,dest2@example.com
```

## Autenticación Google Cloud

Si usas Google Cloud (USE_MOCK_ADK=false):

```bash
# Instalar Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Autenticarte
gcloud auth application-default login

# Verificar proyecto
gcloud config set project TU-PROYECTO-ID
```

## Verificar Instalación

```bash
cd etl-movilidad-local
bash verificar_estructura.sh
```

## Estructura de Salida

Después de ejecutar `main.py`:

```
etl-movilidad-local/
├── data/
│   └── etl_movilidad.db    # Base de datos SQLite (si no usas Supabase)
└── logs/
    ├── etl_pipeline.log    # Log completo del pipeline
    └── alerts.json         # Alertas de severidad alta/crítica
```

## Salida Esperada

```
==========================================
Starting ETL Pipeline execution
==========================================
STEP 1: Extracting news from sources...
✓ Extracted 45 news items

STEP 2: Deduplicating news...
✓ Deduplicated: 12 duplicates found, 33 unique items

STEP 3: Scoring news with ADK...
✓ Scored 33 items: 8 kept, 25 discarded

STEP 4: Saving to database...
✓ Saved 8 news items to database

STEP 5: Sending alerts for high severity news...
⚠️ ALERTA DE MOVILIDAD - HIGH
============================================================
Título: Cierre vial en Avenida 80 por obras...
Área: Avenida_80
Resumen: Cierre parcial afectará movilidad durante 3 días
============================================================
✓ Sent 2 alerts

==========================================
ETL Pipeline execution complete
Duration: 12.34 seconds
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

## Solución de Problemas

### Error: "GOOGLE_CLOUD_PROJECT environment variable required"
**Solución:** Configura `USE_MOCK_ADK=true` en `.env` para testing

### Error: "ModuleNotFoundError: No module named 'dotenv'"
**Solución:** `pip install -r requirements.txt`

### Error: "No module named 'google.adk'"
**Solución:** `pip install google-adk`

### Error al autenticar con Google Cloud
**Solución:**
```bash
gcloud auth application-default login
gcloud config set project TU-PROYECTO-ID
```

### No se extraen noticias
**Verificar:**
- Conexión a internet
- URLs de las fuentes están activas
- Si usas Apify, verificar que APIFY_API_TOKEN sea válido

## Siguientes Pasos

1. **Revisar logs**: `tail -f logs/etl_pipeline.log`
2. **Ver alertas**: `cat logs/alerts.json | python -m json.tool`
3. **Consultar BD**:
   - SQLite: `sqlite3 data/etl_movilidad.db "SELECT * FROM news_item LIMIT 10;"`
   - Supabase: Usar dashboard web o `scripts/query_supabase.py` (si existe)

## Documentación Adicional

- `README.md` - Descripción general del proyecto
- `FLUJO_DATOS.md` - Diagrama detallado del flujo de datos
- `LIMPIEZA_REALIZADA.md` - Archivos eliminados y estructura final

## Preguntas Frecuentes

**¿Puedo ejecutar sin Google Cloud?**
Sí, configura `USE_MOCK_ADK=true`

**¿Necesito Apify?**
No, el sistema hace fallback a scraping directo

**¿Necesito Supabase?**
No, por defecto usa SQLite local

**¿Cómo personalizo las fuentes de noticias?**
Edita `src/extractors_apify_simple.py` o `src/extractors.py`

**¿Cómo cambio el modelo de Gemini?**
Edita `GEMINI_MODEL` en `.env` (ej: `gemini-1.5-flash`, `gemini-2.0-flash`)
