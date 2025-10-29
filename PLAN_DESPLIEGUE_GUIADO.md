# Plan de Despliegue Guiado - ETL Movilidad Medellín

## 🎯 Objetivo
Desplegar el MVP Local completamente funcional en ~1 hora, con guía paso a paso.

## 📊 Progreso General

```
FASE 1: Preparación       [░░░░░░░░░░] 0% - 30 min
FASE 2: Instalación       [░░░░░░░░░░] 0% - 15 min
FASE 3: Pruebas           [░░░░░░░░░░] 0% - 10 min
FASE 4: Despliegue Real   [░░░░░░░░░░] 0% - 10 min
FASE 5: Automatización    [░░░░░░░░░░] 0% - 5 min
```

---

## FASE 1: PREPARACIÓN (30 minutos)

### ✅ PASO 1.1: Verificar Python instalado (2 min)

**Acción:**
```bash
python --version
```

**Resultado esperado:**
```
Python 3.9.x o superior
```

**Si NO tienes Python:**
- Windows: https://www.python.org/downloads/ (marcar "Add to PATH")
- Mac: `brew install python3`
- Linux: `sudo apt install python3 python3-venv python3-pip`

**Checkpoint:** ✅ Python >= 3.9 instalado

---

### ✅ PASO 1.2: Crear cuenta Google Cloud (10 min)

**Acción:**

1. Ve a: https://console.cloud.google.com
2. Clic en "Get started for free" o "Console"
3. Acepta términos y condiciones
4. Configura billing (necesitas tarjeta pero hay $300 free credits)

**Checkpoint:** ✅ Acceso a Google Cloud Console

---

### ✅ PASO 1.3: Crear proyecto en Google Cloud (3 min)

**Acción:**

1. En Google Cloud Console, clic en selector de proyectos (arriba)
2. Clic en "NEW PROJECT"
3. **Nombre:** `etl-movilidad-medellin`
4. Clic en "CREATE"
5. **IMPORTANTE:** Anota el **Project ID** (ej: `etl-movilidad-medellin-425316`)

**Resultado esperado:**
```
Project created: etl-movilidad-medellin
Project ID: etl-movilidad-medellin-XXXXXX
```

**Checkpoint:** ✅ Project ID anotado: ___________________________

---

### ✅ PASO 1.4: Habilitar Vertex AI API (2 min)

**Acción:**

1. En Google Cloud Console, busca "Vertex AI API" en la barra superior
2. Clic en el resultado "Vertex AI API"
3. Clic en "ENABLE"
4. Espera 1-2 minutos (aparecerá "API enabled")

**Resultado esperado:**
```
✓ Vertex AI API enabled for project etl-movilidad-medellin-XXXXXX
```

**Checkpoint:** ✅ Vertex AI API habilitada

---

### ✅ PASO 1.5: Instalar gcloud CLI (10 min)

**Windows:**

1. Descargar: https://cloud.google.com/sdk/docs/install#windows
2. Ejecutar `GoogleCloudSDKInstaller.exe`
3. Seguir instalador (dejar opciones por defecto)
4. **IMPORTANTE:** Cerrar y abrir nueva terminal PowerShell

**macOS:**

```bash
# Opción 1: Homebrew (recomendado)
brew install google-cloud-sdk

# Opción 2: Script
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Linux:**

```bash
# Ubuntu/Debian
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt update && sudo apt install google-cloud-cli

# Otras distros
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Verificar instalación:**
```bash
gcloud --version
```

**Resultado esperado:**
```
Google Cloud SDK 460.0.0
...
```

**Checkpoint:** ✅ gcloud CLI instalado

---

### ✅ PASO 1.6: Autenticar gcloud CLI (3 min)

**Acción:**

```bash
# 1. Autenticar tu cuenta
gcloud auth login
```

Esto abrirá navegador → Selecciona tu cuenta Google → Permite acceso

```bash
# 2. Configurar proyecto (REEMPLAZAR con tu Project ID)
gcloud config set project etl-movilidad-medellin-XXXXXX

# 3. Autenticar para aplicaciones (IMPORTANTE)
gcloud auth application-default login
```

Esto abrirá navegador nuevamente → Permite acceso

**Verificar configuración:**
```bash
gcloud config list
```

**Resultado esperado:**
```
[core]
account = tu-email@gmail.com
project = etl-movilidad-medellin-XXXXXX
```

**Checkpoint:** ✅ gcloud autenticado y configurado

---

## FASE 2: INSTALACIÓN (15 minutos)

### ✅ PASO 2.1: Navegar al proyecto (1 min)

**Acción:**

```bash
# Ir al directorio del proyecto
cd etl-movilidad-local

# Verificar contenido
ls
```

**Resultado esperado:**
Deberías ver:
```
src/
scripts/
requirements.txt
README.md
.env.example
...
```

**Checkpoint:** ✅ En directorio etl-movilidad-local

---

### ✅ PASO 2.2: Crear entorno virtual (2 min)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Resultado esperado:**
Deberías ver `(venv)` al inicio de tu línea de comando:
```
(venv) PS C:\...\etl-movilidad-local>
```

**Checkpoint:** ✅ Entorno virtual activado (ves "(venv)")

---

### ✅ PASO 2.3: Actualizar pip (1 min)

**Acción:**
```bash
pip install --upgrade pip
```

**Resultado esperado:**
```
Successfully installed pip-24.x.x
```

**Checkpoint:** ✅ pip actualizado

---

### ✅ PASO 2.4: Instalar dependencias (5 min)

**Acción:**
```bash
pip install -r requirements.txt
```

**Resultado esperado:**
```
Collecting google-cloud-aiplatform...
Collecting vertexai...
...
Successfully installed google-cloud-aiplatform-X.X.X vertexai-X.X.X ...
```

**Verificar instalación:**
```bash
pip list | grep google
```

Deberías ver:
```
google-cloud-aiplatform    X.X.X
google-auth                X.X.X
...
```

**Checkpoint:** ✅ Todas las dependencias instaladas

---

### ✅ PASO 2.5: Configurar variables de entorno (5 min)

**Acción:**

```bash
# Copiar archivo de ejemplo
cp .env.example .env
```

**Editar .env:**

Abrir archivo `.env` con tu editor favorito:

**Windows:**
```bash
notepad .env
```

**Mac:**
```bash
open -e .env
```

**Linux:**
```bash
nano .env
# o
vim .env
```

**Modificar estas líneas (IMPORTANTE):**

```env
# CAMBIAR ESTO con tu Project ID del Paso 1.3
GOOGLE_CLOUD_PROJECT=etl-movilidad-medellin-XXXXXX

# Dejar estos valores por ahora
VERTEX_AI_LOCATION=us-central1
USE_MOCK_ADK=false
SCHEDULE_INTERVAL_MINUTES=5
ENABLE_EMAIL_ALERTS=false
```

**Guardar y cerrar el archivo.**

**Verificar:**
```bash
cat .env | grep GOOGLE_CLOUD_PROJECT
```

**Resultado esperado:**
```
GOOGLE_CLOUD_PROJECT=etl-movilidad-medellin-XXXXXX
```

**Checkpoint:** ✅ Archivo .env configurado con Project ID correcto

---

### ✅ PASO 2.6: Crear directorios necesarios (1 min)

**Acción:**
```bash
# Windows
mkdir data logs 2>$null

# Linux/Mac
mkdir -p data logs
```

**Checkpoint:** ✅ Directorios data/ y logs/ creados

---

## FASE 3: PRUEBAS (10 minutos)

### ✅ PASO 3.1: Probar extracción de noticias (3 min)

**Acción:**

```bash
cd scripts
python test_extraction.py
```

**Resultado esperado:**

```
============================================================
Testing News Extraction
============================================================

--- Testing Metro de Medellín RSS ---
✓ Extracted 15 news items

Sample (first item):
{
  "source": "Metro de Medellín",
  "url": "https://www.metrodemedellin.gov.co/...",
  "title": "...",
  "body": "...",
  "published_at": "2025-01-15T10:30:00"
}

--- Testing Alcaldía de Medellín ---
✓ Extracted 12 news items

--- Testing AMVA ---
✓ Extracted 8 news items

============================================================
Total extracted: 35 news items
============================================================
```

**Si ves errores de extracción:**
- Es NORMAL si algunas fuentes fallan (URLs pueden haber cambiado)
- Lo importante es que al menos una fuente funcione
- Podemos ajustar extractores después

**Checkpoint:** ✅ Al menos una fuente extrae noticias correctamente

---

### ✅ PASO 3.2: Ejecutar pipeline en modo MOCK (3 min)

Primero probemos sin llamar a Google API (modo seguro):

**Editar .env temporalmente:**
```bash
cd ..
# Editar .env y cambiar:
USE_MOCK_ADK=true
```

**Ejecutar pipeline:**
```bash
cd src
python main.py
```

**Resultado esperado:**

```
============================================================
Starting ETL Pipeline execution
============================================================
WARNING:root:Using MockADKScorer - for testing only!

STEP 1: Extracting news from sources...
✓ Extracted 35 news items

STEP 2: Deduplicating news...
✓ Deduplicated: 0 duplicates found, 35 unique items

STEP 3: Scoring news with ADK...
✓ Scored 35 items: 12 kept, 23 discarded

STEP 4: Saving to database...
✓ Saved 12 news items to database

STEP 5: Sending alerts for high severity news...
⚠️ ALERTA DE MOVILIDAD - MEDIUM
============================================================
Título: Metro de Medellín implementa nuevas medidas...
...
✓ Sent 2 alerts

============================================================
ETL Pipeline execution complete
Duration: 5.23 seconds
============================================================
```

**Si hay errores:**
- Verificar que estás en directorio `src/`
- Verificar que entorno virtual está activo (ves "(venv)")
- Verificar que .env tiene `USE_MOCK_ADK=true`

**Checkpoint:** ✅ Pipeline funciona en modo mock

---

### ✅ PASO 3.3: Verificar base de datos (2 min)

**Acción:**

```bash
cd ../scripts
python db_stats.py
```

**Resultado esperado:**

```
============================================================
DATABASE STATISTICS
============================================================

📊 Total News Items: 12

📈 By Severity:
  medium    :    8 ( 66.7%)
  low       :    4 ( 33.3%)

📰 By Source:
  Metro de Medellín         :    7 ( 58.3%)
  Alcaldía de Medellín      :    3 ( 25.0%)
  AMVA                      :    2 ( 16.7%)

🔄 Recent Executions: 1

📋 Recent News (last 10):
  1. [MEDIUM] Cambios en horarios del Metro...
     Source: Metro de Medellín
     ...
```

**Checkpoint:** ✅ Base de datos creada y con datos

---

### ✅ PASO 3.4: Ver alertas generadas (2 min)

**Acción:**

```bash
python view_alerts.py
```

**Resultado esperado:**

```
============================================================
ALERTS LOG (2 total)
============================================================

1. ℹ️ [MEDIUM] Nuevas rutas de buses en El Poblado...
   Timestamp: 2025-01-15T14:23:45
   Area: El Poblado
   Source: Alcaldía de Medellín
   Summary: Se implementan nuevas rutas...
   ...
```

**Checkpoint:** ✅ Sistema de alertas funciona

---

## FASE 4: DESPLIEGUE REAL (10 minutos)

### ✅ PASO 4.1: Cambiar a modo REAL (ADK) (1 min)

**Editar .env:**

```bash
cd ..
# Editar .env y cambiar:
USE_MOCK_ADK=false
```

Guardar archivo.

**Checkpoint:** ✅ .env configurado con USE_MOCK_ADK=false

---

### ✅ PASO 4.2: Ejecutar pipeline con Google Gemini (5 min)

**ESTE ES EL MOMENTO DE VERDAD! 🎯**

**Acción:**

```bash
cd src
python main.py
```

**Resultado esperado:**

```
============================================================
Starting ETL Pipeline execution
============================================================
INFO:root:Initialized Vertex AI: etl-movilidad-medellin-XXXXXX in us-central1

STEP 1: Extracting news from sources...
✓ Extracted 35 news items

STEP 2: Deduplicating news...
✓ Deduplicated: 12 duplicates found, 23 unique items

STEP 3: Scoring news with ADK...
INFO:root:News scored: Metro suspende servicio temporalmente... | Severity: high | Score: 0.92
INFO:root:News scored: Nuevas ciclorrutas en Laureles... | Severity: medium | Score: 0.75
...
✓ Scored 23 items: 8 kept, 15 discarded

STEP 4: Saving to database...
✓ Saved 8 news items to database

STEP 5: Sending alerts for high severity news...

🚨 ALERTA DE MOVILIDAD - HIGH
============================================================
Título: Metro suspende servicio temporalmente en Línea A
Área: Linea_A_Metro
Resumen: Suspensión temporal del servicio entre Niquía y Bello por
mantenimiento de emergencia. Se estima reanudación en 2 horas.
Fuente: Metro de Medellín
URL: https://...
Tags: metro, suspension, urgente, linea_a
============================================================

✓ Sent 2 alerts

============================================================
ETL Pipeline execution complete
Duration: 34.56 seconds
Stats: {'extracted': 35, 'deduplicated': 12, 'scored': 23, ...}
============================================================
```

**Si hay errores comunes:**

**Error: "DefaultCredentialsError"**
```bash
gcloud auth application-default login
```

**Error: "Permission denied" o "API not enabled"**
```bash
gcloud services enable aiplatform.googleapis.com
```

**Error: "Invalid project"**
- Verificar Project ID en .env
- Verificar que proyecto existe: `gcloud projects list`

**Checkpoint:** ✅ Pipeline ejecuta correctamente con Google Gemini

---

### ✅ PASO 4.3: Verificar calidad de clasificación (2 min)

**Acción:**

```bash
cd ../scripts
python db_stats.py
```

**Analizar:**
- ¿Las noticias guardadas son relevantes para movilidad?
- ¿Los niveles de severidad tienen sentido?
- ¿Las áreas están correctamente identificadas?

**Ver ejemplos específicos:**
```bash
python db_stats.py | head -30
```

**Checkpoint:** ✅ Clasificación de calidad aceptable

---

### ✅ PASO 4.4: Ver costos en Google Cloud (2 min)

**Acción:**

1. Ve a: https://console.cloud.google.com/billing
2. Selecciona tu proyecto
3. Ve a "Reports"
4. Verifica costos de Vertex AI

**Costo esperado por ejecución:**
- ~35 noticias × 500 tokens = 17,500 tokens input
- ~35 resúmenes × 100 tokens = 3,500 tokens output
- **Costo: ~$0.002 por ejecución** (menos de 1 centavo!)

**Checkpoint:** ✅ Costos verificados y dentro de lo esperado

---

## FASE 5: AUTOMATIZACIÓN (5 minutos)

### ✅ PASO 5.1: Configurar scheduler (2 min)

El scheduler ya está configurado para ejecutar cada 5 minutos.

**Si quieres cambiar el intervalo:**

Editar `.env`:
```env
# Cada 15 minutos (recomendado para empezar)
SCHEDULE_INTERVAL_MINUTES=15

# O cada hora
SCHEDULE_INTERVAL_MINUTES=60
```

**Checkpoint:** ✅ Intervalo de scheduler configurado

---

### ✅ PASO 5.2: Ejecutar scheduler (3 min)

**Acción:**

```bash
cd ../src
python scheduler.py
```

**Resultado esperado:**

```
============================================================
ETL Scheduler Starting
============================================================
Interval: Every 15 minutes
Mock ADK: False
Email Alerts: False
Press Ctrl+C to stop
============================================================

Running initial pipeline execution...
[Pipeline completo ejecuta...]

Scheduler running. Waiting for next execution...
Next execution at: 2025-01-15 14:45:00
```

**El scheduler:**
- Ejecuta inmediatamente al iniciar
- Luego ejecuta cada N minutos
- Logs en `logs/scheduler.log`
- Detener con `Ctrl+C`

**Para ejecutar en segundo plano:**

**Windows (PowerShell):**
```powershell
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden
```

**Linux/Mac:**
```bash
nohup python scheduler.py > ../logs/scheduler.log 2>&1 &
```

**Ver logs en tiempo real:**
```bash
# Otra terminal
tail -f ../logs/scheduler.log
```

**Checkpoint:** ✅ Scheduler ejecutando automáticamente

---

## ✅ FASE 6: CONFIGURACIÓN AVANZADA (OPCIONAL)

### 📧 PASO 6.1: Configurar alertas por email (10 min)

**Solo si quieres recibir emails de alertas**

**Gmail Setup:**

1. Ve a: https://myaccount.google.com/security
2. Habilita "2-Step Verification"
3. Ve a: https://myaccount.google.com/apppasswords
4. Crea App Password para "Mail"
5. Copia el password (16 caracteres)

**Editar .env:**

```env
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App Password
ALERT_RECIPIENTS=destinatario@ejemplo.com,otro@ejemplo.com
```

**Probar:**
```bash
cd src
python main.py
```

Deberías recibir emails para noticias high/critical.

**Checkpoint:** ✅ Emails de alertas configurados (opcional)

---

## 🎉 ¡DESPLIEGUE COMPLETO!

## 📊 Resumen de lo logrado

✅ **Sistema completo funcionando:**
- Extracción automática de múltiples fuentes
- Clasificación inteligente con Google Gemini 1.5 Flash
- Deduplicación automática
- Base de datos SQLite con historial
- Alertas en consola, archivo JSON, y email (opcional)
- Ejecución automática programada

✅ **Tiempo de despliegue:** ~1 hora

✅ **Costo operativo:** $0.50 - $2/mes

---

## 📝 Siguientes pasos recomendados

### Inmediato (próximas 24 horas)
- [ ] Dejar scheduler ejecutando
- [ ] Monitorear logs: `tail -f logs/scheduler.log`
- [ ] Verificar calidad de clasificación

### Esta semana
- [ ] Ajustar prompts si es necesario (`src/prompts/system_prompt.py`)
- [ ] Agregar fuentes adicionales si se requiere
- [ ] Configurar alertas por email

### Próximas 2 semanas
- [ ] Recopilar métricas de uso
- [ ] Validar con usuarios reales
- [ ] Documentar casos especiales

### Decisión en 1 mes
- [ ] Evaluar volumen de noticias procesadas
- [ ] Si > 500/día → considerar migración a cloud
- [ ] Ver PLAN_IMPLEMENTACION.md para versión cloud

---

## 🛠️ Comandos útiles

### Monitoreo
```bash
# Ver logs del pipeline
tail -f logs/etl_pipeline.log

# Ver logs del scheduler
tail -f logs/scheduler.log

# Ver estadísticas
cd scripts && python db_stats.py

# Ver alertas recientes
python view_alerts.py
```

### Mantenimiento
```bash
# Limpiar base de datos (CUIDADO!)
rm data/etl_movilidad.db

# Limpiar logs
rm logs/*.log logs/*.json

# Actualizar dependencias
pip install --upgrade -r requirements.txt
```

### Testing
```bash
# Probar extractores
cd scripts && python test_extraction.py

# Ejecutar pipeline manualmente
cd src && python main.py

# Modo mock (sin API calls)
# Editar .env: USE_MOCK_ADK=true
cd src && python main.py
```

---

## 🐛 Troubleshooting rápido

### Scheduler no ejecuta
```bash
# Verificar que está corriendo
ps aux | grep scheduler  # Linux/Mac
tasklist | findstr python  # Windows

# Ver logs
tail -f logs/scheduler.log
```

### No se extraen noticias
```bash
# Probar cada fuente individualmente
cd scripts
python test_extraction.py

# Verificar conectividad
curl https://www.metrodemedellin.gov.co/feed
```

### ADK clasifica mal
```bash
# Ajustar prompts
nano src/prompts/system_prompt.py

# Cambiar criterios de relevancia
# Agregar más contexto de Medellín
# Modificar umbrales de severidad
```

### Costos muy altos
```bash
# Reducir frecuencia
# Editar .env: SCHEDULE_INTERVAL_MINUTES=60

# Verificar costos
# https://console.cloud.google.com/billing
```

---

## 📞 Soporte

**Documentación:**
- README.md (este directorio)
- GUIA_DESPLIEGUE.md (paso a paso detallado)
- RESUMEN_ANALISIS_MVP.md (directorio raíz)

**Logs:**
- `logs/etl_pipeline.log` - Ejecuciones del pipeline
- `logs/scheduler.log` - Ejecuciones programadas
- `logs/alerts.json` - Historial de alertas

---

## ✅ Checklist Final

Verifica que todo está funcionando:

- [ ] Python 3.9+ instalado
- [ ] Google Cloud proyecto creado
- [ ] Vertex AI API habilitada
- [ ] gcloud CLI instalado y autenticado
- [ ] Entorno virtual creado y activo
- [ ] Dependencias instaladas
- [ ] .env configurado con Project ID correcto
- [ ] Test de extracción ejecutado exitosamente
- [ ] Pipeline en modo mock funciona
- [ ] Pipeline con ADK real funciona
- [ ] Base de datos creada con noticias
- [ ] Alertas generándose correctamente
- [ ] Scheduler ejecutando automáticamente
- [ ] Logs monitoreándose
- [ ] Costos verificados en Google Cloud

---

## 🎊 ¡Felicitaciones!

Tienes un sistema ETL profesional de alertas de movilidad:
- ✅ Completamente funcional
- ✅ Clasificación con IA (Google Gemini)
- ✅ Ejecución automática
- ✅ Bajo costo ($0.50-$2/mes)
- ✅ Escalable a futuro

**Duración total:** ~1 hora
**Listo para producción:** ✅

---

*Última actualización: 2025-01-15*
