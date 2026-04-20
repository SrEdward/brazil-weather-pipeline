# 🌦️ Brazil Weather Pipeline

A production-grade data platform that ingests daily weather data from 10 Brazilian cities, processes it through a full modern data stack — batch ELT, lakehouse storage, and real-time streaming — orchestrated end-to-end with Apache Airflow.

Built as a portfolio project to demonstrate modern data engineering practices.

---

## 🏗️ Architecture

```
Open-Meteo API
      │
      ▼
Python Extractor
      │
      ├──► AWS S3 (raw/weather/YYYY-MM-DD/data.json)
      │         │
      │         ▼
      │    Snowflake STAGING.RAW_WEATHER
      │         │
      │         ▼
      │    dbt Models
      │    ├── STAGING.stg_weather (view)
      │    └── MARTS.*
      │        ├── mart_daily_temperature (table)
      │        ├── mart_state_summary (table)
      │        └── mart_rain_alerts (table)
      │
      └──► Apache Iceberg (S3 Parquet)
                s3://brazil-weather-pipeline-raw/iceberg/
                Partitioned by month │ Catalog: AWS Glue
                Queried via DuckDB   │

Kafka Streaming (parallel to batch):
Producer → Topic: weather-events → Consumer → Iceberg

Orchestration (Airflow DAG: weather_pipeline):
extract_to_s3 → load_to_snowflake → dbt_transform → dbt_test → write_to_iceberg
Scheduled: daily at 06:00 UTC

Infrastructure: fully provisioned via Terraform
```

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| Extraction | Python, Open-Meteo API |
| Raw Storage | AWS S3 |
| Data Warehouse | Snowflake |
| Transformation | dbt (staging + marts) |
| Orchestration | Apache Airflow 2.9 |
| Lakehouse Format | Apache Iceberg (PyIceberg 0.7.1) |
| Glue Catalog | AWS Glue |
| Query Engine | DuckDB |
| Streaming | Apache Kafka (kafka-python 2.3.1) |
| IaC | Terraform 1.14.8 |
| Containerization | Docker + Docker Compose |
| Cloud | AWS (S3, IAM, Glue) |
| Version Control | Git + GitHub (PRs, semantic commits) |

---

## 📊 Dataset

- **Source:** [Open-Meteo Historical Weather API](https://open-meteo.com/)
- **Coverage:** 10 Brazilian cities across all major regions
- **Period:** 2024 full year (366 days)
- **Volume:** ~3,740 records (batch + streaming)
- **Metrics:** Max/Min/Mean temperature, precipitation, wind speed, humidity
- **Iceberg partitioning:** by month (`weather_date_month`)

### Cities covered

| City | State | Region |
| --- | --- | --- |
| Porto Alegre | RS | South |
| São Paulo | SP | Southeast |
| Rio de Janeiro | RJ | Southeast |
| Salvador | BA | Northeast |
| Fortaleza | CE | Northeast |
| Recife | PE | Northeast |
| Manaus | AM | North |
| Belém | PA | North |
| Brasília | DF | Center-West |
| Cuiabá | MT | Center-West |

---

## 🔄 Pipeline DAG

The Airflow DAG runs daily at 06:00 UTC:

```
extract_to_s3 → load_to_snowflake → dbt_transform → dbt_test → write_to_iceberg
```

- **extract_to_s3** — Fetches previous day's weather data and uploads to S3 as partitioned JSON
- **load_to_snowflake** — Reads from S3 and inserts into Snowflake staging table
- **dbt_transform** — Runs all dbt models (1 staging view + 3 mart tables)
- **dbt_test** — Runs 11 data quality tests across all models
- **write_to_iceberg** — Writes processed data to Iceberg tables on S3, catalogued via AWS Glue

---

## 🌊 Kafka Streaming Layer

A parallel real-time streaming pipeline runs independently of the batch layer:

- **Producer** (`kafka/producer.py`) — fetches current weather data and publishes to the `weather-events` topic
- **Consumer** (`kafka/consumer.py`) — consumes events and writes them directly to Iceberg on S3

Both services run as Docker containers alongside Airflow via Docker Compose.

---

## 📁 Project Structure

```
brazil-weather-pipeline/
├── Dockerfile                         # Custom Airflow image
├── docker-compose.yml                 # Airflow + Postgres + Kafka + Zookeeper
├── requirements.txt
├── dags/
│   └── weather_pipeline.py            # Main Airflow DAG
├── ingestion/
│   ├── inmet_extractor.py             # Open-Meteo extractor + S3 upload
│   └── snowflake_loader.py            # S3 → Snowflake loader
├── iceberg/
│   ├── iceberg_writer.py              # PyIceberg writer → S3 Parquet
│   └── duckdb_query.py                # Analytical queries via DuckDB
├── kafka/
│   ├── producer.py                    # Kafka producer (current weather)
│   └── consumer.py                    # Kafka consumer → Iceberg
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_weather.sql
│   │   │   └── sources.yml
│   │   └── marts/
│   │       ├── mart_daily_temperature.sql
│   │       ├── mart_state_summary.sql
│   │       ├── mart_rain_alerts.sql
│   │       └── schema.yml
│   └── macros/
│       └── generate_schema_name.sql
└── terraform/
    ├── main.tf                        # S3 bucket + IAM + Glue policies
    ├── variables.tf
    └── outputs.tf
```

---

## 🚀 How to Run Locally

### Prerequisites

- Docker + Docker Compose
- AWS account with S3 bucket and Glue catalog
- Snowflake account (free trial works)

### Setup

**1. Clone the repository**

```bash
git clone https://github.com/SrEdward/brazil-weather-pipeline.git
cd brazil-weather-pipeline
```

**2. Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your credentials
```

**3. Start all services**

```bash
sudo modprobe overlay   # required on some Linux setups
docker compose up -d
```

**4. Access Airflow UI**

```
URL:      http://localhost:8080
User:     admin
Password: admin
```

**5. Trigger the pipeline**

Enable and trigger the `weather_pipeline` DAG in the Airflow UI.

---

## 🧪 Data Quality

dbt tests run automatically after every transformation:

| Test | Models |
| --- | --- |
| `not_null` | All key columns across all marts |
| `accepted_values` | `temp_category`, `rain_category` |

**11 tests passing** on every pipeline run.

---

## 📈 Sample Queries

```sql
-- Average temperature by state in 2024
SELECT state, ROUND(AVG(temp_mean_c), 2) AS avg_temp
FROM MARTS.MART_DAILY_TEMPERATURE
GROUP BY state
ORDER BY avg_temp DESC;
```

```python
# Query Iceberg directly via DuckDB (no Snowflake needed)
import duckdb
con = duckdb.connect()
con.execute("INSTALL iceberg; LOAD iceberg;")
df = con.execute("""
    SELECT weather_date, city, temp_max_c, temp_min_c
    FROM iceberg_scan('s3://brazil-weather-pipeline-raw/iceberg/brazil_weather.db/weather_data')
    WHERE weather_date_month = '2024-07'
    ORDER BY temp_max_c DESC
    LIMIT 10
""").df()
```

---

## 🗺️ Roadmap

- [x] ELT Pipeline (Extract → S3 → Snowflake)
- [x] dbt Transformations (staging + 3 marts)
- [x] Airflow Orchestration
- [x] Docker containerization
- [x] Terraform infrastructure provisioning
- [x] Apache Iceberg lakehouse layer
- [x] Kafka real-time streaming layer
- [ ] Snowflake External Iceberg Tables (read Iceberg directly from Snowflake)

---

## 👨‍💻 Author

**Eduardo Nunes de Almeida**
Data Engineer | Brazil
