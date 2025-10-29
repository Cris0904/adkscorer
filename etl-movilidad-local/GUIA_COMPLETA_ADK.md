# 🚀 Guía Completa: Ejecución del Proyecto con Google ADK

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Verificación del Entorno](#verificación-del-entorno)
3. [Ejecución Paso a Paso](#ejecución-paso-a-paso)
4. [Interpretación de Resultados](#interpretación-de-resultados)
5. [Solución de Problemas](#solución-de-problemas)

---

## 1. Requisitos Previos

### ✅ Software Necesario

- **Python 3.11+** instalado
- **Git** instalado
- **Google Cloud SDK** (gcloud) instalado
- Cuenta de **Google Cloud** activa

### ✅ Configuración de Google Cloud

Debes tener:
- Un proyecto de Google Cloud creado
- Vertex AI API habilitada
- Credenciales configuradas

---

## 2. Verificación del Entorno

### Paso 2.1: Verificar Python

```bash
python --version
# Debe mostrar: Python 3.11.x o superior
```

### Paso 2.2: Verificar Ubicación del Proyecto

```bash
cd etl-movilidad-local
pwd
# Debes estar en: .../etl-movilidad-local/
```

### Paso 2.3: Verificar Archivo .env

```bash
cat .env
```

**Debe mostrar:**
```
GOOGLE_CLOUD_PROJECT=healthy-anthem-418104
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_LOCATION=us-central1
```

### Paso 2.4: Verificar Autenticación de Google Cloud

```bash
gcloud auth application-default print-access-token
```

**Si muestra un token (empieza con `ya29.`)**: ✅ Autenticado correctamente

**Si muestra error**: Ejecuta:
```bash
gcloud auth application-default login
```

### Paso 2.5: Verificar Dependencias Instaladas

```bash
pip show google-adk
```

**Debe mostrar:**
```
Name: google-adk
Version: 1.17.0
...
```

**Si no está instalado:**
```bash
pip install --user -r requirements.txt
```

---

## 3. Ejecución Paso a Paso

### 🎯 Opción 1: Ejecutar el Test Completo (Recomendado)

Este es el test que acabamos de probar exitosamente.

#### Paso 3.1: Ir al directorio del proyecto

```bash
cd etl-movilidad-local
```

#### Paso 3.2: Ejecutar el script de test

```bash
python scripts/test_gemini_v3.py
```

#### Paso 3.3: Observar la Salida

Deberías ver algo como esto:

```
======================================================================
TESTING GOOGLE ADK WITH OUTPUT_SCHEMA (October 2025)
======================================================================

✅ Project ID: healthy-anthem-418104
✅ Using Google ADK (Agent Development Kit)
✅ With Pydantic output_schema for automatic validation
✅ Framework: google-adk v0.2+

--- Initializing ADK Scorer V3 (True ADK Implementation) ---
INFO:adk_scorer_v3:Initializing Google ADK Agent...
INFO:adk_scorer_v3:   GenAI Client created for Vertex AI
INFO:adk_scorer_v3:✅ ADK Agent initialized successfully
INFO:adk_scorer_v3:   Model: gemini-2.0-flash
INFO:adk_scorer_v3:   Project: healthy-anthem-418104
INFO:adk_scorer_v3:   Location: us-central1
INFO:adk_scorer_v3:   Output schema: ScoringResponse (Pydantic validated)

✅ ADK Agent initialized successfully

Agent Configuration:
  model: gemini-2.0-flash
  project: healthy-anthem-418104
  location: us-central1
  sdk_version: google-adk (Agent Development Kit)
  agent_name: mobility_news_scorer
  output_schema: ScoringResponse (Pydantic)
  framework: Google ADK v0.2+

--- Generating test news ---
✅ Generated 3 test news items

--- Testing ADK Agent Scoring with Structured Output ---

[1/3] Suspensión temporal de servicio en Línea A del Metro por man...
INFO:httpx:HTTP Request: POST https://us-central1-aiplatform.googleapis.com/v1beta1/projects/healthy-anthem-418104/locations/us-central1/publishers/google/models/gemini-2.0-flash:generateContent "HTTP/1.1 200 OK"
INFO:adk_scorer_v3:✅ News kept: Suspensión temporal de servicio en Línea A del Met... | Severity: Severity.MEDIUM | Score: 0.90

    ✅ KEPT (Validated by Pydantic schema)
       Severity: Severity.MEDIUM
       Score: 0.90
       Area: Linea_A_Metro
       Tags: metro, suspension, mantenimiento
       Entities: Metro de Medellín, Estación Niquía
       Summary: Suspensión temporal del servicio en la Línea A del Metro...
       Reasoning: Afecta el servicio de transporte masivo y requiere...

[2/3] Inauguran nuevas ciclorrutas en el sector de Laureles...
INFO:httpx:HTTP Request: POST https://us-central1-aiplatform.googleapis.com/v1beta1/projects/healthy-anthem-418104/locations/us-central1/publishers/google/models/gemini-2.0-flash:generateContent "HTTP/1.1 200 OK"
INFO:adk_scorer_v3:✅ News kept: Inauguran nuevas ciclorrutas en el sector de Laure... | Severity: Severity.LOW | Score: 0.60

    ✅ KEPT (Validated by Pydantic schema)
       Severity: Severity.LOW
       Score: 0.60
       Area: Laureles
       Tags: encicla, obra, mejora
       Entities: Alcaldía de Medellín, Estadio Atanasio Girardot
       Summary: Inauguración de 5 km de ciclorrutas en Laureles...
       Reasoning: Aumenta la infraestructura para movilidad en bicicleta...

[3/3] Pico y placa especial por festividades del fin de semana...
INFO:httpx:HTTP Request: POST https://us-central1-aiplatform.googleapis.com/v1beta1/projects/healthy-anthem-418104/locations/us-central1/publishers/google/models/gemini-2.0-flash:generateContent "HTTP/1.1 200 OK"
INFO:adk_scorer_v3:✅ News kept: Pico y placa especial por festividades del fin de ... | Severity: Severity.MEDIUM | Score: 0.85

    ✅ KEPT (Validated by Pydantic schema)
       Severity: Severity.MEDIUM
       Score: 0.85
       Area: Valle_Aburra
       Tags: restriccion, pico_y_placa, fin_de_semana
       Entities: Área Metropolitana del Valle de Aburrá
       Summary: Se anuncia pico y placa especial para el fin de semana...
       Reasoning: La noticia informa sobre una restricción vehicular...

======================================================================
TEST COMPLETE - Google ADK with output_schema
======================================================================

✅ Success indicators:
   - Agent initialized without errors
   - Structured responses validated by Pydantic
   - All required fields present in responses

📊 Key differences from V2 (SDK):
   - Using google.adk.agents.LlmAgent (not google.generativeai)
   - Automatic JSON validation via output_schema
   - No manual JSON parsing or error handling needed
   - Production-ready with guaranteed schema compliance
```

---

### 🎯 Opción 2: Uso Programático en Python

Si quieres integrar el scorer en tu propio código:

#### Paso 3.1: Crear un script de prueba

```bash
# Crear archivo test_custom.py
nano test_custom.py
```

#### Paso 3.2: Copiar este código

```python
import sys
import os
from dotenv import load_dotenv

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Cargar variables de entorno
load_dotenv()

from adk_scorer_v3 import ADKScorerV3

# Obtener project ID
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

print("🚀 Inicializando Google ADK Scorer...")
scorer = ADKScorerV3(project_id=project_id)
print("✅ Scorer inicializado correctamente\n")

# Noticia de prueba
noticia = {
    'source': 'Metro de Medellín',
    'url': 'https://www.metrodemedellin.gov.co/test',
    'title': 'Cierre completo de la Línea A por emergencia',
    'body': 'Se reporta un cierre total de la Línea A del Metro debido a una emergencia técnica. Se espera que el servicio se restablezca en 3 horas. Buses de contingencia están disponibles.',
    'published_at': '2025-10-29T15:00:00'
}

print(f"📰 Analizando noticia: {noticia['title']}\n")

# Puntuar noticia
resultado = scorer.score(noticia)

if resultado:
    print("✅ NOTICIA RELEVANTE - Será incluida en el sistema")
    print(f"\n📊 Detalles del scoring:")
    print(f"   • Severity: {resultado['severity']}")
    print(f"   • Score: {resultado['relevance_score']}")
    print(f"   • Área: {resultado['area']}")
    print(f"   • Tags: {', '.join(resultado['tags'])}")
    print(f"   • Entities: {', '.join(resultado['entities'])}")
    print(f"   • Summary: {resultado['summary']}")
    print(f"   • Reasoning: {resultado['reasoning']}")
else:
    print("❌ NOTICIA NO RELEVANTE - Será descartada")
```

#### Paso 3.3: Ejecutar tu script

```bash
python test_custom.py
```

---

### 🎯 Opción 3: Probar con Tus Propias Noticias

#### Paso 3.1: Modificar generate_test_news.py

Abre el archivo:
```bash
nano scripts/generate_test_news.py
```

#### Paso 3.2: Agregar tus propias noticias

Agrega noticias al array `news_samples`:

```python
news_samples = [
    {
        'source': 'Tu Fuente',
        'url': 'https://ejemplo.com',
        'title': 'Tu Título de Noticia',
        'body': 'Contenido completo de la noticia...',
        'published_at': '2025-10-29T10:00:00'
    },
    # ... más noticias
]
```

#### Paso 3.3: Ejecutar el test

```bash
python scripts/test_gemini_v3.py
```

---

## 4. Interpretación de Resultados

### 🔍 Entendiendo la Salida

#### ✅ Indicadores de Éxito

1. **Inicialización Exitosa:**
   ```
   INFO:adk_scorer_v3:✅ ADK Agent initialized successfully
   ```

2. **Conexión a Vertex AI:**
   ```
   INFO:httpx:HTTP Request: POST https://us-central1-aiplatform.googleapis.com/...
   "HTTP/1.1 200 OK"
   ```

3. **Respuesta Validada:**
   ```
   ✅ KEPT (Validated by Pydantic schema)
   ```

#### 📊 Campos de Respuesta

Cada noticia procesada devuelve:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **keep** | Si la noticia es relevante | `true` / `false` |
| **severity** | Nivel de urgencia | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| **relevance_score** | Puntuación 0.0-1.0 | `0.90` |
| **area** | Zona geográfica afectada | `Linea_A_Metro`, `Laureles` |
| **tags** | Etiquetas clasificatorias | `["metro", "suspension"]` |
| **entities** | Entidades mencionadas | `["Metro de Medellín"]` |
| **summary** | Resumen del impacto | "Suspensión temporal..." |
| **reasoning** | Justificación de la decisión | "Afecta transporte masivo..." |

#### 🎯 Interpretación de Severity

- **CRITICAL**: Bloqueos totales, accidentes graves, suspensión de servicios principales
- **HIGH**: Desvíos importantes, retrasos significativos, obras mayores
- **MEDIUM**: Cambios moderados en rutas, eventos que aumenten tráfico
- **LOW**: Información general, mejoras menores, mantenimientos programados

#### 📈 Interpretación de Score

- **0.9 - 1.0**: Muy relevante, impacto inmediato en movilidad
- **0.7 - 0.89**: Relevante, afecta movilidad de manera significativa
- **0.5 - 0.69**: Moderadamente relevante, impacto limitado
- **0.0 - 0.49**: Poco relevante (generalmente keep=false)

---

## 5. Solución de Problemas

### ❌ Error: "GOOGLE_CLOUD_PROJECT not set"

**Solución:**
```bash
# Verificar .env
cat .env

# Si no existe o está mal, editarlo:
nano .env

# Agregar:
GOOGLE_CLOUD_PROJECT=healthy-anthem-418104
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_LOCATION=us-central1
```

### ❌ Error: "Could not automatically determine credentials"

**Solución:**
```bash
gcloud auth application-default login
```

Esto abrirá tu navegador para autenticarte.

### ❌ Error: "ModuleNotFoundError: No module named 'google.adk'"

**Solución:**
```bash
pip install --user -r requirements.txt
```

### ❌ Error: "HTTP/1.1 403 Forbidden"

**Causa:** Vertex AI API no está habilitada

**Solución:**
```bash
# Habilitar Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=healthy-anthem-418104
```

O ve a: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com

### ❌ Error: "Session not found"

**Causa:** Problema con la creación de sesiones

**Solución:** Este error ya está corregido en la versión actual. Asegúrate de tener la última versión del código.

### ❌ Error: "Event loop is closed"

**Causa:** Problema con el manejo de asyncio

**Solución:** Este error ya está corregido en la versión actual. El código ahora maneja correctamente el event loop.

### ❌ Las 3 noticias aparecen como "DISCARDED"

**Causa:** Problema con la extracción de la respuesta del agente

**Solución:** Verifica que tienes la versión más reciente de `adk_scorer_v3.py` que extrae correctamente del `Event.content.parts[0].text`

---

## 6. Flujo Completo del Proceso

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INICIALIZACIÓN                                           │
│    python scripts/test_gemini_v3.py                         │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CARGA DE CONFIGURACIÓN                                   │
│    • Lee .env (GOOGLE_CLOUD_PROJECT, etc.)                  │
│    • Carga ADKScorerV3                                      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CREACIÓN DEL AGENTE ADK                                  │
│    • genai.Client(vertexai=True)                            │
│    • Gemini model con client                                │
│    • LlmAgent con output_schema=ScoringResponse             │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. GENERACIÓN DE NOTICIAS DE PRUEBA                         │
│    • generate_test_news() crea 3 noticias ejemplo           │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. SCORING DE CADA NOTICIA                                  │
│    Para cada noticia:                                       │
│    ├─ Construir prompt con datos de la noticia             │
│    ├─ Crear mensaje (types.Content)                        │
│    ├─ Llamar runner.run_async()                            │
│    ├─ Enviar a Vertex AI / Gemini 2.0 Flash               │
│    ├─ Recibir respuesta (Event object)                     │
│    ├─ Extraer JSON de event.content.parts[0].text          │
│    ├─ Validar con Pydantic (ScoringResponse)               │
│    └─ Devolver resultado enriquecido                       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. MOSTRAR RESULTADOS                                        │
│    • Imprime detalles de cada noticia procesada            │
│    • Indica si fue KEPT o DISCARDED                        │
│    • Muestra severity, score, tags, summary, etc.          │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Ejemplo Completo de Sesión

```bash
# 1. Ir al directorio
cd etl-movilidad-local

# 2. Verificar autenticación
gcloud auth application-default print-access-token
# Salida: ya29.a0ATi6K2uTGMsa3Qkn-f4483zq-uHDaU...

# 3. Verificar .env
cat .env
# Salida:
# GOOGLE_CLOUD_PROJECT=healthy-anthem-418104
# GOOGLE_GENAI_USE_VERTEXAI=true
# GOOGLE_CLOUD_LOCATION=us-central1

# 4. Ejecutar test
python scripts/test_gemini_v3.py

# 5. Observar salida (debe tardar ~10-15 segundos)
# ...
# ✅ KEPT (Validated by Pydantic schema)
# ...
```

---

## 8. Verificación Final

### ✅ Checklist de Verificación

- [ ] Python 3.11+ instalado
- [ ] Google Cloud SDK instalado
- [ ] Autenticado con `gcloud auth application-default login`
- [ ] Archivo `.env` configurado correctamente
- [ ] Dependencias instaladas (`pip show google-adk` funciona)
- [ ] Vertex AI API habilitada en el proyecto
- [ ] Test `python scripts/test_gemini_v3.py` ejecuta sin errores
- [ ] Las 3 noticias muestran resultado con detalles completos

### 🎉 Si todos los items están ✅

**¡Felicitaciones! El sistema Google ADK está funcionando correctamente.**

---

## 9. Próximos Pasos

Una vez que el test funciona, puedes:

1. **Integrar en tu ETL:**
   ```python
   from adk_scorer_v3 import ADKScorerV3

   scorer = ADKScorerV3(project_id="healthy-anthem-418104")
   noticias_enriquecidas = scorer.score_batch(noticias_originales)
   ```

2. **Procesar noticias reales:**
   - Leer de RSS feeds
   - Filtrar y enriquecer con ADK
   - Guardar en base de datos

3. **Monitorear y optimizar:**
   - Agregar logs detallados
   - Implementar caché
   - Ajustar prompts según resultados

---

## 📞 Soporte

**Si encuentras problemas:**

1. Revisa la sección [Solución de Problemas](#solución-de-problemas)
2. Verifica los logs en la consola
3. Consulta `MIGRACION_ADK.md` para detalles técnicos
4. Revisa `FUNCIONAMIENTO_ADK.md` para entender el flujo interno

---

**¡Listo para producción!** 🚀
