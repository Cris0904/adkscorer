#!/bin/bash
echo "=========================================="
echo "VERIFICACIÓN DE ESTRUCTURA DEL PROYECTO"
echo "=========================================="
echo ""

echo "Archivos Python esenciales:"
echo "----------------------------"
ls -lh src/main.py src/adk_scorer_v3.py src/extractors_apify_simple.py src/db.py 2>/dev/null || echo "✗ Faltan archivos"

echo ""
echo "Módulos de soporte:"
echo "-------------------"
ls -lh src/prompts/*.py src/schemas/*.py 2>/dev/null | grep -v "^total"

echo ""
echo "Configuración:"
echo "--------------"
ls -lh requirements.txt .env.example 2>/dev/null

echo ""
echo "Estructura completa:"
echo "--------------------"
find . -type f ! -path './.git/*' ! -name '*.pyc' ! -path '*/__pycache__/*' | wc -l | xargs echo "Total de archivos:"

echo ""
echo "Líneas de código:"
echo "-----------------"
find src -name "*.py" -exec wc -l {} + | tail -1

echo ""
echo "=========================================="
echo "Para ejecutar el proyecto:"
echo "1. pip install -r requirements.txt"
echo "2. cp .env.example .env"
echo "3. Configurar .env con tus credenciales"
echo "4. cd src && python main.py"
echo "=========================================="
