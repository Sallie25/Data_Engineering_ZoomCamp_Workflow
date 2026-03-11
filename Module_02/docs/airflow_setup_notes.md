# 🌀 Apache Airflow — Simple Notes
*A plain-English breakdown for beginners*

---

## 💡 What is Apache Airflow?

Airflow is a tool that lets you automate and schedule workflows — basically, it runs tasks in the right order at the right time. Think of it like a smart alarm clock that also knows what to do after it wakes you up.

---

## 🤔 Why isn't it just ONE container?

Unlike a simple app, Airflow has multiple jobs to do at once — it needs to:

- Show you a website (the dashboard)
- Watch for scheduled tasks and run them
- Remember everything using a database
- Set itself up the first time

That's why it needs multiple containers working together.

---

## 🧱 The 4 Components You Need

### 🖥️ 1. Airflow Webserver
The visual dashboard — the website you open in your browser to see what's running, what failed, and what's scheduled. Without this, you'd have no way to see anything.

### ⏰ 2. Airflow Scheduler
The brain. It watches the clock and says "Okay, it's time to run Task A!" It constantly checks what needs to run and triggers it. Without this, nothing ever actually runs.

### 🗄️ 3. Airflow Metadata Database (Postgres)
Airflow's memory. It stores everything — task history, logs, DAG definitions, users, and settings. Postgres is the most common database used here. Without this, Airflow has no memory and can't function.

### 🚀 4. Airflow Init Container
This only runs **once** at the start. It sets up the database tables, creates default users, and makes sure everything is ready to go. After setup, it stops — it's done its job.

---

## 🍕 Think of it Like a Restaurant

| Airflow Part | Restaurant Equivalent |
|---|---|
| Webserver | The menu board & front of house — what you see |
| Scheduler | The head chef — decides what gets cooked and when |
| Postgres Database | The order book — remembers every order ever made |
| Init Container | Opening day setup crew — sets the kitchen up once |

---

## 🐳 The Docker Compose File

Copy this into a file called `docker-compose.yml` and run: `docker compose up -d`

```yaml
# ──────────────────────────────────────
#  Apache Airflow — Minimal Setup
# ──────────────────────────────────────

version: '3.8'

x-airflow-common:  # Reusable config block
  &airflow-common
  image: apache/airflow:2.9.1
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
  volumes:
    - ./dags:/opt/airflow/dags    # your DAG files go here
    - ./logs:/opt/airflow/logs
  depends_on:
    postgres:
      condition: service_healthy

services:

  # ── 1. DATABASE ─────────────────────
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_data:/var/lib/postgresql
    healthcheck:
      test: ['CMD', 'pg_isready', '-U', 'airflow']
      interval: 5s
      retries: 5

  # ── 2. INIT (runs once, then exits) ──
  airflow-init:
    <<: *airflow-common
    command: >
      bash -c "airflow db init &&
      airflow users create --username admin
      --password admin --firstname Admin
      --lastname User --role Admin
      --email admin@example.com"
    restart: on-failure

  # ── 3. SCHEDULER ─────────────────────
  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    restart: always
    depends_on:
      airflow-init:
        condition: service_completed_successfully

  # ── 4. WEBSERVER ─────────────────────
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
  postgres_data:
```

---

## 🔍 What Each Part Does

| Section | Plain English Explanation |
|---|---|
| `x-airflow-common` | A reusable block of settings shared by all Airflow containers. The `&airflow-common` / `<<: *airflow-common` syntax avoids repeating the same config 3 times. |
| `AIRFLOW__CORE__EXECUTOR: LocalExecutor` | Tells Airflow to run tasks locally (in the same container). Good for simple setups. For scale, you'd switch to CeleryExecutor. |
| `SQL_ALCHEMY_CONN` | Tells Airflow where the database is. It points to the postgres service using the credentials you set. |
| `volumes: ./dags` | Maps a local `dags/` folder into the container. Put your workflow files here — Airflow will pick them up automatically. |
| `healthcheck (postgres)` | Docker will wait until Postgres is actually ready before starting Airflow. Without this, Airflow might crash on startup. |
| `airflow-init command` | Runs two things: sets up the DB tables (`db init`) and creates an admin login (admin/admin). It exits when done. |
| `restart: always` | If the scheduler or webserver crashes, Docker will automatically restart it. |
| `ports: 8080:8080` | Exposes the Airflow dashboard on your machine at http://localhost:8080 |
| `service_completed_successfully` | Scheduler and webserver wait for airflow-init to fully finish before they start. Order matters! |

---

## ▶️ How to Run It

1. Create a folder: `mkdir airflow-project && cd airflow-project`
2. Create subfolders: `mkdir dags logs`
3. Save the compose file above as: `docker-compose.yml`
4. Start everything: `docker compose up -d`
5. Wait ~30 seconds for init to finish
6. Open your browser at: http://localhost:8080
7. Login with: **username:** `admin` / **password:** `admin`

---

## ⚙️ Understanding Key Environment Variables

### 🔐 AIRFLOW__CORE__FERNET_KEY
A secret encryption key Airflow uses to encrypt sensitive data in the database — things like passwords and connection strings. Set to `''` (empty) here, which disables encryption. Fine for local testing, but in production you should generate a real key:

```python
from cryptography.fernet import Fernet
Fernet.generate_key()
```

### ⏸️ AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION
When set to `'true'`, any new DAG (workflow) you add won't automatically start running — it stays paused until you manually switch it on in the dashboard. This is a safety net so dropping a new file into your `dags/` folder doesn't trigger it unexpectedly. Keep this `'true'` as a good default.

### 📂 AIRFLOW__CORE__LOAD_EXAMPLES
Airflow ships with a bunch of built-in example DAGs to demonstrate features. Setting this to `'false'` hides them so your dashboard only shows your actual workflows. Almost always set this to `'false'` once you know what you're doing — otherwise your DAG list gets cluttered with demos you don't need.

---

### 💡 The Naming Pattern

All Airflow environment variables follow the same structure:

```
AIRFLOW__[SECTION]__[SETTING_NAME]
```

Double underscores (`__`) separate each part. So `AIRFLOW__CORE__LOAD_EXAMPLES` means: in the `[core]` section of Airflow's config file, the `load_examples` setting. Once you see the pattern, every setting becomes readable.

---

> ✅ **Key Takeaway:** You NEED all 4 pieces for Airflow to work. Remove any one of them and the whole thing breaks. That's why Airflow setups always look bigger than you expect — each container has a specific job it can't share with the others.
