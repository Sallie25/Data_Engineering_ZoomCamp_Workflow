FROM python:3.11

RUN pip install \
    pandas \
    click \
    sqlalchemy \
    tqdm \
    psycopg2-binary \
    requests

COPY 01_simple_postgres_pipeline.py .

ENTRYPOINT ["python", "01_simple_postgres_pipeline.py"]