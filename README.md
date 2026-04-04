# 🌦️ Brazil Weather Pipeline

A production-grade ELT pipeline that extracts daily weather data from 10 Brazilian cities, loads it into AWS S3, transforms it with dbt, and orchestrates everything with Apache Airflow.

Built as a portfolio project to demonstrate modern data engineering practices.

---

## 🏗️ Architecture

```
Open-Meteo API → Python Extractor → AWS S3 (Raw)
                                         ↓
                                   Snowflake Staging
                                         ↓
                                    dbt Models
                            ┌────────────┼────────────┐
                            ↓            ↓            ↓
        mart_daily_temperature  mart_state_summary  mart_rain_alerts
                            
                    Orchestrated by Apache Airflow (daily @ 06:00 UTC)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Extraction | Python, Open-Meteo API |
| Storage | AWS S3 |
| Data Warehouse | Snowflake |
| Transformation | dbt (staging + marts) |
| Orchestration | Apache Airflow 2.9 |
| Containerization | Docker + Docker Compose |
| Version Control | Git + GitHub (PRs, semantic commits) |

---

## 📊 Dataset

- **Source:** [Open-Meteo Historical Weather API](https://open-meteo.com/)
- **Coverage:** 10 Brazilian cities across all major regions
- **Period:** 2024 full year (366 days)
- **Volume:** 3,660+ records
- **Metrics:** Max/Min/Mean temperature, precipitation, wind speed, humidity

### Cities covered

| City | State | Region |
|---|---|---|
| Porto Alegre | RS | South |
| São Paulo | SP | Southeast |
| Rio de Janeiro | RJ | Southeast |
| Salvador | BA | Northeast |
| Fortaleza | CE | Northeast |
| Recife | PE | Northeast |
| Manaus | AM | North |
| Belém | PA | North |
| Brasília | GO | Center-West |
| Cuiabá | MT | Center-West |

---

## 🔄 Pipeline DAG

The Airflow DAG runs daily at 06:00 UTC with the following tasks:

```
extract_to_s3 → load_to_snowflake → dbt_transform → dbt_test
```

- **extract_to_s3** — Fetches previous day's weather data and uploads to S3 as partitioned JSON
- **load_to_snowflake** — Reads from S3 and inserts into Snowflake staging table
- **dbt_transform** — Runs all dbt models (1 staging view + 3 mart tables)
- **dbt_test** — Runs 11 data quality tests across all models

---

## 📁 Project Structure

```
brazil-weather-pipeline/
├── Dockerfile                    # Custom Airflow image with dependencies
├── docker-compose.yml            # Airflow + Postgres services
├── requirements.txt              # Python dependencies
├── dags/
│   └── weather_pipeline.py       # Main Airflow DAG
├── ingestion/
│   ├── inmet_extractor.py        # Open-Meteo extractor + S3 upload
│   └── snowflake_loader.py       # S3 → Snowflake loader
└── dbt_project/
    ├── models/
    │   ├── staging/
    │   │   ├── stg_weather.sql   # Staging view with cleaned columns
    │   │   └── sources.yml       # Source definitions
    │   └── marts/
    │       ├── mart_daily_temperature.sql
    │       ├── mart_state_summary.sql
    │       ├── mart_rain_alerts.sql
    │       └── schema.yml        # Tests + documentation
    └── macros/
        └── generate_schema_name.sql
```

---

## 🚀 How to Run Locally

### Prerequisites

- Docker + Docker Compose
- AWS account with S3 bucket
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

**3. Start Airflow**
```bash
echo "AIRFLOW_UID=$(id -u)" >> .env
docker compose up -d
```

**4. Access Airflow UI**
```
URL: http://localhost:8080
User: admin
Password: admin
```

**5. Trigger the pipeline**

Enable and trigger the `weather_pipeline` DAG in the Airflow UI.

---

## 🧪 Data Quality

dbt tests run automatically after every transformation:

| Test | Models |
|---|---|
| `not_null` | All key columns across all marts |
| `accepted_values` | `temp_category`, `rain_category` |

**11 tests passing** on every pipeline run.

---

## 📈 Sample Insights

```sql
-- Average temperature by state in 2024
SELECT state, ROUND(AVG(temp_mean_c), 2) AS avg_temp
FROM MARTS.MART_DAILY_TEMPERATURE
GROUP BY state
ORDER BY avg_temp DESC;
```

---

## 🗺️ Roadmap

- [x] ELT Pipeline (Extract → S3 → Snowflake)
- [x] dbt Transformations (staging + 3 marts)
- [x] Airflow Orchestration
- [x] Docker containerization
- [X] Terraform infrastructure provisioning
- [ ] Apache Iceberg lakehouse layer
- [ ] Kafka real-time streaming layer

---

## 👨‍💻 Author

**Eduardo Nunes de Almeida**  
Data Engineer | Brazil  
[GitHub](https://github.com/SrEdward) · [LinkedIn](#) · [Upwork](#)
