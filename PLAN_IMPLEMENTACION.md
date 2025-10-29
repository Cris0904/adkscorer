# Plan de Implementación - ETL Movilidad Medellín

## Resumen Ejecutivo

Sistema ETL para extraer, procesar y alertar sobre noticias de movilidad en Medellín usando:
- **n8n**: Orquestador principal (cron cada 5 min)
- **Cloud Run**: Microservicios (ADK Scorer + Scraper Playwright)
- **Postgres + pgvector**: Persistencia y búsqueda semántica
- **Alertas**: Slack/Telegram para severidad alta

**Duración estimada**: 3-4 semanas (1 dev senior)
**Complejidad**: Media-Alta
**Prioridad**: Alta

---

## 0. PRE-REQUISITOS

### Infraestructura Base
- [ ] Cuenta GCP activa con billing habilitado
- [ ] Proyecto GCP creado (ej: `etl-movilidad-mde`)
- [ ] gcloud CLI instalado y autenticado
- [ ] Terraform >= 1.5 instalado (IaC)

### Servicios Externos
- [ ] Instancia n8n desplegada (Railway/Render/GCP VM)
  - URL de acceso configurada
  - Webhook habilitado
  - TZ configurada a `America/Bogota`
- [ ] Base de datos Postgres 14+
  - Cloud SQL con pgvector O
  - Supabase con extensión vector
  - Credenciales de superusuario disponibles
- [ ] Cuentas para alertas
  - Slack: Webhook URL o Bot Token
  - Telegram: Bot Token + Chat ID

### Acceso a Fuentes
- [ ] Credenciales Twitter/X API (Bearer Token)
- [ ] URLs de RSS/HTML identificadas
- [ ] Permisos para scraping verificados (robots.txt)

### Repositorios Git
- [ ] Repo `adk-scorer` creado
- [ ] Repo `scraper-adv` creado
- [ ] Repo `n8n-workflows` creado
- [ ] Repo `db-migrations` creado

### Herramientas de Desarrollo
- [ ] Node.js >= 18 (para n8n testing)
- [ ] Python >= 3.11 (para microservicios)
- [ ] Docker Desktop (testing local)
- [ ] Postman/Bruno (testing APIs)

---

## ÉPICAS Y ESTIMACIONES

| Epic | Historias | Tiempo Estimado |
|------|-----------|-----------------|
| EP-01: Infraestructura Base | 4 | 3 días |
| EP-02: Base de Datos | 3 | 2 días |
| EP-03: Microservicio ADK Scorer | 4 | 5 días |
| EP-04: Microservicio Scraper | 3 | 3 días |
| EP-05: Workflows n8n | 5 | 6 días |
| EP-06: Observabilidad | 3 | 2 días |
| EP-07: Testing & Validación | 4 | 4 días |
| **TOTAL** | **26** | **25 días** |

---

## EP-01: INFRAESTRUCTURA BASE

**Objetivo**: Provisionar servicios GCP, Secret Manager y networking

### US-01.1: Configuración de Proyecto GCP
**Estimación**: 4h | **Prioridad**: P0

#### Tareas
- [ ] **T-01.1.1**: Crear proyecto GCP `etl-movilidad-mde`
  ```bash
  gcloud projects create etl-movilidad-mde --name="ETL Movilidad Medellín"
  gcloud config set project etl-movilidad-mde
  ```
- [ ] **T-01.1.2**: Habilitar APIs necesarias
  ```bash
  gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
  ```
- [ ] **T-01.1.3**: Crear service account para Cloud Run
  ```bash
  gcloud iam service-accounts create etl-runner \
    --display-name="ETL Services Runner"
  ```
- [ ] **T-01.1.4**: Asignar roles IAM
  ```bash
  gcloud projects add-iam-policy-binding etl-movilidad-mde \
    --member="serviceAccount:etl-runner@etl-movilidad-mde.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
  gcloud projects add-iam-policy-binding etl-movilidad-mde \
    --member="serviceAccount:etl-runner@etl-movilidad-mde.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
  ```

**DoD**: Proyecto configurado, APIs habilitadas, service account con permisos

---

### US-01.2: Infraestructura como Código (Terraform)
**Estimación**: 6h | **Prioridad**: P0

#### Tareas
- [ ] **T-01.2.1**: Crear estructura de directorios Terraform
  ```
  terraform/
  ├── main.tf
  ├── variables.tf
  ├── outputs.tf
  ├── versions.tf
  ├── modules/
  │   ├── database/
  │   ├── cloud-run/
  │   └── secrets/
  ```
- [ ] **T-01.2.2**: Configurar provider GCP
  ```hcl
  # versions.tf
  terraform {
    required_version = ">= 1.5"
    required_providers {
      google = {
        source  = "hashicorp/google"
        version = "~> 5.0"
      }
    }
    backend "gcs" {
      bucket = "etl-movilidad-tfstate"
      prefix = "terraform/state"
    }
  }
  ```
- [ ] **T-01.2.3**: Crear módulo de base de datos (Cloud SQL)
  - Ver sección EP-02 para detalles
- [ ] **T-01.2.4**: Crear módulo de Cloud Run genérico
- [ ] **T-01.2.5**: Crear módulo de Secret Manager
- [ ] **T-01.2.6**: Ejecutar `terraform plan` y revisar recursos

**DoD**: IaC funcional, plan revisado, bucket de estado creado

---

### US-01.3: Secret Manager y Credenciales
**Estimación**: 3h | **Prioridad**: P0

#### Tareas
- [ ] **T-01.3.1**: Crear secrets en GCP Secret Manager
  ```bash
  echo -n "postgresql://user:pass@host:5432/etl_movilidad" | \
    gcloud secrets create DATABASE_URL --data-file=-

  echo -n "xoxb-your-slack-token" | \
    gcloud secrets create SLACK_WEBHOOK --data-file=-

  echo -n "Bearer YOUR_TWITTER_TOKEN" | \
    gcloud secrets create TWITTER_TOKEN --data-file=-

  echo -n "your-telegram-bot-token" | \
    gcloud secrets create TELEGRAM_TOKEN --data-file=-

  echo -n "your-n8n-api-key" | \
    gcloud secrets create N8N_API_KEY --data-file=-
  ```
- [ ] **T-01.3.2**: Configurar acceso a secrets en Cloud Run
  - Añadir policy bindings para service account
- [ ] **T-01.3.3**: Documentar rotación de secrets
  - Crear script `scripts/rotate-secrets.sh`
  - Calendario de rotación (90 días)

**DoD**: Todos los secrets creados, acceso verificado, doc de rotación

---

### US-01.4: Configuración de n8n
**Estimación**: 3h | **Prioridad**: P0

#### Tareas
- [ ] **T-01.4.1**: Desplegar n8n en plataforma elegida
  - **Railway**: Deploy desde template
  - **Render**: Docker image `n8nio/n8n:latest`
  - **GCP VM**: Docker Compose
- [ ] **T-01.4.2**: Configurar variables de entorno
  ```env
  TZ=America/Bogota
  N8N_BASIC_AUTH_ACTIVE=true
  N8N_BASIC_AUTH_USER=admin
  N8N_BASIC_AUTH_PASSWORD=[STRONG_PASSWORD]
  WEBHOOK_URL=https://your-n8n.app
  EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
  EXECUTIONS_DATA_PRUNE=true
  EXECUTIONS_DATA_MAX_AGE=168
  ```
- [ ] **T-01.4.3**: Configurar credenciales en n8n
  - PostgreSQL (con DATABASE_URL)
  - HTTP Header Auth (para Cloud Run services)
  - Slack/Telegram credentials
- [ ] **T-01.4.4**: Verificar conectividad
  - Test connection a Postgres
  - Test webhook externo

**DoD**: n8n desplegado, credenciales configuradas, conectividad OK

---

## EP-02: BASE DE DATOS

**Objetivo**: Desplegar Postgres, instalar pgvector, crear esquema y migraciones

### US-02.1: Provisión de Postgres con pgvector
**Estimación**: 4h | **Prioridad**: P0

#### Tareas
- [ ] **T-02.1.1**: Crear instancia Cloud SQL (Terraform)
  ```hcl
  # terraform/modules/database/main.tf
  resource "google_sql_database_instance" "etl_postgres" {
    name             = "etl-movilidad-db"
    database_version = "POSTGRES_15"
    region           = var.region

    settings {
      tier = "db-f1-micro"  # Escalar según necesidad

      database_flags {
        name  = "cloudsql.enable_pgvector"
        value = "on"
      }

      backup_configuration {
        enabled                        = true
        start_time                     = "03:00"
        point_in_time_recovery_enabled = true
        transaction_log_retention_days = 7
      }

      ip_configuration {
        ipv4_enabled    = true
        require_ssl     = true
        authorized_networks {
          name  = "n8n-instance"
          value = var.n8n_ip
        }
      }
    }

    deletion_protection = true
  }

  resource "google_sql_database" "etl_db" {
    name     = "etl_movilidad"
    instance = google_sql_database_instance.etl_postgres.name
  }

  resource "google_sql_user" "etl_user" {
    name     = "etl_app"
    instance = google_sql_database_instance.etl_postgres.name
    password = var.db_password
  }
  ```
- [ ] **T-02.1.2**: Ejecutar `terraform apply` para DB
- [ ] **T-02.1.3**: Conectar vía Cloud SQL Proxy (local testing)
  ```bash
  cloud-sql-proxy etl-movilidad-mde:us-central1:etl-movilidad-db
  ```
- [ ] **T-02.1.4**: Instalar extensión pgvector
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  SELECT * FROM pg_extension WHERE extname = 'vector';
  ```

**DoD**: Postgres desplegado, pgvector instalado, conexión verificada

---

### US-02.2: Esquema de Base de Datos
**Estimación**: 4h | **Prioridad**: P0

#### Tareas
- [ ] **T-02.2.1**: Crear esquema inicial (migración 001)
  ```sql
  -- db-migrations/001_initial_schema.sql

  CREATE TABLE news_item (
      id BIGSERIAL PRIMARY KEY,
      source VARCHAR(100) NOT NULL,
      url TEXT NOT NULL,
      hash_url VARCHAR(64) UNIQUE NOT NULL,
      title TEXT NOT NULL,
      body TEXT NOT NULL,
      published_at TIMESTAMPTZ NOT NULL,

      -- Enriquecimiento ADK
      area VARCHAR(100),
      entities JSONB DEFAULT '[]'::jsonb,
      tags TEXT[] DEFAULT ARRAY[]::TEXT[],
      severity VARCHAR(20) CHECK (severity IN ('low', 'medium', 'high', 'critical')),
      relevance_score DECIMAL(3,2) CHECK (relevance_score BETWEEN 0 AND 1),
      summary TEXT,

      -- Control
      status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'duplicate')),

      -- Timestamps
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE INDEX idx_news_published_at ON news_item(published_at DESC);
  CREATE INDEX idx_news_source ON news_item(source);
  CREATE INDEX idx_news_severity ON news_item(severity) WHERE status = 'active';
  CREATE INDEX idx_news_area ON news_item(area) WHERE status = 'active';
  CREATE INDEX idx_news_created_at ON news_item(created_at DESC);

  -- Tabla de embeddings
  CREATE TABLE news_embedding (
      id BIGSERIAL PRIMARY KEY,
      news_id BIGINT NOT NULL REFERENCES news_item(id) ON DELETE CASCADE,
      embedding vector(768) NOT NULL,
      model VARCHAR(50) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE INDEX idx_embedding_news_id ON news_embedding(news_id);
  CREATE INDEX idx_embedding_vector ON news_embedding
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

  -- Trigger para updated_at
  CREATE OR REPLACE FUNCTION update_updated_at_column()
  RETURNS TRIGGER AS $$
  BEGIN
      NEW.updated_at = NOW();
      RETURN NEW;
  END;
  $$ language 'plpgsql';

  CREATE TRIGGER update_news_item_updated_at BEFORE UPDATE ON news_item
      FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

  -- Función para generar hash_url
  CREATE OR REPLACE FUNCTION generate_hash_url(url_text TEXT)
  RETURNS VARCHAR(64) AS $$
  BEGIN
      RETURN encode(digest(url_text, 'sha256'), 'hex');
  END;
  $$ LANGUAGE plpgsql IMMUTABLE;
  ```

- [ ] **T-02.2.2**: Crear tabla de log de ejecuciones
  ```sql
  -- Tracking de ejecuciones ETL
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

  CREATE INDEX idx_etl_log_started ON etl_execution_log(started_at DESC);
  CREATE INDEX idx_etl_log_source ON etl_execution_log(source);
  ```

- [ ] **T-02.2.3**: Crear vistas para métricas
  ```sql
  -- Vista de métricas diarias
  CREATE VIEW v_daily_metrics AS
  SELECT
      DATE(started_at) as date,
      source,
      COUNT(*) as executions,
      SUM(items_extracted) as total_extracted,
      SUM(items_kept) as total_kept,
      SUM(items_discarded) as total_discarded,
      SUM(items_duplicated) as total_duplicated,
      AVG(duration_seconds) as avg_duration,
      SUM(CASE WHEN errors::text != '[]' THEN 1 ELSE 0 END) as error_count
  FROM etl_execution_log
  GROUP BY DATE(started_at), source
  ORDER BY date DESC, source;

  -- Vista de noticias recientes con embeddings
  CREATE VIEW v_recent_news_with_embeddings AS
  SELECT
      ni.*,
      CASE WHEN ne.id IS NOT NULL THEN true ELSE false END as has_embedding
  FROM news_item ni
  LEFT JOIN news_embedding ne ON ni.id = ne.news_id
  WHERE ni.status = 'active'
    AND ni.created_at > NOW() - INTERVAL '7 days'
  ORDER BY ni.published_at DESC;
  ```

- [ ] **T-02.2.4**: Aplicar migración
  ```bash
  psql $DATABASE_URL -f db-migrations/001_initial_schema.sql
  ```

**DoD**: Esquema creado, índices aplicados, vistas funcionales

---

### US-02.3: Scripts de Utilidad SQL
**Estimación**: 2h | **Prioridad**: P1

#### Tareas
- [ ] **T-02.3.1**: Script de búsqueda semántica
  ```sql
  -- db-migrations/functions/semantic_search.sql

  CREATE OR REPLACE FUNCTION semantic_search(
      query_embedding vector(768),
      match_threshold FLOAT DEFAULT 0.7,
      match_count INT DEFAULT 10
  )
  RETURNS TABLE (
      news_id BIGINT,
      title TEXT,
      body TEXT,
      published_at TIMESTAMPTZ,
      similarity FLOAT
  )
  LANGUAGE plpgsql
  AS $$
  BEGIN
      RETURN QUERY
      SELECT
          ni.id,
          ni.title,
          ni.body,
          ni.published_at,
          1 - (ne.embedding <=> query_embedding) as similarity
      FROM news_embedding ne
      JOIN news_item ni ON ne.news_id = ni.id
      WHERE ni.status = 'active'
        AND 1 - (ne.embedding <=> query_embedding) > match_threshold
      ORDER BY ne.embedding <=> query_embedding
      LIMIT match_count;
  END;
  $$;
  ```

- [ ] **T-02.3.2**: Script de limpieza de duplicados
  ```sql
  -- db-migrations/maintenance/cleanup_duplicates.sql

  -- Marcar duplicados basados en hash_url
  UPDATE news_item
  SET status = 'duplicate'
  WHERE id IN (
      SELECT id
      FROM (
          SELECT id,
                 ROW_NUMBER() OVER (PARTITION BY hash_url ORDER BY created_at) as rn
          FROM news_item
          WHERE status = 'active'
      ) t
      WHERE rn > 1
  );

  -- Archivar noticias antiguas (>90 días)
  UPDATE news_item
  SET status = 'archived'
  WHERE status = 'active'
    AND published_at < NOW() - INTERVAL '90 days';
  ```

- [ ] **T-02.3.3**: Script de health check
  ```sql
  -- db-migrations/monitoring/health_check.sql

  SELECT
      'news_item' as table_name,
      COUNT(*) as total_rows,
      COUNT(*) FILTER (WHERE status = 'active') as active_rows,
      COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
      pg_size_pretty(pg_total_relation_size('news_item')) as table_size
  FROM news_item
  UNION ALL
  SELECT
      'news_embedding',
      COUNT(*),
      COUNT(*),
      COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
      pg_size_pretty(pg_total_relation_size('news_embedding'))
  FROM news_embedding;
  ```

**DoD**: Funciones creadas, scripts testeados, documentación agregada

---

## EP-03: MICROSERVICIO ADK SCORER

**Objetivo**: Crear servicio Cloud Run que evalúa noticias con ADK y devuelve scoring/etiquetado

### US-03.1: Estructura del Proyecto ADK
**Estimación**: 3h | **Prioridad**: P0

#### Tareas
- [ ] **T-03.1.1**: Inicializar proyecto Python
  ```bash
  mkdir adk-scorer && cd adk-scorer
  python -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  ```

- [ ] **T-03.1.2**: Crear estructura de directorios
  ```
  adk-scorer/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py           # FastAPI app
  │   ├── models.py         # Pydantic models
  │   ├── scorer.py         # Lógica ADK
  │   └── prompts.py        # Prompts del agente
  ├── tests/
  │   ├── test_api.py
  │   └── test_scorer.py
  ├── Dockerfile
  ├── .dockerignore
  ├── requirements.txt
  ├── cloudbuild.yaml
  └── README.md
  ```

- [ ] **T-03.1.3**: Crear requirements.txt
  ```txt
  fastapi==0.109.0
  uvicorn[standard]==0.27.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  google-cloud-aiplatform==1.40.0
  google-cloud-logging==3.9.0
  structlog==24.1.0
  httpx==0.26.0
  tenacity==8.2.3
  ```

- [ ] **T-03.1.4**: Crear Dockerfile optimizado
  ```dockerfile
  FROM python:3.11-slim as builder

  WORKDIR /app

  RUN pip install --no-cache-dir poetry==1.7.1

  COPY pyproject.toml poetry.lock ./
  RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

  FROM python:3.11-slim

  WORKDIR /app

  COPY --from=builder /app/requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  COPY app/ ./app/

  ENV PORT=8080
  ENV PYTHONUNBUFFERED=1

  CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2
  ```

**DoD**: Proyecto inicializado, estructura creada, Dockerfile funcional

---

### US-03.2: API REST con FastAPI
**Estimación**: 4h | **Prioridad**: P0

#### Tareas
- [ ] **T-03.2.1**: Definir modelos Pydantic
  ```python
  # app/models.py
  from pydantic import BaseModel, Field, HttpUrl
  from typing import Optional, List
  from datetime import datetime
  from enum import Enum

  class SeverityLevel(str, Enum):
      LOW = "low"
      MEDIUM = "medium"
      HIGH = "high"
      CRITICAL = "critical"

  class NewsInput(BaseModel):
      source: str = Field(..., max_length=100)
      url: HttpUrl
      title: str = Field(..., min_length=5)
      body: str = Field(..., min_length=20)
      published_at: datetime

      # Contexto adicional opcional
      context: Optional[dict] = None

  class ScoringOutput(BaseModel):
      keep: bool
      relevance_score: float = Field(..., ge=0, le=1)
      severity: Optional[SeverityLevel] = None
      area: Optional[str] = Field(None, max_length=100)
      tags: List[str] = Field(default_factory=list)
      summary: Optional[str] = Field(None, max_length=500)
      entities: List[dict] = Field(default_factory=list)
      reasoning: Optional[str] = None  # Para debugging

  class HealthResponse(BaseModel):
      status: str
      version: str
      uptime_seconds: float

  class ErrorResponse(BaseModel):
      error: str
      detail: Optional[str] = None
      request_id: Optional[str] = None
  ```

- [ ] **T-03.2.2**: Implementar FastAPI application
  ```python
  # app/main.py
  from fastapi import FastAPI, HTTPException, Request, status
  from fastapi.responses import JSONResponse
  from contextlib import asynccontextmanager
  import structlog
  import time
  import uuid
  from .models import NewsInput, ScoringOutput, HealthResponse, ErrorResponse
  from .scorer import NewsScorer

  logger = structlog.get_logger()

  start_time = time.time()

  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # Startup
      logger.info("Starting ADK Scorer service")
      app.state.scorer = NewsScorer()
      yield
      # Shutdown
      logger.info("Shutting down ADK Scorer service")

  app = FastAPI(
      title="ADK News Scorer",
      version="1.0.0",
      lifespan=lifespan
  )

  @app.middleware("http")
  async def add_request_id(request: Request, call_next):
      request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
      request.state.request_id = request_id

      structlog.contextvars.bind_contextvars(request_id=request_id)

      response = await call_next(request)
      response.headers["X-Request-ID"] = request_id

      return response

  @app.get("/health", response_model=HealthResponse)
  async def health_check():
      return HealthResponse(
          status="healthy",
          version="1.0.0",
          uptime_seconds=time.time() - start_time
      )

  @app.post("/score", response_model=ScoringOutput)
  async def score_news(
      news: NewsInput,
      request: Request
  ):
      try:
          logger.info(
              "scoring_request",
              source=news.source,
              url=str(news.url),
              title=news.title[:100]
          )

          result = await request.app.state.scorer.score(news)

          logger.info(
              "scoring_complete",
              keep=result.keep,
              severity=result.severity,
              score=result.relevance_score
          )

          return result

      except Exception as e:
          logger.error("scoring_error", error=str(e), exc_info=True)
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail=str(e)
          )

  @app.exception_handler(Exception)
  async def global_exception_handler(request: Request, exc: Exception):
      logger.error("unhandled_exception", error=str(exc), exc_info=True)
      return JSONResponse(
          status_code=500,
          content=ErrorResponse(
              error="Internal server error",
              detail=str(exc),
              request_id=getattr(request.state, "request_id", None)
          ).dict()
      )
  ```

- [ ] **T-03.2.3**: Configurar logging estructurado
  ```python
  # app/__init__.py
  import structlog
  import logging
  import sys

  def configure_logging():
      structlog.configure(
          processors=[
              structlog.contextvars.merge_contextvars,
              structlog.processors.add_log_level,
              structlog.processors.TimeStamper(fmt="iso"),
              structlog.dev.ConsoleRenderer() if sys.stderr.isatty()
                  else structlog.processors.JSONRenderer()
          ],
          wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
          context_class=dict,
          logger_factory=structlog.PrintLoggerFactory(),
          cache_logger_on_first_use=False
      )

  configure_logging()
  ```

**DoD**: API funcional, endpoints documentados, logging configurado

---

### US-03.3: Lógica de Scoring con ADK
**Estimación**: 8h | **Prioridad**: P0

#### Tareas
- [ ] **T-03.3.1**: Crear sistema de prompts
  ```python
  # app/prompts.py

  SYSTEM_PROMPT = """Eres un experto analista de noticias de movilidad urbana en Medellín, Colombia.

  Tu tarea es evaluar si una noticia es relevante para el sistema de alertas de movilidad y extraer información estructurada.

  CONTEXTO DE MEDELLÍN:
  - Metro de Medellín: Sistema de transporte masivo (líneas A, B, T, H, M, P)
  - Áreas clave: El Poblado, Laureles, Belén, Centro, Robledo, Castilla, Aranjuez
  - Eventos típicos: cierres viales, manifestaciones, accidentes, obras, Metro

  CRITERIOS DE RELEVANCIA (keep=true):
  1. Afecta tráfico vehicular o transporte público
  2. Eventos en vías principales o zonas con alta afluencia
  3. Cierres programados o emergencias viales
  4. Incidentes del Metro/Metroplús/buses
  5. Eventos masivos que impacten movilidad

  CRITERIOS DE DESCARTE (keep=false):
  - Noticias generales sin impacto en movilidad
  - Eventos en municipios fuera de Medellín
  - Publicidad o contenido comercial
  - Duplicados o contenido irrelevante

  SEVERIDAD:
  - critical: Bloqueos totales, emergencias, Metro fuera de servicio
  - high: Cierres importantes, accidentes graves, manifestaciones grandes
  - medium: Obras programadas, cierres parciales, tráfico pesado
  - low: Alertas menores, mantenimientos nocturnos

  ÁREAS:
  Comuna o barrio afectado (ej: "El Poblado", "Centro", "Laureles-Estadio")
  """

  USER_PROMPT_TEMPLATE = """Analiza la siguiente noticia:

  FUENTE: {source}
  URL: {url}
  TÍTULO: {title}
  FECHA: {published_at}

  CONTENIDO:
  {body}

  Responde en JSON con esta estructura:
  {{
      "keep": true/false,
      "relevance_score": 0.0-1.0,
      "severity": "low|medium|high|critical" (solo si keep=true),
      "area": "nombre_del_area" (solo si keep=true),
      "tags": ["tag1", "tag2", ...],
      "summary": "Resumen breve en 1-2 oraciones",
      "entities": [
          {{"type": "location", "value": "Calle 10 con Carrera 43A"}},
          {{"type": "organization", "value": "Metro de Medellín"}},
          {{"type": "datetime", "value": "2024-01-15 14:30"}}
      ],
      "reasoning": "Breve explicación de tu decisión"
  }}

  TAGS disponibles: cierre_vial, accidente, obra, metro, bus, manifestacion, evento, trafico, emergencia, mantenimiento
  """

  def build_scoring_prompt(news_input) -> tuple[str, str]:
      user_prompt = USER_PROMPT_TEMPLATE.format(
          source=news_input.source,
          url=str(news_input.url),
          title=news_input.title,
          published_at=news_input.published_at.isoformat(),
          body=news_input.body[:2000]  # Limitar tokens
      )
      return SYSTEM_PROMPT, user_prompt
  ```

- [ ] **T-03.3.2**: Implementar NewsScorer con ADK
  ```python
  # app/scorer.py
  import json
  import structlog
  from typing import Optional
  from tenacity import retry, stop_after_attempt, wait_exponential
  from google.cloud import aiplatform
  from vertexai.generative_models import GenerativeModel, GenerationConfig
  from .models import NewsInput, ScoringOutput, SeverityLevel
  from .prompts import build_scoring_prompt

  logger = structlog.get_logger()

  class NewsScorer:
      def __init__(self):
          self.project_id = "etl-movilidad-mde"
          self.location = "us-central1"
          self.model_name = "gemini-1.5-flash"

          aiplatform.init(project=self.project_id, location=self.location)

          self.model = GenerativeModel(
              self.model_name,
              generation_config=GenerationConfig(
                  temperature=0.1,
                  max_output_tokens=1024,
                  response_mime_type="application/json"
              )
          )

          logger.info("scorer_initialized", model=self.model_name)

      @retry(
          stop=stop_after_attempt(3),
          wait=wait_exponential(multiplier=1, min=2, max=10)
      )
      async def score(self, news: NewsInput) -> ScoringOutput:
          system_prompt, user_prompt = build_scoring_prompt(news)

          try:
              response = self.model.generate_content(
                  [system_prompt, user_prompt]
              )

              result_json = json.loads(response.text)

              # Validación y normalización
              return ScoringOutput(
                  keep=result_json.get("keep", False),
                  relevance_score=self._normalize_score(result_json.get("relevance_score", 0.0)),
                  severity=result_json.get("severity") if result_json.get("keep") else None,
                  area=result_json.get("area"),
                  tags=result_json.get("tags", []),
                  summary=result_json.get("summary"),
                  entities=result_json.get("entities", []),
                  reasoning=result_json.get("reasoning")
              )

          except json.JSONDecodeError as e:
              logger.error("json_parse_error", error=str(e), response=response.text)
              # Fallback conservador
              return self._conservative_fallback(news)

          except Exception as e:
              logger.error("scoring_exception", error=str(e), exc_info=True)
              raise

      def _normalize_score(self, score: float) -> float:
          return max(0.0, min(1.0, score))

      def _conservative_fallback(self, news: NewsInput) -> ScoringOutput:
          """Fallback cuando ADK falla: conservador, marca como relevante para revisión manual"""
          return ScoringOutput(
              keep=True,
              relevance_score=0.5,
              severity=SeverityLevel.MEDIUM,
              area="desconocido",
              tags=["revision_manual"],
              summary=f"ERROR AL PROCESAR: {news.title[:100]}",
              entities=[],
              reasoning="Fallback por error en ADK"
          )
  ```

- [ ] **T-03.3.3**: Crear tests unitarios
  ```python
  # tests/test_scorer.py
  import pytest
  from app.models import NewsInput
  from app.scorer import NewsScorer
  from datetime import datetime

  @pytest.fixture
  def scorer():
      return NewsScorer()

  @pytest.fixture
  def sample_news_relevant():
      return NewsInput(
          source="test",
          url="https://example.com/news1",
          title="Cierre total en la Avenida El Poblado por manifestación",
          body="La Alcaldía informó que la Avenida El Poblado estará cerrada desde las 2pm hasta las 8pm debido a una manifestación pacífica...",
          published_at=datetime.now()
      )

  @pytest.fixture
  def sample_news_irrelevant():
      return NewsInput(
          source="test",
          url="https://example.com/news2",
          title="Nueva tienda de ropa abre en Laureles",
          body="Una nueva tienda de moda internacional abrió sus puertas en el barrio Laureles...",
          published_at=datetime.now()
      )

  @pytest.mark.asyncio
  async def test_score_relevant_news(scorer, sample_news_relevant):
      result = await scorer.score(sample_news_relevant)

      assert result.keep is True
      assert result.severity in ["high", "critical"]
      assert result.relevance_score > 0.6
      assert "manifestacion" in result.tags or "cierre_vial" in result.tags

  @pytest.mark.asyncio
  async def test_score_irrelevant_news(scorer, sample_news_irrelevant):
      result = await scorer.score(sample_news_irrelevant)

      assert result.keep is False
      assert result.relevance_score < 0.4
  ```

**DoD**: Scorer funcional, prompts ajustados, tests passing

---

### US-03.4: Despliegue en Cloud Run
**Estimación**: 3h | **Prioridad**: P1

#### Tareas
- [ ] **T-03.4.1**: Crear Cloud Build config
  ```yaml
  # cloudbuild.yaml
  steps:
    # Build image
    - name: 'gcr.io/cloud-builders/docker'
      args: [
        'build',
        '-t', 'gcr.io/$PROJECT_ID/adk-scorer:$SHORT_SHA',
        '-t', 'gcr.io/$PROJECT_ID/adk-scorer:latest',
        '.'
      ]

    # Push image
    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'gcr.io/$PROJECT_ID/adk-scorer:$SHORT_SHA']

    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'gcr.io/$PROJECT_ID/adk-scorer:latest']

    # Deploy to Cloud Run
    - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
      entrypoint: gcloud
      args:
        - 'run'
        - 'deploy'
        - 'adk-scorer'
        - '--image=gcr.io/$PROJECT_ID/adk-scorer:$SHORT_SHA'
        - '--region=us-central1'
        - '--platform=managed'
        - '--allow-unauthenticated=false'
        - '--memory=1Gi'
        - '--cpu=1'
        - '--timeout=60s'
        - '--max-instances=10'
        - '--min-instances=0'
        - '--service-account=etl-runner@$PROJECT_ID.iam.gserviceaccount.com'

  options:
    logging: CLOUD_LOGGING_ONLY

  images:
    - 'gcr.io/$PROJECT_ID/adk-scorer:$SHORT_SHA'
    - 'gcr.io/$PROJECT_ID/adk-scorer:latest'
  ```

- [ ] **T-03.4.2**: Ejecutar primer despliegue
  ```bash
  gcloud builds submit --config=cloudbuild.yaml
  ```

- [ ] **T-03.4.3**: Obtener URL del servicio
  ```bash
  gcloud run services describe adk-scorer \
    --region=us-central1 \
    --format='value(status.url)'
  ```

- [ ] **T-03.4.4**: Test de integración
  ```bash
  # Obtener token de autenticación
  TOKEN=$(gcloud auth print-identity-token)

  # Test endpoint /health
  curl -H "Authorization: Bearer $TOKEN" \
    https://adk-scorer-xxx-uc.a.run.app/health

  # Test endpoint /score
  curl -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "source": "test",
      "url": "https://example.com",
      "title": "Cierre en Avenida 80",
      "body": "La Avenida 80 estará cerrada por obras...",
      "published_at": "2024-01-15T10:00:00Z"
    }' \
    https://adk-scorer-xxx-uc.a.run.app/score
  ```

**DoD**: Servicio desplegado, tests exitosos, URL documentada

---

## EP-04: MICROSERVICIO SCRAPER AVANZADO

**Objetivo**: Servicio Cloud Run con Playwright para scraping de sitios que bloquean peticiones normales

### US-04.1: Proyecto Scraper con Playwright
**Estimación**: 4h | **Prioridad**: P1

#### Tareas
- [ ] **T-04.1.1**: Inicializar proyecto Node.js
  ```bash
  mkdir scraper-adv && cd scraper-adv
  npm init -y
  ```

- [ ] **T-04.1.2**: Crear estructura de directorios
  ```
  scraper-adv/
  ├── src/
  │   ├── index.ts         # Express server
  │   ├── scraper.ts       # Playwright logic
  │   ├── config.ts        # Configuración
  │   └── middleware.ts    # Rate limiting, auth
  ├── tests/
  │   └── scraper.test.ts
  ├── Dockerfile
  ├── .dockerignore
  ├── package.json
  ├── tsconfig.json
  └── cloudbuild.yaml
  ```

- [ ] **T-04.1.3**: Instalar dependencias
  ```json
  {
    "name": "scraper-adv",
    "version": "1.0.0",
    "scripts": {
      "start": "node dist/index.js",
      "dev": "ts-node-dev src/index.ts",
      "build": "tsc",
      "test": "jest"
    },
    "dependencies": {
      "express": "^4.18.2",
      "playwright": "^1.40.0",
      "winston": "^3.11.0",
      "dotenv": "^16.3.1",
      "express-rate-limit": "^7.1.5",
      "helmet": "^7.1.0",
      "zod": "^3.22.4"
    },
    "devDependencies": {
      "@types/express": "^4.17.21",
      "@types/node": "^20.10.0",
      "typescript": "^5.3.3",
      "ts-node-dev": "^2.0.0",
      "jest": "^29.7.0"
    }
  }
  ```

- [ ] **T-04.1.4**: Crear Dockerfile con Playwright
  ```dockerfile
  FROM mcr.microsoft.com/playwright:v1.40.0-focal

  WORKDIR /app

  # Copiar package files
  COPY package*.json ./

  # Instalar dependencias
  RUN npm ci --only=production

  # Copiar código compilado
  COPY dist/ ./dist/

  # Usuario no-root
  USER pwuser

  ENV PORT=8080
  ENV NODE_ENV=production

  EXPOSE 8080

  CMD ["node", "dist/index.js"]
  ```

**DoD**: Proyecto inicializado, dependencias instaladas, Dockerfile funcional

---

### US-04.2: API de Scraping con Express
**Estimación**: 5h | **Prioridad**: P1

#### Tareas
- [ ] **T-04.2.1**: Implementar servidor Express
  ```typescript
  // src/index.ts
  import express, { Request, Response } from 'express';
  import helmet from 'helmet';
  import rateLimit from 'express-rate-limit';
  import { scrapeUrl } from './scraper';
  import { logger } from './config';
  import { z } from 'zod';

  const app = express();
  const PORT = process.env.PORT || 8080;

  // Middleware
  app.use(helmet());
  app.use(express.json());

  // Rate limiting: 30 req/min por IP
  const limiter = rateLimit({
    windowMs: 60 * 1000,
    max: 30,
    message: 'Too many requests from this IP'
  });
  app.use(limiter);

  // Schema de validación
  const FetchRequestSchema = z.object({
    url: z.string().url(),
    waitFor: z.string().optional(),
    timeout: z.number().min(1000).max(30000).default(10000),
    userAgent: z.string().optional(),
    headers: z.record(z.string()).optional()
  });

  // Health check
  app.get('/health', (req: Request, res: Response) => {
    res.json({ status: 'healthy', service: 'scraper-adv', version: '1.0.0' });
  });

  // Endpoint principal de scraping
  app.post('/fetch', async (req: Request, res: Response) => {
    try {
      const params = FetchRequestSchema.parse(req.body);

      logger.info('Scraping request', { url: params.url });

      const result = await scrapeUrl(params);

      res.json({
        success: true,
        data: {
          html: result.html,
          text: result.text,
          title: result.title,
          metadata: result.metadata
        }
      });

    } catch (error) {
      if (error instanceof z.ZodError) {
        logger.warn('Validation error', { errors: error.errors });
        return res.status(400).json({
          success: false,
          error: 'Invalid request',
          details: error.errors
        });
      }

      logger.error('Scraping error', { error: String(error) });
      res.status(500).json({
        success: false,
        error: 'Scraping failed',
        message: String(error)
      });
    }
  });

  app.listen(PORT, () => {
    logger.info(`Scraper service listening on port ${PORT}`);
  });
  ```

- [ ] **T-04.2.2**: Implementar lógica de Playwright
  ```typescript
  // src/scraper.ts
  import { chromium, Browser, Page } from 'playwright';
  import { logger } from './config';

  interface ScrapeParams {
    url: string;
    waitFor?: string;
    timeout?: number;
    userAgent?: string;
    headers?: Record<string, string>;
  }

  interface ScrapeResult {
    html: string;
    text: string;
    title: string;
    metadata: {
      url: string;
      statusCode: number;
      loadTime: number;
    };
  }

  let browser: Browser | null = null;

  async function getBrowser(): Promise<Browser> {
    if (!browser) {
      browser = await chromium.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu'
        ]
      });

      logger.info('Browser launched');
    }
    return browser;
  }

  export async function scrapeUrl(params: ScrapeParams): Promise<ScrapeResult> {
    const startTime = Date.now();
    const browser = await getBrowser();
    const context = await browser.newContext({
      userAgent: params.userAgent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      extraHTTPHeaders: params.headers || {}
    });

    const page = await context.newPage();

    try {
      // Navegar con timeout
      const response = await page.goto(params.url, {
        timeout: params.timeout || 10000,
        waitUntil: 'domcontentloaded'
      });

      // Esperar selector específico si se proporciona
      if (params.waitFor) {
        await page.waitForSelector(params.waitFor, { timeout: 5000 });
      }

      // Extraer contenido
      const html = await page.content();
      const text = await page.evaluate(() => document.body.innerText);
      const title = await page.title();

      const loadTime = Date.now() - startTime;

      logger.info('Scraping successful', {
        url: params.url,
        loadTime,
        statusCode: response?.status()
      });

      return {
        html,
        text,
        title,
        metadata: {
          url: params.url,
          statusCode: response?.status() || 0,
          loadTime
        }
      };

    } finally {
      await page.close();
      await context.close();
    }
  }

  // Cleanup al cerrar
  process.on('SIGTERM', async () => {
    if (browser) {
      await browser.close();
      logger.info('Browser closed');
    }
  });
  ```

- [ ] **T-04.2.3**: Configurar logging
  ```typescript
  // src/config.ts
  import winston from 'winston';

  export const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    ),
    transports: [
      new winston.transports.Console()
    ]
  });
  ```

**DoD**: API funcional, Playwright integrado, validación de requests

---

### US-04.3: Despliegue y Testing
**Estimación**: 2h | **Prioridad**: P1

#### Tareas
- [ ] **T-04.3.1**: Compilar TypeScript
  ```bash
  npm run build
  ```

- [ ] **T-04.3.2**: Crear Cloud Build config
  ```yaml
  # cloudbuild.yaml
  steps:
    # Install & build
    - name: 'gcr.io/cloud-builders/npm'
      args: ['ci']

    - name: 'gcr.io/cloud-builders/npm'
      args: ['run', 'build']

    # Build Docker image
    - name: 'gcr.io/cloud-builders/docker'
      args: [
        'build',
        '-t', 'gcr.io/$PROJECT_ID/scraper-adv:$SHORT_SHA',
        '-t', 'gcr.io/$PROJECT_ID/scraper-adv:latest',
        '.'
      ]

    # Push
    - name: 'gcr.io/cloud-builders/docker'
      args: ['push', 'gcr.io/$PROJECT_ID/scraper-adv:$SHORT_SHA']

    # Deploy
    - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
      entrypoint: gcloud
      args:
        - 'run'
        - 'deploy'
        - 'scraper-adv'
        - '--image=gcr.io/$PROJECT_ID/scraper-adv:$SHORT_SHA'
        - '--region=us-central1'
        - '--platform=managed'
        - '--memory=2Gi'
        - '--cpu=1'
        - '--timeout=60s'
        - '--max-instances=5'
        - '--allow-unauthenticated=false'

  images:
    - 'gcr.io/$PROJECT_ID/scraper-adv:$SHORT_SHA'
  ```

- [ ] **T-04.3.3**: Desplegar servicio
  ```bash
  gcloud builds submit --config=cloudbuild.yaml
  ```

- [ ] **T-04.3.4**: Test de integración
  ```bash
  TOKEN=$(gcloud auth print-identity-token)
  SCRAPER_URL=$(gcloud run services describe scraper-adv --region=us-central1 --format='value(status.url)')

  curl -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "url": "https://www.metrodemedellin.gov.co/viajeconnosotros/estado-del-sistema",
      "timeout": 15000
    }' \
    $SCRAPER_URL/fetch
  ```

**DoD**: Servicio desplegado, tests exitosos, latencia < 10s

---

## EP-05: WORKFLOWS N8N

**Objetivo**: Crear flujos de extracción, procesamiento y alertas en n8n

### US-05.1: Workflow Principal - ETL Movilidad
**Estimación**: 8h | **Prioridad**: P0

#### Tareas
- [ ] **T-05.1.1**: Crear workflow vacío en n8n
  - Nombre: `ETL Movilidad - Main`
  - Tags: `production`, `etl`, `movilidad`

- [ ] **T-05.1.2**: Configurar trigger de cron
  ```
  Nodo: Cron
  - Modo: Every 5 minutes
  - Timezone: America/Bogota
  - Enabled: true
  ```

- [ ] **T-05.1.3**: Agregar nodo de inicialización
  ```javascript
  // Nodo: Code - Initialize Execution
  const executionId = $execution.id;
  const startedAt = new Date().toISOString();

  return [{
    json: {
      execution_id: executionId,
      started_at: startedAt,
      sources: [
        { name: 'twitter', enabled: true },
        { name: 'metro_medellin', enabled: true },
        { name: 'el_colombiano', enabled: true }
      ]
    }
  }];
  ```

- [ ] **T-05.1.4**: Implementar extracción por fuente (Twitter/X)
  ```
  Nodo: HTTP Request - Twitter API
  - Method: GET
  - URL: https://api.twitter.com/2/tweets/search/recent
  - Query Parameters:
    * query: (movilidad OR tráfico OR Metro) (Medellín OR Medellin) -is:retweet
    * max_results: 50
    * tweet.fields: created_at,author_id,text,entities
    * expansions: author_id
  - Authentication: Bearer Token (desde credenciales)
  - Headers:
    * User-Agent: n8n-etl-movilidad/1.0
  ```

- [ ] **T-05.1.5**: Extracción Metro de Medellín (HTML/RSS)
  ```
  Nodo: HTTP Request - Metro Web
  - Method: GET
  - URL: https://www.metrodemedellin.gov.co/feed
  - Si bloquea → llamar a scraper-adv:

  Nodo: IF - Check if blocked
  - Condition: {{$json.statusCode}} === 403

  Nodo: HTTP Request - Scraper Fallback
  - Method: POST
  - URL: https://scraper-adv-xxx.run.app/fetch
  - Authentication: Bearer Token
  - Body JSON:
    {
      "url": "https://www.metrodemedellin.gov.co/viajeconnosotros/estado-del-sistema",
      "waitFor": ".estado-sistema",
      "timeout": 15000
    }
  ```

- [ ] **T-05.1.6**: Extracción medios locales (El Colombiano RSS)
  ```
  Nodo: HTTP Request - El Colombiano RSS
  - Method: GET
  - URL: https://www.elcolombiano.com/rss/medellin.xml
  - Response Format: XML

  Nodo: XML - Parse Feed
  - Options: Normalize
  ```

- [ ] **T-05.1.7**: Normalización de datos
  ```javascript
  // Nodo: Code - Normalize Items
  const crypto = require('crypto');

  function generateHashUrl(url) {
    return crypto.createHash('sha256').update(url).digest('hex');
  }

  function cleanHtml(html) {
    // Usar Readability o simple strip tags
    return html.replace(/<[^>]*>/g, '').trim();
  }

  function parsePublishedAt(dateStr, source) {
    // Normalizar diferentes formatos de fecha
    const date = new Date(dateStr);
    return date.toISOString();
  }

  const items = $input.all();
  const normalized = [];

  for (const item of items) {
    const data = item.json;

    normalized.push({
      source: data.source || 'unknown',
      url: data.url || data.link,
      hash_url: generateHashUrl(data.url || data.link),
      title: data.title || data.text?.substring(0, 200),
      body: cleanHtml(data.description || data.text || data.content),
      published_at: parsePublishedAt(data.created_at || data.pubDate, data.source),
      raw_data: data
    });
  }

  return normalized;
  ```

- [ ] **T-05.1.8**: Deduplicación contra DB
  ```
  Nodo: Postgres - Check Duplicates
  - Operation: Execute Query
  - Query:
    SELECT hash_url
    FROM news_item
    WHERE hash_url = ANY($1::text[])
  - Parameters:
    {{$json.items.map(i => i.hash_url)}}

  Nodo: Code - Filter Duplicates
  const existing = $('Postgres - Check Duplicates').all()[0].json.map(r => r.hash_url);
  const items = $input.all();

  return items.filter(item => !existing.includes(item.json.hash_url));
  ```

- [ ] **T-05.1.9**: Llamada a ADK Scorer
  ```
  Nodo: HTTP Request - ADK Score
  - Method: POST
  - URL: https://adk-scorer-xxx.run.app/score
  - Authentication: Bearer Token (OIDC)
  - Batch Size: 1 (procesar uno a uno)
  - Body JSON:
    {
      "source": "{{$json.source}}",
      "url": "{{$json.url}}",
      "title": "{{$json.title}}",
      "body": "{{$json.body}}",
      "published_at": "{{$json.published_at}}"
    }

  Nodo: Code - Merge Score Results
  // Combinar datos originales con scoring
  const items = $('Normalize Items').all();
  const scores = $input.all();

  return items.map((item, idx) => ({
    ...item.json,
    scoring: scores[idx].json
  }));
  ```

- [ ] **T-05.1.10**: Filtrar items a mantener
  ```
  Nodo: IF - Keep Item
  - Condition: {{$json.scoring.keep}} === true
  ```

- [ ] **T-05.1.11**: Persistir en Postgres
  ```
  Nodo: Postgres - Insert News Item
  - Operation: Insert
  - Table: news_item
  - Columns: source, url, hash_url, title, body, published_at, area, entities, tags, severity, relevance_score, summary
  - Return Fields: id
  - On Conflict: Do Nothing (hash_url)
  ```

- [ ] **T-05.1.12**: Generar embeddings
  ```
  Nodo: HTTP Request - Generate Embedding
  - Method: POST
  - URL: https://api.openai.com/v1/embeddings
  - Authentication: Bearer Token
  - Body JSON:
    {
      "model": "text-embedding-3-small",
      "input": "{{$json.title}} {{$json.body}}"
    }

  Nodo: Postgres - Insert Embedding
  - Operation: Execute Query
  - Query:
    INSERT INTO news_embedding (news_id, embedding, model)
    VALUES ($1, $2, $3)
  - Parameters:
    - $1: {{$json.id}}
    - $2: {{$json.embedding}}
    - $3: 'text-embedding-3-small'
  ```

- [ ] **T-05.1.13**: Alertas para severidad alta
  ```
  Nodo: IF - High Severity
  - Condition: {{$json.severity}} in ['high', 'critical']

  Nodo: Slack - Send Alert
  - Channel: #movilidad-alertas
  - Message:
    🚨 *ALERTA DE MOVILIDAD - {{$json.severity.toUpperCase()}}*

    *Fuente:* {{$json.source}}
    *Área:* {{$json.area}}
    *Fecha:* {{$json.published_at}}

    *Título:* {{$json.title}}

    *Resumen:* {{$json.summary}}

    *Tags:* {{$json.tags.join(', ')}}

    <{{$json.url}}|Ver noticia completa>

  Nodo: Telegram - Send Alert (parallel)
  - Chat ID: {{$credentials.telegram.chatId}}
  - Message: [Similar format]
  ```

- [ ] **T-05.1.14**: Logging de ejecución
  ```javascript
  // Nodo: Code - Log Execution
  const execution = $('Initialize Execution').first().json;
  const allItems = $('Normalize Items').all();
  const keptItems = $('Keep Item').all();
  const discarded = allItems.length - keptItems.length;

  const logEntry = {
    execution_id: execution.execution_id,
    source: 'aggregated',
    items_extracted: allItems.length,
    items_kept: keptItems.length,
    items_discarded: discarded,
    items_duplicated: 0, // calcular desde dedup
    errors: [],
    duration_seconds: (Date.now() - new Date(execution.started_at)) / 1000,
    started_at: execution.started_at,
    finished_at: new Date().toISOString()
  };

  return [{ json: logEntry }];

  // Nodo: Postgres - Insert Log
  - Operation: Insert
  - Table: etl_execution_log
  ```

- [ ] **T-05.1.15**: Manejo de errores global
  ```
  Nodo: Error Trigger (workflow settings)
  - On Error: Continue
  - Error Workflow: ETL Movilidad - Error Handler

  Crear workflow separado:
  Nodo: Slack - Error Notification
  - Channel: #etl-errors
  - Message:
    ❌ *ERROR EN ETL MOVILIDAD*

    *Execution ID:* {{$json.executionId}}
    *Error:* {{$json.error.message}}
    *Node:* {{$json.error.node}}
    *Timestamp:* {{$json.timestamp}}
  ```

**DoD**: Workflow completo, testeado end-to-end, logs funcionando

---

### US-05.2: Workflow de Salud del Sistema
**Estimación**: 4h | **Prioridad**: P2

#### Tareas
- [ ] **T-05.2.1**: Crear workflow de health check
  ```
  Workflow: ETL Movilidad - Health Check
  Trigger: Cron (cada hora)
  ```

- [ ] **T-05.2.2**: Consultar métricas de DB
  ```sql
  -- Nodo: Postgres - Get Metrics
  SELECT
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as items_last_hour,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as items_last_24h,
    AVG(relevance_score) as avg_score,
    COUNT(DISTINCT source) as active_sources
  FROM news_item
  WHERE status = 'active';
  ```

- [ ] **T-05.2.3**: Verificar errores recientes
  ```sql
  SELECT
    source,
    COUNT(*) as error_count,
    AVG(duration_seconds) as avg_duration
  FROM etl_execution_log
  WHERE started_at > NOW() - INTERVAL '1 hour'
    AND errors::text != '[]'
  GROUP BY source;
  ```

- [ ] **T-05.2.4**: Alertar si anomalías
  ```javascript
  // Nodo: Code - Check Thresholds
  const metrics = $input.first().json;

  const alerts = [];

  // Menos de 5 items en última hora
  if (metrics.items_last_hour < 5) {
    alerts.push({
      severity: 'warning',
      message: `Baja ingesta: solo ${metrics.items_last_hour} items en última hora`
    });
  }

  // Error rate > 10%
  const errorRate = metrics.error_count / metrics.total_executions;
  if (errorRate > 0.1) {
    alerts.push({
      severity: 'critical',
      message: `Alto error rate: ${(errorRate * 100).toFixed(1)}%`
    });
  }

  // Duración promedio > 2 minutos
  if (metrics.avg_duration > 120) {
    alerts.push({
      severity: 'warning',
      message: `Ejecuciones lentas: promedio ${metrics.avg_duration}s`
    });
  }

  return alerts.length > 0 ? alerts : [];

  // Si hay alertas → notificar Slack
  ```

**DoD**: Health check funcional, alertas configuradas, métricas visibles

---

### US-05.3: Workflow de Mantenimiento
**Estimación**: 3h | **Prioridad**: P2

#### Tareas
- [ ] **T-05.3.1**: Crear workflow de cleanup
  ```
  Workflow: ETL Movilidad - Maintenance
  Trigger: Cron (diario a las 3am)
  ```

- [ ] **T-05.3.2**: Archivar noticias antiguas
  ```sql
  -- Nodo: Postgres - Archive Old News
  UPDATE news_item
  SET status = 'archived'
  WHERE status = 'active'
    AND published_at < NOW() - INTERVAL '90 days'
  RETURNING id;
  ```

- [ ] **T-05.3.3**: Limpiar logs antiguos
  ```sql
  DELETE FROM etl_execution_log
  WHERE started_at < NOW() - INTERVAL '30 days';
  ```

- [ ] **T-05.3.4**: Vacuum DB
  ```sql
  VACUUM ANALYZE news_item;
  VACUUM ANALYZE news_embedding;
  ```

**DoD**: Mantenimiento automático funcional

---

### US-05.4: Exportar Workflows como JSON
**Estimación**: 1h | **Prioridad**: P1

#### Tareas
- [ ] **T-05.4.1**: Exportar workflow principal
  - En n8n: Menu → Download
  - Guardar en `n8n-workflows/etl-movilidad-main.json`

- [ ] **T-05.4.2**: Exportar workflow de health
  - Guardar en `n8n-workflows/etl-movilidad-health.json`

- [ ] **T-05.4.3**: Exportar workflow de maintenance
  - Guardar en `n8n-workflows/etl-movilidad-maintenance.json`

- [ ] **T-05.4.4**: Crear README con instrucciones de importación
  ```markdown
  # N8N Workflows - ETL Movilidad

  ## Importación

  1. Acceder a n8n UI
  2. Menu → Import from File
  3. Seleccionar JSON
  4. Configurar credenciales:
     - Postgres (DATABASE_URL)
     - ADK Scorer (Bearer Token)
     - Scraper Adv (Bearer Token)
     - Slack/Telegram
  5. Activar workflows

  ## Workflows

  - `etl-movilidad-main.json`: Flujo principal (cada 5 min)
  - `etl-movilidad-health.json`: Health check (cada hora)
  - `etl-movilidad-maintenance.json`: Limpieza (diario 3am)
  ```

**DoD**: Workflows exportados, versionados en Git, README completo

---

### US-05.5: Variables de Entorno y Secrets
**Estimación**: 2h | **Prioridad**: P0

#### Tareas
- [ ] **T-05.5.1**: Documentar variables necesarias
  ```bash
  # .env.example

  # Database
  DATABASE_URL=postgresql://user:pass@host:5432/etl_movilidad

  # Cloud Run Services
  ADK_SCORER_URL=https://adk-scorer-xxx.run.app
  SCRAPER_ADV_URL=https://scraper-adv-xxx.run.app

  # GCP
  GCP_PROJECT_ID=etl-movilidad-mde
  GCP_SERVICE_ACCOUNT=etl-runner@etl-movilidad-mde.iam.gserviceaccount.com

  # Alerts
  SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
  TELEGRAM_BOT_TOKEN=123456:ABC-DEF
  TELEGRAM_CHAT_ID=-1001234567890

  # APIs
  TWITTER_BEARER_TOKEN=Bearer AAAAAAAAAAAAAAAAAAAAAxxxx
  OPENAI_API_KEY=sk-proj-xxx

  # n8n
  N8N_ENCRYPTION_KEY=random-32-char-string
  N8N_BASIC_AUTH_PASSWORD=strong-password
  ```

- [ ] **T-05.5.2**: Configurar credenciales en n8n UI
  - Credentials → Add Credential
  - Postgres: Connection String
  - HTTP Auth: Bearer Token para Cloud Run
  - Slack: Webhook URL o OAuth
  - Telegram: Access Token

- [ ] **T-05.5.3**: Verificar acceso desde n8n a GCP
  ```bash
  # Test connection desde workflow
  HTTP Request → ADK Scorer /health
  Expected: 200 OK
  ```

**DoD**: Variables documentadas, credenciales configuradas, acceso verificado

---

## EP-06: OBSERVABILIDAD Y MONITOREO

**Objetivo**: Configurar logs, métricas y dashboards para monitorear el sistema

### US-06.1: Logging Centralizado
**Estimación**: 3h | **Prioridad**: P1

#### Tareas
- [ ] **T-06.1.1**: Verificar logs en Cloud Logging
  ```bash
  # Ver logs de ADK Scorer
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adk-scorer" --limit 50 --format json

  # Ver logs de Scraper
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=scraper-adv" --limit 50
  ```

- [ ] **T-06.1.2**: Crear filtros de logs útiles
  ```
  # Errores en últimas 24h
  severity>=ERROR
  timestamp>="2024-01-15T00:00:00Z"

  # Scoring decisions
  jsonPayload.keep=false
  severity="INFO"

  # Scraping timeouts
  jsonPayload.error=~"timeout"
  ```

- [ ] **T-06.1.3**: Configurar retención de logs
  ```bash
  # Crear sink a BigQuery para análisis (opcional)
  gcloud logging sinks create etl-logs-bq \
    bigquery.googleapis.com/projects/etl-movilidad-mde/datasets/etl_logs \
    --log-filter='resource.type="cloud_run_revision"'
  ```

**DoD**: Logs accesibles, filtros útiles creados, retención configurada

---

### US-06.2: Métricas y KPIs
**Estimación**: 4h | **Prioridad**: P1

#### Tareas
- [ ] **T-06.2.1**: Crear vista de KPIs en DB
  ```sql
  -- db-migrations/views/kpi_dashboard.sql

  CREATE OR REPLACE VIEW v_kpi_dashboard AS
  WITH recent_executions AS (
    SELECT
      DATE_TRUNC('hour', started_at) as hour,
      source,
      SUM(items_extracted) as extracted,
      SUM(items_kept) as kept,
      SUM(items_discarded) as discarded,
      AVG(duration_seconds) as avg_duration,
      COUNT(*) FILTER (WHERE errors::text != '[]') as error_count,
      COUNT(*) as total_executions
    FROM etl_execution_log
    WHERE started_at > NOW() - INTERVAL '24 hours'
    GROUP BY 1, 2
  )
  SELECT
    hour,
    source,
    extracted,
    kept,
    discarded,
    ROUND(100.0 * kept / NULLIF(extracted, 0), 1) as keep_rate,
    ROUND(avg_duration, 2) as avg_duration,
    error_count,
    ROUND(100.0 * error_count / NULLIF(total_executions, 0), 1) as error_rate
  FROM recent_executions
  ORDER BY hour DESC, source;

  -- Vista de distribución por severidad
  CREATE OR REPLACE VIEW v_severity_distribution AS
  SELECT
    severity,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 1) as percentage
  FROM news_item
  WHERE status = 'active'
    AND created_at > NOW() - INTERVAL '7 days'
  GROUP BY severity
  ORDER BY
    CASE severity
      WHEN 'critical' THEN 1
      WHEN 'high' THEN 2
      WHEN 'medium' THEN 3
      WHEN 'low' THEN 4
    END;

  -- Vista de top áreas afectadas
  CREATE OR REPLACE VIEW v_top_areas AS
  SELECT
    area,
    COUNT(*) as incident_count,
    COUNT(*) FILTER (WHERE severity IN ('high', 'critical')) as high_severity_count,
    MAX(published_at) as last_incident
  FROM news_item
  WHERE status = 'active'
    AND created_at > NOW() - INTERVAL '7 days'
    AND area IS NOT NULL
  GROUP BY area
  ORDER BY incident_count DESC
  LIMIT 10;
  ```

- [ ] **T-06.2.2**: Crear script de consulta rápida
  ```bash
  # scripts/check-kpis.sh
  #!/bin/bash

  psql $DATABASE_URL << EOF
  \echo '=== KPIs Últimas 24h ==='
  SELECT * FROM v_kpi_dashboard LIMIT 20;

  \echo ''
  \echo '=== Distribución por Severidad (7d) ==='
  SELECT * FROM v_severity_distribution;

  \echo ''
  \echo '=== Top Áreas Afectadas (7d) ==='
  SELECT * FROM v_top_areas;

  \echo ''
  \echo '=== Resumen de Embeddings ==='
  SELECT
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT news_id) as news_with_embeddings,
    model,
    DATE(created_at) as date
  FROM news_embedding
  WHERE created_at > NOW() - INTERVAL '7 days'
  GROUP BY model, DATE(created_at)
  ORDER BY date DESC;
  EOF
  ```

- [ ] **T-06.2.3**: Configurar alertas en Cloud Monitoring (opcional)
  ```bash
  # Alerta: Error rate > 10%
  gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="ETL Error Rate High" \
    --condition-display-name="Error rate > 10%" \
    --condition-threshold-value=0.1 \
    --condition-threshold-duration=300s \
    --condition-filter='resource.type="cloud_run_revision" AND severity="ERROR"'
  ```

**DoD**: KPIs consultables, script funcional, alertas configuradas

---

### US-06.3: Dashboard Simple (SQL-based)
**Estimación**: 3h | **Prioridad**: P2

#### Tareas
- [ ] **T-06.3.1**: Crear notebook/script de visualización
  ```python
  # scripts/dashboard.py (opcional con plotly/streamlit)
  import psycopg2
  import pandas as pd
  import plotly.express as px
  from datetime import datetime, timedelta

  conn = psycopg2.connect(os.environ['DATABASE_URL'])

  # KPIs principales
  df_kpis = pd.read_sql("SELECT * FROM v_kpi_dashboard", conn)

  # Gráfico de items por hora
  fig1 = px.line(df_kpis, x='hour', y='kept', color='source',
                 title='Items Procesados por Hora')
  fig1.show()

  # Distribución de severidad
  df_severity = pd.read_sql("SELECT * FROM v_severity_distribution", conn)
  fig2 = px.pie(df_severity, values='count', names='severity',
                title='Distribución de Severidad (7d)')
  fig2.show()

  # Top áreas
  df_areas = pd.read_sql("SELECT * FROM v_top_areas", conn)
  fig3 = px.bar(df_areas, x='area', y='incident_count',
                title='Top Áreas con Más Incidentes')
  fig3.show()

  conn.close()
  ```

- [ ] **T-06.3.2**: Alternativa: Metabase/Redash (si disponible)
  - Conectar a Postgres
  - Crear dashboards con vistas ya creadas
  - Compartir URL pública/privada

- [ ] **T-06.3.3**: Documentar acceso a métricas
  ```markdown
  # OBSERVABILITY.md

  ## Consultar Métricas

  ### Via SQL
  ```bash
  ./scripts/check-kpis.sh
  ```

  ### Via Cloud Logging
  ```bash
  gcloud logging read "resource.type=cloud_run_revision" --limit 100
  ```

  ### Via Dashboard
  - URL: [Metabase/Script]
  - Actualización: Cada 5 min

  ## Alertas Activas
  - Slack: #movilidad-alertas (severidad high/critical)
  - Slack: #etl-errors (errores de ejecución)
  - Email: ops@example.com (health checks fallidos)
  ```

**DoD**: Dashboard básico funcional, documentación de acceso completa

---

## EP-07: TESTING Y VALIDACIÓN

**Objetivo**: Crear plan de pruebas completo y ejecutar validaciones pre-producción

### US-07.1: Tests Unitarios
**Estimación**: 4h | **Prioridad**: P1

#### Tareas
- [ ] **T-07.1.1**: Tests ADK Scorer
  ```python
  # Ejecutar tests
  cd adk-scorer
  pytest tests/ -v --cov=app

  # Casos de prueba mínimos:
  # - test_score_relevant_news: keep=true esperado
  # - test_score_irrelevant_news: keep=false esperado
  # - test_severity_assignment: severidad correcta
  # - test_area_extraction: área detectada
  # - test_tags_generation: tags relevantes
  # - test_api_validation: errores 400 para input inválido
  # - test_idempotency: mismo input → mismo output
  ```

- [ ] **T-07.1.2**: Tests Scraper
  ```bash
  cd scraper-adv
  npm test

  # Casos de prueba:
  # - test_fetch_success: HTML extraído correctamente
  # - test_timeout_handling: timeout respetado
  # - test_user_agent: UA customizado aplicado
  # - test_invalid_url: error 400 devuelto
  # - test_rate_limiting: límite de 30 req/min
  ```

- [ ] **T-07.1.3**: Tests de funciones SQL
  ```sql
  -- tests/test_sql_functions.sql

  -- Test: generate_hash_url
  DO $$
  DECLARE
    url1 TEXT := 'https://example.com/news1';
    url2 TEXT := 'https://example.com/news2';
    hash1 TEXT;
    hash2 TEXT;
  BEGIN
    hash1 := generate_hash_url(url1);
    hash2 := generate_hash_url(url2);

    ASSERT hash1 != hash2, 'Hashes deben ser diferentes';
    ASSERT length(hash1) = 64, 'Hash debe tener 64 caracteres';
    ASSERT hash1 = generate_hash_url(url1), 'Hash debe ser idempotente';

    RAISE NOTICE 'Test generate_hash_url: PASSED';
  END $$;

  -- Test: semantic_search
  -- (requiere datos de ejemplo y embedding de prueba)
  ```

**DoD**: Tests unitarios pasando, cobertura > 70%

---

### US-07.2: Tests de Integración
**Estimación**: 5h | **Prioridad**: P0

#### Tareas
- [ ] **T-07.2.1**: Test end-to-end del flujo completo
  ```bash
  # scripts/test-e2e.sh
  #!/bin/bash

  set -e

  echo "=== ETL Movilidad - Test E2E ==="

  # 1. Preparar datos de prueba
  TEST_NEWS='[
    {
      "source": "test",
      "url": "https://test.com/news1",
      "title": "Cierre total Avenida El Poblado por manifestación",
      "body": "La Alcaldía informó cierre total desde 2pm hasta 8pm...",
      "published_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }
  ]'

  # 2. Test ADK Scorer
  echo "Testing ADK Scorer..."
  TOKEN=$(gcloud auth print-identity-token)
  SCORER_URL=$(gcloud run services describe adk-scorer --region=us-central1 --format='value(status.url)')

  SCORE_RESULT=$(echo $TEST_NEWS | jq '.[0]' | curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @- \
    $SCORER_URL/score)

  echo "Score result: $SCORE_RESULT"
  KEEP=$(echo $SCORE_RESULT | jq -r '.keep')

  if [ "$KEEP" != "true" ]; then
    echo "ERROR: Expected keep=true for test news"
    exit 1
  fi

  # 3. Test inserción en DB
  echo "Testing DB insertion..."
  HASH_URL=$(echo -n "https://test.com/news1" | sha256sum | cut -d' ' -f1)

  psql $DATABASE_URL -c "
  INSERT INTO news_item (source, url, hash_url, title, body, published_at, severity, relevance_score)
  VALUES (
    'test',
    'https://test.com/news1',
    '$HASH_URL',
    'Test news',
    'Test body',
    NOW(),
    'high',
    0.8
  )
  ON CONFLICT (hash_url) DO NOTHING
  RETURNING id;
  "

  # 4. Test generación de embedding
  echo "Testing embedding generation..."
  # (requiere llamar a OpenAI API o similar)

  # 5. Limpiar datos de prueba
  echo "Cleaning up..."
  psql $DATABASE_URL -c "DELETE FROM news_item WHERE source = 'test';"

  echo "=== E2E Test PASSED ==="
  ```

- [ ] **T-07.2.2**: Test de conectividad n8n → servicios
  ```javascript
  // En n8n: Crear workflow de test
  // Nodo: HTTP Request → ADK Scorer /health
  // Expected: 200 OK

  // Nodo: HTTP Request → Scraper /health
  // Expected: 200 OK

  // Nodo: Postgres Query
  // Query: SELECT 1
  // Expected: Success
  ```

- [ ] **T-07.2.3**: Test de deduplicación
  ```bash
  # Insertar mismo item 2 veces
  # Verificar que solo haya 1 registro en DB

  psql $DATABASE_URL << EOF
  INSERT INTO news_item (source, url, hash_url, title, body, published_at)
  VALUES ('test', 'https://dupe.com', 'dupe123', 'Title', 'Body', NOW());

  INSERT INTO news_item (source, url, hash_url, title, body, published_at)
  VALUES ('test', 'https://dupe.com', 'dupe123', 'Title', 'Body', NOW())
  ON CONFLICT (hash_url) DO NOTHING;

  SELECT COUNT(*) FROM news_item WHERE hash_url = 'dupe123';
  -- Expected: 1

  DELETE FROM news_item WHERE hash_url = 'dupe123';
  EOF
  ```

- [ ] **T-07.2.4**: Test de alertas
  ```bash
  # Crear item con severity=critical
  # Verificar que llegue alerta a Slack/Telegram

  # Via n8n workflow o script manual
  curl -X POST https://hooks.slack.com/services/xxx \
    -H 'Content-Type: application/json' \
    -d '{
      "text": "🧪 TEST: Sistema de alertas funcionando"
    }'
  ```

**DoD**: Tests de integración pasando, conectividad verificada

---

### US-07.3: Tests de Carga (Opcional)
**Estimación**: 3h | **Prioridad**: P3

#### Tareas
- [ ] **T-07.3.1**: Test de carga ADK Scorer
  ```bash
  # Con Apache Bench o Locust
  ab -n 100 -c 10 \
    -H "Authorization: Bearer $TOKEN" \
    -T "application/json" \
    -p payload.json \
    https://adk-scorer-xxx.run.app/score

  # Verificar:
  # - Latencia p95 < 5s
  # - Error rate < 1%
  # - Cloud Run escala correctamente
  ```

- [ ] **T-07.3.2**: Test de throughput n8n
  ```bash
  # Simular 100 items en workflow
  # Verificar que procese en < 10 minutos
  # Memoria y CPU dentro de límites
  ```

**DoD**: Performance aceptable bajo carga, escalado automático funcional

---

### US-07.4: Checklist de Validación Pre-Producción
**Estimación**: 2h | **Prioridad**: P0

#### Tareas
- [ ] **T-07.4.1**: Crear checklist completo
  ```markdown
  # VALIDACION_PRE_PROD.md

  ## Infraestructura
  - [ ] GCP proyecto creado y billing habilitado
  - [ ] APIs habilitadas (Cloud Run, SQL, Secret Manager)
  - [ ] Service accounts con permisos correctos
  - [ ] Secrets creados y accesibles

  ## Base de Datos
  - [ ] Postgres desplegado y accesible
  - [ ] Extensión pgvector instalada
  - [ ] Esquema aplicado (tablas, índices, vistas)
  - [ ] Usuario de aplicación con permisos limitados
  - [ ] Backups automáticos configurados

  ## Microservicios
  - [ ] ADK Scorer desplegado en Cloud Run
  - [ ] Scraper desplegado en Cloud Run
  - [ ] Endpoints /health responden 200 OK
  - [ ] Autenticación OIDC funcional
  - [ ] Logs visibles en Cloud Logging

  ## n8n
  - [ ] Instancia desplegada y accesible
  - [ ] TZ configurada a America/Bogota
  - [ ] Credenciales configuradas (Postgres, Cloud Run, Slack, Telegram)
  - [ ] Workflows importados
  - [ ] Cron triggers habilitados
  - [ ] Error workflow configurado

  ## Fuentes de Datos
  - [ ] Twitter API credentials válidas
  - [ ] RSS feeds accesibles
  - [ ] Scraper puede acceder a sitios target
  - [ ] robots.txt respetado

  ## Alertas
  - [ ] Slack webhook funcional
  - [ ] Telegram bot configurado
  - [ ] Test de alerta enviado y recibido

  ## Testing
  - [ ] Tests unitarios pasando (ADK, Scraper, SQL)
  - [ ] Test E2E ejecutado con éxito
  - [ ] Deduplicación verificada
  - [ ] Embeddings generándose correctamente

  ## Observabilidad
  - [ ] Logs accesibles en Cloud Logging
  - [ ] KPIs consultables vía SQL
  - [ ] Health check workflow funcionando
  - [ ] Alertas de sistema configuradas

  ## Documentación
  - [ ] README con arquitectura
  - [ ] Variables de entorno documentadas
  - [ ] Guía de despliegue completa
  - [ ] Runbook de operación
  - [ ] Plan de rollback documentado

  ## Seguridad
  - [ ] Secrets no en código
  - [ ] Cloud Run sin acceso público no autenticado
  - [ ] Postgres con SSL requerido
  - [ ] Rate limiting configurado
  - [ ] Plan de rotación de secrets
  ```

- [ ] **T-07.4.2**: Ejecutar checklist completo
  - Marcar cada item
  - Documentar bloqueadores
  - Resolver issues críticos

- [ ] **T-07.4.3**: Smoke test en producción
  ```bash
  # 1. Forzar ejecución manual de workflow
  # 2. Verificar inserción en DB
  # 3. Verificar embeddings generados
  # 4. Verificar alerta si severity=high
  # 5. Consultar KPIs
  # 6. Verificar logs sin errores
  ```

**DoD**: Checklist 100% completado, smoke test exitoso, sistema listo para producción

---

## GUÍA DE DESPLIEGUE

### Orden de Despliegue

1. **Infraestructura Base** (EP-01)
   ```bash
   # Crear proyecto GCP
   gcloud projects create etl-movilidad-mde
   gcloud config set project etl-movilidad-mde

   # Habilitar APIs
   gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com

   # Crear service accounts
   gcloud iam service-accounts create etl-runner
   ```

2. **Base de Datos** (EP-02)
   ```bash
   # Desplegar con Terraform
   cd terraform
   terraform init
   terraform plan
   terraform apply

   # Aplicar migraciones
   psql $DATABASE_URL -f db-migrations/001_initial_schema.sql
   psql $DATABASE_URL -f db-migrations/views/kpi_dashboard.sql
   ```

3. **Microservicios** (EP-03, EP-04)
   ```bash
   # ADK Scorer
   cd adk-scorer
   gcloud builds submit --config=cloudbuild.yaml

   # Scraper
   cd scraper-adv
   npm run build
   gcloud builds submit --config=cloudbuild.yaml

   # Verificar despliegues
   gcloud run services list
   ```

4. **n8n** (EP-05)
   ```bash
   # Configurar variables de entorno
   # Importar workflows
   # Configurar credenciales
   # Activar workflows
   ```

5. **Validación** (EP-07)
   ```bash
   # Ejecutar tests
   ./scripts/test-e2e.sh

   # Forzar ejecución manual
   # Verificar resultados

   # Habilitar cron
   ```

### Comandos de Rollback

```bash
# Rollback de Cloud Run service
gcloud run services update-traffic adk-scorer \
  --to-revisions=adk-scorer-previous=100

# Rollback de workflow n8n
# Restaurar versión anterior desde Git
# Importar en n8n UI

# Rollback de DB (con precaución)
psql $DATABASE_URL -f db-migrations/rollback/001_down.sql
```

### Monitoreo Post-Despliegue

```bash
# Logs en tiempo real
gcloud logging tail "resource.type=cloud_run_revision"

# Métricas
./scripts/check-kpis.sh

# Health checks
curl https://adk-scorer-xxx.run.app/health
curl https://scraper-adv-xxx.run.app/health
```

---

## COSTOS ESTIMADOS

### GCP Recursos (mensual)

| Recurso | Config | Costo Estimado |
|---------|--------|----------------|
| Cloud SQL (Postgres) | db-f1-micro | $7-15 |
| Cloud Run (ADK) | 1 CPU, 1GB, scale-to-zero | $5-20 |
| Cloud Run (Scraper) | 1 CPU, 2GB, scale-to-zero | $3-15 |
| Cloud Storage (backups) | 10GB | $0.20 |
| Secret Manager | 5 secrets | $0.18 |
| Cloud Logging | 5GB/mes | $0.50 |
| **TOTAL** | | **$15-50/mes** |

### Servicios Externos (mensual)

| Servicio | Tier | Costo |
|----------|------|-------|
| n8n (Railway/Render) | Starter | $5-20 |
| Twitter API | Basic | $100 (opcional) |
| OpenAI Embeddings | Pay-as-you-go | $5-15 |
| **TOTAL** | | **$110-135/mes** |

**Costo Total Estimado: $125-185/mes**

### Optimizaciones de Costo

- Usar Supabase free tier para Postgres (si aplica)
- Self-host n8n en GCP VM pequeña
- Usar modelos de embedding open-source (sentence-transformers)
- Limitar scraping a fuentes esenciales
- Configurar aggressive scale-to-zero

---

## CRITERIOS DE ACEPTACIÓN FINALES

### Funcionales
- [x] Workflow n8n ejecuta cada 5 minutos en TZ America/Bogota
- [x] Extrae noticias de 3+ fuentes (Twitter, Metro, medios)
- [x] ADK Scorer clasifica con keep/discard, severity, tags, area
- [x] Items únicos insertados en Postgres (deduplicación por hash_url)
- [x] Embeddings generados y almacenados en pgvector
- [x] Alertas enviadas a Slack/Telegram para severity=high/critical
- [x] Búsqueda semántica funcional

### No Funcionales
- [x] Error rate < 2% por día
- [x] Latencia ADK Scorer < 5s p95
- [x] Latencia Scraper < 10s p95
- [x] Uptime > 99% (excluye mantenimiento programado)
- [x] Logs estructurados y accesibles
- [x] Secrets rotables sin downtime
- [x] Backups diarios de DB

### Operacionales
- [x] Panel de KPIs consultable (SQL o UI)
- [x] Health check automatizado cada hora
- [x] Mantenimiento automático (archivado, limpieza)
- [x] Documentación completa (README, runbook, IaC)
- [x] Plan de rollback documentado y testeado

---

## PRÓXIMOS PASOS POST-MVP

1. **Dashboard visual** (Metabase/Grafana)
2. **API pública** para consultar eventos
3. **Webhooks** para integración externa
4. **ML para predicción** de eventos recurrentes
5. **App móvil** con notificaciones push
6. **Integración con Waze/Google Maps** para validación
7. **Análisis de sentimiento** en comentarios
8. **Detección de tendencias** con time-series

---

## CONTACTO Y SOPORTE

- **Project Lead**: [Nombre]
- **Repo**: https://github.com/org/etl-movilidad-mde
- **Slack**: #etl-movilidad
- **Documentación**: https://docs.example.com/etl-movilidad
- **Incidentes**: [Email/Ticket system]

---

**Versión**: 1.0.0
**Última actualización**: 2024-01-15
**Estado**: En desarrollo
