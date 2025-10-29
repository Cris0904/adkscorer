"""
Reset database - Delete and recreate from scratch
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    print("="*70)
    print("RESETEANDO BASE DE DATOS")
    print("="*70)

    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'etl_movilidad.db')

    # Delete if exists
    if os.path.exists(db_path):
        print(f"\n🗑️  Eliminando base de datos anterior...")
        os.remove(db_path)
        print("✓ Base de datos anterior eliminada")
    else:
        print(f"\n📋 No hay base de datos anterior")

    # Create new
    print(f"\n📂 Creando nueva base de datos...")
    from db import NewsDatabase
    db = NewsDatabase(db_path=db_path)
    print("✓ Nueva base de datos creada")

    # Verify
    print(f"\n🔍 Verificando...")
    stats = db.get_stats()
    print(f"✓ Total de noticias: {stats['total_news']}")

    print("\n" + "="*70)
    print("✅ BASE DE DATOS RESETEADA CORRECTAMENTE")
    print("="*70)
    print(f"\n📁 Ubicación: {db_path}")
    print("📊 Estado: Vacía, lista para datos nuevos")
    print("\n")

if __name__ == "__main__":
    main()
