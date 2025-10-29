# Funcionamiento del ADKScorerV3 - Explicación Detallada

## 🔄 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INICIO: Script de Usuario                         │
│                  (test_gemini_v3.py o ETL principal)                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ 1. INICIALIZACIÓN      │
                    │ ADKScorerV3(project_id)│
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼───────────────────────────────────┐
                    │ 2. CREACIÓN DEL AGENTE ADK                     │
                    │ =======================================        │
                    │ ✅ AQUÍ SE USA GOOGLE ADK                      │
                    │                                                │
                    │ from google.adk.agents import LlmAgent         │
                    │ from google.adk.models import Gemini           │
                    │                                                │
                    │ agent = LlmAgent(                              │
                    │     name="mobility_news_scorer",               │
                    │     model=Gemini(...),                         │
                    │     instruction=SYSTEM_PROMPT,                 │
                    │     output_schema=ScoringResponse              │
                    │ )                                              │
                    └────────────┬───────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ 3. RECIBIR NOTICIA     │
                    │ scorer.score(news_item)│
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼───────────┐
                    │ 4. CONSTRUIR PROMPT    │
                    │ build_user_prompt()    │
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼────────────────────────────────────┐
                    │ 5. LLAMADA AL AGENTE ADK                        │
                    │ =====================================           │
                    │ ✅ AQUÍ SE EJECUTA GOOGLE ADK                   │
                    │                                                 │
                    │ response = agent.run(user_prompt)               │
                    │                                                 │
                    │ Internamente, Google ADK:                       │
                    │ • Combina system prompt + user prompt           │
                    │ • Llama a Gemini via Vertex AI                  │
                    │ • Obtiene respuesta del LLM                     │
                    │ • Valida contra output_schema (Pydantic)        │
                    │ • Convierte a ScoringResponse                   │
                    └────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────▼───────────────────────────────────┐
                    │ 6. EXTRAER RESULTADO VALIDADO                  │
                    │ =====================================          │
                    │ ✅ RESULTADO YA VALIDADO POR ADK               │
                    │                                                │
                    │ scoring_result = response.data["scoring_result"]│
                    │ # scoring_result es un ScoringResponse validado│
                    │                                                │
                    │ result = scoring_result.model_dump()           │
                    │ # Convierte a dict Python                      │
                    └────────────┬───────────────────────────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │ 7. VERIFICAR keep      │
                    │ if result['keep']:     │
                    └────────┬───────┬───────┘
                             │       │
                    keep=True│       │keep=False
                             │       │
                             ▼       ▼
                    ┌────────────┐  ┌────────────┐
                    │ 8a. ENRICHED│  │ 8b. None   │
                    │ news item   │  │ (descartada)│
                    └────────────┘  └────────────┘
```

---

## 🎯 Puntos Clave donde se Usa Google ADK

### 📍 **PUNTO 1: Inicialización del Agente** (src/adk_scorer_v3.py:45-69)

```python
# Este es el PRIMER punto donde usamos Google ADK

from google.adk.agents import LlmAgent  # ✅ Import de Google ADK
from google.adk.models import Gemini    # ✅ Modelo Gemini del ADK

def __init__(self, project_id: str, ...):
    # Crear configuración del modelo Gemini usando ADK
    model = Gemini(
        model="gemini-2.0-flash",
        project=project_id,
        location="us-central1",
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=2048
    )

    # Crear el Agente ADK con output_schema
    self.agent = LlmAgent(
        name="mobility_news_scorer",
        model=model,                           # ✅ Modelo Gemini (ADK)
        instruction=SYSTEM_PROMPT,             # Instrucciones del agente
        output_schema=ScoringResponse,         # ✅ Schema Pydantic
        output_key="scoring_result"            # Clave para el resultado
    )
```

**¿Qué hace Google ADK aquí?**
- Crea un "agente inteligente" que encapsula:
  - El modelo Gemini
  - Las instrucciones (system prompt)
  - El schema de salida esperado
  - La clave donde guardar el resultado

---

### 📍 **PUNTO 2: Ejecución del Agente** (src/adk_scorer_v3.py:90-95)

```python
# Este es el SEGUNDO punto - la llamada real al agente

def score(self, news_item: Dict) -> Optional[Dict]:
    # Construir el prompt del usuario
    user_prompt = build_user_prompt(news_item)

    # ✅ AQUÍ SE EJECUTA GOOGLE ADK
    response = self.agent.run(user_prompt)

    # El response ya viene validado por el output_schema
```

**¿Qué hace `agent.run()` internamente?**

1. **Combina prompts:**
   - System prompt (instrucciones del agente)
   - User prompt (datos de la noticia)

2. **Llama a Gemini:**
   - Usa Vertex AI API
   - Envía el prompt completo
   - Recibe respuesta del LLM

3. **Valida la respuesta:**
   - Parsea el JSON devuelto por Gemini
   - Valida contra `ScoringResponse` (Pydantic)
   - Si no coincide, lanza error
   - Si coincide, crea objeto validado

4. **Retorna resultado estructurado:**
   - `response.data["scoring_result"]` contiene el `ScoringResponse`

---

### 📍 **PUNTO 3: Extracción del Resultado** (src/adk_scorer_v3.py:97-105)

```python
# El resultado ya está validado por Google ADK

# Extraer el resultado validado
scoring_result = response.data.get("scoring_result")

if not scoring_result:
    return None

# Convertir de Pydantic a dict
result = scoring_result.model_dump()

# result es un dict con estructura garantizada:
# {
#     "keep": bool,
#     "severity": str,
#     "tags": List[str],
#     "area": str,
#     ...
# }
```

---

## 🔬 Ejemplo Concreto Paso a Paso

Imaginemos que llega esta noticia:

```python
news_item = {
    "title": "Suspensión temporal de servicio en Línea A del Metro",
    "body": "El Metro informa suspensión por mantenimiento...",
    "source": "Metro de Medellín",
    "published_at": "2025-10-29T10:00:00",
    "url": "https://..."
}
```

### **Paso 1: Llamada Inicial**

```python
scorer = ADKScorerV3(project_id="mi-proyecto")
result = scorer.score(news_item)
```

### **Paso 2: Construcción del Prompt**

```python
user_prompt = """
Analiza la siguiente noticia y determina su relevancia...

**Fuente:** Metro de Medellín
**Título:** Suspensión temporal de servicio en Línea A del Metro
**Contenido:** El Metro informa suspensión por mantenimiento...
**Fecha de publicación:** 2025-10-29T10:00:00

Responde en formato JSON según las instrucciones del sistema.
"""
```

### **Paso 3: Google ADK en Acción**

```python
# ✅ Esto es lo que hace Google ADK internamente:

# 1. Combinar prompts
full_prompt = SYSTEM_PROMPT + "\n\n" + user_prompt

# 2. Llamar a Gemini via Vertex AI
gemini_response = vertex_ai_client.generate_content(
    model="gemini-2.0-flash",
    prompt=full_prompt
)

# 3. Gemini responde (texto JSON):
gemini_text = """{
    "keep": true,
    "severity": "high",
    "tags": ["metro", "suspension", "urgente"],
    "area": "Linea_A_Metro",
    "entities": ["Metro de Medellín"],
    "summary": "Suspensión temporal por mantenimiento",
    "relevance_score": 0.95,
    "reasoning": "Afecta transporte principal"
}"""

# 4. Google ADK valida con Pydantic
try:
    scoring_response = ScoringResponse.model_validate_json(gemini_text)
    # ✅ Validación exitosa - todos los campos correctos
except ValidationError as e:
    # ❌ Si falla validación, ADK lanza error
    raise

# 5. Retorna respuesta estructurada
return AgentResponse(
    data={"scoring_result": scoring_response}
)
```

### **Paso 4: Tu Código Recibe el Resultado**

```python
# Esto es lo que recibes en tu código:
response = agent.run(user_prompt)

scoring_result = response.data["scoring_result"]
# scoring_result es un ScoringResponse validado

result = scoring_result.model_dump()
# result = {
#     "keep": True,
#     "severity": "high",
#     "tags": ["metro", "suspension", "urgente"],
#     "area": "Linea_A_Metro",
#     "entities": ["Metro de Medellín"],
#     "summary": "Suspensión temporal por mantenimiento",
#     "relevance_score": 0.95,
#     "reasoning": "Afecta transporte principal"
# }

# ✅ GARANTIZADO: Todos los campos existen y tienen el tipo correcto
```

---

## 🆚 Comparación: SDK vs ADK

### **Versión Anterior (V2 - SDK)**

```python
# ❌ Sin Google ADK

import google.generativeai as genai

# Llamada directa al SDK
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content(prompt)

# Parsing manual - puede fallar
try:
    result = json.loads(response.text)

    # Validación manual - tediosa y propensa a errores
    if "keep" not in result:
        raise ValueError("Missing 'keep' field")
    if "tags" not in result or not isinstance(result["tags"], list):
        raise ValueError("Invalid 'tags' field")
    # ... más validaciones manuales

except json.JSONDecodeError:
    # ❌ JSON inválido - manejo manual
    return None
except ValueError as e:
    # ❌ Campos faltantes - manejo manual
    return None
```

### **Versión Nueva (V3 - ADK)**

```python
# ✅ Con Google ADK

from google.adk.agents import LlmAgent
from schemas.scoring_schema import ScoringResponse

# Crear agente con schema
agent = LlmAgent(
    model=Gemini(...),
    instruction=SYSTEM_PROMPT,
    output_schema=ScoringResponse  # ✅ Validación automática
)

# Llamada simple
response = agent.run(prompt)
result = response.data["scoring_result"].model_dump()

# ✅ GARANTIZADO:
# - JSON válido
# - Todos los campos presentes
# - Tipos correctos
# - Sin necesidad de try/except
```

---

## 🧩 Componentes del Google ADK Usados

### 1. **`google.adk.agents.LlmAgent`**
- **Qué es:** Clase principal para crear agentes basados en LLMs
- **Dónde se usa:** `adk_scorer_v3.py` línea 56
- **Qué hace:** Encapsula modelo + instrucciones + validación

### 2. **`google.adk.models.Gemini`**
- **Qué es:** Configuración del modelo Gemini para ADK
- **Dónde se usa:** `adk_scorer_v3.py` línea 47
- **Qué hace:** Define parámetros del modelo (temperature, top_p, etc.)

### 3. **`output_schema` (Pydantic)**
- **Qué es:** Schema de validación automática
- **Dónde se define:** `src/schemas/scoring_schema.py`
- **Qué hace:** Garantiza que la respuesta del LLM sea válida

### 4. **`agent.run(prompt)`**
- **Qué es:** Método para ejecutar el agente
- **Dónde se usa:** `adk_scorer_v3.py` línea 94
- **Qué hace:** Toda la magia - llamada + validación + respuesta

---

## 📊 Flujo de Datos Interno

```
Noticia → build_user_prompt() → Prompt texto
                                      ↓
                            agent.run(prompt)
                                      ↓
                        ┌─────────────────────────┐
                        │   GOOGLE ADK INTERNO    │
                        ├─────────────────────────┤
                        │ 1. Combina prompts      │
                        │ 2. Llama Vertex AI      │
                        │ 3. Recibe texto de LLM  │
                        │ 4. Parsea JSON          │
                        │ 5. Valida con Pydantic  │
                        │ 6. Crea ScoringResponse │
                        └────────────┬────────────┘
                                     ↓
                        response.data["scoring_result"]
                                     ↓
                        ScoringResponse (validado)
                                     ↓
                        .model_dump() → dict
                                     ↓
                        Resultado final (JSON garantizado)
```

---

## 🎓 Conclusión

**Google ADK se usa en dos momentos críticos:**

1. **Inicialización** (`__init__`): Crear el agente con `LlmAgent`
2. **Ejecución** (`score`): Llamar al agente con `agent.run()`

**Ventajas de usar Google ADK:**
- ✅ Validación automática con Pydantic
- ✅ Sin parsing manual de JSON
- ✅ Manejo de errores simplificado
- ✅ Schema garantizado en producción
- ✅ Base para multi-agent systems

**Lo que Google ADK hace por ti:**
- Combina prompts inteligentemente
- Llama a Vertex AI / Gemini
- Valida la respuesta automáticamente
- Convierte a objetos tipados
- Maneja errores de forma robusta

---

¿Quedó más claro cómo funciona el flujo y dónde exactamente se usa Google ADK? 🚀
