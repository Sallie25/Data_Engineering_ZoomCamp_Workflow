FROM python:3.13.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /code
ENV PATH="/code/.venv/bin:$PATH"

COPY pyproject.toml .python-version uv.lock ./
RUN uv sync --locked

COPY pipeline/complete_ingest_data.py .

ENTRYPOINT ["uv", "run", "python", "complete_ingest_data.py"]



# # Start with slim Python 3.13 image
# FROM python:3.13.10-slim

# # Copy uv binary from official uv image (multi-stage build pattern)
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# # Set working directory
# WORKDIR /app

# # Add virtual environment to PATH so we can use installed packages
# ENV PATH="/app/.venv/bin:$PATH"

# # Copy dependency files first (better layer caching)
# COPY "pyproject.toml" "uv.lock" ".python-version" ./
# # Install dependencies from lock file (ensures reproducible builds)
# RUN uv sync --locked

# # Copy application code
# COPY pipeline/pipeline.py pipeline.py

# # Set entry point
# ENTRYPOINT ["uv", "run", "python", "pipeline.py"]



# # Base docker image
# FROM python:3.13.11-slim

# # Setting up my image by installing Prerequisites
# RUN pip install pandas pyarrow

# # Setting up the working directory inside the container
# WORKDIR /app

# # Copying the script to the container. 1st name is source file, 2nd is destination
# COPY pipeline/pipeline.py pipeline.py

# # Defining what to do first when the container runs
# # In this example, we will just run the script
# ENTRYPOINT ["python", "pipeline.py"]
