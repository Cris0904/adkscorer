# Índice de Archivos - ETL Movilidad Medellín

Este proyecto contiene **26 archivos** organizados en una estructura modular y escalable.

## Estructura Completa

```
etl-movilidad-medellin/
│
├── README.md                               # Visión general y quick start
├── PLAN_IMPLEMENTACION.md                  # Plan detallado: 7 épicas, 26 historias, tareas
├── ARQUITECTURA.md                         # Diagramas, componentes, flujos de datos
├── RUNBOOK.md                              # Guía operativa y troubleshooting
├── RESUMEN_EJECUTIVO.md                    # Resumen completo de entregables
├── INDEX.md                                # Este archivo (índice de contenidos)
│
├── terraform/                              # Infraestructura como Código
│   ├── main.tf                             # Orquestación principal de Terraform
│   ├── variables.tf                        # Variables configurables
│   │
│   └── modules/                            # Módulos reutilizables
│       ├── database/
│       │   └── main.tf                     # Cloud SQL Postgres + pgvector
│       │
│       ├── cloud-run/
│       │   └── main.tf                     # Cloud Run service (genérico)
│       │
│       └── secrets/
│           └── main.tf                     # Secret Manager
│
├── db-migrations/                          # SQL Schema y Migraciones
│   ├── 001_initial_schema.sql              # Tablas, índices, funciones base
│   │
│   ├── views/
│   │   └── kpi_dashboard.sql               # 6 vistas de métricas y KPIs
│   │
│   ├── functions/
│   │   └── semantic_search.sql             # 4 funciones de búsqueda semántica
│   │
│   └── maintenance/
│       └── cleanup.sql                     # Scripts de mantenimiento automático
│
├── scripts/                                # Scripts de Operación
│   ├── check-kpis.sh                       # Consulta rápida de KPIs
│   └── test-e2e.sh                         # Test end-to-end completo
│
└── n8n-workflows/                          # Workflows de n8n (para exportar)
    ├── (etl-movilidad-main.json)           # Workflow principal (diseño en PLAN)
    ├── (etl-movilidad-health.json)         # Health checks (diseño en PLAN)
    └── (etl-movilidad-maintenance.json)    # Mantenimiento (diseño en PLAN)
```

---

## Documentación Principal (5 archivos)

### 1. README.md
**Propósito:** Punto de entrada al proyecto
**Contenido:**
- Resumen ejecutivo del sistema
- Arquitectura en diagrama ASCII
- Quick start guide
- Estructura del proyecto
- Comandos básicos de operación
- Costos estimados
- Troubleshooting básico
- Contactos

**Audiencia:** Desarrolladores, DevOps, PM

---

### 2. PLAN_IMPLEMENTACION.md (Documento Principal)
**Propósito:** Plan de implementación ejecutable y detallado
**Contenido:**
- **Resumen Ejecutivo:** Duración 3-4 semanas, 1 dev senior
- **Pre-requisitos:** 20+ items verificables
- **7 Épicas desglosadas:**
  - EP-01: Infraestructura Base (4 historias, 3 días)
  - EP-02: Base de Datos (3 historias, 2 días)
  - EP-03: Microservicio ADK Scorer (4 historias, 5 días)
  - EP-04: Microservicio Scraper (3 historias, 3 días)
  - EP-05: Workflows n8n (5 historias, 6 días)
  - EP-06: Observabilidad (3 historias, 2 días)
  - EP-07: Testing & Validación (4 historias, 4 días)

**Total:** 26 Historias de Usuario, cada una con:
- Estimación en horas
- Prioridad (P0, P1, P2)
- Tareas con checklist ejecutables
- Código de ejemplo incluido
- Comandos de referencia
- Definition of Done (DoD)

**Extras:**
- Guía de despliegue paso a paso
- Comandos de rollback
- Costos detallados
- Criterios de aceptación finales
- Próximos pasos post-MVP

**Audiencia:** Desarrolladores implementando el proyecto

**Páginas:** ~150+ líneas markdown

---

### 3. ARQUITECTURA.md
**Propósito:** Documentación técnica profunda
**Contenido:**
- Diagrama de arquitectura completo (ASCII art)
- **Componentes detallados:**
  - n8n Orquestador (workflows, configuración)
  - ADK Scorer (API, prompts, lógica)
  - Scraper Avanzado (Playwright, rate limiting)
  - Base de Datos (esquema, índices, vistas, funciones)
  - Observabilidad (logs, métricas, alertas)

- **Flujo de datos en 9 fases:**
  1. Extracción
  2. Transformación
  3. Deduplicación
  4. Scoring ADK
  5. Filtrado
  6. Carga
  7. Enriquecimiento (embeddings)
  8. Alertas
  9. Logging

- **Patrones de diseño aplicados:**
  - Pipeline Pattern
  - Circuit Breaker
  - Idempotencia
  - Event-Driven
  - Observer Pattern
  - Adapter Pattern

- **Escalabilidad y Resiliencia:**
  - Horizontal scaling
  - Vertical scaling
  - Bottlenecks identificados
  - Manejo de errores
  - Backups

- **Referencias técnicas y repositorios**

**Audiencia:** Arquitectos, Tech Leads, Desarrolladores senior

**Páginas:** ~200+ líneas markdown

---

### 4. RUNBOOK.md
**Propósito:** Guía operativa para administradores
**Contenido:**
- **Inicio Rápido:** Accesos, verificación de salud
- **Operaciones Diarias:**
  - Monitoreo matutino (checklist)
  - Dashboards y métricas
  - Checklist semanal

- **Troubleshooting (6 escenarios comunes):**
  1. ETL no ejecuta
  2. Items no se insertan
  3. Alta latencia
  4. Scraper bloqueado
  5. Embeddings no se generan
  6. Alertas no llegan
  - Cada escenario con: Síntoma, Diagnóstico, Soluciones

- **Mantenimiento:**
  - Rotación de secrets
  - Limpieza de DB
  - Actualización de servicios
  - Escalado de recursos

- **Incidentes Comunes:**
  - Cloud Run down
  - Database full
  - Alta error rate
  - Template de postmortem

- **Contactos y Escalación**

**Audiencia:** SRE, DevOps, On-Call Engineers

**Páginas:** ~180+ líneas markdown

---

### 5. RESUMEN_EJECUTIVO.md
**Propósito:** Resumen completo de todos los entregables
**Contenido:**
- **Checklist de 16 secciones:**
  1. Documentación Principal
  2. Infraestructura como Código
  3. Base de Datos
  4. Scripts de Operación
  5. Especificaciones de Microservicios
  6. Workflows n8n
  7. Observabilidad
  8. Testing
  9. Seguridad
  10. Costos y Escalabilidad
  11. Próximos Pasos
  12. Criterios de Aceptación
  13. Archivos Entregados
  14. Cómo Usar Este Proyecto
  15. Contacto
  16. Conclusión

- **Métricas del proyecto:**
  - 26 archivos entregados
  - 25 días estimados
  - $126-186/mes costo
  - 64 items de validación

**Audiencia:** Stakeholders, PM, Tech Leads

**Páginas:** ~300+ líneas markdown

---

## Infraestructura como Código (7 archivos)

### terraform/main.tf
**Propósito:** Orquestación principal de Terraform
**Contenido:**
- Provider GCP
- Backend GCS
- Invocación de módulos (database, cloud-run, secrets)
- Service accounts e IAM
- Outputs (URLs, connection strings)

**Recursos creados:**
- google_service_account.etl_runner
- google_project_iam_member (Cloud SQL, Secret Manager, Logs)
- Módulos: database, secrets, adk_scorer, scraper

**Líneas:** ~120

---

### terraform/variables.tf
**Propósito:** Variables configurables
**Contenido:**
- project_id, region
- Database: db_name, db_user, db_password
- Cloud Run images
- Secrets: slack, telegram, twitter, openai
- Authorized networks

**Variables:** 10 variables (3 sensibles)

**Líneas:** ~70

---

### terraform/modules/database/main.tf
**Propósito:** Módulo de Cloud SQL Postgres
**Contenido:**
- google_sql_database_instance (Postgres 15)
- Flags: pgvector habilitado
- Backup configuration (PITR, 30 días retention)
- IP configuration (SSL required)
- Insights config
- google_sql_database
- google_sql_user

**Outputs:**
- connection_name
- connection_string
- public_ip
- private_ip

**Líneas:** ~100

---

### terraform/modules/cloud-run/main.tf
**Propósito:** Módulo genérico de Cloud Run
**Contenido:**
- google_cloud_run_v2_service
- Scaling config (min/max instances)
- Resources (CPU, memory)
- Environment variables
- Secret environment variables
- Health checks (startup, liveness)
- IAM (opcional public access)

**Parámetros:** 12 variables configurables
**Outputs:** service_url, service_name

**Líneas:** ~130

---

### terraform/modules/secrets/main.tf
**Propósito:** Módulo de Secret Manager
**Contenido:**
- google_secret_manager_secret (loop sobre secrets map)
- google_secret_manager_secret_version
- Replication auto
- Labels (managed_by, project)

**Outputs:**
- secret_ids (map)
- secret_versions (map)

**Líneas:** ~50

---

## Base de Datos (4 archivos SQL)

### db-migrations/001_initial_schema.sql
**Propósito:** Migración inicial del esquema
**Contenido:**
- CREATE EXTENSION vector
- **Tabla news_item:**
  - 15 columnas (id, source, url, hash_url, title, body, published_at, area, entities, tags, severity, relevance_score, summary, status, timestamps)
  - 7 índices (B-tree, GIN para arrays)
  - Constraints (CHECK, UNIQUE)

- **Tabla news_embedding:**
  - 5 columnas (id, news_id, embedding vector(768), model, created_at)
  - 2 índices (news_id, IVFFlat para vector)

- **Tabla etl_execution_log:**
  - 10 columnas (execution_id, source, items_*, errors, duration, timestamps)
  - 3 índices

- **Funciones:**
  - update_updated_at_column() + trigger
  - generate_hash_url()

- **Comments en todas las tablas y columnas clave**

**Líneas:** ~140

---

### db-migrations/views/kpi_dashboard.sql
**Propósito:** Vistas de métricas y KPIs
**Contenido:**
- **v_kpi_dashboard:** Métricas por hora/fuente (últimas 24h)
- **v_severity_distribution:** Distribución de severidad (7 días)
- **v_top_areas:** Top 10 áreas con más incidentes
- **v_recent_news_with_embeddings:** Noticias con estado de embeddings
- **v_daily_summary:** Resumen diario de performance (30 días)
- **v_embedding_coverage:** Cobertura de embeddings por día/modelo
- **v_source_performance:** Performance con health score (7 días)

**Total:** 7 vistas con agregaciones complejas

**Líneas:** ~180

---

### db-migrations/functions/semantic_search.sql
**Propósito:** Funciones de búsqueda semántica
**Contenido:**
- **semantic_search():** Búsqueda básica por similitud coseno
  - Parámetros: query_embedding, match_threshold, match_count
  - Returns: news_id, title, body, published_at, source, area, severity, tags, similarity

- **semantic_search_with_filters():** Con filtros avanzados
  - Parámetros adicionales: filter_source, filter_severity, filter_area, date_from, date_to

- **find_similar_news():** Encuentra noticias similares a una dada
  - Parámetro: target_news_id
  - Returns: Top 5 similares

- **get_news_by_tag_semantic():** Híbrido tags + semántica
  - Parámetros: search_tags[], query_embedding (opcional)
  - Soporta tag-only o tag+embedding

**Total:** 4 funciones PL/pgSQL

**Líneas:** ~160

---

### db-migrations/maintenance/cleanup.sql
**Propósito:** Scripts de mantenimiento
**Contenido:**
- **Archive Old News:** > 90 días → status='archived'
- **Delete Old Logs:** > 30 días
- **Mark Duplicates:** ROW_NUMBER() por hash_url
- **Vacuum and Analyze:** Optimización de tablas
- **Delete Orphaned Embeddings:** Safeguard
- **Rebuild Vector Index:** REINDEX CONCURRENTLY
- **Database Statistics:** Resumen de tamaño/rows
- **Check for Missing Embeddings:** Noticias sin embeddings
- **Severity Distribution Check:** Validación de distribución
- **Index Health Check:** pg_stat_user_indexes

**Total:** 10 scripts de mantenimiento

**Líneas:** ~200

---

## Scripts de Operación (2 archivos)

### scripts/check-kpis.sh
**Propósito:** Consulta rápida de KPIs
**Contenido:**
- Verificación de DATABASE_URL
- 5 consultas SQL:
  1. KPIs últimas 24h por fuente
  2. Distribución de severidad (7d)
  3. Top 10 áreas afectadas
  4. Estado de embeddings
  5. Resumen general
- Output con colores (GREEN, YELLOW, RED)
- Formato tabular con psql

**Uso:**
```bash
export DATABASE_URL="postgresql://..."
./scripts/check-kpis.sh
```

**Líneas:** ~110 (bash)

---

### scripts/test-e2e.sh
**Propósito:** Test end-to-end del sistema
**Contenido:**
- 7 fases de testing:
  1. Verificar servicios GCP
  2. Generar token OIDC
  3. Health checks (ADK Scorer, Scraper)
  4. Test ADK Scorer con noticia real
  5. Test DB connection
  6. Test data insertion
  7. Cleanup de datos de prueba

- Validaciones:
  - HTTP status codes (200 OK)
  - JSON parsing (keep=true esperado)
  - DB connectivity
  - INSERT con RETURNING id

- Output detallado con colores
- Exit codes apropiados (0 success, 1 error)

**Uso:**
```bash
export DATABASE_URL="postgresql://..."
export GCP_PROJECT_ID="etl-movilidad-mde"
./scripts/test-e2e.sh
```

**Líneas:** ~180 (bash)

---

## Directorio n8n-workflows/

**Propósito:** Almacenar workflows exportados de n8n
**Contenido esperado:**
- `etl-movilidad-main.json` - Workflow principal
- `etl-movilidad-health.json` - Health checks
- `etl-movilidad-maintenance.json` - Mantenimiento

**Nota:** Los workflows están diseñados en detalle en `PLAN_IMPLEMENTACION.md` sección EP-05. Una vez implementados en n8n UI, deben ser exportados y guardados aquí para versionamiento.

**Líneas:** ~0 (directorio vacío, para ser llenado)

---

## Estadísticas del Proyecto

### Por Tipo de Archivo

| Tipo | Archivos | Propósito |
|------|----------|-----------|
| Documentación (.md) | 6 | Guías, planes, arquitectura |
| Terraform (.tf) | 5 | Infraestructura como código |
| SQL (.sql) | 4 | Schema, vistas, funciones, mantenimiento |
| Bash (.sh) | 2 | Scripts de operación |
| Directorios | 9 | Organización modular |
| **TOTAL** | **26** | **Sistema completo** |

### Líneas de Código/Documentación

| Categoría | Líneas Aprox. |
|-----------|---------------|
| Documentación (Markdown) | ~1,200 |
| Terraform (HCL) | ~470 |
| SQL | ~680 |
| Bash | ~290 |
| **TOTAL** | **~2,640 líneas** |

### Contenido por Sección

| Sección | Archivos | Completitud |
|---------|----------|-------------|
| Documentación | 6/6 | ✅ 100% |
| IaC (Terraform) | 5/5 | ✅ 100% |
| Base de Datos | 4/4 | ✅ 100% |
| Scripts | 2/2 | ✅ 100% |
| Workflows n8n | 0/3 | ⚠️ 0% (diseño completo, pendiente export) |

**Nota:** Los workflows n8n están completamente diseñados en `PLAN_IMPLEMENTACION.md` con nodos, configuración y código. Solo falta implementarlos en n8n UI y exportar los JSONs.

---

## Cómo Navegar Este Proyecto

### Para Implementación Rápida:
1. **Leer:** `README.md` (10 min)
2. **Seguir:** `PLAN_IMPLEMENTACION.md` paso a paso (25 días)
3. **Consultar:** `ARQUITECTURA.md` cuando tengas dudas de diseño
4. **Usar:** `RUNBOOK.md` para troubleshooting

### Para Entendimiento de Arquitectura:
1. **Leer:** `ARQUITECTURA.md` (30-40 min)
2. **Revisar:** Diagramas de flujo de datos
3. **Explorar:** Archivos SQL en `db-migrations/`
4. **Estudiar:** Módulos Terraform en `terraform/modules/`

### Para Operación y Mantenimiento:
1. **Leer:** `RUNBOOK.md` (30 min)
2. **Ejecutar:** `./scripts/check-kpis.sh` diariamente
3. **Usar:** Checklist de troubleshooting cuando haya problemas
4. **Seguir:** Procedimientos de rotación de secrets

### Para Stakeholders y PM:
1. **Leer:** `RESUMEN_EJECUTIVO.md` (15 min)
2. **Revisar:** Costos estimados
3. **Verificar:** Criterios de aceptación
4. **Planificar:** Próximos pasos del roadmap

---

## Dependencias Externas

### Servicios GCP:
- Cloud SQL (Postgres 15)
- Cloud Run
- Secret Manager
- Cloud Logging
- Cloud Monitoring

### Servicios Externos:
- n8n (Railway/Render/self-hosted)
- OpenAI API (embeddings)
- Twitter API (opcional)
- Slack (alertas)
- Telegram (alertas)

### Herramientas de Desarrollo:
- Terraform >= 1.5
- gcloud CLI
- psql (PostgreSQL client)
- Node.js >= 18 (para scraper)
- Python >= 3.11 (para ADK scorer)

---

## Licencia

MIT License - Ver README.md

---

## Versión

**Versión del Proyecto:** 1.0.0
**Fecha de Creación:** 2024-01-15
**Última Actualización:** 2024-01-15

---

## Autores

- **Diseño y Arquitectura:** Vibe Kanban
- **Implementación de Plan:** Claude Code + ADK
- **Revisión Técnica:** [Tu equipo]

---

**Fin del Índice**
