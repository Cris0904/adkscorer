# Migración de Google SDK a Google ADK

## 🎯 Objetivo

Migrar **ADKScorerV2** (que usaba incorrectamente `google-generativeai` SDK) a **ADKScorerV3** usando el verdadero **Google ADK (Agent Development Kit)** con `output_schema` para validación estructurada.

---

## ❌ Problema Identificado

### ADKScorerV2 (Incorrecto)
```python
import google.generativeai as genai  # ❌ Esto es el SDK, NO el ADK

model = genai.GenerativeModel(...)
response = model.generate_content(prompt)
result = json.loads(response.text)  # ❌ Parsing manual sin validación
```

**Problemas:**
- No usa Google ADK, sino el SDK básico
- Parsing JSON manual propenso a errores
- Sin validación automática de schema
- Manejo de errores complejo y propenso a fallos

---

## ✅ Solución: ADKScorerV3

### Implementación Correcta con Google ADK
```python
from google.adk.agents import LlmAgent  # ✅ Google ADK real
from google.adk.models import Gemini
from pydantic import BaseModel

# Schema Pydantic para validación automática
class ScoringResponse(BaseModel):
    keep: bool
    severity: Optional[str]
    tags: List[str]
    # ... más campos

# Crear agente ADK con output_schema
agent = LlmAgent(
    name="mobility_news_scorer",
    model=Gemini(model="gemini-2.0-flash", ...),
    instruction=SYSTEM_PROMPT,
    output_schema=ScoringResponse,  # ✅ Validación automática
    output_key="scoring_result"
)

# Uso simple - respuesta ya validada
response = agent.run(prompt)
result = response.data.get("scoring_result")  # ✅ Ya es un ScoringResponse validado
```

**Ventajas:**
- ✅ Usa Google ADK real con LlmAgent
- ✅ Validación automática con Pydantic
- ✅ Sin parsing manual de JSON
- ✅ Manejo de errores simplificado
- ✅ Production-ready

---

## 📁 Archivos Creados

```
etl-movilidad-local/
├── src/
│   ├── schemas/
│   │   ├── __init__.py              # ✅ NUEVO
│   │   └── scoring_schema.py        # ✅ NUEVO - Modelo Pydantic
│   ├── adk_scorer_v3.py             # ✅ NUEVO - Implementación ADK real
│   ├── adk_scorer_v2.py             # ⚠️ OBSOLETO - Usaba SDK
│   └── prompts/
│       └── system_prompt.py         # ✔️ Sin cambios
├── scripts/
│   ├── test_gemini_v3.py            # ✅ NUEVO - Test para V3
│   ├── test_gemini_v2.py            # ⚠️ OBSOLETO - Test para V2
│   └── generate_test_news.py        # ✔️ Sin cambios
├── requirements.txt                 # ✅ ACTUALIZADO - Agregado google-adk
└── MIGRACION_ADK.md                 # ✅ NUEVO - Esta guía
```

---

## 🚀 Pasos para Probar

### 1. Instalar Dependencias

```bash
cd etl-movilidad-local
pip install -r requirements.txt
```

Esto instalará:
- `google-adk>=0.2.0` - Google Agent Development Kit
- `pydantic>=2.0.0` - Validación de schemas
- Otras dependencias existentes

### 2. Configurar Variables de Entorno

Asegúrate de tener un archivo `.env` en la raíz del proyecto:

```bash
# .env
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
```

### 3. Autenticación con Google Cloud

```bash
gcloud auth application-default login
```

### 4. Ejecutar el Test

```bash
python scripts/test_gemini_v3.py
```

---

## 📊 Comparación: V2 vs V3

| Aspecto | V2 (SDK) ❌ | V3 (ADK) ✅ |
|---------|-------------|-------------|
| **Framework** | `google-generativeai` | `google-adk` |
| **Tipo** | SDK básico | Agent Development Kit |
| **Clase principal** | `GenerativeModel` | `LlmAgent` |
| **Validación** | Manual con try/except | Automática con Pydantic |
| **Parsing JSON** | `json.loads()` manual | Automático via `output_schema` |
| **Manejo errores** | Complejo, manual | Simplificado, built-in |
| **Schema enforcement** | No garantizado | Garantizado por ADK |
| **Production-ready** | No | Sí |
| **Multi-agent support** | No | Sí (futuro) |

---

## 🔧 Cambios en el Código de Uso

### Antes (V2)
```python
from adk_scorer_v2 import ADKScorerV2

scorer = ADKScorerV2(project_id="my-project")
result = scorer.score(news_item)
# Posibles errores de parsing JSON
```

### Ahora (V3)
```python
from adk_scorer_v3 import ADKScorerV3

scorer = ADKScorerV3(project_id="my-project")
result = scorer.score(news_item)
# Respuesta garantizada con schema validado
```

**Nota:** La interfaz pública es idéntica, solo cambia la implementación interna.

---

## 🎓 Conceptos Clave de Google ADK

### 1. LlmAgent
Agente impulsado por LLM que puede:
- Ejecutar instrucciones complejas
- Usar herramientas (tools)
- Devolver respuestas estructuradas
- Encadenarse con otros agentes

### 2. output_schema
Define la estructura exacta de la respuesta usando Pydantic:
- Valida automáticamente el JSON de respuesta
- Genera errores si el formato es incorrecto
- Garantiza consistencia en producción

### 3. output_key
Nombre de la clave en `response.data` donde se almacena el resultado validado.

### 4. Gemini Model
Configuración del modelo Gemini con:
- `temperature`: Control de aleatoriedad (0.0-1.0)
- `top_p`: Nucleus sampling
- `max_output_tokens`: Límite de tokens de respuesta

---

## ✅ Validación de la Migración

### Indicadores de Éxito

1. **Importaciones correctas:**
   ```python
   from google.adk.agents import LlmAgent  # ✅
   from google.adk.models import Gemini     # ✅
   ```

2. **Agente inicializado:**
   ```
   ✅ ADK Agent initialized successfully
   Model: gemini-2.0-flash
   Output schema: ScoringResponse (Pydantic validated)
   ```

3. **Respuestas estructuradas:**
   ```
   ✅ KEPT (Validated by Pydantic schema)
   Severity: high
   Score: 0.95
   ```

### Errores Comunes

**Error:** `ModuleNotFoundError: No module named 'google.adk'`
**Solución:** `pip install google-adk>=0.2.0`

**Error:** `GOOGLE_CLOUD_PROJECT not set`
**Solución:** Crear `.env` con `GOOGLE_CLOUD_PROJECT=tu-proyecto`

**Error:** `Could not automatically determine credentials`
**Solución:** `gcloud auth application-default login`

---

## 🔮 Próximos Pasos

1. ✅ Probar V3 con `test_gemini_v3.py`
2. ✅ Validar que todas las respuestas están bien formateadas
3. ⏭️ Integrar V3 en el pipeline ETL principal
4. ⏭️ Deprecar V2 y V1
5. ⏭️ Considerar agregar herramientas (tools) al agente
6. ⏭️ Explorar multi-agent systems para casos complejos

---

## 📚 Referencias

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Python ADK API Reference](https://google.github.io/adk-docs/api-reference/python/)
- [Structured Outputs with ADK](https://saptak.in/writing/2025/05/10/google-adk-masterclass-part4)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 📝 Notas Finales

Esta migración corrige un error fundamental: **estábamos usando el SDK básico de Google Generative AI en lugar del ADK**.

El ADK (Agent Development Kit) es un framework mucho más robusto y production-ready que:
- Valida automáticamente las respuestas
- Soporta arquitecturas multi-agent
- Facilita el uso de herramientas
- Simplifica el manejo de errores

La nueva implementación (V3) es la correcta para un sistema de producción.
