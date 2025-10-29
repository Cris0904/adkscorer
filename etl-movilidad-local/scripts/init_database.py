"""
Initialize database and create schema
This script creates the SQLite database with all necessary tables
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db import NewsDatabase

def main():
    print("="*70)
    print("INICIALIZANDO BASE DE DATOS")
    print("="*70)

    # Create database
    print("\n📂 Paso 1: Creando base de datos SQLite...")
    db = NewsDatabase()
    print("✓ Base de datos creada: data/etl_movilidad.db")

    # Show tables
    print("\n📋 Paso 2: Verificando estructura...")

    import sqlite3
    conn = sqlite3.connect('data/etl_movilidad.db')
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"✓ Tablas creadas: {len(tables)}")
    for table in tables:
        print(f"  • {table[0]}")

        # Get column info
        cursor.execute(f"PRAGMA table_info({table[0]});")
        columns = cursor.fetchall()
        print(f"    Columnas: {len(columns)}")
        for col in columns[:5]:  # Show first 5 columns
            print(f"      - {col[1]} ({col[2]})")
        if len(columns) > 5:
            print(f"      ... y {len(columns) - 5} columnas más")

    conn.close()

    print("\n" + "="*70)
    print("✅ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("="*70)
    print("\n📁 Ubicación: data/etl_movilidad.db")
    print("📊 Estado: Vacía, lista para recibir noticias")
    print("\n💡 Próximos pasos:")
    print("  1. Ejecutar: python demo_full_pipeline.py")
    print("  2. O ejecutar: python ../src/main.py")
    print("\n")

if __name__ == "__main__":
    main()
