# Arquitectura - ETL Movilidad Medellín

## Visión General

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FUENTES DE DATOS                              │
├──────────────┬──────────────────┬──────────────────┬────────────────┤
│ Twitter/X API│  Metro Medellín  │ Medios Locales   │ Waze/RSS      │
│              │  (Web/RSS)       │ (RSS/HTML)       │               │
└──────┬───────┴────────┬─────────┴────────┬─────────┴────────┬──────┘
       │                │                  │                  │
       │                │                  │                  │
       ▼                ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          N8N ORQUESTADOR                              │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  CRON: */5 * * * * (TZ: America/Bogota)                    │     │
│  │                                                             │     │
│  │  1. Extract     → HTTP Requests / Scraper Fallback         │     │
│  │  2. Transform   → Normalize, Clean HTML, Generate hash     │     │
│  │  3. Deduplicate → Check DB by hash_url                     │     │
│  │  4. Score       → Call ADK Scorer (keep/discard)           │     │
│  │  5. Load        → Insert to Postgres                       │     │
│  │  6. Enrich      → Generate embeddings                      │     │
│  │  7. Alert       → Slack/Telegram if severity=high          │     │
│  └────────────────────────────────────────────────────────────┘     │
└──────┬──────────────────────┬──────────────────────┬────────────────┘
       │                      │                      │
       │ HTTP POST            │ HTTP POST            │ SQL
       │                      │                      │
       ▼                      ▼                      ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐
│  ADK SCORER     │  │  SCRAPER ADV     │  │  POSTGRES + pgvector    │
│  (Cloud Run)    │  │  (Cloud Run)     │  │  (Cloud SQL/Supabase)   │
│                 │  │                  │  │                         │
│  - Gemini 1.5   │  │  - Playwright    │  │  - news_item            │
│  - Scoring      │  │  - HTML render   │  │  - news_embedding       │
│  - Tagging      │  │  - User-agent    │  │  - etl_execution_log    │
│  - Severity     │  │  - Rate limit    │  │                         │
└─────────────────┘  └──────────────────┘  └───────────┬─────────────┘
                                                        │
                                                        │ SELECT
                                                        │
                                                        ▼
                                            ┌───────────────────────┐
                                            │  OBSERVABILIDAD       │
                                            │                       │
                                            │  - Cloud Logging      │
                                            │  - SQL KPIs           │
                                            │  - Health Checks      │
                                            └───────────────────────┘
                                                        │
                                                        │
                                                        ▼
                                            ┌───────────────────────┐
                                            │  ALERTAS              │
                                            │                       │
                                            │  - Slack              │
                                            │  - Telegram           │
                                            │  - Email (opcional)   │
                                            └───────────────────────┘
```

## Componentes Detallados

### 1. n8n Orquestador

**Responsabilidad**: Coordinación central del flujo ETL

**Workflows**:
- `etl-movilidad-main`: Flujo principal (cada 5 min)
- `etl-movilidad-health`: Health checks (cada hora)
- `etl-movilidad-maintenance`: Limpieza (diario 3am)

**Nodos Clave**:
- **Cron Trigger**: Ejecución programada
- **HTTP Request**: Llamadas a APIs externas y microservicios
- **Code (JavaScript)**: Transformación, normalización, lógica custom
- **Postgres**: Queries (dedup, insert, select)
- **IF**: Condiciones (keep/discard, severity)
- **Split In Batches**: Procesamiento por lotes
- **Error Workflow**: Manejo global de errores

**Configuración**:
```env
TZ=America/Bogota
N8N_BASIC_AUTH_ACTIVE=true
EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=168  # 7 días
```

---

### 2. ADK Scorer (Cloud Run)

**Responsabilidad**: Clasificación inteligente de noticias

**Stack**:
- **Runtime**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **AI**: Google Vertex AI (Gemini 1.5 Flash)
- **Logging**: structlog

**Endpoints**:
- `GET /health`: Health check
- `POST /score`: Scoring de noticia

**Input** (`POST /score`):
```json
{
  "source": "string",
  "url": "https://...",
  "title": "string",
  "body": "string",
  "published_at": "2024-01-15T10:00:00Z"
}
```

**Output**:
```json
{
  "keep": true,
  "relevance_score": 0.85,
  "severity": "high",
  "area": "El Poblado",
  "tags": ["cierre_vial", "manifestacion"],
  "summary": "Cierre total en Av. El Poblado 2pm-8pm por manifestación",
  "entities": [
    {"type": "location", "value": "Avenida El Poblado"},
    {"type": "datetime", "value": "2024-01-15 14:00"}
  ],
  "reasoning": "Afecta vía principal en hora pico"
}
```

**Características**:
- Retry con backoff exponencial (tenacity)
- Respuestas en JSON estructurado
- Fallback conservador ante errores
- Logging de decisiones para auditoría
- Idempotencia garantizada

**Configuración Cloud Run**:
- **CPU**: 1
- **Memoria**: 1GB
- **Timeout**: 60s
- **Max instances**: 10
- **Min instances**: 0 (scale-to-zero)
- **Auth**: OIDC (Bearer Token)

---

### 3. Scraper Avanzado (Cloud Run)

**Responsabilidad**: Extracción de sitios que bloquean bots

**Stack**:
- **Runtime**: Node.js 20
- **Framework**: Express + TypeScript
- **Browser**: Playwright (Chromium)
- **Validation**: Zod

**Endpoints**:
- `GET /health`: Health check
- `POST /fetch`: Scraping con rendering

**Input** (`POST /fetch`):
```json
{
  "url": "https://example.com",
  "waitFor": ".selector-class",
  "timeout": 10000,
  "userAgent": "Mozilla/5.0 ...",
  "headers": {
    "Accept-Language": "es-CO"
  }
}
```

**Output**:
```json
{
  "success": true,
  "data": {
    "html": "<html>...</html>",
    "text": "Extracted text content",
    "title": "Page title",
    "metadata": {
      "url": "https://example.com",
      "statusCode": 200,
      "loadTime": 2340
    }
  }
}
```

**Características**:
- Rate limiting: 30 req/min por IP
- User-agent configurable
- Respeto a robots.txt (manual, verificar antes)
- Timeout configurable (max 30s)
- Reuso de browser instance
- Validación de input con Zod

**Configuración Cloud Run**:
- **CPU**: 1
- **Memoria**: 2GB (Playwright requiere más memoria)
- **Timeout**: 60s
- **Max instances**: 5
- **Auth**: OIDC

---

### 4. Base de Datos (Postgres + pgvector)

**Responsabilidad**: Persistencia y búsqueda semántica

**Esquema**:

#### Tabla `news_item`
```sql
CREATE TABLE news_item (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    url TEXT NOT NULL,
    hash_url VARCHAR(64) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,

    -- Enriquecimiento
    area VARCHAR(100),
    entities JSONB DEFAULT '[]'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    severity VARCHAR(20),
    relevance_score DECIMAL(3,2),
    summary TEXT,

    -- Control
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Tabla `news_embedding`
```sql
CREATE TABLE news_embedding (
    id BIGSERIAL PRIMARY KEY,
    news_id BIGINT NOT NULL REFERENCES news_item(id) ON DELETE CASCADE,
    embedding vector(768) NOT NULL,
    model VARCHAR(50) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Tabla `etl_execution_log`
```sql
CREATE TABLE etl_execution_log (
    id BIGSERIAL PRIMARY KEY,
    execution_id VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    items_extracted INT DEFAULT 0,
    items_kept INT DEFAULT 0,
    items_discarded INT DEFAULT 0,
    items_duplicated INT DEFAULT 0,
    errors JSONB DEFAULT '[]'::jsonb,
    duration_seconds INT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ
);
```

**Índices Clave**:
- `idx_news_published_at`: Consultas temporales
- `idx_news_source`: Filtrado por fuente
- `idx_news_severity`: Alertas de alta severidad
- `idx_embedding_vector`: Búsqueda semántica (IVFFlat)

**Vistas**:
- `v_kpi_dashboard`: Métricas agregadas
- `v_severity_distribution`: Distribución por severidad
- `v_top_areas`: Áreas más afectadas
- `v_recent_news_with_embeddings`: Join optimizado

**Funciones**:
- `semantic_search(embedding, threshold, limit)`: Búsqueda por similitud
- `generate_hash_url(url)`: Hash SHA256 para deduplicación
- `update_updated_at_column()`: Trigger automático

**Configuración**:
- **Versión**: Postgres 15
- **Extensiones**: pgvector
- **Backups**: Diarios con PITR (7 días)
- **SSL**: Requerido
- **Connection pooling**: PgBouncer (si necesario)

---

### 5. Observabilidad

#### Cloud Logging

**Logs Estructurados** (JSON):
```json
{
  "severity": "INFO",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "request_id": "uuid-1234",
  "service": "adk-scorer",
  "message": "scoring_complete",
  "keep": true,
  "severity": "high",
  "score": 0.85
}
```

**Filtros Útiles**:
```
# Errores últimas 24h
severity>=ERROR timestamp>="2024-01-15T00:00:00Z"

# Decisiones de descarte
jsonPayload.keep=false

# Scraping lento
jsonPayload.loadTime>5000
```

#### Métricas SQL

**KPIs Principales**:
- Items extraídos/hora por fuente
- Keep rate (% de noticias relevantes)
- Error rate por fuente
- Duración promedio de ejecución
- Distribución de severidad
- Top áreas afectadas

**Consulta Rápida**:
```sql
SELECT * FROM v_kpi_dashboard
WHERE hour > NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;
```

#### Health Checks

**Workflow n8n** (cada hora):
1. Consultar métricas DB
2. Verificar error rate < 10%
3. Verificar ingesta > 5 items/hora
4. Verificar duración < 120s
5. Alertar si umbrales excedidos

---

### 6. Seguridad

#### Secrets Management

**GCP Secret Manager**:
- `DATABASE_URL`: Connection string Postgres
- `ADK_SCORER_TOKEN`: OIDC token
- `SCRAPER_ADV_TOKEN`: OIDC token
- `SLACK_WEBHOOK`: Webhook URL
- `TELEGRAM_TOKEN`: Bot token
- `TWITTER_BEARER_TOKEN`: API token
- `OPENAI_API_KEY`: Embeddings API

**Rotación**:
- Calendario: cada 90 días
- Script: `scripts/rotate-secrets.sh`
- Zero-downtime: Dual-write temporalmente

#### Autenticación

**Cloud Run**:
- OIDC (Identity-Aware Proxy)
- Service account: `etl-runner@etl-movilidad-mde.iam.gserviceaccount.com`
- Tokens generados automáticamente por n8n

**n8n**:
- Basic Auth (UI access)
- Webhook Auth (external triggers)
- Credential encryption (N8N_ENCRYPTION_KEY)

#### Rate Limiting

**Scraper**:
- 30 req/min por IP (express-rate-limit)
- Backoff automático en retry

**APIs Externas**:
- Twitter: Límites del tier contratado
- OpenAI: Soft limit monitoring

#### Network Security

- Cloud Run services: **Ingress = internal** (solo n8n)
- Postgres: **Authorized networks** (n8n IP + Cloud SQL Proxy)
- SSL/TLS: **Requerido** en todas las comunicaciones

---

## Flujo de Datos Detallado

### Fase 1: Extracción (Extract)

```
Twitter API
    ↓
[HTTP Request Node] → Query: "(movilidad OR tráfico) Medellín"
    ↓
Raw tweets (JSON)

Metro Medellín RSS
    ↓
[HTTP Request Node] → URL: /feed
    ↓ (Si 403)
[Scraper Fallback] → Playwright rendering
    ↓
HTML/XML

Medios Locales
    ↓
[HTTP Request Node] → RSS feeds
    ↓
XML parsed to JSON
```

### Fase 2: Transformación (Transform)

```
Raw data (diversos formatos)
    ↓
[Code Node: Normalize]
    │
    ├─> Limpiar HTML (strip tags)
    ├─> Unificar campos (title, body, date)
    ├─> Generar hash_url (SHA256)
    ├─> Normalizar timestamps (ISO 8601)
    └─> Validar campos requeridos
    ↓
Normalized data (JSON estándar)
```

### Fase 3: Deduplicación

```
Normalized items
    ↓
[Postgres Node: Check Duplicates]
    SQL: SELECT hash_url FROM news_item WHERE hash_url = ANY($1)
    ↓
List of existing hashes
    ↓
[Code Node: Filter]
    Remove items with existing hash_url
    ↓
Unique items only
```

### Fase 4: Scoring (ADK)

```
Unique items (batched)
    ↓
[HTTP Request: POST /score] (uno a uno)
    Body: {source, url, title, body, published_at}
    ↓
ADK Scorer (Gemini 1.5)
    │
    ├─> Analizar contenido
    ├─> Evaluar relevancia
    ├─> Asignar severidad
    ├─> Extraer entidades
    ├─> Generar tags
    └─> Resumir
    ↓
Scoring results
    {keep, relevance_score, severity, area, tags, summary, entities}
    ↓
[Code Node: Merge]
    Combinar datos originales + scoring
    ↓
Enriched items
```

### Fase 5: Filtrado

```
Enriched items
    ↓
[IF Node: Keep Item]
    Condition: scoring.keep === true
    ↓ YES          ↓ NO
    ↓              └─> [Postgres: Log Discarded]
    ↓                  └─> etl_execution_log (items_discarded++)
Continue
```

### Fase 6: Carga (Load)

```
Kept items
    ↓
[Postgres Node: Insert News]
    INSERT INTO news_item (...)
    ON CONFLICT (hash_url) DO NOTHING
    RETURNING id
    ↓
Inserted items with ID
```

### Fase 7: Enriquecimiento (Embeddings)

```
Inserted items
    ↓
[HTTP Request: OpenAI Embeddings API]
    POST /v1/embeddings
    Body: {model: "text-embedding-3-small", input: "title + body"}
    ↓
Embedding vectors (768 dimensions)
    ↓
[Postgres Node: Insert Embedding]
    INSERT INTO news_embedding (news_id, embedding, model)
    ↓
Complete enriched news
```

### Fase 8: Alertas

```
Enriched items
    ↓
[IF Node: High Severity]
    Condition: severity IN ['high', 'critical']
    ↓ YES
    ↓
[Parallel Split]
    ├─> [Slack Node: Send Message]
    │   Channel: #movilidad-alertas
    │   Format: Structured alert
    │
    └─> [Telegram Node: Send Message]
        Chat ID: configured
        Format: Structured alert
```

### Fase 9: Logging

```
Execution metadata
    ↓
[Code Node: Calculate Metrics]
    │
    ├─> execution_id
    ├─> items_extracted (count all)
    ├─> items_kept (count kept)
    ├─> items_discarded (count discarded)
    ├─> items_duplicated (count dupes)
    ├─> errors (array de errores)
    ├─> duration_seconds (end - start)
    └─> timestamps
    ↓
[Postgres Node: Insert Log]
    INSERT INTO etl_execution_log (...)
    ↓
Audit trail complete
```

---

## Patrones de Diseño Aplicados

### 1. Pipeline Pattern
- Flujo secuencial: Extract → Transform → Load
- Cada etapa independiente y testable

### 2. Circuit Breaker
- Retry con backoff exponencial (tenacity en Python)
- Fallback conservador en ADK scorer

### 3. Idempotencia
- Hash-based deduplication (hash_url único)
- ON CONFLICT DO NOTHING en inserts
- Mismo input → mismo scoring (ADK)

### 4. Event-Driven
- Cron trigger inicia pipeline
- Alertas solo si condiciones (severity=high)

### 5. Observer Pattern
- Logging en cada etapa
- Métricas agregadas en DB
- Health checks periódicos

### 6. Adapter Pattern
- n8n adapta diferentes fuentes a formato común
- Scraper adapta HTML a JSON estructurado

---

## Escalabilidad

### Horizontal

**n8n**:
- Ejecuta workflows en paralelo (por fuente)
- Split in Batches para procesamiento por lotes

**Cloud Run**:
- Auto-scaling: 0 → 10 instancias (ADK)
- Concurrency: hasta 80 requests/instancia
- Scale-to-zero cuando no hay tráfico

**Postgres**:
- Read replicas para consultas (si necesario)
- Connection pooling con PgBouncer

### Vertical

**Limitar crecimiento**:
- Archivar noticias > 90 días
- Cleanup de logs > 30 días
- Vacuum automático

**Optimizar queries**:
- Índices en campos filtrados frecuentemente
- Vistas materializadas para dashboards (si necesario)

### Bottlenecks Identificados

1. **ADK Scorer**: Latencia de Gemini (2-5s por item)
   - Mitigación: Procesamiento paralelo con batching
   - Alternativa: Cache de scoring para URLs repetidas

2. **Embeddings**: Latencia de OpenAI API (1-2s por item)
   - Mitigación: Procesamiento asíncrono (background job)
   - Alternativa: Modelo local (sentence-transformers)

3. **Scraper**: Rendering con Playwright (5-10s por página)
   - Mitigación: Usar solo cuando HTTP normal falla
   - Optimización: Reuso de contexto de browser

---

## Resiliencia

### Manejo de Errores

**n8n Error Workflow**:
- Captura errores de cualquier nodo
- Loggea en DB y notifica a Slack
- No detiene ejecuciones futuras

**Retry Logic**:
- HTTP requests: 3 intentos con backoff
- ADK scoring: 3 intentos (tenacity)
- Postgres: Transacciones con rollback

### Recuperación

**Scenarios**:

1. **ADK Scorer caído**:
   - Fallback: Marcar keep=true, severity=medium, tag="revision_manual"
   - Continuar con persistencia
   - Re-procesar manualmente después

2. **Postgres no disponible**:
   - n8n reintenta ejecución (3 veces)
   - Alerta a ops
   - Data perdida si falla 3 veces (aceptable con cron cada 5 min)

3. **Fuente externa no disponible**:
   - Skip esa fuente
   - Log warning
   - Continuar con otras fuentes

### Backups

**Base de Datos**:
- Automated backups (diarios)
- Point-in-time recovery (7 días)
- Retención: 30 días

**Configuración**:
- n8n workflows en Git (n8n-workflows/)
- Terraform state en GCS
- Secrets documentados (no versionados)

---

## Consideraciones de Producción

### Staging Environment

**Recomendado**:
- Duplicar infraestructura con tier más bajo
- DB separada (db-micro)
- Fuentes de prueba o datos sintéticos
- Validar cambios antes de prod

### Deployment Strategy

**Blue-Green**:
- Cloud Run: Deploy nueva versión sin traffic
- Test smoke
- Gradual rollout (10% → 50% → 100%)
- Rollback instantáneo si errores

### Monitoring Alerts

**Críticos**:
- Cloud Run down (5xx rate > 10%)
- Postgres unreachable (connection errors)
- Error rate > 20% en 15 min
- Zero items ingested en 1 hora

**Warnings**:
- Latencia p95 > 10s
- Error rate > 5%
- Ingesta < 50% de promedio histórico
- Duración de ejecución > 5 min

---

## Referencias Técnicas

### Documentación
- [n8n Docs](https://docs.n8n.io)
- [Playwright Docs](https://playwright.dev)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [pgvector Docs](https://github.com/pgvector/pgvector)
- [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)

### Repositorios
- ADK Scorer: `adk-scorer/`
- Scraper: `scraper-adv/`
- DB Migrations: `db-migrations/`
- n8n Workflows: `n8n-workflows/`
- IaC: `terraform/`

---

**Versión**: 1.0.0
**Fecha**: 2024-01-15
