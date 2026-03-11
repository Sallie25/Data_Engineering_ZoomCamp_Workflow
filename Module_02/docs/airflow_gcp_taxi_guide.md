# Replicating the Kestra GCP Taxi Pipeline in Apache Airflow
### A Complete Beginner's Guide — Concept by Concept, Line by Line

---

## Table of Contents

1. [What is Apache Airflow? (The Mental Model)](#1-what-is-apache-airflow)
2. [How Airflow Differs from Kestra](#2-how-airflow-differs-from-kestra)
3. [Setting Up Your Environment](#3-setting-up-your-environment)
4. [Connecting Airflow to GCP](#4-connecting-airflow-to-gcp)
5. [Understanding the Building Blocks](#5-understanding-the-building-blocks)
6. [The Complete DAG — Annotated Line by Line](#6-the-complete-dag)
7. [Running and Monitoring Your DAG](#7-running-and-monitoring-your-dag)
8. [Kestra vs. Airflow Cheat Sheet](#8-kestra-vs-airflow-cheat-sheet)

---

## 1. What is Apache Airflow?

### The Core Idea

Think of Apache Airflow as a smart task scheduler written entirely in Python. You describe your pipeline as a Python script, and Airflow reads that script, figures out what depends on what, and then runs your tasks in the correct order — automatically, on a schedule, with retries, and with a visual dashboard showing you what's happening.

### The DAG — Your Most Important Concept

The heart of Airflow is the **DAG**, which stands for **Directed Acyclic Graph**. This sounds complicated, but the idea is simple:

- **Directed** — tasks have a direction, meaning Task A runs *before* Task B
- **Acyclic** — there are no loops; the pipeline can never circle back on itself
- **Graph** — it's a network of connected tasks

You can think of a DAG as a flowchart drawn in Python. You define the boxes (tasks) and the arrows (dependencies) between them.

```
download_file → decompress → upload_to_gcs → run_sql → merge_data
```

Every pipeline you write in Airflow is one DAG. The Kestra file you've been studying is equivalent to one Airflow DAG.

### What is an Operator?

In Airflow, every individual task is powered by an **Operator**. An operator is a pre-built Python class that knows how to do one specific thing — download a file, run a SQL query, upload to GCS, branch based on a condition, etc.

Think of operators as the verbs of Airflow:
- `PythonOperator` → run this Python function
- `BranchPythonOperator` → decide which path to take (the Kestra `If` equivalent)
- `BigQueryInsertJobOperator` → run this SQL on BigQuery
- `GCSHook` → interact with Google Cloud Storage

You pick the right operator for each step, configure it, and Airflow handles the execution.

---

## 2. How Airflow Differs from Kestra

Understanding the differences will help you translate concepts directly.

| Concept | Kestra | Airflow |
|---|---|---|
| **Language** | YAML (declarative) | Python (code) |
| **A pipeline file** | A `.yaml` flow file | A `.py` DAG file |
| **A single step** | A `task` with a `type` | An instance of an `Operator` |
| **Conditional logic** | `io.kestra.plugin.core.flow.If` | `BranchPythonOperator` |
| **Inputs (dropdowns)** | `inputs:` section | `Airflow Variables` or `Params` |
| **KV Store** | `kv('KEY_NAME')` | `Variable.get('KEY_NAME')` |
| **Secrets** | `secret('KEY_NAME')` | Airflow Connections (UI) |
| **Task output passing** | `outputs.task_id.uri` | `XCom` (cross-communication) |
| **Shared GCP config** | `pluginDefaults` | `gcp_conn_id` parameter |
| **Scheduling** | `triggers` block | `schedule_interval` parameter |

The most important mental shift: **in Kestra you describe what to do; in Airflow you write Python code that does it.**

---

## 3. Setting Up Your Environment

### Step 3.1 — Install Python and pip

Airflow requires Python 3.8+. Check yours first:

```bash
python3 --version
```

### Step 3.2 — Install Apache Airflow

Airflow has many optional packages. You install the core plus any "providers" (extra plugins) you need. For this pipeline you need the **Google provider** package:

```bash
# Install Airflow with the Google Cloud provider
pip install apache-airflow apache-airflow-providers-google
```

**What is `apache-airflow-providers-google`?**
This is the package that gives you all the GCP operators — the BigQuery operators, GCS operators, and so on. Without it, Airflow knows nothing about Google Cloud. It's the equivalent of the `io.kestra.plugin.gcp` plugin family in Kestra.

### Step 3.3 — Initialise Airflow

Airflow uses a metadata database to track DAG runs, task statuses, logs, etc. You need to set it up once:

```bash
# Set the Airflow home directory (where your DAGs will live)
export AIRFLOW_HOME=~/airflow

# Initialise the metadata database
airflow db init

# Create an admin user so you can log into the UI
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

### Step 3.4 — Start the Airflow Services

Airflow has two main components you need to run:

```bash
# Terminal 1: The Scheduler (reads DAGs and triggers tasks)
airflow scheduler

# Terminal 2: The Web Server (the dashboard UI)
airflow webserver --port 8080
```

Now open `http://localhost:8080` in your browser and log in with `admin/admin`. This is your Airflow UI — the equivalent of the Kestra UI where you ran your flows.

### Step 3.5 — Create Your DAGs Folder

Airflow automatically reads Python files from a `dags/` folder inside `AIRFLOW_HOME`:

```bash
mkdir ~/airflow/dags
```

Any `.py` file you place here is automatically picked up as a DAG.

---

## 4. Connecting Airflow to GCP

In Kestra, GCP credentials were handled via `pluginDefaults` with `secret('GCP_SERVICE_ACCOUNT')`. In Airflow, credentials are stored as a **Connection** — a named object in Airflow's database that stores authentication details securely.

### Step 4.1 — Get Your GCP Service Account Key

You need a JSON key file for a GCP Service Account that has permissions for:
- **BigQuery Admin** (to create/query tables)
- **Storage Object Admin** (to upload to GCS)

Download this JSON key from the GCP Console: IAM & Admin → Service Accounts → your account → Keys → Add Key → JSON.

### Step 4.2 — Create the GCP Connection in Airflow

Open the Airflow UI → Admin → Connections → Click the `+` button to add a new connection.

Fill in these fields:

| Field | Value |
|---|---|
| **Connection Id** | `google_cloud_default` |
| **Connection Type** | `Google Cloud` |
| **Project Id** | Your GCP Project ID (e.g., `my-project-123`) |
| **Keyfile JSON** | Paste the entire contents of your service account JSON key file here |

Click Save. Every GCP operator will look for this connection by default when you pass `gcp_conn_id='google_cloud_default'`.

> **Why `google_cloud_default`?** This is Airflow's conventional default name for GCP connections. You can name it anything, but you'd then need to pass that name explicitly to every operator. Using the default name saves you repeating it everywhere — this is the Airflow equivalent of `pluginDefaults`.

### Step 4.3 — Store Config Values as Airflow Variables

In Kestra, non-secret config (bucket name, dataset name, project ID) was stored in the **KV Store** and retrieved with `kv('KEY')`. In Airflow, the equivalent is **Airflow Variables**.

Go to the Airflow UI → Admin → Variables → Click `+` for each of these:

| Key | Value (Example) |
|---|---|
| `GCP_PROJECT_ID` | `my-gcp-project-123` |
| `GCP_BUCKET_NAME` | `my-taxi-data-bucket` |
| `GCP_DATASET` | `taxi_data` |
| `GCP_LOCATION` | `US` |

In your DAG code you will retrieve these with:
```python
from airflow.models import Variable
project_id = Variable.get("GCP_PROJECT_ID")
```

This is the direct Airflow equivalent of `{{kv('GCP_PROJECT_ID')}}` in Kestra.

---

## 5. Understanding the Building Blocks

Before writing the full DAG, here are the four key concepts you need to understand deeply.

### 5.1 — The `default_args` Dictionary

Every DAG accepts a dictionary of default arguments that apply to every task inside it. This saves you from repeating the same settings on every single operator.

```python
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',           # Who owns this DAG (shown in the UI)
    'retries': 1,                 # Retry a failed task once before giving up
    'retry_delay': timedelta(minutes=5),  # Wait 5 mins before retrying
    'email_on_failure': False,    # Don't send emails on failure (set True in production)
}
```

Think of `default_args` as the Airflow equivalent of Kestra's `pluginDefaults` — a single place to configure behaviour that applies everywhere.

### 5.2 — The `with DAG(...)` Context Manager

The `with DAG(...) as dag:` block is how you define a DAG. Every operator you create **inside** this block automatically belongs to that DAG.

```python
from airflow import DAG

with DAG(
    dag_id='gcp_taxi_pipeline',      # Unique name — like Kestra's `id`
    default_args=default_args,       # The dict from above
    description='NYC Taxi GCP Pipeline',  # Like Kestra's `description`
    schedule_interval=None,          # None = only run manually (no automatic schedule)
    start_date=datetime(2024, 1, 1), # Airflow needs a start date for scheduling logic
    catchup=False,                   # Don't backfill missed runs — very important
    tags=['gcp', 'taxi', 'bigquery'] # Labels for the UI — like Kestra's labels
) as dag:
    # All your tasks go here
    ...
```

**What is `catchup=False`?**
If your `start_date` is 6 months ago and you set a daily schedule, Airflow would by default try to run your DAG for every day it "missed". Setting `catchup=False` prevents this — it only runs from now onwards.

### 5.3 — The `BranchPythonOperator` (The Kestra `If` Equivalent)

In Kestra you had:
```yaml
- id: if_yellow_taxi
  type: io.kestra.plugin.core.flow.If
  condition: "{{inputs.taxi == 'yellow'}}"
```

In Airflow, branching is done with `BranchPythonOperator`. You write a Python function that returns the **task_id** of the branch to follow. All other downstream branches are automatically skipped.

```python
from airflow.operators.python import BranchPythonOperator

def choose_taxi_branch(**context):
    taxi_type = context['params']['taxi']  # Read from DAG Params (like Kestra inputs)
    if taxi_type == 'yellow':
        return 'bq_yellow_tripdata'    # Return the task_id to execute
    else:
        return 'bq_green_tripdata'     # Return the other branch's task_id

branch_task = BranchPythonOperator(
    task_id='choose_taxi_branch',
    python_callable=choose_taxi_branch,  # The function that decides the branch
)
```

**Key rule:** The function **must return a `task_id`** (a string). That task and everything downstream of it will run. All other branches are marked as "skipped".

### 5.4 — XCom: Passing Data Between Tasks

In Kestra, you passed file paths between tasks using `outputs.task_id.uri`. In Airflow, this is done with **XCom** (short for "cross-communication").

XCom is a small key-value store built into Airflow that lets tasks push and pull small pieces of data — like file paths, row counts, status messages, etc.

```python
# Task A: PUSH a value to XCom
def upload_file(**context):
    file_path = "/tmp/my_file.csv"
    # ... do work ...
    context['ti'].xcom_push(key='uploaded_path', value=file_path)
    # 'ti' = task instance — the running instance of this task

# Task B: PULL the value from Task A's XCom
def process_file(**context):
    file_path = context['ti'].xcom_pull(task_ids='upload_file', key='uploaded_path')
    # Now you have the file path from the previous task
```

> **Important:** XCom is for small values (strings, numbers, short paths). It's stored in Airflow's database. Never use XCom to pass large files or dataframes — for that, write to a temp location and pass the path.

---

## 6. The Complete DAG

Now let's write the full Airflow DAG that replicates the Kestra pipeline. Create this file at `~/airflow/dags/gcp_taxi_pipeline.py`.

Every section below has a full explanation of what it does and why.

---

### Section 1: Imports

```python
# ============================================================
# SECTION 1: IMPORTS
# Every Airflow DAG starts by importing the tools it needs.
# ============================================================

import os
import gzip
import shutil
import logging
import requests
from datetime import datetime, timedelta

# The core Airflow DAG class — the container for your pipeline
from airflow import DAG

# Variable: Airflow's equivalent of Kestra's kv() store
from airflow.models import Variable

# PythonOperator: runs any Python function as a task
# BranchPythonOperator: runs a Python function that DECIDES which branch to take
from airflow.operators.python import PythonOperator, BranchPythonOperator

# EmptyOperator: a no-op task, used as a join/anchor point after branches
# (equivalent to a dummy task in older Airflow versions)
from airflow.operators.empty import EmptyOperator

# BigQueryInsertJobOperator: runs any SQL query on BigQuery
# This is the modern replacement for the older BigQueryOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

# GCSHook: a low-level tool for interacting directly with Google Cloud Storage
# Used inside PythonOperator tasks for file uploads
from airflow.providers.google.cloud.hooks.gcs import GCSHook
```

**Why so many imports?** Unlike Kestra where you just specify a `type:` string, Airflow requires you to import every class you use. Think of it as telling Python "go fetch these tools from their library shelves before we start".

---

### Section 2: Configuration Variables

```python
# ============================================================
# SECTION 2: CONFIGURATION
# Equivalent to Kestra's `variables:` section and kv() calls.
# We fetch values from Airflow Variables (set in Admin → Variables).
# Variable.get() is the direct equivalent of kv('KEY') in Kestra.
# ============================================================

GCP_PROJECT_ID  = Variable.get("GCP_PROJECT_ID")
GCP_BUCKET_NAME = Variable.get("GCP_BUCKET_NAME")
GCP_DATASET     = Variable.get("GCP_DATASET")
GCP_LOCATION    = Variable.get("GCP_LOCATION", default_var="US")

# This is the shared GCP connection ID.
# All GCP operators will look up this name to find credentials.
# It's the equivalent of pluginDefaults → serviceAccount in Kestra.
GCP_CONN_ID = "google_cloud_default"
```

---

### Section 3: Helper Functions

These are Python functions that will be called by `PythonOperator` tasks. They are defined outside the DAG — they're just regular Python functions.

```python
# ============================================================
# SECTION 3: HELPER FUNCTIONS
# These are the Python functions that PythonOperator tasks will call.
# They replace Kestra's built-in task types like:
#   - io.kestra.plugin.core.http.Download
#   - io.kestra.plugin.compress.FileDecompress
#   - io.kestra.plugin.gcp.gcs.Upload
# ============================================================

def build_filename(taxi: str, year: str, month: str) -> str:
    """
    Builds the CSV filename from the three input parameters.
    Equivalent to Kestra's variable:
        file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
    
    Example: build_filename('green', '2019', '01') 
             → 'green_tripdata_2019-01.csv'
    """
    return f"{taxi}_tripdata_{year}-{month}.csv"


def download_and_decompress(**context):
    """
    Downloads the .gz file from GitHub and decompresses it to a local .csv.

    This combines TWO Kestra tasks into one Python function:
        1. io.kestra.plugin.core.http.Download   (download the .gz)
        2. io.kestra.plugin.compress.FileDecompress  (decompress it)

    We combine them here because in Airflow it's simpler to handle
    the whole process in one Python function rather than passing
    temp file paths through XCom between two separate tasks.

    The function receives `context` automatically from Airflow — this
    is a dictionary containing information about the current run,
    including `params` (the user-supplied inputs, like Kestra's inputs).
    """
    # Read the user's input parameters (like Kestra's {{inputs.taxi}})
    # `params` is how Airflow DAG Params are accessed at runtime.
    taxi  = context['params']['taxi']
    year  = context['params']['year']
    month = context['params']['month']

    # Build the filename — same logic as Kestra's vars.file
    filename = build_filename(taxi, year, month)

    # Build the download URL — same as Kestra's download_gzip task URI
    url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{taxi}/{filename}.gz"

    # Define where we'll save the files temporarily on the local filesystem
    # /tmp is the standard Unix temp directory — good for intermediate files
    gz_path  = f"/tmp/{filename}.gz"   # The compressed file
    csv_path = f"/tmp/{filename}"      # The decompressed file

    # ---- DOWNLOAD ----
    # requests.get() is standard Python for making HTTP requests
    logging.info(f"Downloading from: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raises an error if the download failed

    # Write the downloaded bytes to a local .gz file
    with open(gz_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logging.info(f"Downloaded to: {gz_path}")

    # ---- DECOMPRESS ----
    # gzip.open() reads a .gz file; we copy its contents to a plain file
    logging.info(f"Decompressing to: {csv_path}")
    with gzip.open(gz_path, 'rb') as f_in:
        with open(csv_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    logging.info(f"Decompressed to: {csv_path}")

    # Clean up the .gz file — we no longer need it
    os.remove(gz_path)

    # ---- XCOM PUSH ----
    # Push the local csv path to XCom so the NEXT task can find the file.
    # This is equivalent to Kestra's `outputs.decompress.uri`.
    # The next task will call xcom_pull to get this value.
    context['ti'].xcom_push(key='csv_path', value=csv_path)
    context['ti'].xcom_push(key='filename', value=filename)
    logging.info(f"Pushed csv_path={csv_path} to XCom")


def upload_to_gcs(**context):
    """
    Uploads the local CSV file to Google Cloud Storage.

    Equivalent to Kestra's task:
        id: upload_to_gcs
        type: io.kestra.plugin.gcp.gcs.Upload
        from: "{{ outputs.decompress.uri }}"
        to: "{{render(vars.gcs_file)}}"

    GCSHook is Airflow's low-level GCS client. It uses the
    connection stored under GCP_CONN_ID to authenticate.
    """
    # Pull the CSV path from XCom — this is what the previous task pushed
    # task_ids tells XCom which task produced the value we want
    csv_path = context['ti'].xcom_pull(task_ids='download_and_decompress', key='csv_path')
    filename = context['ti'].xcom_pull(task_ids='download_and_decompress', key='filename')

    # The destination path in GCS — equivalent to vars.gcs_file in Kestra
    gcs_object_name = filename  # e.g. "green_tripdata_2019-01.csv"

    logging.info(f"Uploading {csv_path} to gs://{GCP_BUCKET_NAME}/{gcs_object_name}")

    # GCSHook: the low-level GCS client in Airflow
    # gcp_conn_id points to the connection we set up in the UI
    hook = GCSHook(gcp_conn_id=GCP_CONN_ID)

    # upload() sends the local file to GCS
    hook.upload(
        bucket_name=GCP_BUCKET_NAME,
        object_name=gcs_object_name,
        filename=csv_path,          # local file path
        mime_type='text/csv',
    )
    logging.info(f"Upload complete: gs://{GCP_BUCKET_NAME}/{gcs_object_name}")

    # Clean up the local CSV file — we no longer need it
    os.remove(csv_path)
    logging.info(f"Cleaned up local file: {csv_path}")


def choose_branch(**context):
    """
    Decides which branch to take based on the taxi type input.

    This is the direct equivalent of Kestra's two If tasks:
        - if_yellow_taxi: condition: "{{inputs.taxi == 'yellow'}}"
        - if_green_taxi:  condition: "{{inputs.taxi == 'green'}}"

    BranchPythonOperator calls this function and expects it to
    RETURN THE TASK_ID of the next task to run. All other branches
    will be automatically skipped by Airflow.
    """
    taxi = context['params']['taxi']
    if taxi == 'yellow':
        return 'bq_yellow_tripdata'   # This is the task_id of the first yellow task
    else:
        return 'bq_green_tripdata'    # This is the task_id of the first green task
```

---

### Section 4: SQL Templates

These are the BigQuery SQL statements. We define them as Python functions so they can receive the dynamic values (taxi type, year, month) at runtime — just as Kestra used `{{render(vars.table)}}` and `{{kv('GCP_PROJECT_ID')}}`.

```python
# ============================================================
# SECTION 4: SQL TEMPLATE FUNCTIONS
# These build the SQL strings dynamically, equivalent to how
# Kestra's BigQuery tasks used Pebble expressions like:
#   {{kv('GCP_PROJECT_ID')}}.{{render(vars.table)}}
# ============================================================

def get_table_id(taxi, year, month):
    """
    Returns the fully qualified BigQuery table name.
    Equivalent to Kestra's vars.table:
        "{{kv('GCP_DATASET')}}.{{inputs.taxi}}_tripdata_{{inputs.year}}_{{inputs.month}}"
    Example: "taxi_data.green_tripdata_2019_01"
    """
    return f"{GCP_DATASET}.{taxi}_tripdata_{year}_{month}"


def sql_create_yellow_table():
    """CREATE TABLE IF NOT EXISTS for yellow taxi — partitioned main table."""
    return f"""
    CREATE TABLE IF NOT EXISTS `{GCP_PROJECT_ID}.{GCP_DATASET}.yellow_tripdata`
    (
        unique_row_id BYTES,
        filename STRING,
        VendorID STRING,
        tpep_pickup_datetime TIMESTAMP,
        tpep_dropoff_datetime TIMESTAMP,
        passenger_count INTEGER,
        trip_distance NUMERIC,
        RatecodeID STRING,
        store_and_fwd_flag STRING,
        PULocationID STRING,
        DOLocationID STRING,
        payment_type INTEGER,
        fare_amount NUMERIC,
        extra NUMERIC,
        mta_tax NUMERIC,
        tip_amount NUMERIC,
        tolls_amount NUMERIC,
        improvement_surcharge NUMERIC,
        total_amount NUMERIC,
        congestion_surcharge NUMERIC
    )
    PARTITION BY DATE(tpep_pickup_datetime)
    """


def sql_create_yellow_ext(year, month):
    """CREATE EXTERNAL TABLE pointing at the CSV in GCS — yellow taxi."""
    table_id   = get_table_id('yellow', year, month)
    gcs_uri    = f"gs://{GCP_BUCKET_NAME}/yellow_tripdata_{year}-{month}.csv"
    return f"""
    CREATE OR REPLACE EXTERNAL TABLE `{GCP_PROJECT_ID}.{table_id}_ext`
    (
        VendorID STRING,
        tpep_pickup_datetime TIMESTAMP,
        tpep_dropoff_datetime TIMESTAMP,
        passenger_count INTEGER,
        trip_distance NUMERIC,
        RatecodeID STRING,
        store_and_fwd_flag STRING,
        PULocationID STRING,
        DOLocationID STRING,
        payment_type INTEGER,
        fare_amount NUMERIC,
        extra NUMERIC,
        mta_tax NUMERIC,
        tip_amount NUMERIC,
        tolls_amount NUMERIC,
        improvement_surcharge NUMERIC,
        total_amount NUMERIC,
        congestion_surcharge NUMERIC
    )
    OPTIONS (
        format = 'CSV',
        uris = ['{gcs_uri}'],
        skip_leading_rows = 1,
        ignore_unknown_values = TRUE
    )
    """


def sql_create_yellow_tmp(year, month):
    """CREATE temp table from external — adds MD5 hash ID — yellow taxi."""
    table_id = get_table_id('yellow', year, month)
    filename = build_filename('yellow', year, month)
    return f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{table_id}`
    AS
    SELECT
        MD5(CONCAT(
            COALESCE(CAST(VendorID AS STRING), ""),
            COALESCE(CAST(tpep_pickup_datetime AS STRING), ""),
            COALESCE(CAST(tpep_dropoff_datetime AS STRING), ""),
            COALESCE(CAST(PULocationID AS STRING), ""),
            COALESCE(CAST(DOLocationID AS STRING), "")
        )) AS unique_row_id,
        "{filename}" AS filename,
        *
    FROM `{GCP_PROJECT_ID}.{table_id}_ext`
    """


def sql_merge_yellow(year, month):
    """MERGE temp table into main yellow_tripdata — idempotent upsert."""
    table_id = get_table_id('yellow', year, month)
    return f"""
    MERGE INTO `{GCP_PROJECT_ID}.{GCP_DATASET}.yellow_tripdata` T
    USING `{GCP_PROJECT_ID}.{table_id}` S
    ON T.unique_row_id = S.unique_row_id
    WHEN NOT MATCHED THEN
        INSERT (unique_row_id, filename, VendorID, tpep_pickup_datetime,
                tpep_dropoff_datetime, passenger_count, trip_distance, RatecodeID,
                store_and_fwd_flag, PULocationID, DOLocationID, payment_type,
                fare_amount, extra, mta_tax, tip_amount, tolls_amount,
                improvement_surcharge, total_amount, congestion_surcharge)
        VALUES (S.unique_row_id, S.filename, S.VendorID, S.tpep_pickup_datetime,
                S.tpep_dropoff_datetime, S.passenger_count, S.trip_distance,
                S.RatecodeID, S.store_and_fwd_flag, S.PULocationID, S.DOLocationID,
                S.payment_type, S.fare_amount, S.extra, S.mta_tax, S.tip_amount,
                S.tolls_amount, S.improvement_surcharge, S.total_amount,
                S.congestion_surcharge)
    """


# ---- GREEN TAXI SQL (same pattern, different column names) ----

def sql_create_green_table():
    """CREATE TABLE IF NOT EXISTS for green taxi — partitioned main table."""
    return f"""
    CREATE TABLE IF NOT EXISTS `{GCP_PROJECT_ID}.{GCP_DATASET}.green_tripdata`
    (
        unique_row_id BYTES,
        filename STRING,
        VendorID STRING,
        lpep_pickup_datetime TIMESTAMP,
        lpep_dropoff_datetime TIMESTAMP,
        store_and_fwd_flag STRING,
        RatecodeID STRING,
        PULocationID STRING,
        DOLocationID STRING,
        passenger_count INT64,
        trip_distance NUMERIC,
        fare_amount NUMERIC,
        extra NUMERIC,
        mta_tax NUMERIC,
        tip_amount NUMERIC,
        tolls_amount NUMERIC,
        ehail_fee NUMERIC,
        improvement_surcharge NUMERIC,
        total_amount NUMERIC,
        payment_type INTEGER,
        trip_type STRING,
        congestion_surcharge NUMERIC
    )
    PARTITION BY DATE(lpep_pickup_datetime)
    """


def sql_create_green_ext(year, month):
    """CREATE EXTERNAL TABLE pointing at the CSV in GCS — green taxi."""
    table_id = get_table_id('green', year, month)
    gcs_uri  = f"gs://{GCP_BUCKET_NAME}/green_tripdata_{year}-{month}.csv"
    return f"""
    CREATE OR REPLACE EXTERNAL TABLE `{GCP_PROJECT_ID}.{table_id}_ext`
    (
        VendorID STRING,
        lpep_pickup_datetime TIMESTAMP,
        lpep_dropoff_datetime TIMESTAMP,
        store_and_fwd_flag STRING,
        RatecodeID STRING,
        PULocationID STRING,
        DOLocationID STRING,
        passenger_count INT64,
        trip_distance NUMERIC,
        fare_amount NUMERIC,
        extra NUMERIC,
        mta_tax NUMERIC,
        tip_amount NUMERIC,
        tolls_amount NUMERIC,
        ehail_fee NUMERIC,
        improvement_surcharge NUMERIC,
        total_amount NUMERIC,
        payment_type INTEGER,
        trip_type STRING,
        congestion_surcharge NUMERIC
    )
    OPTIONS (
        format = 'CSV',
        uris = ['{gcs_uri}'],
        skip_leading_rows = 1,
        ignore_unknown_values = TRUE
    )
    """


def sql_create_green_tmp(year, month):
    """CREATE temp table from external — adds MD5 hash ID — green taxi."""
    table_id = get_table_id('green', year, month)
    filename = build_filename('green', year, month)
    return f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{table_id}`
    AS
    SELECT
        MD5(CONCAT(
            COALESCE(CAST(VendorID AS STRING), ""),
            COALESCE(CAST(lpep_pickup_datetime AS STRING), ""),
            COALESCE(CAST(lpep_dropoff_datetime AS STRING), ""),
            COALESCE(CAST(PULocationID AS STRING), ""),
            COALESCE(CAST(DOLocationID AS STRING), "")
        )) AS unique_row_id,
        "{filename}" AS filename,
        *
    FROM `{GCP_PROJECT_ID}.{table_id}_ext`
    """


def sql_merge_green(year, month):
    """MERGE temp table into main green_tripdata — idempotent upsert."""
    table_id = get_table_id('green', year, month)
    return f"""
    MERGE INTO `{GCP_PROJECT_ID}.{GCP_DATASET}.green_tripdata` T
    USING `{GCP_PROJECT_ID}.{table_id}` S
    ON T.unique_row_id = S.unique_row_id
    WHEN NOT MATCHED THEN
        INSERT (unique_row_id, filename, VendorID, lpep_pickup_datetime,
                lpep_dropoff_datetime, store_and_fwd_flag, RatecodeID,
                PULocationID, DOLocationID, passenger_count, trip_distance,
                fare_amount, extra, mta_tax, tip_amount, tolls_amount,
                ehail_fee, improvement_surcharge, total_amount, payment_type,
                trip_type, congestion_surcharge)
        VALUES (S.unique_row_id, S.filename, S.VendorID, S.lpep_pickup_datetime,
                S.lpep_dropoff_datetime, S.store_and_fwd_flag, S.RatecodeID,
                S.PULocationID, S.DOLocationID, S.passenger_count, S.trip_distance,
                S.fare_amount, S.extra, S.mta_tax, S.tip_amount, S.tolls_amount,
                S.ehail_fee, S.improvement_surcharge, S.total_amount,
                S.payment_type, S.trip_type, S.congestion_surcharge)
    """
```

---

### Section 5: The DAG Definition

This is where all the tasks are assembled and their order (dependencies) is defined.

```python
# ============================================================
# SECTION 5: DAG DEFINITION
# This is the main DAG block. Everything inside `with DAG(...):`
# is part of the pipeline. This is equivalent to the top-level
# structure of the entire Kestra YAML file.
# ============================================================

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id='gcp_taxi_pipeline',
    default_args=default_args,
    description='NYC Taxi data pipeline: GitHub → GCS → BigQuery',
    schedule_interval=None,    # Manual trigger only (like running a Kestra flow manually)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    # Params are Airflow's equivalent of Kestra's `inputs:` section.
    # They appear as a form in the UI when you manually trigger the DAG.
    params={
        'taxi':  'green',    # Default value — like Kestra's `defaults: green`
        'year':  '2019',
        'month': '01',
    },
    tags=['gcp', 'taxi', 'bigquery'],
) as dag:

    # ----------------------------------------------------------
    # TASK 1: download_and_decompress
    # Equivalent to Kestra's `download_gzip` + `decompress` tasks combined.
    # PythonOperator runs our Python function `download_and_decompress`.
    # ----------------------------------------------------------
    t_download = PythonOperator(
        task_id='download_and_decompress',
        python_callable=download_and_decompress,
        # provide_context is True by default in modern Airflow — the function
        # receives the `context` dict (which includes `params`, `ti`, etc.)
    )

    # ----------------------------------------------------------
    # TASK 2: upload_to_gcs
    # Equivalent to Kestra's `upload_to_gcs` task.
    # ----------------------------------------------------------
    t_upload = PythonOperator(
        task_id='upload_to_gcs',
        python_callable=upload_to_gcs,
    )

    # ----------------------------------------------------------
    # TASK 3: branch — choose yellow or green path
    # Equivalent to Kestra's `if_yellow_taxi` and `if_green_taxi` combined.
    # BranchPythonOperator calls `choose_branch()` which returns a task_id.
    # ----------------------------------------------------------
    t_branch = BranchPythonOperator(
        task_id='choose_taxi_branch',
        python_callable=choose_branch,
    )

    # ----------------------------------------------------------
    # YELLOW TAXI TASKS (4 tasks — same four-step pattern from Kestra)
    # Each uses BigQueryInsertJobOperator which runs a SQL query on BigQuery.
    #
    # BigQueryInsertJobOperator is the modern way to run BigQuery SQL in Airflow.
    # The `configuration` dict mirrors the BigQuery Jobs API format.
    # `gcp_conn_id` tells Airflow which GCP connection to use — this applies
    # to every BigQuery operator, and is the equivalent of pluginDefaults in Kestra.
    # ----------------------------------------------------------

    # Step 1 (Yellow): Create the main partitioned table if it doesn't exist
    t_yellow_create_table = BigQueryInsertJobOperator(
        task_id='bq_yellow_tripdata',       # This task_id is what choose_branch() returns!
        configuration={
            "query": {
                "query": sql_create_yellow_table(),  # Our SQL function from Section 4
                "useLegacySql": False,               # Always use Standard SQL, not Legacy SQL
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # Step 2 (Yellow): Create external table pointing at CSV in GCS
    # Note: sql_create_yellow_ext() needs year/month — we use Jinja templating here.
    # `{{ params.year }}` is Airflow's way of accessing DAG params in operator configs.
    t_yellow_ext = BigQueryInsertJobOperator(
        task_id='bq_yellow_table_ext',
        configuration={
            "query": {
                "query": "{{ task_instance.xcom_pull(task_ids='dummy_yellow_sql_ext') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # IMPORTANT NOTE ON DYNAMIC SQL:
    # Because our SQL needs the `year` and `month` params at runtime,
    # we use an intermediate PythonOperator to build the SQL string and
    # push it to XCom. The BigQueryInsertJobOperator then pulls it.
    # This is a common Airflow pattern for parameterised SQL.

    def build_yellow_ext_sql(**context):
        year  = context['params']['year']
        month = context['params']['month']
        sql   = sql_create_yellow_ext(year, month)
        context['ti'].xcom_push(key='return_value', value=sql)

    def build_yellow_tmp_sql(**context):
        year  = context['params']['year']
        month = context['params']['month']
        sql   = sql_create_yellow_tmp(year, month)
        context['ti'].xcom_push(key='return_value', value=sql)

    def build_yellow_merge_sql(**context):
        year  = context['params']['year']
        month = context['params']['month']
        sql   = sql_merge_yellow(year, month)
        context['ti'].xcom_push(key='return_value', value=sql)

    # Helper tasks that build SQL and push to XCom
    t_prep_yellow_ext   = PythonOperator(task_id='prep_yellow_ext_sql',   python_callable=build_yellow_ext_sql)
    t_prep_yellow_tmp   = PythonOperator(task_id='prep_yellow_tmp_sql',   python_callable=build_yellow_tmp_sql)
    t_prep_yellow_merge = PythonOperator(task_id='prep_yellow_merge_sql', python_callable=build_yellow_merge_sql)

    # Step 2 (Yellow): External table
    t_yellow_ext = BigQueryInsertJobOperator(
        task_id='bq_yellow_table_ext',
        configuration={
            "query": {
                # ti.xcom_pull pulls the SQL string built by the prep task above
                "query": "{{ ti.xcom_pull(task_ids='prep_yellow_ext_sql') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # Step 3 (Yellow): Temp table with MD5 hash
    t_yellow_tmp = BigQueryInsertJobOperator(
        task_id='bq_yellow_table_tmp',
        configuration={
            "query": {
                "query": "{{ ti.xcom_pull(task_ids='prep_yellow_tmp_sql') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # Step 4 (Yellow): MERGE into main table (idempotent upsert)
    t_yellow_merge = BigQueryInsertJobOperator(
        task_id='bq_yellow_merge',
        configuration={
            "query": {
                "query": "{{ ti.xcom_pull(task_ids='prep_yellow_merge_sql') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # ----------------------------------------------------------
    # GREEN TAXI TASKS (same four-step pattern, green version)
    # ----------------------------------------------------------

    def build_green_ext_sql(**context):
        year  = context['params']['year']
        month = context['params']['month']
        context['ti'].xcom_push(key='return_value', value=sql_create_green_ext(year, month))

    def build_green_tmp_sql(**context):
        year  = context['params']['year']
        month = context['params']['month']
        context['ti'].xcom_push(key='return_value', value=sql_create_green_tmp(year, month))

    def build_green_merge_sql(**context):
        year  = context['params']['year']
        month = context['params']['month']
        context['ti'].xcom_push(key='return_value', value=sql_merge_green(year, month))

    # Step 1 (Green): Create the main partitioned table if it doesn't exist
    t_green_create_table = BigQueryInsertJobOperator(
        task_id='bq_green_tripdata',        # This task_id is what choose_branch() returns!
        configuration={
            "query": {
                "query": sql_create_green_table(),
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    t_prep_green_ext   = PythonOperator(task_id='prep_green_ext_sql',   python_callable=build_green_ext_sql)
    t_prep_green_tmp   = PythonOperator(task_id='prep_green_tmp_sql',   python_callable=build_green_tmp_sql)
    t_prep_green_merge = PythonOperator(task_id='prep_green_merge_sql', python_callable=build_green_merge_sql)

    # Step 2 (Green): External table
    t_green_ext = BigQueryInsertJobOperator(
        task_id='bq_green_table_ext',
        configuration={
            "query": {
                "query": "{{ ti.xcom_pull(task_ids='prep_green_ext_sql') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # Step 3 (Green): Temp table with MD5 hash
    t_green_tmp = BigQueryInsertJobOperator(
        task_id='bq_green_table_tmp',
        configuration={
            "query": {
                "query": "{{ ti.xcom_pull(task_ids='prep_green_tmp_sql') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # Step 4 (Green): MERGE into main table (idempotent upsert)
    t_green_merge = BigQueryInsertJobOperator(
        task_id='bq_green_merge',
        configuration={
            "query": {
                "query": "{{ ti.xcom_pull(task_ids='prep_green_merge_sql') }}",
                "useLegacySql": False,
            }
        },
        location=GCP_LOCATION,
        project_id=GCP_PROJECT_ID,
        gcp_conn_id=GCP_CONN_ID,
    )

    # ----------------------------------------------------------
    # JOIN TASK
    # After both branches complete, we need a common "done" task.
    # This is because Airflow requires branches to merge back.
    # EmptyOperator does nothing — it's just a structural anchor.
    # trigger_rule='none_failed_min_one_success' means:
    #   "run this task as long as at least one upstream path succeeded
    #    and none failed" — perfect for joining after a branch.
    # ----------------------------------------------------------
    from airflow.utils.trigger_rule import TriggerRule

    t_done = EmptyOperator(
        task_id='pipeline_complete',
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # ==========================================================
    # TASK DEPENDENCIES — The Pipeline's Wiring
    # This is the most important section. The >> operator means
    # "this task runs BEFORE that task". It's how you draw the
    # arrows in the DAG flowchart.
    #
    # This is equivalent to Kestra's sequential task ordering
    # (Kestra tasks run top-to-bottom by default).
    # ==========================================================

    # Phase 1: Download → Upload (runs for both yellow and green)
    t_download >> t_upload

    # Phase 2: After upload, decide which branch to take
    t_upload >> t_branch

    # Phase 3a: Yellow branch — 4 steps in sequence
    t_branch >> t_yellow_create_table
    t_yellow_create_table >> t_prep_yellow_ext >> t_yellow_ext
    t_yellow_ext >> t_prep_yellow_tmp >> t_yellow_tmp
    t_yellow_tmp >> t_prep_yellow_merge >> t_yellow_merge
    t_yellow_merge >> t_done

    # Phase 3b: Green branch — 4 steps in sequence
    t_branch >> t_green_create_table
    t_green_create_table >> t_prep_green_ext >> t_green_ext
    t_green_ext >> t_prep_green_tmp >> t_green_tmp
    t_green_tmp >> t_prep_green_merge >> t_green_merge
    t_green_merge >> t_done
```

---

## 7. Running and Monitoring Your DAG

### Step 7.1 — Place the DAG File

Save your complete DAG file to:
```
~/airflow/dags/gcp_taxi_pipeline.py
```

The Airflow Scheduler scans this folder every 30 seconds by default. You'll see your DAG appear in the UI shortly.

### Step 7.2 — Trigger the DAG Manually

Since `schedule_interval=None`, this DAG only runs when you trigger it manually.

In the Airflow UI:
1. Find `gcp_taxi_pipeline` in the DAG list
2. Click the **▶ Trigger DAG** button (the play icon)
3. A panel opens where you can fill in the **Params** (taxi, year, month) — these are your Kestra-style inputs
4. Click **Trigger**

### Step 7.3 — Monitor the Run

Click on the DAG name → **Graph** view. You'll see your tasks as boxes with coloured status indicators:

| Colour | Meaning |
|---|---|
| 🟢 Green | Success |
| 🔴 Red | Failed |
| 🟡 Yellow | Running |
| ⬜ Grey | Skipped (the branch not taken) |
| 🔵 Blue | Queued |

Click any task box → **Log** to see the detailed output — equivalent to clicking on a task execution in Kestra.

### Step 7.4 — Checking XCom Values

To debug XCom values passed between tasks: click a task box → **XCom** tab. You'll see all the key-value pairs that task pushed.

### Step 7.5 — Rerunning a Failed Task

If a task fails, you can rerun just that task without rerunning the whole pipeline. Click the failed task → **Clear** → Confirm. Airflow will rerun it from that point forward.

---

## 8. Kestra vs. Airflow Cheat Sheet

### Concept Translation

| Kestra Concept | Kestra Syntax | Airflow Equivalent |
|---|---|---|
| Flow identity | `id: my_flow` | `dag_id='my_flow'` |
| Description | `description: \|` | `description='...'` in DAG() |
| User inputs | `inputs: - id: taxi type: SELECT` | `params={'taxi': 'green'}` in DAG() |
| Non-secret config | `kv('GCP_PROJECT_ID')` | `Variable.get('GCP_PROJECT_ID')` |
| Credentials/secrets | `secret('GCP_SERVICE_ACCOUNT')` | Airflow Connection (`gcp_conn_id`) |
| Shared plugin config | `pluginDefaults:` | Pass `gcp_conn_id` to each operator |
| A task | `- id: my_task type: io.kestra...` | An Operator instance |
| HTTP download | `io.kestra.plugin.core.http.Download` | `requests.get()` in PythonOperator |
| Decompress | `io.kestra.plugin.compress.FileDecompress` | `gzip.open()` in PythonOperator |
| GCS upload | `io.kestra.plugin.gcp.gcs.Upload` | `GCSHook.upload()` in PythonOperator |
| Run BigQuery SQL | `io.kestra.plugin.gcp.bigquery.Query` | `BigQueryInsertJobOperator` |
| If/conditional | `io.kestra.plugin.core.flow.If` | `BranchPythonOperator` |
| Passing data between tasks | `outputs.task_id.uri` | `XCom` (push/pull) |
| Template expressions | `{{inputs.taxi}}` | `{{ params.taxi }}` (Jinja) |
| Task ordering | Top-to-bottom YAML order | `>>` operator (`task_a >> task_b`) |
| Cleanup | `PurgeCurrentExecutionFiles` | `os.remove()` in PythonOperator |

### Operator Quick Reference

| What you want to do | Operator to use | Import from |
|---|---|---|
| Run a Python function | `PythonOperator` | `airflow.operators.python` |
| Branch based on a condition | `BranchPythonOperator` | `airflow.operators.python` |
| Run a BigQuery SQL query | `BigQueryInsertJobOperator` | `airflow.providers.google.cloud.operators.bigquery` |
| Upload a file to GCS | `GCSHook` inside PythonOperator | `airflow.providers.google.cloud.hooks.gcs` |
| Do nothing (join/anchor) | `EmptyOperator` | `airflow.operators.empty` |
| Run a bash command | `BashOperator` | `airflow.operators.bash` |

### The `>>` Dependency Operator

```python
# Task A must finish before Task B starts
task_a >> task_b

# Task A must finish before both B and C start (parallel)
task_a >> [task_b, task_c]

# Both A and B must finish before C starts
[task_a, task_b] >> task_c

# A full chain
task_a >> task_b >> task_c >> task_d
```

---

> **Key Takeaway:** Airflow is more verbose than Kestra because you write Python code instead of YAML. But this gives you complete control — any Python library, any logic, any data transformation is available to you. The trade-off is that you need to understand Python well, manage your own imports, and explicitly wire up your task dependencies with `>>`.
