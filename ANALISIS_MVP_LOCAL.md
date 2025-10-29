# Análisis de Viabilidad - MVP Local Simplificado

## Resumen Ejecutivo

**Pregunta Clave:** ¿Es posible implementar este ETL de forma local, más simple y rápida?

**Respuesta:** ✅ **SÍ, TOTALMENTE VIABLE** con reducciones significativas:
- **Tiempo:** 25 días → **3-5 días** (85-90% reducción)
- **Costo:** $126-186/mes → **$0-20/mes** (95% reducción)
- **Complejidad:** Cloud-native distribuido → **Script Python local monolítico**
- **Requisito obligatorio:** ✅ ADK de Google se mantiene

---

## Comparativa: Plan Original vs MVP Local

| Aspecto | Plan Original (Cloud) | MVP Local Simplificado |
|---------|----------------------|------------------------|
| **Tiempo implementación** | 25 días (1 dev senior) | 3-5 días (1 dev) |
| **Componentes** | 6 servicios distribuidos | 1 script Python |
| **Infraestructura** | GCP (Cloud Run, SQL, etc) | Docker Compose local |
| **Costo mensual** | $126-186 | $0-20 |
| **Complejidad** | Alta (microservicios) | Baja (monolito) |
| **Escalabilidad** | Auto-scaling, cloud-native | Limitada (1 máquina) |
| **Producción ready** | Sí | No (prototipo) |
| **Líneas código** | ~7,400 | ~800-1,200 |

---

## Análisis de Componentes

### 1. n8n (Orquestador) → ❌ **ELIMINAR**

**Original:**
- Servicio complejo de orquestación
- Requiere hosting ($5-20/mes)
- Configuración visual de workflows
- Gestión de credenciales
- **Tiempo:** 6 días (EP-05)

**Alternativa Local:**
- Simple `cron` de sistema operativo
- Script Python con scheduler (`schedule` library)
- Archivo `.env` para credenciales
- **Tiempo:** 30 minutos

**Reducción:** 6 días → 0.5 horas = **99% más rápido**

```python
# Reemplazo de n8n (10 líneas)
import schedule
import time

def run_etl():
    print("Ejecutando ETL...")
    # Llamar función principal

schedule.every(5).minutes.do(run_etl)

while True:
    schedule.run_pending()
    time.sleep(1)
```

---

### 2. Microservicio Scraper (Playwright) → ⚠️ **SIMPLIFICAR**

**Original:**
- Servicio Cloud Run separado
- Express + TypeScript + Playwright
- Rate limiting, health checks
- **Tiempo:** 3 días (EP-04)
- **Costo:** $3-15/mes

**Alternativa Local:**
- Librería Python `requests` o `httpx`
- Fallback a `playwright` solo si es necesario
- Sin servicio separado (función en script principal)
- **Tiempo:** 2-3 horas

**Reducción:** 3 días → 2-3 horas = **95% más rápido**

**Evaluación de necesidad:**
- ✅ Twitter API: No requiere Playwright (API REST)
- ⚠️ Metro Medellín: Probar primero con `requests`, Playwright solo si bloquea
- ✅ RSS feeds: `feedparser` library (Python)

**Conclusión:** Playwright probablemente **NO NECESARIO** para MVP.

```python
# Reemplazo simple (20 líneas)
import requests
import feedparser

def scrape_metro():
    response = requests.get("https://www.metrodemedellin.gov.co/feed")
    return feedparser.parse(response.content)

def scrape_twitter():
    headers = {"Authorization": f"Bearer {TWITTER_TOKEN}"}
    response = requests.get(TWITTER_API_URL, headers=headers)
    return response.json()
```

---

### 3. ADK Scorer → ✅ **MANTENER (OBLIGATORIO)**

**Original:**
- Microservicio FastAPI en Cloud Run
- Pydantic models, structlog
- **Tiempo:** 5 días (EP-03)
- **Costo:** $5-20/mes

**Alternativa Local:**
- Función Python simple (no API REST)
- Llamada directa a Vertex AI desde script principal
- **Tiempo:** 4-6 horas

**Reducción:** 5 días → 4-6 horas = **90% más rápido**

**Costo:** Mismo (Vertex AI API calls), pero sin hosting de microservicio.

```python
# Reemplazo ADK (40 líneas)
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
import json

def score_news_with_adk(news_item):
    model = GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    Analiza esta noticia de movilidad en Medellín:
    Título: {news_item['title']}
    Contenido: {news_item['body']}

    Responde en JSON:
    {{"keep": true/false, "severity": "low|medium|high|critical",
      "tags": ["tag1", "tag2"], "summary": "resumen"}}
    """

    response = model.generate_content(prompt)
    return json.loads(response.text)
```

---

### 4. Base de Datos (Cloud SQL + pgvector) → ⚠️ **SIMPLIFICAR DRÁSTICAMENTE**

**Original:**
- Cloud SQL Postgres 15
- Extensión pgvector
- 3 tablas, 12 índices, 7 vistas, 4 funciones
- Búsqueda semántica avanzada
- **Tiempo:** 2 días (EP-02)
- **Costo:** $7-15/mes

**Alternativa Local (Opción A - SQLite):**
- SQLite local (sin servidor)
- Sin pgvector (embeddings opcionales)
- 2 tablas simples
- **Tiempo:** 1-2 horas
- **Costo:** $0

**Alternativa Local (Opción B - Postgres Docker):**
- Docker Compose con Postgres + pgvector
- Mantener búsqueda semántica
- **Tiempo:** 2-3 horas
- **Costo:** $0

**Recomendación para MVP:** **Opción A (SQLite)**
- Búsqueda semántica NO es crítica para MVP
- SQLite más que suficiente para prototipo
- Migración a Postgres después si es necesario

**Reducción:** 2 días → 1-2 horas = **95% más rápido**

```python
# Reemplazo SQLite (30 líneas)
import sqlite3
from datetime import datetime
import hashlib

def init_db():
    conn = sqlite3.connect('etl_movilidad.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS news_item (
            id INTEGER PRIMARY KEY,
            source TEXT,
            url TEXT UNIQUE,
            hash_url TEXT UNIQUE,
            title TEXT,
            body TEXT,
            published_at TEXT,
            severity TEXT,
            tags TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def insert_news(conn, news):
    hash_url = hashlib.sha256(news['url'].encode()).hexdigest()
    try:
        conn.execute('''
            INSERT INTO news_item (source, url, hash_url, title, body,
                                   published_at, severity, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (news['source'], news['url'], hash_url, news['title'],
              news['body'], news['published_at'], news['severity'],
              ','.join(news['tags'])))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicado
```

---

### 5. Embeddings (OpenAI + pgvector) → ❌ **ELIMINAR para MVP**

**Original:**
- OpenAI API para embeddings
- Almacenamiento en pgvector
- Búsqueda semántica
- **Tiempo:** Incluido en workflows (1 día)
- **Costo:** $5-15/mes

**Alternativa Local:**
- **Eliminar completamente para MVP**
- No es crítico para funcionalidad básica
- Agregar después si es necesario

**Reducción:** 1 día → 0 horas = **100% eliminado**

**Justificación:** Búsqueda semántica es feature avanzado, no necesario para validar concepto.

---

### 6. Infraestructura (GCP, Terraform) → ❌ **ELIMINAR**

**Original:**
- Terraform (IaC)
- Cloud Run, Secret Manager
- IAM, Service Accounts
- **Tiempo:** 3 días (EP-01)
- **Costo:** Incluido en servicios

**Alternativa Local:**
- Docker Compose (opcional)
- Archivo `.env` para secrets
- **Tiempo:** 1 hora (si se usa Docker)
- **Costo:** $0

**Reducción:** 3 días → 1 hora = **96% más rápido**

```yaml
# docker-compose.yml (opcional, 15 líneas)
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: etl_movilidad
      POSTGRES_USER: etl_app
      POSTGRES_PASSWORD: local_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

### 7. Observabilidad → ⚠️ **SIMPLIFICAR**

**Original:**
- Cloud Logging
- Vistas SQL complejas
- Dashboards
- **Tiempo:** 2 días (EP-06)

**Alternativa Local:**
- `logging` library de Python (archivo de texto)
- Consultas SQLite simples
- Print statements para debugging
- **Tiempo:** 30 minutos

**Reducción:** 2 días → 0.5 horas = **97% más rápido**

```python
# Logging simple (5 líneas)
import logging

logging.basicConfig(
    filename='etl.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("ETL iniciado")
```

---

### 8. Alertas (Slack/Telegram) → ✅ **MANTENER (SIMPLIFICADO)**

**Original:**
- Integración en n8n
- Webhooks configurables
- **Tiempo:** Incluido en workflows

**Alternativa Local:**
- Librería `requests` para webhook Slack
- O librería `python-telegram-bot`
- **Tiempo:** 1 hora

**Reducción:** Incluido → 1 hora

```python
# Alertas simples (10 líneas)
import requests

def send_slack_alert(message):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    requests.post(webhook_url, json={"text": message})

# Usar solo para severity=high/critical
if scoring['severity'] in ['high', 'critical']:
    send_slack_alert(f"🚨 {news['title']}")
```

---

## Arquitectura Simplificada (MVP Local)

### Antes (Cloud-Native)

```
Fuentes → n8n → [ADK Scorer | Scraper] → Cloud SQL → Alertas
  ↓        ↓              ↓                    ↓          ↓
Twitter  Cron      Cloud Run            pgvector    Slack/
Metro   Workflows  Microservicios       Búsqueda    Telegram
Medios  Complex    FastAPI/Express      Semántica
```

**Componentes:** 6 servicios separados
**Costo:** $126-186/mes
**Tiempo:** 25 días

---

### Después (Local Monolito)

```
main.py (1 script Python)
    ↓
    ├─ Scheduler (schedule library) → Ejecuta cada 5 min
    ├─ Extractors (requests/feedparser) → Twitter, Metro, RSS
    ├─ ADK Scorer (Vertex AI API) → Gemini 1.5 Flash
    ├─ SQLite Database → Persistencia local
    └─ Alerts (requests) → Slack webhook
```

**Componentes:** 1 script Python (~800-1,200 líneas)
**Costo:** $0-5/mes (solo API calls)
**Tiempo:** 3-5 días

---

## Plan de Implementación MVP Local

### Día 1: Setup Base (4-5 horas)

**Mañana (2-3h):**
- [ ] Crear proyecto Python
  ```bash
  mkdir etl-movilidad-local
  cd etl-movilidad-local
  python -m venv venv
  source venv/bin/activate  # Windows: venv\Scripts\activate
  ```
- [ ] Instalar dependencias
  ```bash
  pip install google-cloud-aiplatform requests feedparser schedule python-dotenv
  ```
- [ ] Configurar `.env`
  ```
  GOOGLE_CLOUD_PROJECT=tu-proyecto
  TWITTER_BEARER_TOKEN=tu-token
  SLACK_WEBHOOK_URL=tu-webhook
  ```
- [ ] Inicializar SQLite
  ```python
  # db.py - 50 líneas
  import sqlite3
  # ... schema básico
  ```

**Tarde (2h):**
- [ ] Implementar extractores básicos
  ```python
  # extractors.py - 100 líneas
  def extract_twitter(): ...
  def extract_metro(): ...
  def extract_rss(): ...
  ```
- [ ] Test de extracción (print results)

**Entregable Día 1:** Extracción funcional desde 2-3 fuentes

---

### Día 2: ADK Scoring (6-7 horas)

**Mañana (3-4h):**
- [ ] Configurar Vertex AI
  ```bash
  gcloud auth application-default login
  gcloud config set project tu-proyecto
  ```
- [ ] Implementar ADK Scorer
  ```python
  # adk_scorer.py - 80 líneas
  from vertexai.generative_models import GenerativeModel

  def score_news(news_item):
      # Prompt optimizado
      # Llamada a Gemini
      # Parse JSON response
      return scoring_result
  ```
- [ ] Crear prompts efectivos
  - System prompt con contexto Medellín
  - User prompt con estructura JSON

**Tarde (3h):**
- [ ] Test con noticias reales
- [ ] Ajustar prompts según resultados
- [ ] Implementar retry logic básico
- [ ] Logging de decisiones

**Entregable Día 2:** ADK clasificando noticias correctamente

---

### Día 3: Pipeline Completo (6-7 horas)

**Mañana (3h):**
- [ ] Implementar normalización
  ```python
  # normalizer.py - 60 líneas
  def normalize_news(raw_news, source):
      # Limpiar HTML
      # Generar hash_url
      # Unificar formato
      return normalized
  ```
- [ ] Implementar deduplicación (check hash_url en SQLite)
- [ ] Integrar todo en pipeline
  ```python
  # main.py - 150 líneas
  def run_etl_pipeline():
      # 1. Extract
      # 2. Normalize
      # 3. Deduplicate
      # 4. Score (ADK)
      # 5. Filter (keep=true)
      # 6. Save (SQLite)
      # 7. Alert (if high severity)
  ```

**Tarde (3-4h):**
- [ ] Implementar alertas Slack
  ```python
  # alerts.py - 30 líneas
  def send_alert(news_item):
      message = format_slack_message(news_item)
      requests.post(SLACK_WEBHOOK_URL, json={"text": message})
  ```
- [ ] Test end-to-end manual
- [ ] Fix bugs

**Entregable Día 3:** Pipeline completo funcional

---

### Día 4: Scheduler y Refinamiento (4-5 horas)

**Mañana (2h):**
- [ ] Implementar scheduler
  ```python
  # scheduler.py - 20 líneas
  import schedule

  schedule.every(5).minutes.do(run_etl_pipeline)

  while True:
      schedule.run_pending()
      time.sleep(1)
  ```
- [ ] Configurar logging
  ```python
  # logger.py - 30 líneas
  import logging
  # File + console handlers
  ```

**Tarde (2-3h):**
- [ ] Test de ejecución continua (30+ min)
- [ ] Verificar duplicados no se insertan
- [ ] Verificar alertas llegan
- [ ] Ajustar intervalos si es necesario

**Entregable Día 4:** Sistema autónomo ejecutándose

---

### Día 5: Testing y Documentación (3-4 horas)

**Mañana (2h):**
- [ ] Crear tests básicos
  ```python
  # test_etl.py - 100 líneas
  import pytest

  def test_normalize():
      assert normalize_news(...) == expected

  def test_adk_scoring():
      result = score_news(sample_news)
      assert 'keep' in result
      assert result['severity'] in VALID_SEVERITIES
  ```
- [ ] Test casos edge (URLs malformadas, HTML roto, etc.)

**Tarde (1-2h):**
- [ ] Crear README_MVP.md
  ```markdown
  # ETL Movilidad - MVP Local

  ## Setup
  1. Install Python 3.11+
  2. pip install -r requirements.txt
  3. Configure .env
  4. python main.py

  ## Configuración
  ...
  ```
- [ ] Documentar variables de entorno
- [ ] Crear requirements.txt
- [ ] Script de setup (`setup.sh`)

**Entregable Día 5:** Sistema testeado y documentado

---

## Comparativa Detallada de Esfuerzo

| Tarea | Plan Original | MVP Local | Reducción |
|-------|---------------|-----------|-----------|
| Infraestructura GCP | 3 días | 1 hora | 96% |
| Base de Datos | 2 días | 1-2 horas | 94% |
| Microservicio ADK | 5 días | 4-6 horas | 90% |
| Microservicio Scraper | 3 días | 2-3 horas | 95% |
| Workflows n8n | 6 días | 30 min | 99% |
| Observabilidad | 2 días | 30 min | 97% |
| Testing | 4 días | 2-3 horas | 95% |
| **TOTAL** | **25 días** | **3-5 días** | **85-90%** |

---

## Análisis de Viabilidad por Requisito

### Requisitos Funcionales

| Requisito | Original | MVP Local | Viable? |
|-----------|----------|-----------|---------|
| Extracción multi-fuente | ✅ 3+ fuentes | ✅ 2-3 fuentes | ✅ Sí |
| Normalización | ✅ Compleja | ✅ Básica | ✅ Sí |
| Deduplicación | ✅ hash_url | ✅ hash_url | ✅ Sí |
| **Scoring ADK** | ✅ Gemini | ✅ Gemini | ✅ **Sí (obligatorio)** |
| Severidad/Tags | ✅ Sí | ✅ Sí | ✅ Sí |
| Persistencia | ✅ Cloud SQL | ✅ SQLite | ✅ Sí |
| Búsqueda semántica | ✅ pgvector | ❌ No | ⚠️ No crítico |
| Alertas | ✅ Slack/Telegram | ✅ Slack | ✅ Sí |
| Ejecución automática | ✅ n8n cron | ✅ schedule lib | ✅ Sí |

**Conclusión:** Todos los requisitos funcionales críticos son viables localmente.

---

### Requisitos No Funcionales

| Requisito | Original | MVP Local | Viable? |
|-----------|----------|-----------|---------|
| Escalabilidad | ✅ Auto-scaling | ❌ 1 máquina | ⚠️ Limitado |
| Alta disponibilidad | ✅ Cloud-native | ❌ Single point | ❌ No |
| Latencia | ✅ < 5s | ✅ < 10s | ✅ Aceptable |
| Error rate | ✅ < 2% | ⚠️ < 5% | ⚠️ Aceptable |
| Backups automáticos | ✅ Cloud SQL | ❌ Manual | ⚠️ No crítico MVP |
| Monitoreo 24/7 | ✅ Cloud Monitoring | ❌ Logs locales | ⚠️ No crítico MVP |
| Costo | 💰 $126-186/mes | 💰 $0-5/mes | ✅ Mucho mejor |

**Conclusión:** MVP no cumple requisitos de producción, pero suficiente para **validar concepto**.

---

## Limitaciones del MVP Local

### ❌ Lo que NO tendrás:

1. **Escalabilidad**
   - 1 máquina = 1 límite de throughput
   - No auto-scaling si crece la carga
   - **Impacto:** OK para ~100-500 noticias/día, insuficiente para 10,000+

2. **Alta Disponibilidad**
   - Si tu máquina se apaga, ETL se detiene
   - Sin redundancia
   - **Impacto:** OK para prototipo, inaceptable para producción

3. **Búsqueda Semántica**
   - Sin embeddings ni pgvector
   - Solo búsqueda por texto (LIKE)
   - **Impacto:** Feature avanzado, no crítico inicialmente

4. **Observabilidad Profesional**
   - Sin dashboards visuales
   - Logs en archivos de texto
   - Sin alertas sofisticadas
   - **Impacto:** Suficiente para debugging, insuficiente para ops

5. **Disaster Recovery**
   - Backups manuales
   - Sin PITR (Point-in-Time Recovery)
   - **Impacto:** Riesgo de pérdida de datos

6. **Compliance y Seguridad**
   - Secrets en `.env` (no rotados)
   - Sin encriptación en reposo
   - **Impacto:** Inaceptable para producción con datos sensibles

### ✅ Lo que SÍ tendrás:

1. **Validación de Concepto**
   - ¿Funciona la idea?
   - ¿ADK clasifica bien?
   - ¿Las fuentes tienen data útil?

2. **Prototipo Funcional**
   - Extrae noticias reales
   - Clasifica con ADK
   - Alerta en Slack
   - Almacena en DB

3. **Desarrollo Rápido**
   - 3-5 días vs 25 días
   - Iteración rápida
   - Fácil debugging

4. **Costo Mínimo**
   - $0-5/mes vs $126-186/mes
   - Solo API calls de Vertex AI

5. **Base para Escalar**
   - Código Python reutilizable
   - Prompts ADK optimizados
   - Schema SQL fácil de migrar

---

## Migración Futura: Local → Cloud

Si el MVP funciona bien y quieres escalar:

### Migración Incremental (2-3 semanas)

**Fase 1: Base de Datos (3 días)**
- Migrar SQLite → Cloud SQL Postgres
- Aplicar migraciones del plan original
- Agregar pgvector

**Fase 2: Containerización (2 días)**
- Dockerizar script Python
- Desplegar en Cloud Run
- Configurar cron con Cloud Scheduler

**Fase 3: Observabilidad (2 días)**
- Integrar Cloud Logging
- Crear dashboards
- Configurar alertas

**Fase 4: Microservicios (opcional, 1-2 semanas)**
- Separar ADK Scorer
- Separar Scraper
- Implementar n8n si se necesita

**Ventaja:** Puedes migrar incrementalmente según necesidad, sin reescribir todo.

---

## Estructura de Archivos MVP

```
etl-movilidad-local/
│
├── .env                    # Secrets (no versionar)
├── .env.example            # Template de variables
├── .gitignore
├── requirements.txt        # Dependencias Python
├── README_MVP.md           # Documentación
│
├── main.py                 # Entry point (150 líneas)
├── scheduler.py            # Cron local (20 líneas)
│
├── extractors.py           # Extracción multi-fuente (100 líneas)
├── normalizer.py           # Limpieza y normalización (60 líneas)
├── adk_scorer.py           # Scoring con Gemini (80 líneas)
├── db.py                   # SQLite operations (100 líneas)
├── alerts.py               # Slack notifications (30 líneas)
├── logger.py               # Logging config (30 líneas)
│
├── prompts/
│   └── system_prompt.txt   # Prompt ADK (50 líneas)
│
├── tests/
│   ├── test_extractors.py
│   ├── test_adk_scorer.py
│   └── test_pipeline.py
│
├── data/
│   ├── etl_movilidad.db    # SQLite database
│   └── logs/
│       └── etl.log         # Logs de ejecución
│
└── scripts/
    ├── setup.sh            # Setup inicial
    └── query_db.py         # Consultas útiles
```

**Total:** ~800-1,200 líneas de código Python (vs 7,400 del plan original)

---

## Recomendación Final

### ¿Cuándo usar MVP Local?

✅ **Usa MVP Local si:**
- Quieres validar la idea rápidamente (3-5 días)
- Presupuesto limitado ($0-5/mes)
- Equipo pequeño (1-2 devs)
- Prototipo o prueba de concepto
- Aprendiendo ADK/ETL
- Volumen bajo (<500 noticias/día)

### ¿Cuándo usar Plan Original (Cloud)?

✅ **Usa Plan Original si:**
- Producción real con usuarios
- Alta disponibilidad requerida (99%+)
- Escalabilidad necesaria (1,000+ noticias/día)
- Compliance y seguridad críticos
- Equipo grande (3+ devs)
- Presupuesto disponible ($150+/mes)
- Largo plazo (6+ meses)

---

## Estrategia Recomendada: Híbrida

### Semana 1-2: MVP Local
1. Implementar MVP local (3-5 días)
2. Validar concepto
3. Iterar prompts ADK
4. Verificar calidad de fuentes

### Evaluación (Día 6-7)
- ¿ADK clasifica bien? (>70% accuracy)
- ¿Las fuentes tienen suficientes noticias? (>20/día)
- ¿Las alertas son útiles? (no spam)

### Decisión:
- ✅ **Si funciona bien:** Continuar a Semana 3-4
- ❌ **Si no funciona:** Pivotar o cancelar (bajo costo hundido)

### Semana 3-4: Migración a Cloud (si aplica)
1. Migrar DB a Cloud SQL
2. Containerizar en Cloud Run
3. Agregar observabilidad
4. Desplegar a producción

**Beneficio:** Validas rápido con bajo riesgo antes de invertir en cloud.

---

## Estimación de Costos Real

### MVP Local (Mensual)

| Item | Costo |
|------|-------|
| Vertex AI (Gemini) | $2-5 (estimado 1,000-2,000 requests/mes) |
| Máquina local | $0 (ya la tienes) |
| Twitter API | $0 (tier gratis) o $100 (Basic) |
| **TOTAL** | **$2-105/mes** |

**Nota:** Twitter API es el costo variable más grande. Alternativas:
- Usar tier gratis (limitado)
- Scraping de Twitter (riesgoso, puede bloquear)
- Omitir Twitter inicialmente (usar solo Metro + medios)

### Comparativa Detallada

| Concepto | Cloud (Original) | Local (MVP) | Ahorro |
|----------|------------------|-------------|--------|
| Infraestructura | $16-51/mes | $0 | 100% |
| Hosting n8n | $5-20/mes | $0 | 100% |
| APIs (Twitter, OpenAI) | $105-115/mes | $2-105/mes | 10-95% |
| **TOTAL** | **$126-186/mes** | **$2-105/mes** | **43-98%** |

---

## Riesgos y Mitigaciones

### Riesgo 1: Máquina local se apaga
**Probabilidad:** Alta
**Impacto:** Alto (ETL se detiene)
**Mitigación:**
- Ejecutar en servidor VPS barato ($5/mes DigitalOcean/Hetzner)
- Script de auto-restart en boot
- Monitoreo con herramienta gratuita (UptimeRobot)

### Riesgo 2: SQLite se corrompe
**Probabilidad:** Media
**Impacto:** Alto (pérdida de datos)
**Mitigación:**
- Backups diarios automáticos (cron + rsync)
- Guardar en Dropbox/Google Drive
- WAL mode habilitado en SQLite

### Riesgo 3: API rate limits
**Probabilidad:** Media
**Impacto:** Medio (menos noticias)
**Mitigación:**
- Respetar límites (sleep entre requests)
- Implementar backoff exponencial
- Diversificar fuentes

### Riesgo 4: Vertex AI cuota excedida
**Probabilidad:** Baja
**Impacto:** Alto (scoring no funciona)
**Mitigación:**
- Monitorear cuota en GCP Console
- Configurar alertas de facturación
- Fallback: marcar keep=true si API falla

---

## Conclusión

### ✅ Viabilidad: ALTA

**Es completamente posible** implementar este ETL de forma local y simplificada manteniendo ADK como único requisito obligatorio.

**Reducción lograda:**
- ⏱️ **Tiempo:** 25 días → 3-5 días (80-90% reducción)
- 💰 **Costo:** $126-186/mes → $2-105/mes (43-98% reducción)
- 📊 **Complejidad:** 6 servicios → 1 script (83% reducción)
- 📝 **Código:** 7,400 líneas → 800-1,200 líneas (84% reducción)

**Lo que se mantiene:**
- ✅ ADK de Google (Gemini 1.5 Flash)
- ✅ Extracción multi-fuente
- ✅ Clasificación inteligente (severity, tags, area)
- ✅ Deduplicación
- ✅ Alertas
- ✅ Persistencia

**Lo que se pierde:**
- ❌ Escalabilidad cloud-native
- ❌ Alta disponibilidad
- ❌ Búsqueda semántica (pgvector)
- ❌ Observabilidad profesional
- ❌ Microservicios

**Recomendación:**
1. **Implementa MVP local** (3-5 días)
2. **Valida concepto** (1 semana)
3. **Si funciona bien, migra a cloud** (2-3 semanas)
4. **Si no funciona, pivotas rápido** (bajo costo hundido)

**Estrategia ganadora:** Empezar local, escalar cuando sea necesario.

---

**Próximos Pasos Inmediatos:**
1. Leer documento completo
2. Decidir: ¿MVP local o plan original?
3. Si MVP local: Seguir "Plan de Implementación MVP Local" (Día 1-5)
4. Si plan original: Seguir `PLAN_IMPLEMENTACION.md`

**Pregunta clave a responder:** ¿Necesitas validar la idea o lanzar a producción inmediatamente?
- Validar idea → **MVP Local**
- Producción inmediata → **Plan Original Cloud**

---

**Versión:** 1.0.0
**Fecha:** 2025-01-29
**Estado:** Análisis completo - Listo para decisión
