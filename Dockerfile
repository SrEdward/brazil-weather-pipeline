FROM apache/airflow:2.9.1

USER airflow

WORKDIR /opt/airflow

COPY ./.env /opt/airflow/

RUN pip install --no-cache-dir \
	boto3 \
	requests \
	python-dotenv \
	snowflake-connector-python \
	dbt-snowflake \
	pyOpenSSL==23.2.0 \
	"pyiceberg[s3fs,glue]==0.7.1" \
	duckdb
