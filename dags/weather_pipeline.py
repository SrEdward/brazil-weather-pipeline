from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, '/opt/airflow')

default_args = {
    'owner': 'eduardo',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_and_load_s3(**context):
    """Extrai dados da Open-Meteo e carrega no S3."""
    from ingestion.inmet_extractor import extract_and_load
    from dotenv import load_dotenv

    load_dotenv('/opt/airflow/.env')

    execution_date = context['ds']  # formato YYYY-MM-DD
    extract_and_load(
        bucket=os.getenv('S3_BUCKET'),
        target_date=execution_date,
    )

def load_s3_to_snowflake(**context):
    """Carrega dados do S3 para o Snowflake."""
    from ingestion.snowflake_loader import s3_to_snowflake
    from dotenv import load_dotenv

    load_dotenv('/opt/airflow/.env')

    execution_date = context['ds']
    s3_to_snowflake(
        bucket=os.getenv('S3_BUCKET'),
        target_date=execution_date,
    )

with DAG(
    dag_id='weather_pipeline',
    description='Pipeline ELT completo: Open-Meteo → S3 → Snowflake → dbt',
    default_args=default_args,
    start_date=datetime(2025, 1, 15),
    schedule_interval='0 6 * * *',  # Todo dia às 6h
    catchup=False,
    tags=['weather', 'elt', 'snowflake', 'dbt'],
) as dag:

    extract_task = PythonOperator(
        task_id='extract_to_s3',
        python_callable=extract_and_load_s3,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id='load_to_snowflake',
        python_callable=load_s3_to_snowflake,
        provide_context=True,
    )

    transform_task = BashOperator(
        task_id='dbt_transform',
        bash_command='cd /opt/airflow/dbt_project && dbt run --profiles-dir /root/.dbt',
    )

    test_task = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt_project && dbt test --profiles-dir /root/.dbt',
    )

    # Define a ordem de execução
    extract_task >> load_task >> transform_task >> test_task
