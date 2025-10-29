# Changelog - ETL Movilidad Medellín

Todos los cambios notables del proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planeado
- Dashboard visual con Metabase/Grafana
- API pública REST para consultas
- Webhooks para integración externa
- ML para predicción de eventos recurrentes
- App móvil con notificaciones push
- Integración con Waze/Google Maps
- Análisis de sentimiento en comentarios
- Detección de tendencias con time-series

## [1.0.0] - 2024-01-15

### Inicial - Plan de Implementación Completo

#### Añadido

**Documentación Principal:**
- `README.md` - Visión general y quick start guide
- `PLAN_IMPLEMENTACION.md` - Plan detallado con 7 épicas y 26 historias de usuario
- `ARQUITECTURA.md` - Documentación técnica completa con diagramas
- `RUNBOOK.md` - Guía operativa y troubleshooting
- `RESUMEN_EJECUTIVO.md` - Resumen completo de entregables
- `INDEX.md` - Índice de todos los archivos del proyecto
- `CHANGELOG.md` - Este archivo

**Infraestructura como Código (Terraform):**
- `terraform/main.tf` - Orquestación principal
- `terraform/variables.tf` - Variables configurables
- `terraform/modules/database/main.tf` - Módulo Cloud SQL Postgres + pgvector
- `terraform/modules/cloud-run/main.tf` - Módulo genérico Cloud Run
- `terraform/modules/secrets/main.tf` - Módulo Secret Manager

**Base de Datos:**
- `db-migrations/001_initial_schema.sql` - Schema inicial con 3 tablas principales
  - Tabla `news_item` con 15 columnas
  - Tabla `news_embedding` con vector(768) para búsqueda semántica
  - Tabla `etl_execution_log` para auditoría
  - Funciones: `generate_hash_url()`, `update_updated_at_column()`

- `db-migrations/views/kpi_dashboard.sql` - 7 vistas de métricas
  - v_kpi_dashboard
  - v_severity_distribution
  - v_top_areas
  - v_recent_news_with_embeddings
  - v_daily_summary
  - v_embedding_coverage
  - v_source_performance

- `db-migrations/functions/semantic_search.sql` - 4 funciones de búsqueda
  - semantic_search()
  - semantic_search_with_filters()
  - find_similar_news()
  - get_news_by_tag_semantic()

- `db-migrations/maintenance/cleanup.sql` - Scripts de mantenimiento
  - Archivar noticias antiguas
  - Limpiar logs
  - Marcar duplicados
  - VACUUM y ANALYZE
  - Health checks

**Scripts de Operación:**
- `scripts/check-kpis.sh` - Consulta rápida de KPIs del sistema
- `scripts/test-e2e.sh` - Test end-to-end completo

**Configuración:**
- `.gitignore` - Exclusiones para Git
- `.env.example` - Plantilla de variables de entorno

**Directorios:**
- `n8n-workflows/` - Para almacenar workflows exportados
- `terraform/modules/` - Módulos reutilizables de IaC

#### Especificaciones Técnicas

**Arquitectura:**
- n8n como orquestador principal (cron cada 5 min)
- Microservicio ADK Scorer (FastAPI + Gemini 1.5 Flash)
- Microservicio Scraper (Express + Playwright)
- Postgres 15 + pgvector para búsqueda semántica
- Cloud Run para auto-scaling
- Secret Manager para gestión de credenciales

**Flujo ETL:**
1. Extracción (Twitter, Metro, medios locales)
2. Transformación (normalización, limpieza)
3. Deduplicación (hash_url)
4. Scoring ADK (keep/discard, severity, tags)
5. Persistencia (Postgres)
6. Enriquecimiento (embeddings)
7. Alertas (Slack/Telegram)

**Observabilidad:**
- Logs estructurados en Cloud Logging
- KPIs en vistas SQL
- Health checks automatizados
- Alertas en Slack/Telegram

**Seguridad:**
- Secrets en GCP Secret Manager
- OIDC authentication en Cloud Run
- SSL requerido en Postgres
- Rate limiting en Scraper

#### Métricas del Proyecto

- **Archivos entregados:** 28
- **Líneas de código/docs:** ~2,800
- **Épicas:** 7
- **Historias de usuario:** 26
- **Duración estimada:** 25 días (1 dev senior)
- **Costo mensual estimado:** $126-186

#### Criterios de Aceptación

✅ **Funcionales:**
- Workflow ejecuta cada 5 min
- Extracción multi-fuente
- Scoring ADK funcional
- Deduplicación por hash
- Embeddings generados
- Alertas en tiempo real
- Búsqueda semántica

✅ **No Funcionales:**
- Error rate < 2%
- Latencia ADK < 5s
- Latencia Scraper < 10s
- Auto-scaling configurado
- Backups diarios

✅ **Operacionales:**
- KPIs consultables
- Health checks automáticos
- Mantenimiento automático
- Documentación completa
- Plan de rollback

---

## Roadmap

### v1.1.0 (Q2 2024) - Mejoras Operacionales
- [ ] Dashboard visual (Metabase/Grafana)
- [ ] Más fuentes de datos (3-5 adicionales)
- [ ] Optimización de prompts ADK
- [ ] Tests unitarios completos para microservicios

### v1.2.0 (Q3 2024) - API Pública
- [ ] REST API para consultas
- [ ] Documentación OpenAPI/Swagger
- [ ] Rate limiting y authentication
- [ ] Webhooks para eventos

### v2.0.0 (Q4 2024) - ML y Predicción
- [ ] Modelo de predicción de eventos
- [ ] Detección de tendencias
- [ ] Análisis de sentimiento
- [ ] Dashboard predictivo

### v3.0.0 (2025) - Plataforma Completa
- [ ] App móvil (iOS/Android)
- [ ] Integración con Waze/Google Maps
- [ ] API de terceros (para otros sistemas)
- [ ] Expansión a otras ciudades

---

## Guía de Contribución

### Versionado

- **MAJOR** (X.0.0): Cambios incompatibles en API/arquitectura
- **MINOR** (1.X.0): Nuevas funcionalidades compatibles
- **PATCH** (1.0.X): Bug fixes y mejoras menores

### Proceso de Release

1. Actualizar `CHANGELOG.md` en sección `[Unreleased]`
2. Crear tag: `git tag -a v1.0.0 -m "Release 1.0.0"`
3. Mover cambios de `[Unreleased]` a nueva sección versionada
4. Desplegar a producción siguiendo `RUNBOOK.md`
5. Verificar smoke tests
6. Notificar en Slack

### Formato de Entradas

```markdown
### Añadido
- Nueva funcionalidad X que permite Y

### Cambiado
- Mejora en Z que aumenta performance en N%

### Deprecado
- Función W será removida en v2.0.0

### Removido
- Eliminado soporte para V

### Corregido
- Bug en S que causaba T

### Seguridad
- Parcheado CVE-XXXX-YYYY
```

---

## Contacto

- **Equipo:** ETL Movilidad Medellín
- **Slack:** #etl-movilidad
- **Email:** ops@example.com
- **Issues:** GitHub Issues

---

[Unreleased]: https://github.com/org/etl-movilidad-mde/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/org/etl-movilidad-mde/releases/tag/v1.0.0
