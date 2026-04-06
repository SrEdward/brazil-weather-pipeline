import boto3
import json
import logging
import os
import duckdb
import pyarrow as pa

from datetime import datetime
from dotenv import load_dotenv
from pyiceberg.catalog_glue import GlueCatalog
from pyiceberg.schema import Schema
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transform import MonthTransform

from pyiceberg.types import (
        NestedField, StringType, FloatType, DateType, TimestampType
)


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEMA = Schema(
        NestedField(1, "station_id", StringType(), required=True),
        NestedField(2, "station_name", StringType(), required=True),
        NestedField(3, "state", StringType(), required=True),
        NestedField(4, "latitude", FloatType(), required=False),
        NestedField(5, "longitude", FloatType(), required=False),
        NestedField(6, "weather_date", DateType(), required=True),
        NestedField(7, "temp_max_c", FloatType(), required=False),
        NestedField(8, "temp_min_c", FloatType(), required=False),
        NestedField(9, "temp_mean_c", FloatType(), required=False),
        NestedField(10, "precipitation_mm", FloatType(), required=False),
        NestedField(11, "windspeed_max_kmh", FloatType(), required=False),
        NestedField(12, "humidity_max_pct", FloatType(), required=False),
        NestedField(13, "humidity_min_pct", FloatType(), required=False),
        NestedField(14, "extracted_at", TimestampType(), required=False)
)

PARTITION_SPEC = PartitionSpec(
        PartitionField(
            source_id=6,
            field_id=1000,
            transform=MonthTransform(),
            name="weather_date_month"
        )
)


def get_catalog():
    """Retorna o catálogo da Glue."""

    return GlueCatalog(
            "glue",
            **{
                "warehouse": "s3://{}/iceberg".format(os.getenv("S3_BUCKET")),
                "region_name": os.getenv("AWS_REGION", "us-east-1"),
                "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
                "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY")
            }
        )


def get_or_create_table(catalog):
    """Cria a tabela no Iceberg caso ela não exista."""

    namespace = "brazil_weather"
    table_name = "weather_data"
    full_name = "{}.{}".format(namespace, table_name)

    if not catalog.namespace_exists(namespace):
        catalog.create_namespace(namespace)
        logger.info("Namespace '{}' criado.".format(namespace))

    if not catalog.table_exists(full_name):
        table = catalog.create_table(
                full_name,
                schema=SCHEMA,
                partition_spec=PARTITION_SPEC,
                properties={
                    "write.format.default": "parquet",
                    "write.parquet.compression-codec": "snappy"
                }
        )

        logger.info("Tabela '{}' criada.".format(full_name))
    else:
        table = catalog.load_table(full_name)
        logger.info("Tabela '{}' carregada.".format(full_name))

    return table
