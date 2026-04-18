import json
import logging
import os
import pyarrow as pa

from datetime import datetime, timezone, date
from kafka import KafkaConsumer
from dotenv import load_dotenv
from pyiceberg.catalog.glue import GlueCatalog


load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC = "weather_events"


def get_catalog():
    return GlueCatalog(
            "glue",
            **{
                "warehouse": "s3://{}/iceberg".format(os.getenv("S3_BUCKET")),
                "glue.region": os.getenv("AWS_REGION", "us-east-1"),
                "client.region": os.getenv("AWS_REGION", "us-east-1"),
                "client.access-key-id": os.getenv("AWS_ACCESS_KEY_ID"),
                "client.secret-access-key": os.getenv("AWS_SECRET_ACCESS_KEY")
            }
    )


def write_events_to_iceberg(events: list[dict]) -> None:
    """Escreve batch de eventos no Iceberg."""

    catalog = get_catalog()
    table = catalog.load_table("brazil_weather.weather_data")

    arrow_table = pa.table({
        "station_id": pa.array([e["station_id"] for e in events], type=pa.string()),
        "station_name": pa.array([e["station_name"] for e in events], type=pa.string()),
        "state": pa.array([e["state"] for e in events], type=pa.string()),
        "latitude": pa.array([e["latitude"] for e in events], type=pa.float32()),
        "longitude": pa.array([e["longitude"] for e in events], type=pa.float32()),
        "weather_date": pa.array([date.today() for _ in events], type=pa.date32()),
        "temp_max_c": pa.array([e["temperature_c"] for e in events], type=pa.float32()),
        "temp_min_c": pa.array([e["temperature_c"] for e in events], type=pa.float32()),
        "temp_mean_c": pa.array([e["temperature_c"] for e in events], type=pa.float32()),
        "precipitation_mm": pa.array([e["precipitation_mm"] for e in events], type=pa.float32()),
        "windspeed_max_kmh": pa.array([e["windspeed_kmh"] for e in events], type=pa.float32()),
        "humidity_max_pct": pa.array([e["humidity_pct"] for e in events], type=pa.float32()),
        "humidity_min_pct": pa.array([e["humidity_pct"] for e in events], type=pa.float32()),
        "extracted_at": pa.array([datetime.now(timezone.utc) for _ in events], type=pa.timestamp("us"))
    })

    table.append(arrow_table)

    logger.info("{} eventos escritos no Iceberg.".format(len(events)))


def run_consumer(batch_size: int = 10) -> None:
    """
    Consome eventos do Kafka e escreve no Iceberg em micro-batches.
    batch_size: número de mensagens por batch
    """

    consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=["localhost:9092"],
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="earliest",
            group_id="weather-iceberg-consumer"
    )

    logger.info("Consumer iniciado. Consumindo tópico '{}'.".format(TOPIC))

    batch = list()

    try:
        for message in consumer:
            event = message.value
            batch.append(event)

            logger.info("Recebido: {} - {}°C".format(event["station_name"], event["temperature_c"]))

            if len(batch) >= batch_size:
                write_events_to_iceberg(batch)
                batch = list()

    except KeyboardInterrupt:
        if batch:
            write_events_to_iceberg(batch)

        logger.info("Consumer encerrado.")

    finally:
        consumer.close()


if __name__ == "__main__":
    run_consumer(batch_size=10)
