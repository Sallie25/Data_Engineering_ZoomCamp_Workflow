# Kestra GCP Taxi Pipeline — Complete Explanation

> A line-by-line breakdown of `08_gcp_taxi` for someone who needs to understand and replicate it from memory.

---

## 🏷️ Flow Identity (Top 3 Lines)

```yaml
id: 08_gcp_taxi
namespace: zoomcamp
description: |
  The CSV Data used in the course: https://github.com/DataTalksClub/nyc-tlc-data/releases
```

- **`id`**: The unique name of this flow within Kestra. Think of it like a function name.
- **`namespace`**: The folder/group this flow belongs to. `zoomcamp` is like a project folder. Kestra uses namespaces to organise flows and share KV store values.
- **`description`**: A human-readable note. The `|` means the text continues on the next line as a multi-line string. This is just documentation — it doesn't execute anything.

---

## 🎛️ Inputs (User-Facing Controls)

Inputs in Kestra are strongly typed and validated before the flow starts. The `SELECT` type renders as a dropdown in the UI. If `allowCustomValue: true`, the user can also type a value not in the list.

```yaml
inputs:
  - id: taxi
    type: SELECT
    displayName: Select taxi type
    values: [yellow, green]
    defaults: green
```

Creates a dropdown for taxi type. Defaults to `green` if nothing is selected. Referenced throughout the flow as `{{inputs.taxi}}`.

```yaml
  - id: year
    type: SELECT
    displayName: Select year
    values: ["2019", "2020"]
    defaults: "2019"
    allowCustomValue: true
```

Dropdown for year. Values are quoted strings (not integers) because they'll be used in filenames. `allowCustomValue: true` lets a user type `2021` manually. Referenced as `{{inputs.year}}`.

```yaml
  - id: month
    type: SELECT
    displayName: Select month
    values: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    defaults: "01"
```

Dropdown for month, zero-padded (e.g. `"01"`, `"09"`) so they format correctly in filenames. Referenced as `{{inputs.month}}`.

---

## 📦 Variables (Reusable Computed Values)

Variables are key-value pairs that let you reuse values across tasks using `{{ vars.variable_name }}`. They are computed once and referenced many times.

```yaml
variables:
  file: "{{inputs.taxi}}_tripdata_{{inputs.year}}-{{inputs.month}}.csv"
```

Dynamically builds the CSV filename. For `green`, `2019`, `01` this becomes `green_tripdata_2019-01.csv`. The `{{ }}` syntax is Kestra's **Pebble templating engine** — it substitutes values at runtime.

```yaml
  gcs_file: "gs://{{kv('GCP_BUCKET_NAME')}}/{{vars.file}}"
```

The `kv()` function retrieves a value from Kestra's **KV Store** by key name. So `kv('GCP_BUCKET_NAME')` fetches your stored bucket name (e.g. `my-project-bucket`). The full path becomes something like `gs://my-project-bucket/green_tripdata_2019-01.csv`.

> **Note:** Because this variable itself references `{{vars.file}}` (another variable), you must wrap it in `render()` when using it in tasks — explained below.

```yaml
  table: "{{kv('GCP_DATASET')}}.{{inputs.taxi}}_tripdata_{{inputs.year}}_{{inputs.month}}"
```

Builds a BigQuery table name like `my_dataset.green_tripdata_2019_01`. Uses `kv()` to fetch the dataset name from the KV store.

```yaml
  # data: "{{outputs.extract.outputFiles[inputs.taxi ~ '_tripdata_' ~ inputs.year ~ '-' ~ inputs.month ~ '.csv']}}"
```

This line is **commented out** (starts with `#`) — kept for reference but disabled. The `~` operator in Pebble is string concatenation.

---

## ✅ Tasks (The Actual Pipeline Steps)

Tasks are the most important part of a flow. They run **sequentially** by default. Every task needs at minimum an `id` and a `type`. The `type` is the full Java class name of the Kestra plugin being used.

---

### Task 1: `set_label`

```yaml
  - id: set_label
    type: io.kestra.plugin.core.execution.Labels
    labels:
      file: "{{render(vars.file)}}"
      taxi: "{{inputs.taxi}}"
```

Tags the execution with metadata labels so you can search and filter runs in the Kestra UI.

**Why `render(vars.file)` and not just `vars.file`?**
The `render()` function is required when a variable itself contains Pebble expressions (`{{ }}`). Without it, Kestra returns the raw string `"{{inputs.taxi}}_tripdata_..."` instead of the resolved value `"green_tripdata_2019-01.csv"`. Think of `render()` as "evaluate this variable's template too".

---

### Task 2: `download_gzip`

```yaml
  - id: download_gzip
    type: io.kestra.plugin.core.http.Download
    uri: https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{{inputs.taxi}}/{{render(vars.file)}}.gz
```

Uses the built-in HTTP Download plugin to download a `.gz` (gzip-compressed CSV) from GitHub. The URI is built dynamically — e.g. it resolves to `.../download/green/green_tripdata_2019-01.csv.gz`. The downloaded file is stored in Kestra's internal storage and available to later tasks as `outputs.download_gzip.uri`.

---

### Task 3: `decompress`

```yaml
  - id: decompress
    type: io.kestra.plugin.compress.FileDecompress
    from: "{{ outputs.download_gzip.uri }}"
    compression: GZIP
```

Takes the `.gz` file from the previous step (referenced via `outputs.download_gzip.uri`) and decompresses it into a plain `.csv`.

> This is the standard Kestra pattern: **each task's output becomes the next task's input** via `outputs.<task_id>.<output_name>`.

The result is available as `outputs.decompress.uri`.

---

### Task 4: `upload_to_gcs`

```yaml
  - id: upload_to_gcs
    type: io.kestra.plugin.gcp.gcs.Upload
    from: "{{ outputs.decompress.uri }}"
    to: "{{render(vars.gcs_file)}}"
```

Uploads the decompressed CSV to **Google Cloud Storage (GCS)**. `from` is the local Kestra-internal file from the previous step. `to` is the destination GCS path — `render()` is needed here because `vars.gcs_file` contains a nested reference to `vars.file`.

---

### Task 5: `if_yellow_taxi` — Conditional Branch

```yaml
  - id: if_yellow_taxi
    type: io.kestra.plugin.core.flow.If
    condition: "{{inputs.taxi == 'yellow'}}"
    then:
      ...
```

A conditional block. If the user chose `yellow`, execute the sub-tasks inside `then:`. Otherwise, skip entirely. This is Kestra's equivalent of an `if` statement.

Inside this block, **four sub-tasks** run in sequence:

---

#### `bq_yellow_tripdata` — Create the main table

```sql
CREATE TABLE IF NOT EXISTS `project.dataset.yellow_tripdata` (...)
PARTITION BY DATE(tpep_pickup_datetime);
```

Creates the main partitioned BigQuery table **if it doesn't already exist**. Partitioned by pickup date, which makes date-filtered queries significantly faster and cheaper. Includes a `unique_row_id` (bytes/hash) column and a `filename` column alongside all standard trip fields.

---

#### `bq_yellow_table_ext` — Create the external table

```sql
CREATE OR REPLACE EXTERNAL TABLE `project.dataset.yellow_tripdata_YYYY_MM_ext` (...)
OPTIONS (format = 'CSV', uris = ['gs://bucket/file.csv'], skip_leading_rows = 1, ignore_unknown_values = TRUE);
```

Creates an **external table** in BigQuery pointing directly at the CSV in GCS. BigQuery reads the data on-demand without copying it. `skip_leading_rows = 1` skips the CSV header row. `ignore_unknown_values = TRUE` tolerates unexpected columns. The `_ext` suffix distinguishes this as the staging/external table.

---

#### `bq_yellow_table_tmp` — Create the temp table with hash ID

```sql
CREATE OR REPLACE TABLE `project.dataset.yellow_tripdata_YYYY_MM` AS
SELECT
  MD5(CONCAT(
    COALESCE(CAST(VendorID AS STRING), ""),
    COALESCE(CAST(tpep_pickup_datetime AS STRING), ""),
    ...
  )) AS unique_row_id,
  "green_tripdata_2019-01.csv" AS filename,
  *
FROM `...yellow_tripdata_YYYY_MM_ext`;
```

Creates a real (non-external) temporary BigQuery table from the external one. Critically, it **generates the `unique_row_id`** using `MD5(CONCAT(...))` — a hash fingerprint of VendorID, pickup/dropoff datetimes, and location IDs. `COALESCE(..., "")` handles NULLs gracefully so the hash is always consistent. The `filename` column records which source file the row came from.

---

#### `bq_yellow_merge` — Upsert into the main table

```sql
MERGE INTO `project.dataset.yellow_tripdata` T
USING `project.dataset.yellow_tripdata_YYYY_MM` S
ON T.unique_row_id = S.unique_row_id
WHEN NOT MATCHED THEN
  INSERT (...) VALUES (...);
```

Performs a **MERGE (upsert)** operation. Compares the temp table against the main `yellow_tripdata` table using `unique_row_id`. If a row from the temp table doesn't already exist in the main table (`WHEN NOT MATCHED`), it inserts it. This makes the pipeline **idempotent** — you can run it multiple times without creating duplicate rows.

---

### Task 6: `if_green_taxi` — The Green Taxi Branch

```yaml
  - id: if_green_taxi
    type: io.kestra.plugin.core.flow.If
    condition: "{{inputs.taxi == 'green'}}"
    then:
      ...
```

Identical structure to the yellow taxi block, but for green taxis. Key differences:

| Aspect | Yellow | Green |
|---|---|---|
| Datetime columns | `tpep_pickup_datetime`, `tpep_dropoff_datetime` | `lpep_pickup_datetime`, `lpep_dropoff_datetime` |
| Extra columns | — | `ehail_fee`, `trip_type` |
| Partition column | `tpep_pickup_datetime` | `lpep_pickup_datetime` |

Everything else follows the same four-step pattern: **create table → external table → temp table with hash → merge**.

---

### Task 7: `purge_files`

```yaml
  - id: purge_files
    type: io.kestra.plugin.core.storage.PurgeCurrentExecutionFiles
    description: If you'd like to explore Kestra outputs, disable it.
    disabled: false
```

Cleans up all intermediate files (the downloaded `.gz`, the decompressed `.csv`) from Kestra's internal storage once the flow finishes. Keeps storage tidy. Set `disabled: true` if you want to inspect those intermediate files for debugging.

---

## 🔧 Plugin Defaults (Shared Configuration)

```yaml
pluginDefaults:
  - type: io.kestra.plugin.gcp
    values:
      serviceAccount: "{{secret('GCP_SERVICE_ACCOUNT')}}"
      projectId: "{{kv('GCP_PROJECT_ID')}}"
      location: "{{kv('GCP_LOCATION')}}"
      bucket: "{{kv('GCP_BUCKET_NAME')}}"
```

Plugin defaults are default values applied to **every task of a given type** within the flow. The prefix `io.kestra.plugin.gcp` means these defaults apply to all GCP tasks — the GCS Upload and all BigQuery queries. Instead of repeating credentials in every task, you define them once here.

- **`secret()`** — Retrieves sensitive values stored securely in Kestra's secret backend. `secret('GCP_SERVICE_ACCOUNT')` fetches your GCP service account JSON key. Secrets are encrypted — never hard-code them in your YAML.
- **`kv()`** — Retrieves less-sensitive config values from Kestra's KV store, reusable across flows in the same namespace.

---

## 🧠 Mental Model for Exam Day

When writing this from scratch, remember this top-to-bottom structure:

| Section | Purpose | Key Syntax |
|---|---|---|
| `id` / `namespace` / `description` | Identity & location of the flow | Plain strings |
| `inputs` | What the user controls (dropdowns) | `type: SELECT`, `values:`, `defaults:` |
| `variables` | Shorthand names computed once, reused everywhere | `{{inputs.x}}`, `kv('KEY')` |
| `tasks` | What the flow actually does, in order | `id:`, `type:`, `outputs.<id>.uri` |
| `pluginDefaults` | Shared config across all tasks of the same plugin type | `type: io.kestra.plugin.gcp` |

### Key Functions to Remember

| Function | What it does |
|---|---|
| `{{inputs.x}}` | Gets a user-provided input value |
| `{{vars.x}}` | Gets a variable defined in the `variables` section |
| `{{render(vars.x)}}` | Gets a variable AND evaluates any `{{ }}` expressions inside it |
| `{{kv('KEY')}}` | Fetches a value from the KV Store (non-sensitive config) |
| `{{secret('KEY')}}` | Fetches a value from the Secrets backend (sensitive credentials) |
| `{{outputs.task_id.uri}}` | Gets a file output from a previous task |

### The Four-Step BigQuery Pattern

Every time new data arrives, this pipeline does the same four things:

```
1. CREATE TABLE IF NOT EXISTS  →  Ensures the main table exists (partitioned)
2. CREATE EXTERNAL TABLE       →  Points BigQuery at the CSV in GCS
3. CREATE TABLE AS SELECT      →  Copies data + adds MD5 hash ID + filename
4. MERGE INTO                  →  Inserts only new rows (idempotent upsert)
```

> The `render()` function is your single most important thing to remember. Any variable that contains `{{ }}` inside it **must** be wrapped in `render()` when used in a task, otherwise Kestra returns the literal template string instead of the resolved value.
