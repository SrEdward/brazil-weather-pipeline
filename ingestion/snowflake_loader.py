import boto3
import json
import logging
import os
import snowflake.connector

from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_snowflake_connection():
    """Cria e retorna uma conexão com o Snowflake."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def read_from_s3(bucket: str, key: str) -> list[dict]:
    """Lê um arquivo JSON do S3 e retorna como lista de dicionários."""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    response = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(response["Body"].read().decode("utf-8"))
    logger.info(f"Lidos {len(data)} registros de s3://{bucket}/{key}")
    return data


def load_to_snowflake(records: list[dict], conn) -> None:
    """Carrega registros na tabela RAW_WEATHER do Snowflake."""
    cursor = conn.cursor()

    insert_sql = """
        INSERT INTO RAW_WEATHER (
            STATION_ID, STATION_NAME, STATE,
            LATITUDE, LONGITUDE, DATE,
            TEMP_MAX, TEMP_MIN, TEMP_MEAN,
            PRECIPITATION_MM, WINDSPEED_MAX,
            HUMIDITY_MAX, HUMIDITY_MIN, EXTRACTED_AT
        ) VALUES (
            %(station_id)s, %(station_name)s, %(state)s,
            %(latitude)s, %(longitude)s, %(date)s,
            %(temp_max)s, %(temp_min)s, %(temp_mean)s,
            %(precipitation_mm)s, %(windspeed_max)s,
            %(humidity_max)s, %(humidity_min)s, %(extracted_at)s
        )
    """

    cursor.executemany(insert_sql, records)
    conn.commit()
    logger.info(f"{len(records)} registros inseridos no Snowflake.")
    cursor.close()


def s3_to_snowflake(bucket: str, target_date: str) -> None:
    """Orquestra a leitura do S3 e carga no Snowflake."""
    s3_key = f"raw/weather/{target_date}/data.json"

    logger.info(f"Iniciando carga S3 → Snowflake para data: {target_date}")

    records = read_from_s3(bucket, s3_key)

    conn = get_snowflake_connection()
    try:
        load_to_snowflake(records, conn)
    finally:
        conn.close()

    logger.info("Carga concluída com sucesso!")


if __name__ == "__main__":
    s3_to_snowflake(
        bucket=os.getenv("S3_BUCKET"),
        target_date="2025-01-15"
    )
