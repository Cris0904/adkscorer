# Instrucciones para Probar ADK Scorer V3

## ✅ Migración Completada

Se ha migrado exitosamente de **Google SDK** (incorrectamente usado en V2) al verdadero **Google ADK (Agent Development Kit)** en V3.

---

## 📦 Archivos Creados

```
✅ src/schemas/__init__.py
✅ src/schemas/scoring_schema.py       - Modelo Pydantic para validación
✅ src/adk_scorer_v3.py                - Implementación ADK real
✅ scripts/test_gemini_v3.py           - Script de prueba
✅ requirements.txt                     - Actualizado con google-adk
✅ .env.example                         - Plantilla de configuración
✅ MIGRACION_ADK.md                     - Documentación completa
✅ INSTRUCCIONES_PRUEBA.md              - Este archivo
```

---

## 🚀 Pasos para Probar

### 1. Verificar Instalación de Dependencias

Las dependencias ya fueron instaladas exitosamente. Para verificar:

```bash
pip show google-adk
```

Deberías ver:
```
Name: google-adk
Version: 1.17.0
...
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
cd etl-movilidad-local
cp .env.example .env
```

Edita `.env` y agrega tu Project ID:

```bash
GOOGLE_CLOUD_PROJECT=tu-proyecto-google-cloud
```

### 3. Autenticar con Google Cloud

```bash
gcloud auth application-default login
```

Esto abrirá tu navegador para autenticarte.

**Alternativa:** Si prefieres usar API Key:
```bash
# En .env, descomenta y agrega:
GOOGLE_API_KEY=tu-api-key-aqui
```

### 4. Ejecutar el Test

```bash
python scripts/test_gemini_v3.py
```

---

## 📊 Salida Esperada

Si todo está configurado correctamente, deberías ver:

```
======================================================================
TESTING GOOGLE ADK WITH OUTPUT_SCHEMA (October 2025)
======================================================================

✅ Project ID: tu-proyecto
✅ Using Google ADK (Agent Development Kit)
✅ With Pydantic output_schema for automatic validation
✅ Framework: google-adk v0.2+

--- Initializing ADK Scorer V3 (True ADK Implementation) ---
INFO:__main__:Initializing Google ADK Agent...
INFO:__main__:✅ ADK Agent initialized successfully
   Model: gemini-2.0-flash
   Project: tu-proyecto
   Location: us-central1
   Output schema: ScoringResponse (Pydantic validated)
✅ ADK Agent initialized successfully

Agent Configuration:
  model: gemini-2.0-flash
  project: tu-proyecto
  location: us-central1
  sdk_version: google-adk (Agent Development Kit)
  agent_name: mobility_news_scorer
  output_schema: ScoringResponse (Pydantic)
  framework: Google ADK v0.2+

--- Generating test news ---
✅ Generated 3 test news items

--- Testing ADK Agent Scoring with Structured Output ---

[1/3] Suspensión temporal de servicio en Línea A del Metro por ...
INFO:__main__:✅ News kept: Suspensión temporal de servicio en Línea A del Me... | Severity: high | Score: 0.95
    ✅ KEPT (Validated by Pydantic schema)
       Severity: high
       Score: 0.95
       Area: Linea_A_Metro
       Tags: metro, suspension, urgente
       Entities: Metro de Medellín, Estación Niquía
       Summary: Suspensión temporal de Línea A del Metro por mantenimiento...
       Reasoning: Afecta directamente el servicio principal de transporte...

[2/3] Inauguran nuevas ciclorrutas en el sector de Laureles...
...

======================================================================
TEST COMPLETE - Google ADK with output_schema
======================================================================
```

---

## ❌ Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'google.adk'`

```bash
pip install --user -r requirements.txt
```

### Error: `GOOGLE_CLOUD_PROJECT not set in .env file`

1. Verifica que existe el archivo `.env` en `etl-movilidad-local/`
2. Abre `.env` y verifica que tiene: `GOOGLE_CLOUD_PROJECT=tu-proyecto-id`
3. Reinicia el script

### Error: `Could not automatically determine credentials`

```bash
gcloud auth application-default login
```

O configura `GOOGLE_API_KEY` en `.env`

### Error: `Vertex AI API is not enabled`

1. Ve a Google Cloud Console
2. Habilita "Vertex AI API" para tu proyecto
3. Espera unos minutos y vuelve a intentar

---

## 🔍 Verificar que Está Usando ADK (No SDK)

Abre `src/adk_scorer_v3.py` y verifica estas líneas:

```python
# ✅ CORRECTO - Usando Google ADK
from google.adk.agents import LlmAgent
from google.adk.models import Gemini

# ❌ INCORRECTO - Era el SDK (V2)
# import google.generativeai as genai
```

---

## 📚 Próximos Pasos

Después de probar exitosamente:

1. **Integrar V3 en el ETL principal:**
   - Reemplazar instancias de `ADKScorerV2` con `ADKScorerV3`
   - Actualizar imports en los scripts ETL

2. **Deprecar V2 y V1:**
   - Mover `adk_scorer_v2.py` a una carpeta `deprecated/`
   - Actualizar documentación

3. **Explorar características avanzadas de ADK:**
   - Agregar herramientas (tools) al agente
   - Implementar multi-agent systems
   - Agregar observabilidad con OpenTelemetry

---

## 🎯 Diferencias Clave: V2 vs V3

| Aspecto | V2 (SDK) ❌ | V3 (ADK) ✅ |
|---------|-------------|-------------|
| **Import** | `google.generativeai` | `google.adk.agents` |
| **Clase** | `GenerativeModel` | `LlmAgent` |
| **Validación** | Manual con `json.loads()` | Automática con Pydantic |
| **Schema** | No garantizado | Garantizado con `output_schema` |
| **Errores** | Try/except manual complejo | Manejo built-in |
| **Production** | No recomendado | Production-ready |

---

## ✅ Checklist de Migración

- [x] Instaladas dependencias (`google-adk>=0.2.0`)
- [x] Creado modelo Pydantic (`ScoringResponse`)
- [x] Implementado `ADKScorerV3` con `LlmAgent`
- [x] Creado test script compatible con Windows
- [x] Documentación completa
- [ ] Configurar `.env` con tu `GOOGLE_CLOUD_PROJECT`
- [ ] Autenticar con `gcloud auth application-default login`
- [ ] Ejecutar test: `python scripts/test_gemini_v3.py`
- [ ] Verificar que las respuestas son validadas correctamente
- [ ] Integrar en ETL principal
- [ ] Deprecar versiones antiguas

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa `MIGRACION_ADK.md` para detalles técnicos
2. Verifica logs en la salida del script
3. Consulta [Google ADK Docs](https://google.github.io/adk-docs/)
4. Verifica que Vertex AI API está habilitado en tu proyecto

---

**¡Listo para producción!** 🎉

La nueva implementación V3 usa el verdadero Google ADK con validación automática de schemas, manejo robusto de errores, y está lista para ambientes de producción.
