# Taxi Data Ingestion Pipeline with Docker and Apache Airflow

## Overview

This project demonstrates a **containerized data ingestion pipeline** where a Python ingestion script loads NYC taxi data into a PostgreSQL database. The ingestion process is orchestrated using **Apache Airflow**, while **Docker** is used to containerize all services.

The system includes:

* PostgreSQL database for storing taxi data
* pgAdmin for database management
* Apache Airflow for workflow orchestration
* A custom Docker image that runs the ingestion script

Airflow triggers the ingestion container as a task, allowing the pipeline to be scheduled and automated.

---

## Architecture

The architecture separates **orchestration**, **execution**, and **storage**.

```
                Airflow Scheduler
                        │
                        │ triggers task
                        ▼
              taxi_ingest Docker container
                        │
                        ▼
                 Postgres (ny_taxi)
                        ▲
                        │
                     pgAdmin
```

### Components

| Component                | Description                                   |
| ------------------------ | --------------------------------------------- |
| PostgreSQL               | Stores the taxi dataset                       |
| pgAdmin                  | Web interface to manage PostgreSQL            |
| Airflow Webserver        | UI to monitor and trigger workflows           |
| Airflow Scheduler        | Executes scheduled tasks                      |
| Taxi Ingestion Container | Python script that loads data into PostgreSQL |

---

## Project Structure

```
project/
│
├── docker-compose.yml
├── Dockerfile
├── ingest_data.py
├── requirements.txt
│
└── dags/
    └── taxi_ingestion_dag.py
```

### Files

**docker-compose.yml**

``` 
# ──────────────────────────────────────
#  Apache Airflow — Full Setup
# ──────────────────────────────────────

version: '3.8'

x-airflow-common:  # Reusable config block
  &airflow-common
  image: apache/airflow:2.9.3
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@airflow-db:5432/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
  volumes:
    - ./dags:/opt/airflow/dags    # your DAG files go here
    - ./logs:/opt/airflow/logs
    - /var/run/docker.sock:/var/run/docker.sock  # Docker access
  depends_on:
    airflow-db:
      condition: service_healthy

services:

  # ── 1. YOUR DATA DATABASE ────────────
  pgdatabase:
    image: postgres:18
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
      POSTGRES_DB: ny_taxi
    ports:
      - '5432:5432'

  # ── 2. PGADMIN (DB visual UI) ────────
  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: root
    ports:
      - '8085:80'   # open localhost:8085 in browser

  # ── 3. AIRFLOW METADATA DATABASE ─────
  airflow-db:
    image: postgres:18
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - airflow_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD', 'pg_isready', '-U', 'airflow']
      interval: 5s
      retries: 5

  # ── 4. INIT (runs once, then exits) ──
  airflow-init:
    <<: *airflow-common
    command: >
      bash -c "airflow db init &&
      airflow users create --username admin
      --password admin --firstname Admin
      --lastname User --role Admin
      --email admin@example.com"
    restart: on-failure

  # ── 5. SCHEDULER ─────────────────────
  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    restart: always
    depends_on:
      airflow-init:
        condition: service_completed_successfully

  # ── 6. WEBSERVER ─────────────────────
  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - '8080:8080'   # open localhost:8080 in browser
    restart: always
    depends_on:
      airflow-init:
        condition: service_completed_successfully

volumes:
  airflow_db_data:
```

Defines all services including:

* Postgres database
* pgAdmin
* Airflow services
* Airflow metadata database


**Note that:-** ``` /var/run/docker.sock:/var/run/docker.sock``` lets Airflow control Docker from inside the container.

**Dockerfile**

Builds the ingestion container that runs the Python script.

**ingest_data.py**

Python script that downloads and loads taxi data into Postgres.

**dags/taxi_ingestion_dag.py**

Airflow DAG that launches the ingestion container using Docker.

---

## Docker Ingestion Container

The ingestion container is built from the following Dockerfile:

```
FROM python:3.10

WORKDIR /app

COPY ingest_data.py .

RUN pip install pandas sqlalchemy psycopg2-binary requests

ENTRYPOINT ["python", "ingest_data.py"]
```

The `ENTRYPOINT` ensures the ingestion script runs whenever the container starts.

---

## CLI Parameters

The ingestion script accepts parameters from the command line such as:

```
--pg_user
--pg_pass
--pg_host
--pg_port
--pg_db
--zone_table
--target_table
--year
--month
```

These parameters allow the same container image to ingest different datasets without modifying the code.

Example command executed inside the container:

```
python ingest_data.py \
--pg_user=root \
--pg_pass=root \
--pg_host=pgdatabase \
--pg_port=5432 \
--pg_db=ny_taxi \
--zone_table=taxi_zone_lookup \
--target_table=green_taxi_trip_data \
--year=2025 \
--month=11
```

---

## Airflow DAG

The Airflow DAG orchestrates the ingestion process by launching the Docker container.

Example DAG:

```
from datetime import datetime
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

with DAG(
    dag_id="taxi_ingestion_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@monthly",
    catchup=False,
) as dag:

    ingest_task = DockerOperator(
        task_id="ingest_taxi_data",
        image="taxi_ingest:v002",
        command="""
        --pg_user=root
        --pg_pass=root
        --pg_host=pgdatabase
        --pg_port=5432
        --pg_db=ny_taxi
        --zone_table=taxi_zone_lookup
        --target_table=green_taxi_trip_data
        --year=2025
        --month=11
        """,
        auto_remove=True
    )
```

When the DAG runs, Airflow executes the ingestion container.

---

## Running the Project

### 1. Build the ingestion image

```
docker build -t taxi_ingest:v002 .
```

### 2. Start all services

```
docker compose up -d
```

This starts:

* PostgreSQL
* pgAdmin
* Airflow Webserver
* Airflow Scheduler
* Airflow metadata database

---

## Accessing Services

### Airflow UI

```
http://localhost:8080
```

Enable the DAG and trigger it to run the ingestion pipeline.

### pgAdmin

```
http://localhost:8085
```

Login with:

```
email: admin@admin.com
password: root
```

Connect to the Postgres server using:

```
host: pgdatabase
user: root
password: root
database: ny_taxi
```

---

## Workflow

1. Airflow scheduler triggers the DAG.
2. The DAG launches the ingestion Docker container.
3. The container runs the ingestion script.
4. The script downloads taxi data.
5. Data is loaded into PostgreSQL.
6. The container exits after completion.

---

## Benefits of This Architecture

* Containerized and reproducible
* Airflow manages scheduling and retries
* CLI parameters allow flexible ingestion
* Services are isolated using Docker

---

## Possible Improvements

Future enhancements may include:

* Dynamic ingestion of multiple months
* Data transformation steps
* Loading data into a warehouse
* Adding monitoring and alerting

---

## Conclusion

This project demonstrates how to build a **containerized data pipeline with Airflow orchestration**. By separating ingestion logic from orchestration, the system becomes scalable, maintainable, and closer to real-world data engineering workflows.
