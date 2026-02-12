import pandas as pd
import click
from sqlalchemy import create_engine
from tqdm.auto import tqdm

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

@click.command()
@click.option('--year', default=2021, type=int, help='Year for the taxi data.')
@click.option('--month', default=1, type=int, help='Month for the taxi data.')
@click.option('--pg_user', default='root', help='PostgreSQL user.')
@click.option('--pg_pass', default='root', help='PostgreSQL password.')
@click.option('--pg_host', default='localhost', help='PostgreSQL host.')
@click.option('--pg_port', default=5432, type=int, help='PostgreSQL port.')
@click.option('--pg_db', default='ny_taxi', help='PostgreSQL database name.')
@click.option('--target_table', default='yellow_taxi_data', help='Name of the target table in PostgreSQL.')
@click.option('--zone_table', default='taxi_zone_lookup', help='Name of the taxi zone lookup table in PostgreSQL.')
@click.option('--chunksize', default=100000, type=int, help='Size of chunks to read from CSV.')
def run(year, month, pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, zone_table, chunksize):
    print('started')

    engine = create_engine(f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')
    print('engine created')

    # --- Ingest yellow taxi trip data ---
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download'
    url = f'{prefix}/yellow/yellow_tripdata_{year}-{month:02d}.csv.gz'

    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize
    )

    first = True
    for df_chunk in tqdm(df_iter):
        if first:
            df_chunk.head(0).to_sql(
                name=target_table,
                con=engine, 
                if_exists='replace'
            )
            first = False
            
        df_chunk.to_sql(
            name=target_table, 
            con=engine, 
            if_exists='append'
        )

    print('yellow taxi data ingested')

    # --- Ingest taxi zone lookup data ---
    zone_url = f'{prefix}/misc/taxi_zone_lookup.csv'
    df_zone = pd.read_csv(zone_url)

    df_zone.to_sql(
        name=zone_table,
        con=engine,
        if_exists='replace',
        index=False
    )

    print('taxi zone lookup ingested')

if __name__ == '__main__':
    run()
