"""
Generate test news for demo purposes
Creates realistic Medellín mobility news samples
"""
from datetime import datetime, timedelta
import random

def generate_test_news():
    """Generate sample news items for testing"""

    # Sample realistic news about Medellín mobility
    news_samples = [
        {
            'source': 'Metro de Medellín',
            'url': 'https://www.metrodemedellin.gov.co/noticias/suspension-temporal-linea-a',
            'title': 'Suspensión temporal de servicio en Línea A del Metro por mantenimiento',
            'body': 'El Metro de Medellín informa que habrá una suspensión temporal del servicio en la Línea A entre las estaciones Niquía y Bello el próximo sábado de 6:00 AM a 12:00 PM por trabajos de mantenimiento preventivo en la infraestructura. Se habilitarán buses de apoyo para transportar a los usuarios.',
            'published_at': (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            'source': 'Alcaldía de Medellín',
            'url': 'https://www.medellin.gov.co/movilidad/nuevas-ciclorrutas-laureles',
            'title': 'Inauguran nuevas ciclorrutas en el sector de Laureles',
            'body': 'La Alcaldía de Medellín inauguró este lunes 5 kilómetros de nuevas ciclorrutas en el barrio Laureles, conectando el Estadio Atanasio Girardot con la Avenida 80. Este proyecto busca promover el uso de la bicicleta como medio de transporte sostenible.',
            'published_at': (datetime.now() - timedelta(hours=5)).isoformat()
        },
        {
            'source': 'AMVA',
            'url': 'https://www.metropol.gov.co/movilidad/pico-y-placa-especial',
            'title': 'Pico y placa especial por festividades del fin de semana',
            'body': 'El Área Metropolitana del Valle de Aburrá anunció un pico y placa especial para el próximo fin de semana debido a las festividades. La restricción aplicará de 6:00 AM a 9:00 PM tanto el sábado como el domingo para vehículos particulares con placas terminadas en dígitos impares.',
            'published_at': (datetime.now() - timedelta(hours=1)).isoformat()
        },
        {
            'source': 'Metro de Medellín',
            'url': 'https://www.metrodemedellin.gov.co/noticias/accidente-estacion-poblado',
            'title': 'Accidente en cercanías de la estación Poblado genera congestión',
            'body': 'Un accidente de tránsito en las inmediaciones de la estación Poblado del Metro está generando congestión vehicular en la zona. Las autoridades de tránsito se encuentran en el lugar atendiendo la emergencia. Se recomienda a los ciudadanos usar vías alternas.',
            'published_at': (datetime.now() - timedelta(minutes=30)).isoformat()
        },
        {
            'source': 'Alcaldía de Medellín',
            'url': 'https://www.medellin.gov.co/movilidad/obras-avenida-oriental',
            'title': 'Inicio de obras en la Avenida Oriental afectará movilidad',
            'body': 'A partir del próximo lunes iniciarán obras de mejoramiento en la Avenida Oriental entre las calles 10 y 30. Los trabajos se extenderán por tres meses y generarán cierres parciales de la vía. Se recomienda planificar rutas alternas.',
            'published_at': (datetime.now() - timedelta(hours=3)).isoformat()
        },
        {
            'source': 'AMVA',
            'url': 'https://www.metropol.gov.co/movilidad/congreso-transporte',
            'title': 'AMVA organiza congreso sobre movilidad sostenible',
            'body': 'El Área Metropolitana realizará en marzo el Congreso Internacional de Movilidad Sostenible con expertos de América Latina. El evento buscará compartir experiencias sobre transporte público y movilidad urbana.',
            'published_at': (datetime.now() - timedelta(hours=24)).isoformat()
        },
        {
            'source': 'Metro de Medellín',
            'url': 'https://www.metrodemedellin.gov.co/noticias/extension-horario-navidad',
            'title': 'Metro extenderá horarios durante temporada decembrina',
            'body': 'El sistema Metro de Medellín extenderá sus horarios de operación durante diciembre para facilitar el desplazamiento de usuarios en la temporada de compras navideñas. El servicio operará hasta la medianoche los viernes y sábados.',
            'published_at': (datetime.now() - timedelta(hours=8)).isoformat()
        },
        {
            'source': 'Alcaldía de Medellín',
            'url': 'https://www.medellin.gov.co/movilidad/deslizamiento-via-las-palmas',
            'title': 'Deslizamiento en vía Las Palmas mantiene cerrada la carretera',
            'body': 'Un deslizamiento de tierra en el kilómetro 8 de la vía Las Palmas mantiene cerrada la carretera desde la madrugada. Maquinaria pesada trabaja en la remoción de escombros. No se reportan personas heridas pero sí daños materiales en dos vehículos.',
            'published_at': (datetime.now() - timedelta(minutes=45)).isoformat()
        },
        {
            'source': 'AMVA',
            'url': 'https://www.metropol.gov.co/noticias/estudio-calidad-aire',
            'title': 'Nuevo estudio sobre calidad del aire y transporte público',
            'body': 'El AMVA presentó un estudio que muestra la mejora en la calidad del aire gracias al uso del transporte público. Los resultados indican una reducción del 15% en emisiones de CO2 en los últimos dos años.',
            'published_at': (datetime.now() - timedelta(hours=12)).isoformat()
        },
        {
            'source': 'Metro de Medellín',
            'url': 'https://www.metrodemedellin.gov.co/noticias/falla-tecnica-cable',
            'title': 'Falla técnica en Cable Arví suspende servicio temporalmente',
            'body': 'Una falla técnica en el sistema de Cable Arví ha obligado a suspender el servicio desde las 10:00 AM. Los técnicos del Metro trabajan en la solución del problema. Se estima reanudar operaciones en las próximas horas.',
            'published_at': (datetime.now() - timedelta(minutes=90)).isoformat()
        }
    ]

    return news_samples


if __name__ == "__main__":
    news = generate_test_news()
    print(f"\nGenerated {len(news)} test news items:")
    for i, item in enumerate(news, 1):
        print(f"\n{i}. [{item['source']}] {item['title']}")
