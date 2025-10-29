# Scheduler - Ejecución Automática del Pipeline

El scheduler ejecuta automáticamente el pipeline ETL cada 20 minutos para mantener la base de datos actualizada con las últimas noticias de movilidad.

## 🚀 Inicio Rápido

### Opción 1: Usando el archivo .bat (Windows)

Simplemente haz doble clic en:
```
run_scheduler.bat
```

### Opción 2: Desde la línea de comandos

```bash
python scheduler_advanced.py
```

### Opción 3: Scheduler simple (sin librería schedule)

```bash
python scheduler.py
```

## 📋 Características

- ✅ **Ejecución inicial inmediata**: Corre el pipeline al iniciar
- ✅ **Ejecución periódica**: Cada 20 minutos automáticamente
- ✅ **Logs detallados**: Guarda logs en `logs/scheduler.log`
- ✅ **Manejo de errores**: Continúa ejecutando aunque falle una iteración
- ✅ **Contador de ejecuciones**: Muestra cuántas veces se ha ejecutado
- ✅ **Detención segura**: Presiona Ctrl+C para detener

## 📊 ¿Qué hace el Scheduler?

Cada 20 minutos:
1. Extrae noticias de 4 fuentes con Apify
2. Califica con Google ADK (Gemini 2.0 Flash)
3. Deduplica (solo procesa noticias nuevas)
4. Guarda noticias relevantes en Supabase
5. Registra la ejecución en los logs

## 🔧 Configuración

El scheduler usa la misma configuración del archivo `.env`:

```bash
# Base de datos
USE_SUPABASE=true

# Google Cloud (para ADK)
GOOGLE_CLOUD_PROJECT=healthy-anthem-418104

# Apify (para scraping)
APIFY_API_TOKEN=apify_api_...

# Supabase (para almacenamiento)
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_KEY=eyJ...
```

## 📝 Logs

Los logs se guardan en dos lugares:

1. **Consola**: Salida en tiempo real
2. **Archivo**: `logs/scheduler.log`

Ejemplo de log:
```
2025-10-29 12:00:00 - INFO - ============================================================
2025-10-29 12:00:00 - INFO - Pipeline Execution #1
2025-10-29 12:00:00 - INFO - Time: 2025-10-29 12:00:00
2025-10-29 12:00:00 - INFO - ============================================================
2025-10-29 12:02:15 - INFO - ✓ Execution #1 completed successfully
2025-10-29 12:02:15 - INFO - Next run scheduled in 20 minutes
```

## ⏰ Cambiar el Intervalo

Para cambiar el intervalo de ejecución, edita `scheduler_advanced.py`:

```python
# De 20 minutos a otro intervalo:
schedule.every(20).minutes.do(run_pipeline)  # Cada 20 minutos
schedule.every(1).hour.do(run_pipeline)      # Cada hora
schedule.every(30).minutes.do(run_pipeline)  # Cada 30 minutos
schedule.every().day.at("09:00").do(run_pipeline)  # Diario a las 9 AM
```

O edita `scheduler.py`:

```python
# Cambiar intervalo (en segundos)
interval_seconds = 20 * 60  # 20 minutos
interval_seconds = 60 * 60  # 1 hora
interval_seconds = 30 * 60  # 30 minutos
```

## 🛑 Detener el Scheduler

Presiona **Ctrl+C** en la consola donde está corriendo.

Verás un mensaje como:
```
============================================================
Scheduler stopped by user
Total executions: 5
Stopped at: 2025-10-29 14:30:00
============================================================
```

## 🔄 Ejecutar como Servicio (Opcional)

### Windows - Tarea Programada

1. Abre **Programador de tareas** (Task Scheduler)
2. Clic en **Crear tarea básica**
3. Nombre: `ETL Movilidad Scheduler`
4. Desencadenador: **Al iniciar sesión** o **Al iniciar el equipo**
5. Acción: **Iniciar un programa**
6. Programa: `C:\ruta\al\python.exe`
7. Argumentos: `scheduler_advanced.py`
8. Directorio: `C:\ruta\al\proyecto\etl-movilidad-local`

### Linux/Mac - systemd o cron

**systemd** (`/etc/systemd/system/etl-movilidad.service`):
```ini
[Unit]
Description=ETL Movilidad Scheduler
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/ruta/al/proyecto/etl-movilidad-local
ExecStart=/usr/bin/python3 scheduler_advanced.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Luego:
```bash
sudo systemctl enable etl-movilidad
sudo systemctl start etl-movilidad
sudo systemctl status etl-movilidad
```

**cron** (cada 20 minutos):
```bash
crontab -e
```

Añadir:
```
*/20 * * * * cd /ruta/al/proyecto/etl-movilidad-local && python src/main.py >> logs/cron.log 2>&1
```

## 📈 Monitoreo

Para ver el progreso en tiempo real:

```bash
# Ver logs en vivo
tail -f logs/scheduler.log

# En Windows con PowerShell
Get-Content logs/scheduler.log -Wait
```

## 🐛 Troubleshooting

### El scheduler no inicia

**Problema**: Error al importar módulos
```
ModuleNotFoundError: No module named 'schedule'
```

**Solución**: Instala las dependencias
```bash
pip install -r requirements.txt
```

### El scheduler se detiene solo

**Problema**: Error en el pipeline
```
Pipeline execution failed: ...
```

**Solución**: Revisa los logs en `logs/scheduler.log` y `logs/etl_pipeline.log`

### No se guardan noticias nuevas

**Problema**: Todas las noticias son duplicadas

**Explicación**: Es normal si no ha pasado suficiente tiempo. Las páginas web no actualizan noticias cada 20 minutos.

**Recomendación**:
- Mantén el scheduler corriendo 24/7
- Las noticias se actualizarán cuando los sitios web publiquen contenido nuevo
- Puedes cambiar el intervalo a 1 hora si prefieres

## 📊 Estadísticas

Para ver estadísticas de ejecución:

```bash
python scripts/query_supabase.py
# Opción 7: View recent executions
```

Verás:
```
Recent Executions (10 items)

[1] Execution at 2025-10-29T14:00:00
    Extracted:      31
    Deduplicated:   28
    Scored:         3
    Kept:           2
    Duration:       45.23s

[2] Execution at 2025-10-29T13:40:00
    ...
```

## ✅ Ventajas del Scheduler

1. **Automatización**: No necesitas ejecutar manualmente
2. **Actualización continua**: Base de datos siempre actualizada
3. **Eficiencia**: Solo procesa noticias nuevas (deduplicación)
4. **Resiliencia**: Continúa aunque falle una ejecución
5. **Trazabilidad**: Logs detallados de cada ejecución

## 🎯 Uso Recomendado

**Para Desarrollo**:
```bash
# Ejecutar manualmente cuando necesites
python src/main.py
```

**Para Producción**:
```bash
# Scheduler 24/7
python scheduler_advanced.py
```

O mejor aún, configúralo como servicio del sistema para que se ejecute automáticamente al iniciar el servidor.

## 📝 Notas

- El scheduler guarda todos los logs en `logs/scheduler.log`
- El pipeline guarda sus logs en `logs/etl_pipeline.log`
- Puedes tener ambos corriendo sin conflictos
- El scheduler es independiente - si falla, se recupera en la siguiente ejecución
