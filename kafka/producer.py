import json
import logging
import os
import time
import requests

from datetime import datetime, timezone
from kafka import KafkaProducer
from dotenv import load_dotenv


load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC = "weather_events"

STATIONS = [
        {"id": "porto_alegre", "name": "Porto Alegre", "state": "RS", "lat": -30.0346, "lon": -51.2177},
        {"id": "sao_paulo", "name": "São Paulo", "state": "SP", "lat": -23.5505, "lon": -46.6333},
        {"id": "rio_de_janeiro", "name": "Rio de Janeiro", "state": "RJ", "lat": -22.9068, "lon": -43.1729},
        {"id": "salvador", "name": "Salvador", "state": "BA", "lat": -12.9714, "lon": -38.5014},
        {"id": "fortaleza", "name": "Fortaleza", "state": "CE", "lat": -3.7172, "lon": -38.5433},
        {"id": "manaus", "name": "Manaus", "state": "AM", "lat": -3.1190, "lon": -60.0217},
        {"id": "belem", "name": "Belém", "state": "PA", "lat": -1.4558, "lon": -48.5044},
        {"id": "brasilia", "name": "Brasília", "state": "GO", "lat": -15.7801, "lon": -47.9292},
        {"id": "cuiaba", "name": "Cuiabá", "state": "MT", "lat": -15.6014, "lon": -56.0979},
        {"id": "recife", "name": "Recife", "state": "PE", "lat": -8.0476, "lon": -34.8770}
]


def fetch_current_weather(station: dict) -> dict:
    """Busca dados atuais da Open-Meteo para uma estação."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
            "latitude": station["lat"],
            "longitude": station["lon"],
            "current": [
                "temperature_2m",
                "precipitation",
                "windspeed_10m",
                "relativehumidity_2m"
            ],
            "timezone": "America/Sao_Paulo"
    }

    response = requests.get(url, params=params, timeout=30)

    response.raise_for_status()

    current = response.json().get("current", {})

    return {
            "station_id": station["id"],
            "station_name": station["name"],
            "state": station["state"],
            "latitude": station["lat"],
            "longitude": station["lon"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature_c": current.get("temperature_2m"),
            "precipitation_mm": current.get("precipitation"),
            "windspeed_kmh": current.get("windspeed_10m"),
            "humidity_pct": current.get("relativehumidity_2m"),
            "humidity_pct": current.get("relativehumidity_2m")
    }
    

def create_producer() -> KafkaProducer:
    """Cria e retorna um KafkaProducer."""

    return KafkaProducer(
            bootstrap_servers=["localhost:9092"],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8")
    )


def run_producer(interval_seconds: int = 60) -> None:
    """
    Publica dados meteorológicos no Kafka continuamente.
    interval_seconds: intervalo entre publicações (default: 60s)
    """

    producer = create_producer()
    logger.info("Producer iniciado. Publicando no tópico '{}' a cada {} segundos.".format(TOPIC, interval_seconds))

    try:
        while True:
            for station in STATIONS:
                try:
                    event = fetch_current_weather(station)

                    producer.send(
                            topic=TOPIC,
                            key=station["id"],
                            value=event
                    )

                    logger.info("Publicado: {} ({})".format(station.get("name"), station.get("state")))

                except Exception as e:
                    logger.warning("Erro na estação {}: {}".format(station.get("name"), e))

            producer.flush()
            logger.info("Batch publicado. Aguardando {} segundos...".format(interval_seconds))
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        logger.info("Producer encerrado.")
    finally:
        producer.close()


if __name__ == "__main__":
    run_producer(interval_seconds=60)
