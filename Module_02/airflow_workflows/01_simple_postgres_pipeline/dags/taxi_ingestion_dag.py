from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}
with DAG(
    dag_id="taxi_ingestion_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@monthly",
    catchup=False,
    default_args=default_args,
) as dag:

    ingest_task = DockerOperator(
        task_id="ingest_taxi_data",
        image="taxi:v002",
        command="""
        --pg_user=root
        --pg_pass=root
        --pg_host=pgdatabase
        --pg_port=5432
        --pg_db=ny_taxi
        --zone_table=taxi_zone_lookup
        --target_table=yellow_taxi_data
        --year=2021
        --month=1
        """,
        network_mode="01_simple_postgres_pipeline_default", 
        auto_remove=True,
    )