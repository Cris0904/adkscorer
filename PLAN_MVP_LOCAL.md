# Plan de Implementación - MVP Local (3-5 días)

## Resumen Ejecutivo

**Objetivo:** Crear un ETL funcional de noticias de movilidad en Medellín ejecutándose localmente.

**Duración:** 3-5 días (1 desarrollador)
**Costo:** $0-5/mes (solo API calls de Vertex AI)
**Tecnologías:** Python 3.11+, SQLite, Google Vertex AI (ADK), Schedule

**Resultado Final:** Script Python autónomo que cada 5 minutos:
1. Extrae noticias de 2-3 fuentes
2. Clasifica con ADK (Gemini 1.5 Flash)
3. Guarda en SQLite
4. Alerta en Slack si severity=high/critical

---

## Pre-requisitos (1 hora)

### Requisitos de Software

- [ ] **Python 3.11 o superior**
  ```bash
  python --version  # Debe ser >= 3.11
  ```

- [ ] **Git**
  ```bash
  git --version
  ```

- [ ] **Cuenta GCP con Vertex AI habilitado**
  - Ir a https://console.cloud.google.com
  - Crear proyecto o usar existente
  - Habilitar Vertex AI API
  - Configurar billing (modelo pago por uso)

- [ ] **gcloud CLI instalado**
  ```bash
  gcloud --version
  ```

- [ ] **Editor de código** (VSCode, PyCharm, etc.)

### Credenciales y Accesos

- [ ] **Autenticación GCP**
  ```bash
  gcloud auth application-default login
  gcloud config set project TU_PROYECTO_ID
  ```

- [ ] **Slack Webhook** (opcional pero recomendado)
  - Ir a https://api.slack.com/messaging/webhooks
  - Crear Incoming Webhook
  - Copiar URL (ej: `https://hooks.slack.com/services/xxx`)

- [ ] **Twitter API** (opcional)
  - Tier gratuito: https://developer.twitter.com/
  - O omitir Twitter inicialmente

### Verificación de Setup

```bash
# Test de autenticación GCP
gcloud auth list

# Test de Python
python -c "import sys; print(f'Python {sys.version}')"

# Test de pip
pip --version
```

✅ Si todo funciona, continuar al Día 1.

---

## DÍA 1: SETUP Y EXTRACCIÓN (4-5 horas)

### Objetivos del Día
- ✅ Proyecto Python inicializado
- ✅ Dependencias instaladas
- ✅ Extracción funcional desde 2 fuentes
- ✅ SQLite inicializado

---

### Parte 1: Inicialización del Proyecto (30 min)

#### T1.1: Crear estructura de proyecto

```bash
mkdir etl-movilidad-local
cd etl-movilidad-local

# Crear estructura de directorios
mkdir -p data/logs prompts tests scripts

# Crear archivos base
touch main.py scheduler.py extractors.py normalizer.py
touch adk_scorer.py db.py alerts.py logger.py
touch .env .gitignore requirements.txt README.md
```

#### T1.2: Configurar entorno virtual

```bash
python -m venv venv

# Activar entorno
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Verificar activación
which python  # Debe apuntar a venv/bin/python
```

#### T1.3: Crear requirements.txt

```txt
# requirements.txt
google-cloud-aiplatform==1.40.0
requests==2.31.0
feedparser==6.0.10
schedule==1.2.0
python-dotenv==1.0.0
beautifulsoup4==4.12.2
lxml==4.9.3
pytest==7.4.3
```

#### T1.4: Instalar dependencias

```bash
pip install -r requirements.txt

# Verificar instalación
pip list | grep google-cloud-aiplatform
```

#### T1.5: Configurar .env

```bash
# .env
GCP_PROJECT_ID=tu-proyecto-gcp
GCP_LOCATION=us-central1

# Fuentes de datos
TWITTER_BEARER_TOKEN=Bearer_tu_token_aqui  # Opcional
METRO_RSS_URL=https://www.metrodemedellin.gov.co/feed

# Alertas
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Configuración
LOG_LEVEL=INFO
ETL_INTERVAL_MINUTES=5
DB_PATH=data/etl_movilidad.db
```

#### T1.6: Configurar .gitignore

```
# .gitignore
venv/
__pycache__/
*.pyc
.env
data/*.db
data/logs/*.log
*.log
.DS_Store
.vscode/
.idea/
```

**✅ Checkpoint 1:** Proyecto inicializado con estructura y dependencias.

---

### Parte 2: Base de Datos SQLite (45 min)

#### T1.7: Implementar db.py

```python
# db.py
import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class NewsDatabase:
    def __init__(self, db_path: str = "data/etl_movilidad.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicializa el esquema de base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla principal de noticias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                hash_url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                published_at TEXT NOT NULL,

                -- Scoring ADK
                severity TEXT,
                tags TEXT,
                area TEXT,
                summary TEXT,
                relevance_score REAL,

                -- Metadata
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash_url ON news_item(hash_url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON news_item(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON news_item(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON news_item(severity)')

        # Tabla de log de ejecuciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS etl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                source TEXT NOT NULL,
                items_extracted INTEGER DEFAULT 0,
                items_kept INTEGER DEFAULT 0,
                items_discarded INTEGER DEFAULT 0,
                items_duplicated INTEGER DEFAULT 0,
                errors TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def generate_hash_url(self, url: str) -> str:
        """Genera hash SHA256 para deduplicación"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def is_duplicate(self, url: str) -> bool:
        """Verifica si una URL ya existe"""
        hash_url = self.generate_hash_url(url)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT 1 FROM news_item WHERE hash_url = ?', (hash_url,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists

    def insert_news(self, news: Dict) -> Optional[int]:
        """Inserta una noticia y retorna el ID"""
        hash_url = self.generate_hash_url(news['url'])

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO news_item (
                    source, url, hash_url, title, body, published_at,
                    severity, tags, area, summary, relevance_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news['source'],
                news['url'],
                hash_url,
                news['title'],
                news['body'],
                news['published_at'],
                news.get('severity'),
                ','.join(news.get('tags', [])),
                news.get('area'),
                news.get('summary'),
                news.get('relevance_score')
            ))

            conn.commit()
            news_id = cursor.lastrowid
            logger.info(f"Inserted news ID {news_id}: {news['title'][:50]}")
            return news_id

        except sqlite3.IntegrityError:
            logger.warning(f"Duplicate news: {news['url']}")
            return None

        finally:
            conn.close()

    def get_recent_news(self, limit: int = 20):
        """Obtiene noticias recientes"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM news_item
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def log_execution(self, execution_data: Dict):
        """Registra una ejecución del ETL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO etl_log (
                execution_id, source, items_extracted, items_kept,
                items_discarded, items_duplicated, errors,
                started_at, finished_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            execution_data['execution_id'],
            execution_data['source'],
            execution_data['items_extracted'],
            execution_data['items_kept'],
            execution_data['items_discarded'],
            execution_data['items_duplicated'],
            execution_data.get('errors', ''),
            execution_data['started_at'],
            execution_data['finished_at']
        ))

        conn.commit()
        conn.close()
```

**✅ Checkpoint 2:** Base de datos SQLite con schema funcional.

---

### Parte 3: Extracción de Fuentes (2 horas)

#### T1.8: Implementar extractors.py

```python
# extractors.py
import requests
import feedparser
import logging
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NewsExtractor:
    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ETL-Movilidad-Bot/1.0)'
        })

    def extract_all(self) -> List[Dict]:
        """Extrae de todas las fuentes configuradas"""
        all_news = []

        # Fuente 1: Metro de Medellín (RSS)
        try:
            metro_news = self.extract_metro_rss()
            all_news.extend(metro_news)
            logger.info(f"Extracted {len(metro_news)} items from Metro RSS")
        except Exception as e:
            logger.error(f"Error extracting Metro RSS: {e}")

        # Fuente 2: El Colombiano (RSS)
        try:
            colombiano_news = self.extract_el_colombiano_rss()
            all_news.extend(colombiano_news)
            logger.info(f"Extracted {len(colombiano_news)} items from El Colombiano")
        except Exception as e:
            logger.error(f"Error extracting El Colombiano: {e}")

        # Fuente 3: Twitter (opcional)
        if self.config.get('TWITTER_BEARER_TOKEN'):
            try:
                twitter_news = self.extract_twitter()
                all_news.extend(twitter_news)
                logger.info(f"Extracted {len(twitter_news)} items from Twitter")
            except Exception as e:
                logger.error(f"Error extracting Twitter: {e}")

        return all_news

    def extract_metro_rss(self) -> List[Dict]:
        """Extrae noticias del RSS del Metro de Medellín"""
        url = "https://www.metrodemedellin.gov.co/feed"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            news_items = []

            for entry in feed.entries[:10]:  # Primeras 10 entradas
                news_items.append({
                    'source': 'metro_medellin',
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'body': self._clean_html(entry.get('description', '')),
                    'published_at': self._parse_date(entry.get('published', '')),
                    'raw_data': entry
                })

            return news_items

        except Exception as e:
            logger.error(f"Metro RSS extraction failed: {e}")
            return []

    def extract_el_colombiano_rss(self) -> List[Dict]:
        """Extrae noticias del RSS de El Colombiano (sección Medellín)"""
        url = "https://www.elcolombiano.com/rss/medellin.xml"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            news_items = []

            for entry in feed.entries[:10]:
                news_items.append({
                    'source': 'el_colombiano',
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'body': self._clean_html(entry.get('description', '')),
                    'published_at': self._parse_date(entry.get('published', '')),
                    'raw_data': entry
                })

            return news_items

        except Exception as e:
            logger.error(f"El Colombiano RSS extraction failed: {e}")
            return []

    def extract_twitter(self) -> List[Dict]:
        """Extrae tweets sobre movilidad en Medellín (requiere API)"""
        bearer_token = self.config.get('TWITTER_BEARER_TOKEN')
        if not bearer_token:
            return []

        url = "https://api.twitter.com/2/tweets/search/recent"
        query = "(movilidad OR tráfico OR Metro) (Medellín OR Medellin) -is:retweet"

        headers = {
            "Authorization": bearer_token
        }

        params = {
            "query": query,
            "max_results": 20,
            "tweet.fields": "created_at,author_id,text",
        }

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            news_items = []

            for tweet in data.get('data', []):
                news_items.append({
                    'source': 'twitter',
                    'url': f"https://twitter.com/user/status/{tweet['id']}",
                    'title': tweet['text'][:100],
                    'body': tweet['text'],
                    'published_at': tweet['created_at'],
                    'raw_data': tweet
                })

            return news_items

        except Exception as e:
            logger.error(f"Twitter extraction failed: {e}")
            return []

    def _clean_html(self, html: str) -> str:
        """Limpia HTML y extrae texto plano"""
        if not html:
            return ""

        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text[:2000]  # Limitar tamaño

    def _parse_date(self, date_str: str) -> str:
        """Normaliza formato de fecha a ISO 8601"""
        if not date_str:
            return datetime.now().isoformat()

        try:
            # feedparser ya parsea las fechas
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
```

**✅ Checkpoint 3:** Extracción funcional desde 2-3 fuentes.

---

### Parte 4: Testing de Extracción (30 min)

#### T1.9: Crear script de prueba

```python
# test_extraction.py
import os
from dotenv import load_dotenv
from extractors import NewsExtractor
from db import NewsDatabase
import json

load_dotenv()

def test_extraction():
    config = {
        'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN')
    }

    extractor = NewsExtractor(config)

    print("🔍 Extrayendo noticias...\n")
    news = extractor.extract_all()

    print(f"✅ Total extraído: {len(news)} noticias\n")

    for i, item in enumerate(news[:5], 1):
        print(f"--- Noticia {i} ---")
        print(f"Fuente: {item['source']}")
        print(f"Título: {item['title']}")
        print(f"URL: {item['url']}")
        print(f"Body: {item['body'][:100]}...")
        print()

    # Guardar en JSON para inspección
    with open('data/extracted_news.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, indent=2, ensure_ascii=False)

    print(f"📄 Datos guardados en data/extracted_news.json")

if __name__ == "__main__":
    test_extraction()
```

#### T1.10: Ejecutar prueba

```bash
python test_extraction.py
```

**Salida esperada:**
```
🔍 Extrayendo noticias...

✅ Total extraído: 25 noticias

--- Noticia 1 ---
Fuente: metro_medellin
Título: Estado del sistema de transporte
URL: https://...
Body: El sistema de transporte masivo opera con normalidad...

...
```

**✅ Checkpoint 4:** Extracción validada con datos reales.

---

### Resumen Día 1

**Tiempo total:** 4-5 horas

**Logros:**
- ✅ Proyecto Python inicializado con estructura modular
- ✅ SQLite con schema completo (2 tablas, 4 índices)
- ✅ Extracción funcional desde Metro Medellín y El Colombiano
- ✅ Opción de Twitter API configurada
- ✅ Test de extracción validado con datos reales

**Archivos creados:**
- `db.py` (~150 líneas)
- `extractors.py` (~180 líneas)
- `test_extraction.py` (~40 líneas)
- `requirements.txt`
- `.env`
- `.gitignore`

**Próximo paso:** Día 2 - Implementar ADK Scorer

---

## DÍA 2: ADK SCORING (6-7 horas)

### Objetivos del Día
- ✅ Integración con Vertex AI (Gemini)
- ✅ Prompts optimizados para Medellín
- ✅ Scoring funcional (keep/discard, severity, tags)
- ✅ Tests con noticias reales

---

### Parte 1: Configuración de Vertex AI (1 hora)

#### T2.1: Verificar acceso a Vertex AI

```bash
# Verificar autenticación
gcloud auth application-default login

# Configurar proyecto
gcloud config set project TU_PROYECTO_ID

# Verificar que Vertex AI esté habilitado
gcloud services list --enabled | grep aiplatform

# Si no está habilitado:
gcloud services enable aiplatform.googleapis.com
```

#### T2.2: Test de Vertex AI

```python
# test_vertex_ai.py
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
import os

def test_vertex_ai():
    project_id = os.getenv('GCP_PROJECT_ID')
    location = os.getenv('GCP_LOCATION', 'us-central1')

    aiplatform.init(project=project_id, location=location)

    model = GenerativeModel("gemini-1.5-flash")

    prompt = "Hola, ¿puedes ayudarme a clasificar noticias de movilidad en Medellín?"

    response = model.generate_content(prompt)

    print("✅ Vertex AI conectado correctamente")
    print(f"Respuesta: {response.text}")

if __name__ == "__main__":
    test_vertex_ai()
```

```bash
python test_vertex_ai.py
```

**Salida esperada:**
```
✅ Vertex AI conectado correctamente
Respuesta: ¡Por supuesto! Puedo ayudarte...
```

**✅ Checkpoint 5:** Vertex AI configurado y funcional.

---

### Parte 2: Prompts para ADK (2 horas)

#### T2.3: Crear system prompt

```python
# prompts/system_prompt.py

SYSTEM_PROMPT = """Eres un experto analista de noticias de movilidad urbana en Medellín, Colombia.

Tu tarea es evaluar si una noticia es RELEVANTE para un sistema de alertas de movilidad y extraer información estructurada.

## CONTEXTO DE MEDELLÍN

**Transporte Público:**
- Metro de Medellín: Líneas A, B (metro elevado), T (Tranvía), H, K, M, P (Metrocable)
- Metroplús: BRT (carriles exclusivos)
- Buses integrados

**Zonas Clave:**
- Centro: El Hueco, La Candelaria, Parque Berrío
- El Poblado: Zona financiera y comercial (Calle 10, Av El Poblado)
- Laureles: Avenida 33, Estadio
- Belén: Av 80, San Antonio de Prado
- Norte: Bello, Aranjuez, Castilla
- Oriente: Buenos Aires, Manrique

**Vías Principales:**
- Autopista Sur, Autopista Norte
- Av 80 (Vía Las Palmas)
- Av Regional
- Av El Poblado
- Av 33 (Laureles)

## CRITERIOS DE RELEVANCIA (keep=true)

✅ INCLUIR si:
1. Afecta tráfico vehicular o transporte público
2. Eventos en vías principales o zonas con alta afluencia
3. Cierres viales programados o emergencias
4. Incidentes del Metro/Metroplús/buses
5. Accidentes con impacto en movilidad
6. Manifestaciones o eventos masivos
7. Obras de infraestructura vial
8. Condiciones climáticas que afectan vías

❌ DESCARTAR si:
- Noticias generales sin impacto directo en movilidad
- Eventos en municipios fuera de Medellín y área metropolitana
- Publicidad o contenido comercial
- Duplicados (ya procesados)
- Contenido irrelevante

## SEVERIDAD

**critical**: Cierre total de vías principales, Metro fuera de servicio, emergencias mayores
**high**: Cierres importantes, accidentes graves, manifestaciones grandes, alteraciones del Metro
**medium**: Obras programadas, cierres parciales, tráfico pesado, retrasos menores
**low**: Alertas preventivas, mantenimientos nocturnos, desvíos menores

## ÁREAS

Especifica la comuna, barrio o zona afectada:
- Ejemplos: "El Poblado", "Centro", "Laureles-Estadio", "Belén", "Aranjuez", "Autopista Sur"

## TAGS

Usa SOLO estos tags (máximo 3):
- cierre_vial
- accidente
- obra
- metro
- bus
- manifestacion
- evento
- trafico
- emergencia
- mantenimiento
- clima

## FORMATO DE RESPUESTA

Responde SIEMPRE en JSON válido con esta estructura exacta:

```json
{
  "keep": true,
  "relevance_score": 0.85,
  "severity": "high",
  "area": "El Poblado",
  "tags": ["cierre_vial", "manifestacion"],
  "summary": "Cierre total en Av El Poblado entre calles 10 y 12 desde las 2pm por manifestación. Se recomienda tomar vías alternas.",
  "reasoning": "Afecta vía principal en zona comercial durante hora pico"
}
```

**IMPORTANTE:**
- Si keep=false, omite severity, area, tags y summary
- summary debe ser máximo 200 caracteres
- reasoning es opcional (para debugging)
- relevance_score entre 0.0 y 1.0
"""

def build_user_prompt(news_item: dict) -> str:
    """Construye el prompt de usuario con la noticia"""
    return f"""Analiza esta noticia:

**FUENTE:** {news_item['source']}
**URL:** {news_item['url']}
**TÍTULO:** {news_item['title']}
**FECHA:** {news_item['published_at']}

**CONTENIDO:**
{news_item['body'][:1500]}

Responde en JSON siguiendo la estructura especificada."""
```

**✅ Checkpoint 6:** Prompts diseñados y optimizados para Medellín.

---

### Parte 3: Implementar ADK Scorer (2-3 horas)

#### T2.4: Crear adk_scorer.py

```python
# adk_scorer.py
import json
import logging
import os
from typing import Dict, Optional
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, GenerationConfig
from prompts.system_prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

class ADKScorer:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.location = os.getenv('GCP_LOCATION', 'us-central1')
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

        logger.info(f"ADK Scorer initialized with {self.model_name}")

    def score(self, news_item: Dict) -> Optional[Dict]:
        """
        Clasifica una noticia usando ADK (Gemini 1.5 Flash)

        Args:
            news_item: Dict con keys: source, url, title, body, published_at

        Returns:
            Dict con scoring result o None si error
        """
        try:
            # Construir prompts
            user_prompt = build_user_prompt(news_item)

            # Llamada a Gemini
            response = self.model.generate_content(
                [SYSTEM_PROMPT, user_prompt]
            )

            # Parsear respuesta JSON
            result = json.loads(response.text)

            # Validar estructura
            if not self._validate_result(result):
                logger.error(f"Invalid ADK response: {result}")
                return self._fallback_result(news_item)

            logger.info(
                f"ADK scored: keep={result['keep']}, "
                f"severity={result.get('severity', 'N/A')}, "
                f"score={result['relevance_score']}"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response.text}")
            return self._fallback_result(news_item)

        except Exception as e:
            logger.error(f"ADK scoring error: {e}", exc_info=True)
            return self._fallback_result(news_item)

    def _validate_result(self, result: Dict) -> bool:
        """Valida que el resultado tenga estructura correcta"""
        required_keys = ['keep', 'relevance_score']

        for key in required_keys:
            if key not in result:
                return False

        # Si keep=true, debe tener campos adicionales
        if result['keep']:
            required_when_keep = ['severity', 'tags', 'summary']
            for key in required_when_keep:
                if key not in result:
                    return False

        return True

    def _fallback_result(self, news_item: Dict) -> Dict:
        """
        Resultado conservador cuando ADK falla.
        Marca como relevante para revisión manual.
        """
        logger.warning(f"Using fallback result for: {news_item['url']}")

        return {
            'keep': True,
            'relevance_score': 0.5,
            'severity': 'medium',
            'area': 'desconocido',
            'tags': ['revision_manual'],
            'summary': f"ERROR AL PROCESAR: {news_item['title'][:100]}",
            'reasoning': 'Fallback conservador por error en ADK'
        }
```

**✅ Checkpoint 7:** ADK Scorer implementado con retry y fallback.

---

### Parte 4: Testing de ADK (1-2 horas)

#### T2.5: Crear tests de scoring

```python
# test_adk_scoring.py
import os
from dotenv import load_dotenv
from adk_scorer import ADKScorer
import json

load_dotenv()

def test_scoring():
    scorer = ADKScorer()

    # Test 1: Noticia relevante (esperado: keep=true, severity=high)
    test_news_1 = {
        'source': 'test',
        'url': 'https://test.com/news1',
        'title': 'Cierre total en Avenida El Poblado por manifestación',
        'body': 'La Alcaldía de Medellín informó que la Avenida El Poblado estará cerrada desde las 2pm hasta las 8pm debido a una manifestación pacífica. Se recomienda tomar vías alternas como la Av Las Vegas o la Loma de Los Balsos.',
        'published_at': '2024-01-15T10:00:00'
    }

    # Test 2: Noticia irrelevante (esperado: keep=false)
    test_news_2 = {
        'source': 'test',
        'url': 'https://test.com/news2',
        'title': 'Nueva tienda de ropa abre en Laureles',
        'body': 'Una nueva tienda de moda internacional abrió sus puertas en el barrio Laureles, ofreciendo las últimas tendencias de la temporada.',
        'published_at': '2024-01-15T11:00:00'
    }

    # Test 3: Incidente Metro (esperado: keep=true, severity=critical)
    test_news_3 = {
        'source': 'test',
        'url': 'https://test.com/news3',
        'title': 'Metro de Medellín suspende servicio en Línea A',
        'body': 'El Metro de Medellín informó la suspensión temporal del servicio en la Línea A debido a una falla técnica. Se están habilitando buses de contingencia.',
        'published_at': '2024-01-15T12:00:00'
    }

    test_cases = [test_news_1, test_news_2, test_news_3]
    results = []

    print("🧪 Iniciando tests de ADK Scoring...\n")

    for i, news in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        print(f"Título: {news['title']}")

        result = scorer.score(news)

        print(f"✓ Keep: {result['keep']}")
        print(f"✓ Relevance Score: {result['relevance_score']}")
        if result['keep']:
            print(f"✓ Severity: {result['severity']}")
            print(f"✓ Area: {result.get('area', 'N/A')}")
            print(f"✓ Tags: {', '.join(result['tags'])}")
            print(f"✓ Summary: {result['summary']}")
        print()

        results.append({
            'test_case': i,
            'news': news,
            'result': result
        })

    # Guardar resultados
    with open('data/adk_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("✅ Tests completados")
    print("📄 Resultados guardados en data/adk_test_results.json")

    # Validaciones básicas
    assert results[0]['result']['keep'] == True, "Test 1 debe ser relevante"
    assert results[1]['result']['keep'] == False, "Test 2 debe ser irrelevante"
    assert results[2]['result']['keep'] == True, "Test 3 debe ser relevante"
    assert results[2]['result']['severity'] in ['high', 'critical'], "Test 3 debe ser severidad alta"

    print("\n✅ Todas las validaciones pasaron")

if __name__ == "__main__":
    test_scoring()
```

#### T2.6: Ejecutar tests

```bash
python test_adk_scoring.py
```

**Salida esperada:**
```
🧪 Iniciando tests de ADK Scoring...

--- Test Case 1 ---
Título: Cierre total en Avenida El Poblado por manifestación
✓ Keep: True
✓ Relevance Score: 0.9
✓ Severity: high
✓ Area: El Poblado
✓ Tags: cierre_vial, manifestacion
✓ Summary: Cierre total en Av El Poblado 2pm-8pm por manifestación

--- Test Case 2 ---
Título: Nueva tienda de ropa abre en Laureles
✓ Keep: False
✓ Relevance Score: 0.1

--- Test Case 3 ---
Título: Metro de Medellín suspende servicio en Línea A
✓ Keep: True
✓ Relevance Score: 0.95
✓ Severity: critical
✓ Area: Centro
✓ Tags: metro, emergencia
✓ Summary: Metro Línea A suspendido por falla técnica, buses de contingencia

✅ Tests completados
✅ Todas las validaciones pasaron
```

**✅ Checkpoint 8:** ADK Scorer validado con casos de prueba.

---

### Parte 5: Ajuste de Prompts (1 hora)

#### T2.7: Iterar y mejorar prompts

Basándote en los resultados de los tests:

1. **Si ADK descarta demasiado** (keep rate < 30%):
   - Ajustar `SYSTEM_PROMPT`: relajar criterios de relevancia
   - Ampliar lista de tags
   - Reducir threshold de relevancia

2. **Si ADK acepta demasiado** (keep rate > 80%):
   - Ajustar `SYSTEM_PROMPT`: ser más estricto en criterios
   - Enfatizar descartes (noticias generales, publicidad)

3. **Si severity es incorrecta**:
   - Ajustar definiciones de severidad con ejemplos más claros
   - Agregar casos edge en el prompt

4. **Ejecutar tests nuevamente** hasta obtener:
   - Keep rate: 40-60%
   - Severity alta solo para casos críticos
   - Tags relevantes y específicos

**✅ Checkpoint 9:** Prompts optimizados y validados.

---

### Resumen Día 2

**Tiempo total:** 6-7 horas

**Logros:**
- ✅ Vertex AI configurado y funcional
- ✅ Prompts optimizados para contexto de Medellín
- ✅ ADK Scorer implementado con fallback robusto
- ✅ Tests de casos reales pasando
- ✅ Clasificación de noticias funcional (keep/discard, severity, tags)

**Archivos creados:**
- `adk_scorer.py` (~120 líneas)
- `prompts/system_prompt.py` (~180 líneas)
- `test_adk_scoring.py` (~90 líneas)

**Métricas obtenidas:**
- Latencia ADK: 2-4 segundos por noticia
- Keep rate: 40-60% (óptimo)
- Accuracy de severidad: visual validation OK

**Próximo paso:** Día 3 - Pipeline completo

---

## DÍA 3: PIPELINE COMPLETO (6-7 horas)

### Objetivos del Día
- ✅ Normalización de datos
- ✅ Pipeline end-to-end funcional
- ✅ Alertas en Slack
- ✅ Integración completa

---

### Parte 1: Normalización (1-2 horas)

#### T3.1: Implementar normalizer.py

```python
# normalizer.py
import re
import logging
from typing import Dict
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class NewsNormalizer:
    def normalize(self, raw_news: Dict) -> Dict:
        """
        Normaliza una noticia cruda a formato estándar.

        Args:
            raw_news: Dict con source, url, title, body, published_at

        Returns:
            Dict normalizado listo para ADK scoring
        """
        try:
            normalized = {
                'source': raw_news['source'],
                'url': self._clean_url(raw_news['url']),
                'title': self._clean_text(raw_news['title']),
                'body': self._clean_body(raw_news['body']),
                'published_at': self._normalize_date(raw_news['published_at']),
                'extracted_at': datetime.now().isoformat()
            }

            # Validar campos obligatorios
            if not self._validate(normalized):
                logger.warning(f"Invalid normalized news: {raw_news['url']}")
                return None

            return normalized

        except Exception as e:
            logger.error(f"Normalization error: {e}", exc_info=True)
            return None

    def _clean_url(self, url: str) -> str:
        """Limpia y normaliza URL"""
        # Remover parámetros de tracking
        url = re.sub(r'\?(utm_|fbclid|gclid).*', '', url)
        # Asegurar https
        url = url.replace('http://', 'https://')
        return url.strip()

    def _clean_text(self, text: str) -> str:
        """Limpia texto general"""
        if not text:
            return ""

        # Remover múltiples espacios
        text = re.sub(r'\s+', ' ', text)
        # Remover caracteres especiales problemáticos
        text = text.replace('\r', '').replace('\n', ' ')
        return text.strip()

    def _clean_body(self, body: str) -> str:
        """Limpia cuerpo de noticia (HTML, etc.)"""
        if not body:
            return ""

        # Remover HTML tags si existen
        soup = BeautifulSoup(body, 'html.parser')
        text = soup.get_text(separator=' ')

        # Limpiar espacios
        text = self._clean_text(text)

        # Limitar tamaño (para no exceder límites de ADK)
        if len(text) > 2000:
            text = text[:2000] + "..."

        return text

    def _normalize_date(self, date_str: str) -> str:
        """Normaliza fecha a formato ISO 8601"""
        if not date_str:
            return datetime.now().isoformat()

        try:
            # Si ya es ISO, retornar
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_str
        except:
            # Intentar parsear formatos comunes
            try:
                from dateutil import parser
                dt = parser.parse(date_str)
                return dt.isoformat()
            except:
                logger.warning(f"Could not parse date: {date_str}")
                return datetime.now().isoformat()

    def _validate(self, news: Dict) -> bool:
        """Valida que la noticia tenga campos obligatorios"""
        required_fields = ['source', 'url', 'title', 'body']

        for field in required_fields:
            if not news.get(field):
                return False

        # Validar tamaños mínimos
        if len(news['title']) < 10:
            return False

        if len(news['body']) < 50:
            return False

        return True
```

**✅ Checkpoint 10:** Normalización implementada y robusta.

---

### Parte 2: Alertas Slack (1 hora)

#### T3.2: Implementar alerts.py

```python
# alerts.py
import requests
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

        if not self.slack_webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not configured, alerts disabled")

    def should_alert(self, news: Dict) -> bool:
        """Decide si una noticia amerita alerta"""
        severity = news.get('severity', '').lower()
        return severity in ['high', 'critical']

    def send_alert(self, news: Dict):
        """Envía alerta a Slack para noticias de alta severidad"""
        if not self.slack_webhook_url:
            logger.info("Alert skipped (Slack not configured)")
            return

        if not self.should_alert(news):
            return

        try:
            message = self._format_slack_message(news)

            response = requests.post(
                self.slack_webhook_url,
                json={"text": message, "unfurl_links": False},
                timeout=5
            )

            response.raise_for_status()

            logger.info(f"Slack alert sent for: {news['title'][:50]}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    def _format_slack_message(self, news: Dict) -> str:
        """Formatea mensaje para Slack"""
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': 'ℹ️',
            'low': '📌'
        }

        emoji = severity_emoji.get(news.get('severity', 'low'), 'ℹ️')

        message = f"""{emoji} *ALERTA DE MOVILIDAD - {news['severity'].upper()}*

*Fuente:* {news['source']}
*Área:* {news.get('area', 'N/A')}
*Fecha:* {news.get('published_at', 'N/A')}

*Título:* {news['title']}

*Resumen:* {news.get('summary', 'N/A')}

*Tags:* {', '.join(news.get('tags', []))}

<{news['url']}|Ver noticia completa>
"""

        return message
```

**✅ Checkpoint 11:** Alertas Slack funcionales.

---

### Parte 3: Logger Configurado (30 min)

#### T3.3: Implementar logger.py

```python
# logger.py
import logging
import sys
from pathlib import Path

def setup_logger(log_level: str = "INFO"):
    """Configura logging para consola y archivo"""

    # Crear directorio de logs si no existe
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configurar formato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Handler para archivo
    file_handler = logging.FileHandler(
        log_dir / 'etl.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Configurar root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[file_handler, console_handler]
    )

    # Reducir verbosidad de librerías externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
```

**✅ Checkpoint 12:** Logging configurado.

---

### Parte 4: Pipeline Principal (2-3 horas)

#### T3.4: Implementar main.py

```python
# main.py
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
import uuid

from logger import setup_logger
from extractors import NewsExtractor
from normalizer import NewsNormalizer
from adk_scorer import ADKScorer
from db import NewsDatabase
from alerts import AlertManager

# Cargar variables de entorno
load_dotenv()

# Configurar logging
setup_logger(log_level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

class ETLPipeline:
    def __init__(self):
        self.config = {
            'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN'),
            'SLACK_WEBHOOK_URL': os.getenv('SLACK_WEBHOOK_URL'),
            'GCP_PROJECT_ID': os.getenv('GCP_PROJECT_ID'),
            'GCP_LOCATION': os.getenv('GCP_LOCATION', 'us-central1')
        }

        self.extractor = NewsExtractor(self.config)
        self.normalizer = NewsNormalizer()
        self.scorer = ADKScorer()
        self.db = NewsDatabase(os.getenv('DB_PATH', 'data/etl_movilidad.db'))
        self.alert_manager = AlertManager()

    def run(self):
        """Ejecuta el pipeline ETL completo"""
        execution_id = str(uuid.uuid4())
        started_at = datetime.now()

        logger.info(f"🚀 Starting ETL execution {execution_id}")

        stats = {
            'execution_id': execution_id,
            'source': 'aggregated',
            'items_extracted': 0,
            'items_kept': 0,
            'items_discarded': 0,
            'items_duplicated': 0,
            'errors': '',
            'started_at': started_at.isoformat(),
            'finished_at': None
        }

        try:
            # 1. EXTRACT
            logger.info("📥 Phase 1: Extraction")
            raw_news = self.extractor.extract_all()
            stats['items_extracted'] = len(raw_news)
            logger.info(f"Extracted {len(raw_news)} items")

            # 2. NORMALIZE
            logger.info("🔧 Phase 2: Normalization")
            normalized_news = []
            for raw in raw_news:
                normalized = self.normalizer.normalize(raw)
                if normalized:
                    normalized_news.append(normalized)

            logger.info(f"Normalized {len(normalized_news)} items")

            # 3. DEDUPLICATE
            logger.info("🔍 Phase 3: Deduplication")
            unique_news = []
            for news in normalized_news:
                if self.db.is_duplicate(news['url']):
                    stats['items_duplicated'] += 1
                    logger.debug(f"Duplicate: {news['url']}")
                else:
                    unique_news.append(news)

            logger.info(f"Found {len(unique_news)} unique items")

            # 4. SCORE (ADK)
            logger.info("🤖 Phase 4: ADK Scoring")
            scored_news = []
            for news in unique_news:
                scoring = self.scorer.score(news)
                if scoring:
                    news.update(scoring)
                    scored_news.append(news)

            logger.info(f"Scored {len(scored_news)} items")

            # 5. FILTER (keep=true)
            logger.info("✅ Phase 5: Filtering")
            filtered_news = [n for n in scored_news if n.get('keep', False)]
            stats['items_kept'] = len(filtered_news)
            stats['items_discarded'] = len(scored_news) - len(filtered_news)

            logger.info(f"Keeping {len(filtered_news)} items, discarding {stats['items_discarded']}")

            # 6. SAVE
            logger.info("💾 Phase 6: Persisting to database")
            saved_count = 0
            for news in filtered_news:
                news_id = self.db.insert_news(news)
                if news_id:
                    saved_count += 1

            logger.info(f"Saved {saved_count} items to database")

            # 7. ALERT
            logger.info("📢 Phase 7: Sending alerts")
            alert_count = 0
            for news in filtered_news:
                if self.alert_manager.should_alert(news):
                    self.alert_manager.send_alert(news)
                    alert_count += 1

            logger.info(f"Sent {alert_count} alerts")

        except Exception as e:
            logger.error(f"ETL execution failed: {e}", exc_info=True)
            stats['errors'] = str(e)

        finally:
            # Log execution stats
            finished_at = datetime.now()
            stats['finished_at'] = finished_at.isoformat()

            duration = (finished_at - started_at).total_seconds()

            logger.info(f"✅ ETL execution completed in {duration:.2f}s")
            logger.info(f"Stats: {stats}")

            self.db.log_execution(stats)

if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run()
```

**✅ Checkpoint 13:** Pipeline end-to-end funcional.

---

### Parte 5: Testing End-to-End (1 hora)

#### T3.5: Ejecutar pipeline completo

```bash
python main.py
```

**Salida esperada:**
```
2024-01-15 14:30:00 - __main__ - INFO - 🚀 Starting ETL execution a1b2c3d4...
2024-01-15 14:30:00 - __main__ - INFO - 📥 Phase 1: Extraction
2024-01-15 14:30:02 - extractors - INFO - Extracted 12 items from Metro RSS
2024-01-15 14:30:04 - extractors - INFO - Extracted 15 items from El Colombiano
2024-01-15 14:30:04 - __main__ - INFO - Extracted 27 items
2024-01-15 14:30:04 - __main__ - INFO - 🔧 Phase 2: Normalization
2024-01-15 14:30:04 - __main__ - INFO - Normalized 27 items
2024-01-15 14:30:04 - __main__ - INFO - 🔍 Phase 3: Deduplication
2024-01-15 14:30:05 - __main__ - INFO - Found 22 unique items
2024-01-15 14:30:05 - __main__ - INFO - 🤖 Phase 4: ADK Scoring
2024-01-15 14:30:48 - __main__ - INFO - Scored 22 items
2024-01-15 14:30:48 - __main__ - INFO - ✅ Phase 5: Filtering
2024-01-15 14:30:48 - __main__ - INFO - Keeping 10 items, discarding 12
2024-01-15 14:30:48 - __main__ - INFO - 💾 Phase 6: Persisting to database
2024-01-15 14:30:49 - __main__ - INFO - Saved 10 items to database
2024-01-15 14:30:49 - __main__ - INFO - 📢 Phase 7: Sending alerts
2024-01-15 14:30:50 - __main__ - INFO - Sent 2 alerts
2024-01-15 14:30:50 - __main__ - INFO - ✅ ETL execution completed in 50.23s
```

#### T3.6: Verificar resultados

```bash
# Consultar SQLite
sqlite3 data/etl_movilidad.db

# Verificar noticias insertadas
SELECT COUNT(*) FROM news_item;

# Ver noticias de alta severidad
SELECT title, severity, area, tags FROM news_item WHERE severity IN ('high', 'critical');

# Ver log de ejecuciones
SELECT * FROM etl_log ORDER BY started_at DESC LIMIT 5;
```

#### T3.7: Verificar alertas en Slack

- Abrir canal de Slack configurado
- Verificar que llegaron alertas para noticias severity=high/critical
- Validar formato del mensaje

**✅ Checkpoint 14:** Pipeline end-to-end validado con datos reales.

---

### Resumen Día 3

**Tiempo total:** 6-7 horas

**Logros:**
- ✅ Normalización robusta con limpieza de HTML
- ✅ Pipeline completo de 7 fases funcional
- ✅ Alertas en Slack para alta severidad
- ✅ Logging completo (archivo + consola)
- ✅ Estadísticas de ejecución guardadas en DB
- ✅ Test end-to-end exitoso

**Archivos creados:**
- `normalizer.py` (~100 líneas)
- `alerts.py` (~70 líneas)
- `logger.py` (~40 líneas)
- `main.py` (~180 líneas)

**Métricas obtenidas:**
- Duración total: ~50 segundos
- Keep rate: 45% (10 de 22)
- Alertas enviadas: 2 de 10
- Items guardados: 10

**Próximo paso:** Día 4 - Scheduler automático

---

## DÍA 4: SCHEDULER Y REFINAMIENTO (4-5 horas)

### Objetivos del Día
- ✅ Scheduler automático cada 5 minutos
- ✅ Manejo robusto de errores
- ✅ Script de consultas útiles
- ✅ Sistema autónomo funcionando

---

### Parte 1: Implementar Scheduler (1 hora)

#### T4.1: Crear scheduler.py

```python
# scheduler.py
import schedule
import time
import logging
import signal
import sys
from main import ETLPipeline

logger = logging.getLogger(__name__)

class ETLScheduler:
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.pipeline = ETLPipeline()
        self.running = True

        # Configurar signal handlers para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handler para SIGINT y SIGTERM"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def run_pipeline(self):
        """Wrapper para ejecutar pipeline con manejo de errores"""
        try:
            logger.info("=" * 60)
            logger.info("🕐 Scheduled execution triggered")
            logger.info("=" * 60)

            self.pipeline.run()

            logger.info("=" * 60)
            logger.info("✅ Scheduled execution completed")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)

    def start(self):
        """Inicia el scheduler"""
        logger.info(f"🚀 Starting ETL Scheduler")
        logger.info(f"📅 Interval: every {self.interval_minutes} minutes")
        logger.info(f"Press Ctrl+C to stop")

        # Ejecutar inmediatamente al iniciar
        logger.info("🏃 Running initial execution...")
        self.run_pipeline()

        # Programar ejecuciones periódicas
        schedule.every(self.interval_minutes).minutes.do(self.run_pipeline)

        # Loop principal
        while self.running:
            schedule.run_pending()
            time.sleep(1)

        logger.info("👋 Scheduler stopped")

if __name__ == "__main__":
    import os
    from logger import setup_logger
    from dotenv import load_dotenv

    load_dotenv()
    setup_logger(log_level=os.getenv('LOG_LEVEL', 'INFO'))

    interval = int(os.getenv('ETL_INTERVAL_MINUTES', '5'))
    scheduler = ETLScheduler(interval_minutes=interval)
    scheduler.start()
```

#### T4.2: Test de scheduler

```bash
# Ejecutar scheduler (se detendrá con Ctrl+C)
python scheduler.py
```

**Salida esperada:**
```
2024-01-15 15:00:00 - scheduler - INFO - 🚀 Starting ETL Scheduler
2024-01-15 15:00:00 - scheduler - INFO - 📅 Interval: every 5 minutes
2024-01-15 15:00:00 - scheduler - INFO - Press Ctrl+C to stop
2024-01-15 15:00:00 - scheduler - INFO - 🏃 Running initial execution...
========================================================
2024-01-15 15:00:00 - scheduler - INFO - 🕐 Scheduled execution triggered
========================================================
... [pipeline execution logs] ...
========================================================
2024-01-15 15:00:45 - scheduler - INFO - ✅ Scheduled execution completed
========================================================
[Esperando próxima ejecución en 5 minutos...]
^C
2024-01-15 15:02:30 - scheduler - INFO - Received signal 2, shutting down gracefully...
2024-01-15 15:02:30 - scheduler - INFO - 👋 Scheduler stopped
```

**✅ Checkpoint 15:** Scheduler funcional con ejecución periódica.

---

### Parte 2: Scripts de Consultas (1 hora)

#### T4.3: Crear scripts/query_db.py

```python
# scripts/query_db.py
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "data" / "etl_movilidad.db"

def print_table(rows, headers):
    """Imprime tabla formateada"""
    if not rows:
        print("No data found")
        return

    # Calcular anchos de columnas
    widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]

    # Header
    header_row = " | ".join(str(headers[i]).ljust(widths[i]) for i in range(len(headers)))
    print(header_row)
    print("-" * len(header_row))

    # Rows
    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))

def recent_news(limit=20):
    """Muestra noticias recientes"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            substr(title, 1, 50) as title,
            source,
            severity,
            area,
            tags,
            datetime(created_at) as created
        FROM news_item
        ORDER BY created_at DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    headers = ['Title', 'Source', 'Severity', 'Area', 'Tags', 'Created']

    print(f"\n📰 {limit} Most Recent News")
    print_table(rows, headers)

    conn.close()

def stats_by_source():
    """Estadísticas por fuente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            source,
            COUNT(*) as total,
            SUM(CASE WHEN severity IN ('high', 'critical') THEN 1 ELSE 0 END) as high_severity,
            datetime(MAX(created_at)) as last_item
        FROM news_item
        GROUP BY source
        ORDER BY total DESC
    ''')

    rows = cursor.fetchall()
    headers = ['Source', 'Total', 'High Severity', 'Last Item']

    print("\n📊 Stats by Source")
    print_table(rows, headers)

    conn.close()

def high_severity_news(hours=24):
    """Noticias de alta severidad en últimas N horas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    since = (datetime.now() - timedelta(hours=hours)).isoformat()

    cursor.execute('''
        SELECT
            datetime(created_at) as time,
            substr(title, 1, 60) as title,
            severity,
            area
        FROM news_item
        WHERE severity IN ('high', 'critical')
          AND created_at > ?
        ORDER BY created_at DESC
    ''', (since,))

    rows = cursor.fetchall()
    headers = ['Time', 'Title', 'Severity', 'Area']

    print(f"\n🚨 High Severity News (last {hours}h)")
    print_table(rows, headers)

    conn.close()

def execution_logs(limit=10):
    """Últimos logs de ejecución"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            datetime(started_at) as started,
            source,
            items_extracted as extracted,
            items_kept as kept,
            items_discarded as discarded,
            items_duplicated as dupes
        FROM etl_log
        ORDER BY started_at DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    headers = ['Started', 'Source', 'Extracted', 'Kept', 'Discarded', 'Dupes']

    print(f"\n📋 Last {limit} Executions")
    print_table(rows, headers)

    conn.close()

def show_menu():
    print("\n" + "=" * 60)
    print("ETL Movilidad - Database Query Tool")
    print("=" * 60)
    print("1. Recent news (last 20)")
    print("2. Stats by source")
    print("3. High severity news (last 24h)")
    print("4. Execution logs (last 10)")
    print("5. All queries")
    print("0. Exit")
    print("=" * 60)

if __name__ == "__main__":
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        sys.exit(1)

    if len(sys.argv) > 1:
        option = sys.argv[1]
    else:
        show_menu()
        option = input("Choose option: ")

    if option == "1":
        recent_news()
    elif option == "2":
        stats_by_source()
    elif option == "3":
        high_severity_news()
    elif option == "4":
        execution_logs()
    elif option == "5":
        recent_news()
        stats_by_source()
        high_severity_news()
        execution_logs()
    elif option == "0":
        print("Bye!")
    else:
        print("Invalid option")
```

#### T4.4: Test de consultas

```bash
# Menú interactivo
python scripts/query_db.py

# O directo
python scripts/query_db.py 5  # Todas las consultas
```

**✅ Checkpoint 16:** Scripts de consultas funcionales.

---

### Parte 3: Refinamiento y Mejoras (2 horas)

#### T4.5: Agregar retry logic robusto

Modificar `adk_scorer.py` para agregar retry exponencial:

```python
# En adk_scorer.py, agregar import
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core import exceptions

# Modificar método score con decorator
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((exceptions.ServiceUnavailable, exceptions.DeadlineExceeded))
)
def score(self, news_item: Dict) -> Optional[Dict]:
    # ... código existente
```

#### T4.6: Agregar health check

```python
# scripts/health_check.py
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import sys

DB_PATH = Path(__file__).parent.parent / "data" / "etl_movilidad.db"

def check_health():
    """Verifica salud del sistema ETL"""
    issues = []

    # 1. Verificar que DB existe
    if not DB_PATH.exists():
        return ["❌ Database not found"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2. Verificar ejecuciones recientes (última hora)
    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
    cursor.execute('SELECT COUNT(*) FROM etl_log WHERE started_at > ?', (one_hour_ago,))
    recent_execs = cursor.fetchone()[0]

    if recent_execs == 0:
        issues.append("⚠️  No executions in last hour")

    # 3. Verificar items recientes (última hora)
    cursor.execute('SELECT COUNT(*) FROM news_item WHERE created_at > ?', (one_hour_ago,))
    recent_items = cursor.fetchone()[0]

    if recent_items == 0:
        issues.append("⚠️  No items inserted in last hour")

    # 4. Verificar error rate
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN errors != '' THEN 1 ELSE 0 END) as errors
        FROM etl_log
        WHERE started_at > ?
    ''', (one_hour_ago,))

    total, errors = cursor.fetchone()
    if total > 0:
        error_rate = (errors / total) * 100
        if error_rate > 20:
            issues.append(f"⚠️  High error rate: {error_rate:.1f}%")

    conn.close()

    # Resultado
    if not issues:
        print("✅ System healthy")
        print(f"   - {recent_execs} executions in last hour")
        print(f"   - {recent_items} items inserted")
        return 0
    else:
        print("⚠️  System issues detected:")
        for issue in issues:
            print(f"   {issue}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
```

#### T4.7: Crear script de setup completo

```bash
# scripts/setup.sh
#!/bin/bash

echo "🚀 ETL Movilidad - Setup Script"
echo ""

# 1. Verificar Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found"
    exit 1
fi

echo "✅ Python found: $(python --version)"

# 2. Crear venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# 3. Activar venv
source venv/bin/activate

# 4. Instalar dependencias
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 5. Verificar .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env not found, creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env with your credentials"
    exit 1
fi

# 6. Crear directorios
mkdir -p data/logs

# 7. Inicializar DB
echo "🗄️  Initializing database..."
python -c "from db import NewsDatabase; NewsDatabase()"

# 8. Test de conexión GCP
echo "🔐 Testing GCP connection..."
python -c "from adk_scorer import ADKScorer; scorer = ADKScorer(); print('✅ GCP OK')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your credentials"
echo "  2. Run: python main.py (single execution)"
echo "  3. Run: python scheduler.py (continuous)"
```

**✅ Checkpoint 17:** Scripts de utilidad completos.

---

### Parte 4: Documentación README (1 hora)

#### T4.8: Crear README.md completo

```markdown
# ETL Movilidad Medellín - MVP Local

Sistema ETL para extraer, clasificar y alertar sobre noticias de movilidad en Medellín usando Google ADK (Gemini).

## Características

- ✅ Extracción automática desde 2-3 fuentes (Metro, medios locales, Twitter opcional)
- ✅ Clasificación inteligente con Google Vertex AI (Gemini 1.5 Flash)
- ✅ Scoring: keep/discard, severity, tags, área
- ✅ Deduplicación por hash SHA256
- ✅ Alertas en Slack para alta severidad
- ✅ Persistencia en SQLite
- ✅ Ejecución automática cada 5 minutos

## Requisitos

- Python 3.11+
- Cuenta GCP con Vertex AI habilitado
- gcloud CLI
- Slack Webhook (opcional)

## Setup Rápido

1. **Clonar y setup:**
   ```bash
   git clone [repo]
   cd etl-movilidad-local
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

2. **Configurar .env:**
   ```bash
   cp .env.example .env
   nano .env  # Editar con tus credenciales
   ```

3. **Autenticar GCP:**
   ```bash
   gcloud auth application-default login
   gcloud config set project TU_PROYECTO_ID
   ```

4. **Ejecutar:**
   ```bash
   # Una ejecución
   python main.py

   # Continuo (cada 5 min)
   python scheduler.py
   ```

## Uso

### Ejecución Manual
```bash
python main.py
```

### Ejecución Continua
```bash
python scheduler.py
```

### Consultas a la DB
```bash
python scripts/query_db.py
```

### Health Check
```bash
python scripts/health_check.py
```

## Estructura

```
etl-movilidad-local/
├── main.py              # Pipeline principal
├── scheduler.py         # Scheduler automático
├── extractors.py        # Extracción de fuentes
├── normalizer.py        # Limpieza de datos
├── adk_scorer.py        # Clasificación con ADK
├── db.py                # SQLite operations
├── alerts.py            # Slack notifications
├── logger.py            # Logging config
├── prompts/
│   └── system_prompt.py # Prompts ADK
├── scripts/
│   ├── query_db.py      # Consultas útiles
│   ├── health_check.py  # Verificación de salud
│   └── setup.sh         # Setup automático
└── data/
    ├── etl_movilidad.db # Database SQLite
    └── logs/
        └── etl.log      # Logs de ejecución
```

## Configuración

Ver `.env.example` para todas las variables disponibles.

Principales:
- `GCP_PROJECT_ID`: Tu proyecto GCP
- `SLACK_WEBHOOK_URL`: Webhook de Slack
- `ETL_INTERVAL_MINUTES`: Intervalo (default: 5)
- `LOG_LEVEL`: INFO, DEBUG, WARNING

## Costos

- GCP Vertex AI: ~$0.002 por 1,000 tokens
- Estimado mensual: $2-5 (asumiendo ~1,000 noticias/mes)
- SQLite: Gratis
- Slack: Gratis

## Limitaciones

- ❌ No escalable (1 máquina)
- ❌ No alta disponibilidad
- ❌ Sin búsqueda semántica
- ❌ Backups manuales

Para producción, ver [PLAN_IMPLEMENTACION.md](../PLAN_IMPLEMENTACION.md) para arquitectura cloud-native.

## Troubleshooting

### Error: "Database locked"
SQLite no soporta alta concurrencia. No ejecutar múltiples instancias simultáneamente.

### Error: "Vertex AI authentication failed"
```bash
gcloud auth application-default login
```

### Error: "SLACK_WEBHOOK_URL not configured"
Agregar webhook URL en `.env` o las alertas se saltarán.

## Roadmap

- [ ] Agregar más fuentes
- [ ] Dashboard visual simple
- [ ] Embeddings con sentence-transformers local
- [ ] Exportar a CSV/JSON
- [ ] Migración a Postgres

## Licencia

MIT
```

**✅ Checkpoint 18:** Documentación completa.

---

### Resumen Día 4

**Tiempo total:** 4-5 horas

**Logros:**
- ✅ Scheduler automático con graceful shutdown
- ✅ Scripts de consultas SQL útiles
- ✅ Health check script
- ✅ Setup script automático
- ✅ Retry logic robusto
- ✅ Documentación README completa
- ✅ Sistema autónomo funcional

**Archivos creados:**
- `scheduler.py` (~60 líneas)
- `scripts/query_db.py` (~150 líneas)
- `scripts/health_check.py` (~60 líneas)
- `scripts/setup.sh` (~40 líneas)
- `README.md` (~200 líneas)

**Sistema funcionando:**
- ✅ Ejecuta cada 5 minutos automáticamente
- ✅ Manejo robusto de errores
- ✅ Logging completo
- ✅ Consultas útiles disponibles
- ✅ Health monitoring

**Próximo paso:** Día 5 (opcional) - Testing y refinamiento

---

## DÍA 5 (OPCIONAL): TESTING Y REFINAMIENTO (3-4 horas)

### Objetivos del Día
- ✅ Tests automatizados
- ✅ Refinamiento de prompts
- ✅ Optimizaciones
- ✅ Documentación final

---

### Parte 1: Tests Automatizados (2 horas)

#### T5.1: Tests unitarios

```python
# tests/test_normalizer.py
import pytest
from normalizer import NewsNormalizer

def test_clean_html():
    normalizer = NewsNormalizer()

    html = "<p>Hola <b>mundo</b></p>"
    result = normalizer._clean_body(html)

    assert result == "Hola mundo"

def test_normalize_valid_news():
    normalizer = NewsNormalizer()

    raw = {
        'source': 'test',
        'url': 'https://example.com/news1?utm_source=facebook',
        'title': '  Título con espacios  ',
        'body': '<p>Contenido</p>',
        'published_at': '2024-01-15T10:00:00Z'
    }

    result = normalizer.normalize(raw)

    assert result is not None
    assert result['url'] == 'https://example.com/news1'
    assert result['title'] == 'Título con espacios'
    assert '<p>' not in result['body']

def test_normalize_invalid_news():
    normalizer = NewsNormalizer()

    raw = {
        'source': 'test',
        'url': '',  # URL vacía
        'title': 'Test',
        'body': 'Short',
        'published_at': '2024-01-15T10:00:00Z'
    }

    result = normalizer.normalize(raw)

    assert result is None  # Debe rechazar
```

```python
# tests/test_db.py
import pytest
import os
from db import NewsDatabase

@pytest.fixture
def test_db():
    db_path = "data/test.db"
    db = NewsDatabase(db_path)
    yield db
    os.remove(db_path)

def test_insert_news(test_db):
    news = {
        'source': 'test',
        'url': 'https://test.com/news1',
        'title': 'Test News',
        'body': 'Test body content',
        'published_at': '2024-01-15T10:00:00Z',
        'severity': 'high',
        'tags': ['test', 'cierre_vial'],
        'area': 'El Poblado',
        'summary': 'Test summary',
        'relevance_score': 0.85
    }

    news_id = test_db.insert_news(news)

    assert news_id is not None
    assert news_id > 0

def test_is_duplicate(test_db):
    news = {
        'source': 'test',
        'url': 'https://test.com/duplicate',
        'title': 'Duplicate Test',
        'body': 'Test body',
        'published_at': '2024-01-15T10:00:00Z'
    }

    # Primera inserción
    test_db.insert_news(news)

    # Verificar que detecta duplicado
    assert test_db.is_duplicate(news['url']) is True

    # URL diferente no debe ser duplicado
    assert test_db.is_duplicate('https://test.com/other') is False
```

#### T5.2: Ejecutar tests

```bash
pytest tests/ -v
```

**✅ Checkpoint 19:** Tests automatizados pasando.

---

### Parte 2: Optimizaciones (1 hora)

#### T5.3: Optimizar prompts ADK

Basándote en datos reales de ejecuciones:

1. **Analizar keep rate:**
   ```bash
   python scripts/query_db.py 2  # Stats by source
   ```

2. **Si keep rate < 30%:** Prompts muy restrictivos
   - Ajustar en `prompts/system_prompt.py`

3. **Si keep rate > 70%:** Prompts muy permisivos
   - Ajustar criterios de descarte

4. **Verificar severity distribution:**
   - No debería haber > 20% critical
   - Mayoría debería ser medium/low

#### T5.4: Optimizar performance

```python
# En main.py, agregar batch processing para ADK

# Antes (lento):
for news in unique_news:
    scoring = self.scorer.score(news)

# Después (más rápido, si ADK lo soporta):
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(self.scorer.score, news) for news in unique_news]
    scored_news = [f.result() for f in futures]
```

**⚠️ Nota:** Verificar límites de rate de Vertex AI antes de paralelizar.

**✅ Checkpoint 20:** Sistema optimizado.

---

### Parte 3: Documentación Final (30 min)

#### T5.5: Crear CHANGELOG.md

```markdown
# Changelog

## [1.0.0] - 2024-01-15

### Added
- Initial MVP release
- Extraction from Metro Medellín and El Colombiano
- ADK scoring with Gemini 1.5 Flash
- SQLite persistence
- Slack alerts
- Automated scheduler (every 5 min)
- Query scripts
- Health check script

### Features
- ✅ Auto-deduplication
- ✅ Severity classification (low/medium/high/critical)
- ✅ Area detection
- ✅ Tag assignment
- ✅ Robust error handling
- ✅ Logging to file

### Known Issues
- No semantic search (pgvector not included in MVP)
- SQLite doesn't support high concurrency
- Manual backups required
```

#### T5.6: Actualizar .env.example

```bash
# .env.example (con comentarios detallados)

# ==========================================
# GCP Configuration (REQUIRED)
# ==========================================
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# ==========================================
# Database (REQUIRED)
# ==========================================
DB_PATH=data/etl_movilidad.db

# ==========================================
# Scheduler (OPTIONAL)
# ==========================================
ETL_INTERVAL_MINUTES=5  # Interval in minutes (default: 5)

# ==========================================
# Logging (OPTIONAL)
# ==========================================
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# ==========================================
# Slack Alerts (OPTIONAL)
# ==========================================
# Get webhook URL from: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# ==========================================
# Twitter API (OPTIONAL)
# ==========================================
# Get from: https://developer.twitter.com/
# If not provided, Twitter source will be skipped
TWITTER_BEARER_TOKEN=Bearer_YOUR_TOKEN_HERE
```

**✅ Checkpoint 21:** Documentación completa y actualizada.

---

### Resumen Día 5

**Tiempo total:** 3-4 horas

**Logros:**
- ✅ Tests unitarios implementados
- ✅ Prompts optimizados basados en datos reales
- ✅ Performance mejorado (opcional: parallel processing)
- ✅ Documentación completa (CHANGELOG, .env.example)
- ✅ Sistema production-ready para MVP local

**Sistema Final:**
- 📦 **Total de archivos:** ~20
- 📝 **Líneas de código:** ~1,200
- ⏱️ **Tiempo de implementación:** 3-5 días
- 💰 **Costo:** $0-5/mes

---

## RESUMEN FINAL DEL MVP

### Logros Totales (5 días)

✅ **Sistema Completo Funcional**
- Extracción automática de 2-3 fuentes
- Clasificación inteligente con ADK (Gemini)
- Deduplicación robusta
- Alertas en Slack
- Persistencia en SQLite
- Scheduler automático cada 5 minutos
- Logging completo
- Scripts de consultas
- Health monitoring
- Tests automatizados

### Archivos Creados

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `main.py` | 180 | Pipeline principal |
| `scheduler.py` | 60 | Scheduler automático |
| `extractors.py` | 180 | Extracción multi-fuente |
| `normalizer.py` | 100 | Limpieza de datos |
| `adk_scorer.py` | 120 | Clasificación ADK |
| `db.py` | 150 | SQLite operations |
| `alerts.py` | 70 | Slack notifications |
| `logger.py` | 40 | Logging config |
| `prompts/system_prompt.py` | 180 | Prompts ADK |
| `scripts/query_db.py` | 150 | Consultas útiles |
| `scripts/health_check.py` | 60 | Health monitoring |
| `scripts/setup.sh` | 40 | Setup automático |
| `tests/test_*.py` | 100 | Tests unitarios |
| `README.md` | 200 | Documentación |
| **TOTAL** | **~1,630 líneas** | **Sistema completo** |

### Métricas Finales

- **Duración implementación:** 3-5 días
- **Complejidad:** Baja-Media (vs Alta del plan original)
- **Costo mensual:** $0-5 (vs $126-186)
- **Reducción de tiempo:** 85-90%
- **Reducción de código:** 78%
- **Reducción de costo:** 95-98%

### Requisito Obligatorio

✅ **ADK de Google mantenido:** Sistema usa Gemini 1.5 Flash vía Vertex AI para todo el scoring inteligente.

---

## Próximos Pasos Post-MVP

Una vez validado el MVP:

1. **Semana 1-2:** Monitorear y ajustar prompts
2. **Semana 3:** Agregar más fuentes si es necesario
3. **Semana 4:** Decidir: ¿Migrar a cloud o quedarse local?

Si decides migrar a cloud, usar [PLAN_IMPLEMENTACION.md](./PLAN_IMPLEMENTACION.md).

---

**Versión:** 1.0.0
**Fecha:** 2025-01-29
**Estado:** Plan completo - Listo para implementación
