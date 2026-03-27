import requests
import boto3
import json
import logging
import os

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIONS = [
    {"id": "porto_alegre",    "name": "Porto Alegre",    "state": "RS", "lat": -30.0346, "lon": -51.2177},
    {"id": "sao_paulo",       "name": "São Paulo",       "state": "SP", "lat": -23.5505, "lon": -46.6333},
    {"id": "rio_de_janeiro",  "name": "Rio de Janeiro",  "state": "RJ", "lat": -22.9068, "lon": -43.1729},
    {"id": "salvador",        "name": "Salvador",        "state": "BA", "lat": -12.9714, "lon": -38.5014},
    {"id": "fortaleza",       "name": "Fortaleza",       "state": "CE", "lat": -3.7172,  "lon": -38.5433},
    {"id": "manaus",          "name": "Manaus",          "state": "AM", "lat": -3.1190,  "lon": -60.0217},
    {"id": "belem",           "name": "Belém",           "state": "PA", "lat": -1.4558,  "lon": -48.5044},
    {"id": "brasilia",        "name": "Brasília",        "state": "GO", "lat": -15.7801, "lon": -47.9292},
    {"id": "cuiaba",          "name": "Cuiabá",          "state": "MT", "lat": -15.6014, "lon": -56.0979},
    {"id": "recife",          "name": "Recife",          "state": "PE", "lat": -8.0476,  "lon": -34.8770},
]


def get_weather_data(station: dict, start_date: str, end_date: str) -> list[dict]:
    """Busca dados históricos diários da Open-Meteo para uma cidade."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":        station["lat"],
        "longitude":       station["lon"],
        "start_date":      start_date,
        "end_date":        end_date,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "windspeed_10m_max",
            "relative_humidity_2m_max",
            "relative_humidity_2m_min",
        ],
        "timezone": "America/Sao_Paulo",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    raw = response.json()

    # Transforma o formato wide em registros por dia
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    records = []

    for i, date in enumerate(dates):
        records.append({
            "station_id":       station["id"],
            "station_name":     station["name"],
            "state":            station["state"],
            "latitude":         station["lat"],
            "longitude":        station["lon"],
            "date":             date,
            "temp_max":         daily.get("temperature_2m_max", [None])[i],
            "temp_min":         daily.get("temperature_2m_min", [None])[i],
            "temp_mean":        daily.get("temperature_2m_mean", [None])[i],
            "precipitation_mm": daily.get("precipitation_sum", [None])[i],
            "windspeed_max":    daily.get("windspeed_10m_max", [None])[i],
            "humidity_max":     daily.get("relative_humidity_2m_max", [None])[i],
            "humidity_min":     daily.get("relative_humidity_2m_min", [None])[i],
            "extracted_at":     datetime.now(timezone.utc).isoformat(),
        })

    return records


def upload_to_s3(data: list[dict], bucket: str, key: str) -> None:
    """Faz upload de dados como JSON para o S3."""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False, indent=2),
        ContentType="application/json",
    )
    logger.info(f"Upload concluído: s3://{bucket}/{key}")


def extract_and_load(bucket: str, target_date: str = None) -> None:
    """
    Extrai dados da Open-Meteo e carrega no S3.
    target_date: formato YYYY-MM-DD (default: ontem)
    """
    if not target_date:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    logger.info(f"Iniciando extração para data: {target_date}")

    all_records = []
    for station in STATIONS:
        logger.info(f"Extraindo dados: {station['name']} ({station['state']})")
        records = get_weather_data(station, target_date, target_date)
        all_records.extend(records)
        logger.info(f"  → {len(records)} registro(s) coletado(s)")

    if not all_records:
        logger.warning("Nenhum dado coletado.")
        return

    s3_key = f"raw/weather/{target_date}/data.json"
    upload_to_s3(all_records, bucket, s3_key)
    logger.info(f"Total de registros carregados no S3: {len(all_records)}")


if __name__ == "__main__":
    extract_and_load(
        bucket=os.getenv("S3_BUCKET"),
        target_date="2025-01-15"
    )
