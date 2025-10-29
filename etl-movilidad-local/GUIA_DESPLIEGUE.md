# Guía de Despliegue Paso a Paso - ETL Movilidad Medellín

Esta guía te llevará paso a paso desde cero hasta tener el sistema funcionando.

## 📋 Pre-requisitos

Antes de empezar, necesitas:

1. **Python 3.9 o superior**
   - Verificar: `python --version`
   - Descargar: https://www.python.org/downloads/

2. **Cuenta de Google Cloud**
   - Crear cuenta: https://console.cloud.google.com
   - Necesitarás tarjeta de crédito (pero hay free tier)

3. **Editor de texto**
   - VS Code (recomendado): https://code.visualstudio.com/
   - O cualquier editor de texto

## 🚀 Paso 1: Configurar Google Cloud (15 minutos)

### 1.1. Crear proyecto

1. Ve a https://console.cloud.google.com
2. Click en "Select a project" → "NEW PROJECT"
3. Nombre: `etl-movilidad-medellin`
4. Click "CREATE"
5. **Anota el Project ID** (ej: `etl-movilidad-medellin-12345`)

### 1.2. Habilitar Vertex AI API

1. En la consola de Google Cloud, busca "Vertex AI API"
2. Click en "ENABLE"
3. Espera 1-2 minutos

### 1.3. Instalar gcloud CLI

**Windows:**
1. Descargar: https://cloud.google.com/sdk/docs/install
2. Ejecutar instalador
3. Abrir nueva terminal PowerShell

**macOS:**
```bash
brew install google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 1.4. Autenticar y configurar

```bash
# Autenticar
gcloud auth login

# Configurar proyecto (reemplazar con tu Project ID)
gcloud config set project etl-movilidad-medellin-12345

# Autenticar para aplicaciones
gcloud auth application-default login
```

✅ **Checkpoint**: Verifica que todo funciona:
```bash
gcloud projects describe etl-movilidad-medellin-12345
```

## 🛠️ Paso 2: Instalar el proyecto (10 minutos)

### 2.1. Navegar al directorio

```bash
# Ir al directorio del proyecto
cd etl-movilidad-local
```

### 2.2. Crear entorno virtual

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

Deberías ver `(venv)` en tu terminal.

### 2.3. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Esto instalará:
- google-cloud-aiplatform
- vertexai
- requests
- feedparser
- beautifulsoup4
- schedule
- python-dotenv

✅ **Checkpoint**: Verifica instalación:
```bash
pip list | grep google
```

Deberías ver `google-cloud-aiplatform` y otros paquetes de Google.

## ⚙️ Paso 3: Configurar variables de entorno (5 minutos)

### 3.1. Crear archivo .env

```bash
# Copiar ejemplo
cp .env.example .env
```

### 3.2. Editar .env

Abrir `.env` con tu editor y modificar:

```env
# Reemplazar con tu Project ID
GOOGLE_CLOUD_PROJECT=etl-movilidad-medellin-12345

# Región (dejar por defecto)
VERTEX_AI_LOCATION=us-central1

# Usar ADK real (no mock)
USE_MOCK_ADK=false

# Ejecutar cada 5 minutos
SCHEDULE_INTERVAL_MINUTES=5

# Alertas por email (opcional, dejar false por ahora)
ENABLE_EMAIL_ALERTS=false
```

**Importante:** Guarda el archivo después de editar.

✅ **Checkpoint**: Verifica que .env existe y tiene tu Project ID:
```bash
cat .env | grep GOOGLE_CLOUD_PROJECT
```

## 🧪 Paso 4: Probar extracción (5 minutos)

Antes de ejecutar el pipeline completo, probemos solo la extracción:

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
  "url": "https://...",
  "title": "...",
  ...
}
...
Total extracted: 45 news items
```

Si ves errores:
- Verifica conexión a internet
- Las URLs de fuentes pueden haber cambiado (es normal, se puede ajustar)

## 🎯 Paso 5: Primera ejecución (MOMENTO DE VERDAD!)

### 5.1. Ejecutar pipeline manualmente

```bash
cd ../src
python main.py
```

**Qué esperar:**

```
============================================================
Starting ETL Pipeline execution
============================================================
STEP 1: Extracting news from sources...
✓ Extracted 42 news items

STEP 2: Deduplicating news...
✓ Deduplicated: 0 duplicates found, 42 unique items

STEP 3: Scoring news with ADK...
[Llamadas a Gemini API aquí...]
✓ Scored 42 items: 15 kept, 27 discarded

STEP 4: Saving to database...
✓ Saved 15 news items to database

STEP 5: Sending alerts for high severity news...
⚠️ ALERTA DE MOVILIDAD - HIGH
============================================================
Título: Cierre de vía en Medellín...
...
✓ Sent 3 alerts

============================================================
ETL Pipeline execution complete
Duration: 45.23 seconds
============================================================
```

### 5.2. Si hay errores

**Error: "DefaultCredentialsError"**
```bash
gcloud auth application-default login
```

**Error: "API not enabled"**
```bash
gcloud services enable aiplatform.googleapis.com
```

**Error: "Permission denied"**
- Verifica que tu cuenta tiene permisos de Vertex AI
- En console.cloud.google.com → IAM → Agregar role "Vertex AI User"

### 5.3. Modo de prueba sin Google Cloud

Si quieres probar sin API calls:

1. Editar `.env`: `USE_MOCK_ADK=true`
2. Ejecutar: `python main.py`

Esto usa clasificación simple sin llamar a Gemini.

## 📊 Paso 6: Verificar resultados (5 minutos)

### 6.1. Ver estadísticas

```bash
cd ../scripts
python db_stats.py
```

Verás:
- Total de noticias guardadas
- Distribución por severidad
- Distribución por fuente
- Últimas noticias

### 6.2. Ver alertas

```bash
python view_alerts.py
```

Verás todas las alertas enviadas con detalles.

### 6.3. Explorar base de datos

La base de datos SQLite está en `data/etl_movilidad.db`

Puedes abrirla con:
- DB Browser for SQLite: https://sqlitebrowser.org/
- DBeaver: https://dbeaver.io/

## ⏰ Paso 7: Configurar ejecución automática (5 minutos)

### 7.1. Ejecutar scheduler

```bash
cd ../src
python scheduler.py
```

Esto ejecutará el pipeline:
1. Inmediatamente al iniciar
2. Luego cada 5 minutos (configurable en `.env`)

**Salida esperada:**
```
============================================================
ETL Scheduler Starting
============================================================
Interval: Every 5 minutes
Mock ADK: False
Email Alerts: False
Press Ctrl+C to stop
============================================================

Running initial pipeline execution...
[Pipeline ejecuta...]

Scheduler running. Waiting for next execution...
[Espera 5 minutos...]
[Pipeline ejecuta nuevamente...]
```

### 7.2. Detener scheduler

Presiona `Ctrl+C` para detener.

### 7.3. Ejecutar en segundo plano (opcional)

**Windows (PowerShell):**
```powershell
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden
```

**Linux/Mac:**
```bash
nohup python scheduler.py > ../logs/scheduler.log 2>&1 &
```

## 📧 Paso 8: Configurar alertas por email (OPCIONAL - 10 minutos)

### 8.1. Configurar Gmail

1. Ve a https://myaccount.google.com/security
2. Habilita autenticación de 2 factores
3. Ve a https://myaccount.google.com/apppasswords
4. Crea App Password para "Mail"
5. Anota la contraseña (16 caracteres)

### 8.2. Editar .env

```env
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # App Password
ALERT_RECIPIENTS=destinatario1@ejemplo.com,destinatario2@ejemplo.com
```

### 8.3. Probar

```bash
cd src
python main.py
```

Deberías recibir emails para noticias de alta severidad.

## 🎉 ¡Listo! El sistema está funcionando

## 📝 Tareas de mantenimiento

### Monitoreo diario

```bash
# Ver logs
tail -f logs/etl_pipeline.log

# Ver estadísticas
cd scripts && python db_stats.py

# Ver alertas recientes
python view_alerts.py
```

### Ajustes comunes

**Cambiar intervalo de ejecución:**
- Editar `.env`: `SCHEDULE_INTERVAL_MINUTES=15`

**Agregar más fuentes:**
- Editar `src/extractors.py`
- Agregar método `extract_nueva_fuente()`
- Llamar en `extract_all()`

**Ajustar prompts de ADK:**
- Editar `src/prompts/system_prompt.py`
- Modificar criterios de relevancia
- Agregar contexto específico

## 🐛 Troubleshooting

### Problema: No se extraen noticias

**Solución:**
1. Verificar conectividad: `curl https://www.metrodemedellin.gov.co/feed`
2. URLs pueden haber cambiado (normal)
3. Actualizar selectores en `src/extractors.py`

### Problema: ADK no clasifica bien

**Solución:**
1. Ajustar prompts en `src/prompts/system_prompt.py`
2. Agregar más ejemplos de contexto de Medellín
3. Modificar criterios de relevancia

### Problema: Muchos falsos positivos/negativos

**Solución:**
1. Ver logs: `tail -f logs/etl_pipeline.log`
2. Verificar score de relevancia en database
3. Ajustar umbral o prompts

### Problema: Costos muy altos

**Solución:**
1. Reducir intervalo: `SCHEDULE_INTERVAL_MINUTES=15`
2. Limitar noticias por fuente en `extractors.py`
3. Verificar en Google Cloud Console → Billing

## 📈 Próximos pasos

### Optimización (Semana 2-3)
- Ajustar prompts basándose en resultados reales
- Agregar más fuentes
- Afinar clasificación de severidad

### Validación (Semana 3-4)
- Comparar con alertas oficiales
- Medir precisión y recall
- Recopilar feedback de usuarios

### Escalamiento (cuando sea necesario)
- Si volumen > 500 noticias/día
- Ver `PLAN_IMPLEMENTACION.md` para versión cloud
- Migración gradual

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa logs**: `logs/etl_pipeline.log`
2. **Verifica configuración**: `cat .env`
3. **Prueba con mock**: `USE_MOCK_ADK=true`
4. **Consulta documentación**:
   - README.md (este directorio)
   - RESUMEN_ANALISIS_MVP.md (directorio raíz)
   - PLAN_MVP_LOCAL.md (directorio raíz)

## ✅ Checklist de verificación

- [ ] Google Cloud proyecto creado
- [ ] Vertex AI API habilitada
- [ ] gcloud CLI instalado y autenticado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Archivo .env configurado con Project ID
- [ ] Test de extracción ejecutado exitosamente
- [ ] Pipeline manual ejecutado al menos una vez
- [ ] Base de datos creada y con noticias
- [ ] Estadísticas verificadas
- [ ] Scheduler probado (opcional)
- [ ] Email alerts configurados (opcional)

## 🎊 ¡Felicitaciones!

Tienes un sistema ETL completo funcionando con:
- ✅ Extracción automática de múltiples fuentes
- ✅ Clasificación inteligente con Google ADK
- ✅ Deduplicación automática
- ✅ Alertas en tiempo real
- ✅ Base de datos persistente
- ✅ Ejecución automática programada
- ✅ Costo: $0.50 - $2/mes

**Duración total de despliegue: ~1 hora**

¡Ahora tienes un sistema de alertas de movilidad profesional para Medellín! 🚇🚌🚗
