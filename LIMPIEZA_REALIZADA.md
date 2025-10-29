# Resumen de Limpieza del Proyecto

## Análisis del Flujo de Datos

### Pipeline Principal (main.py)

```
1. EXTRACCIÓN
   └─> extractors_apify_simple.py (HybridApifyExtractor)
       ├─> Intenta Apify si APIFY_API_TOKEN existe
       └─> Fallback a extractors.py (NewsExtractor) si falla

2. DEDUPLICACIÓN
   └─> db.py (SQLite) o db_supabase.py (Supabase)
       └─> Verifica hash URL para evitar duplicados

3. SCORING CON ADK
   └─> adk_scorer_v3.py (ADKScorerV3) - Producción
       ├─> Google ADK + Gemini 2.0 Flash
       ├─> Usa prompts/system_prompt.py
       └─> Valida con schemas/scoring_schema.py (Pydantic)
   └─> adk_scorer.py (MockADKScorer) - Testing sin credenciales

4. ALMACENAMIENTO
   └─> db.py o db_supabase.py
       └─> Guarda solo noticias relevantes (keep=true)

5. ALERTAS
   └─> alert_manager.py
       └─> Envía alertas para severity high/critical
```

## Archivos Eliminados

### Documentación (11 archivos .md)
- ARQUITECTURA.md
- ANALISIS_MVP_LOCAL.md
- COMPARATIVA_FINAL.md
- CHANGELOG.md
- INDEX.md
- PLAN_DESPLIEGUE_GUIADO.md
- PLAN_IMPLEMENTACION.md
- PLAN_MVP_LOCAL.md
- RESUMEN_EJECUTIVO.md
- RESUMEN_ANALISIS_MVP.md
- RUNBOOK.md

### Infraestructura Cloud
- terraform/ (completo)
  - main.tf
  - variables.tf
  - modules/cloud-run/
  - modules/database/

### Migraciones de Base de Datos
- db-migrations/ (completo)
  - 001_initial_schema.sql
  - functions/semantic_search.sql
  - views/kpi_dashboard.sql
  - maintenance/cleanup.sql

### Scripts de Testing y Utilidades (20+ archivos)
- etl-movilidad-local/scripts/ (completo)
  - test_*.py (8 archivos de testing)
  - verificar_*.py (3 scripts de verificación)
  - db_stats.py
  - demo_full_pipeline.py
  - generate_test_news.py
  - init_database.py
  - list_available_models.py
  - migrate_sqlite_to_supabase.py
  - query_supabase.py
  - reset_database.py
  - clear_supabase.py
  - view_alerts.py
  - data/etl_movilidad.db (base de datos de ejemplo)

### Documentación Técnica Extensa
- etl-movilidad-local/docs/
  - SUPABASE_SETUP.md
- etl-movilidad-local/*.md (15 archivos)
  - FUNCIONAMIENTO_ADK.md
  - GUIA_COMPLETA_ADK.md
  - GUIA_APIFY_SCRAPING.md
  - INSTRUCCIONES_PRUEBA.md
  - GUIA_DESPLIEGUE.md
  - MIGRACION_ADK.md
  - INTEGRACION_PIPELINE.md
  - README.md (reemplazado)
  - README_ADK.md
  - README_SUPABASE.md
  - README_SCHEDULER.md
  - RESUMEN_INTEGRACION.md
  - RESUMEN_CAMBIOS.md
  - PROXIMOS_PASOS.md
  - Y otros...

### Schedulers y Automatización
- etl-movilidad-local/scheduler.py
- etl-movilidad-local/scheduler_advanced.py
- etl-movilidad-local/run_scheduler.bat
- etl-movilidad-local/src/scheduler.py

### SQL y Esquemas
- etl-movilidad-local/sql/
  - clear_database.sql
  - supabase_schema.sql

### Versiones Antiguas de Código
- etl-movilidad-local/src/adk_scorer_v2.py (versión incorrecta con google-generativeai)
- etl-movilidad-local/src/extractors_apify.py (versión compleja de Apify)

### Scripts de Shell
- scripts/test-e2e.sh
- scripts/check-kpis.sh

### Archivos de Configuración Duplicados
- .env.example (raíz) - duplicado
- .gitignore (raíz) - duplicado

## Archivos Mantenidos (17 archivos)

### Código Fuente Principal (13 archivos Python)
```
etl-movilidad-local/src/
├── main.py                      # 326 líneas - Pipeline ETL principal
├── extractors_apify_simple.py   # 262 líneas - Extractor híbrido Apify
├── extractors.py                # 230 líneas - Extractor directo (fallback)
├── adk_scorer_v3.py             # 278 líneas - Scorer ADK oficial
├── adk_scorer.py                # 243 líneas - Mock scorer para testing
├── alert_manager.py             # 293 líneas - Sistema de alertas
├── db.py                        # 243 líneas - Base de datos SQLite
├── db_supabase.py               # 352 líneas - Base de datos Supabase
├── prompts/
│   ├── __init__.py              # 1 línea
│   └── system_prompt.py         # 138 líneas - Prompts para ADK
└── schemas/
    ├── __init__.py              # 9 líneas
    └── scoring_schema.py        # 79 líneas - Schema Pydantic
```

### Configuración (4 archivos)
```
etl-movilidad-local/
├── requirements.txt             # Dependencias Python
├── .env.example                 # Template de variables de entorno
├── .gitignore                   # Archivos ignorados por git
└── data/.gitkeep                # Mantiene directorio data/
```

### Nueva Documentación (1 archivo)
```
README.md                        # Documentación concisa y práctica
```

## Estadísticas de Limpieza

- **Archivos eliminados**: ~80+ archivos
- **Carpetas eliminadas**: 5 carpetas completas (db-migrations, terraform, scripts, docs, sql)
- **Archivos mantenidos**: 17 archivos esenciales
- **Líneas de código**: 2,442 líneas (solo lo necesario)
- **Documentación**: Reducida de 15+ archivos MD a 1 README conciso

## Reducción de Complejidad

### Antes
- 80+ archivos
- Múltiples versiones del mismo código
- Documentación extensa y redundante
- Scripts de testing dispersos
- Infraestructura cloud completa
- Schedulers y automatización

### Después
- 17 archivos esenciales
- Solo versiones funcionales
- README único y claro
- Sin scripts de testing
- Sin infraestructura cloud
- Sin schedulers

## Conclusión

El proyecto ahora contiene **únicamente** los archivos necesarios para ejecutar `main.py`:

1. **Extracción**: extractors_apify_simple.py + extractors.py (fallback)
2. **Scoring**: adk_scorer_v3.py + adk_scorer.py (mock)
3. **Base de datos**: db.py + db_supabase.py (opcional)
4. **Alertas**: alert_manager.py
5. **Configuración**: prompts/ + schemas/ para ADK
6. **Dependencias**: requirements.txt + .env.example

El proyecto pasó de ser un sistema completo de producción con infraestructura cloud, migraciones, testing y documentación extensa, a ser un **script ETL mínimo y funcional** que puede ejecutarse localmente con las dependencias básicas.

## Para Ejecutar

```bash
cd etl-movilidad-local
pip install -r requirements.txt
cp .env.example .env
# Configurar .env con credenciales
cd src
python main.py
```
