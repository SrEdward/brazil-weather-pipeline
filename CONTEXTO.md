# CONTEXTO — Brazil Weather Pipeline

Este arquivo serve como briefing para novas sessões de desenvolvimento.
Leia este arquivo antes de qualquer ação técnica.

---

## 👨‍💻 Desenvolvedor

**Eduardo Nunes de Almeida**
- Data Engineer | Gravataí, RS, Brasil
- Graduado em Ciência da Computação — UNISINOS (Jan 2025)
- Freelancer no Upwork (rate: $40/h)
- GitHub: https://github.com/SrEdward
- Stack principal: Python, SQL, Airflow, dbt, Snowflake, AWS
- SO: Arch Linux | Editor: VS Code | Shell: bash

---

## 🎯 Objetivo do Projeto

Projeto de portfólio para solidificar e demonstrar habilidades em engenharia de dados moderna, com foco em conseguir clientes no Upwork e posições pleno de Data Engineer.

---

## 🏗️ Arquitetura Final

```
Open-Meteo API (dados climáticos gratuitos)
        │
        ▼
Python Extractor (ingestion/inmet_extractor.py)
        │
        ├──► AWS S3 (raw/weather/YYYY-MM-DD/data.json)
        │         │
        │         ▼
        │    Snowflake STAGING.RAW_WEATHER
        │         │
        │         ▼
        │    dbt models
        │    ├── STAGING.stg_weather (view)
        │    └── MARTS.*
        │        ├── mart_daily_temperature (table)
        │        ├── mart_state_summary (table)
        │        └── mart_rain_alerts (table)
        │
        └──► Apache Iceberg (S3 Parquet)
                  s3://brazil-weather-pipeline-raw/iceberg/
                  brazil_weather.db/weather_data/
                  Particionado por mês
                  Catálogo: AWS Glue
                  ├── Queries locais via DuckDB
                  └── Snowflake External Iceberg Table (STAGING.iceberg_weather_data)

Kafka Streaming (paralelo ao batch):
Producer (kafka/producer.py) → Topic: weather-events → Consumer (kafka/consumer.py) → Iceberg

Orquestração (Airflow DAG: weather_pipeline):
extract_to_s3 → load_to_snowflake → dbt_transform → dbt_test → write_to_iceberg
Agendamento: diário às 06:00 UTC
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12.12 (venv) |
| Extração | Open-Meteo API | - |
| Storage raw | AWS S3 | - |
| Data Warehouse | Snowflake | Standard Edition |
| Transformação | dbt-snowflake | 1.11.7 |
| Orquestração | Apache Airflow | 2.9.1 |
| Lakehouse | Apache Iceberg (PyIceberg) | 0.7.1 |
| Query engine | DuckDB | latest |
| Streaming | Kafka (kafka-python) | 2.3.1 |
| Containerização | Docker + Docker Compose | - |
| IaC | Terraform | 1.14.8 |
| Cloud | AWS (S3, IAM, Glue) | - |

---

## ☁️ Infraestrutura AWS

- **Conta:** 183510238779
- **Região:** us-east-1
- **Bucket S3:** `brazil-weather-pipeline-raw`
- **IAM User (aplicação):** `weather-pipeline-user` — acesso restrito a S3 e Glue
- **IAM User (admin):** usuário pessoal do Eduardo — usado para Terraform
- **IAM Role (Snowflake):** `snowflake-iceberg-role` — usada pelo Snowflake para acessar S3 e Glue via sts:AssumeRole
- **Glue Catalog:** namespace `brazil_weather`, tabela `weather_data`
- **Toda infraestrutura gerenciada via Terraform** em `terraform/`

---

## ❄️ Snowflake

- **Account:** RUUBFND-FGB85853
- **Database:** DE_PROJECT_WEATHER_PIPELINE_DB
- **Schemas:** STAGING, MARTS, PUBLIC
- **Warehouse:** WEATHER_PIPELINE_WH
- **Role:** ACCOUNTADMIN
- **External Volume:** `iceberg_s3_vol` (ALLOW_WRITES=FALSE, aponta para s3://brazil-weather-pipeline-raw/iceberg/)
- **Catalog Integration:** `glue_catalog_int` (GLUE, namespace brazil_weather)
- **External Iceberg Table:** `STAGING.iceberg_weather_data` (3.730 registros validados)

---

## 📁 Estrutura do Repositório

```
brazil-weather-pipeline/
├── Dockerfile                         # Imagem customizada do Airflow
├── docker-compose.yml                 # Airflow + Postgres + Kafka + Zookeeper
├── requirements.txt                   # Dependências Python
├── .env                               # Credenciais (nunca no Git)
├── .env.example                       # Template de credenciais
├── .gitignore
├── README.md                          # Documentação pública do projeto
├── CONTEXTO.md                        # Este arquivo
│
├── dags/
│   └── weather_pipeline.py            # DAG principal do Airflow
│
├── ingestion/
│   ├── inmet_extractor.py             # Extrator Open-Meteo + upload S3
│   └── snowflake_loader.py            # Loader S3 → Snowflake
│
├── iceberg/
│   ├── iceberg_writer.py              # Writer PyIceberg → S3 Parquet
│   └── duckdb_query.py               # Queries analíticas via DuckDB
│
├── kafka/
│   ├── producer.py                    # Producer Kafka (dados atuais)
│   └── consumer.py                   # Consumer Kafka → Iceberg
│
├── dbt_project/
│   ├── dbt_project.yml
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
│
└── terraform/
    ├── main.tf                        # S3 bucket + IAM user + Glue policies
    ├── snowflake_iceberg.tf           # IAM Role + policies para Snowflake
    ├── variables.tf
    ├── outputs.tf
    └── terraform.tfvars               # Nunca no Git
```

---

## 🔄 Como Subir o Ambiente Local

```bash
# 1. Ativa o venv (Python 3.12 via pyenv)
source .venv/bin/activate

# 2. Carrega o módulo overlay do kernel (necessário após reboot no Arch)
sudo modprobe overlay

# 3. Inicia o Docker
sudo systemctl start docker

# 4. Sobe os containers
docker compose up -d

# 5. Verifica se está tudo healthy
docker compose ps
```

**Airflow UI:** http://localhost:8080 (admin/admin)

---

## ⚠️ Problemas Conhecidos e Soluções

| Problema | Causa | Solução |
|---|---|---|
| Docker não inicia | Módulo overlay não carregado | `sudo modprobe overlay` |
| Docker sem permissão | Usuário não está no grupo docker | `newgrp docker` ou relogar |
| dbt profile não encontrado | profiles.yml em /root/.dbt | `cp /root/.dbt/profiles.yml ~/.dbt/` |
| pyOpenSSL erro SSL | Versão incompatível | `pip install pyOpenSSL==23.2.0` |
| Iceberg schema mismatch | required vs optional | Todos os campos definidos como `required=False` |
| Kafka tópico não encontrado | Nome diferente entre producer e consumer | Verificar nome do tópico nos dois arquivos |
| Snowflake External Volume — PutObject denied | Role sem permissão de escrita | Criar External Volume com `ALLOW_WRITES=FALSE` |
| Terraform state inconsistente | Recursos criados fora do Terraform | Usar `terraform import` para cada recurso existente |

---

## 📊 Dados

- **Fonte:** Open-Meteo Historical Weather API + Forecast API
- **Cidades:** Porto Alegre, São Paulo, Rio de Janeiro, Salvador, Fortaleza, Manaus, Belém, Brasília, Cuiabá, Recife
- **Período histórico:** 2024-01-01 até 2024-12-31 (366 dias)
- **Volume:** ~3.730 registros (batch + streaming)
- **Particionamento Iceberg:** por mês (`weather_date_month`)

---

## 🔀 Padrões Git Adotados

- **Branch strategy:** feature branches → PR → merge na main
- **Commit convention:** Conventional Commits
  - `feat(scope): descrição`
  - `chore(scope): descrição`
  - `docs(scope): descrição`
- **Nunca push direto na main**

---

## ✅ Status do Projeto

O projeto está **completo**. Todos os itens do roadmap foram implementados:

- [x] ELT Pipeline (Extract → S3 → Snowflake)
- [x] dbt Transformations (staging + 3 marts)
- [x] Airflow Orchestration
- [x] Docker containerização
- [x] Terraform IaC
- [x] Apache Iceberg lakehouse layer (PyIceberg + AWS Glue)
- [x] Kafka real-time streaming layer
- [x] Snowflake External Iceberg Tables

---

## 🗺️ Próximos Passos

- [ ] Projeto 2: discussão arquitetural primeiro, depois escolha da stack
- [ ] Projeto 3: Data Platform com Lakehouse (Iceberg + dbt + Trino)
- [ ] Submissão do artigo JBCS (GRU-based temperature forecasting)
