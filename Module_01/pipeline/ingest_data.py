#!/usr/bin/env python
# coding: utf-8

# In[1]:


print("Notebook is working!")


# In[2]:


import pandas as pd


# In[3]:


# Read a sample of the data
prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
df = pd.read_csv(prefix + 'yellow_tripdata_2021-01.csv.gz', nrows=100)


# In[4]:


# Display first rows
df.head()


# In[5]:


# Check data types
df.dtypes


# In[6]:


# Check data shape
df.shape


# In[7]:


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

df = pd.read_csv(
    prefix + 'yellow_tripdata_2021-01.csv.gz',
    nrows=100,
    dtype=dtype,
    parse_dates=parse_dates
)


# In[8]:


df.head(10)


# In the Jupyter notebook, we created code to:
# 
# - Download the CSV file
# - Read it in chunks with pandas
# - Convert datetime columns
# - Insert data into PostgreSQL using SQLAlchemy

# In[9]:


import sys
print(sys.executable)


# In[10]:


from sqlalchemy import create_engine


# In[11]:


engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')


# ## Getting the DDL Schema
# 

# In[12]:


connection = engine.connect()


# In[16]:


#  Getting the DDL Schema

# The code returns a script that creates a table called "yellow_taxi_data" from
# ... our dataframe using the postgres engine created earlier. It doesnt actually create the table

print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))


# ## Creating the Table

# In[15]:


df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')


# ## Ingesting Data in Chunks

# In[17]:


df_iter = pd.read_csv(
    prefix + 'yellow_tripdata_2021-01.csv.gz',
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=100000
)


# In[18]:


# Iterate over the chunks

for df_chunk in df_iter:
    print(len(df_chunk))


# In[20]:


# Inserting Data

for df_chunk in df_iter:
    print(len(df_chunk))
    df_chunk.to_sql(name='yellow_taxi_data', 
                    con=engine,
                    if_exists='append')


# ##  Complete Ingestion Loop

# In[ ]:


first = True

for df_chunk in df_iter:

    if first:
        # Create table schema (no data)
        df_chunk.head(0).to_sql(
            name="yellow_taxi_data",
            con=engine,
            if_exists="replace"
        )
        first = False
        print("Table created")

    # Insert chunk
    df_chunk.to_sql(
        name="yellow_taxi_data",
        con=engine,
        if_exists="append"
    )

    print("Inserted:", len(df_chunk))

