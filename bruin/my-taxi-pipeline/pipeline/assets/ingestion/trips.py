"""@bruin
name: ingestion.trips
type: python
image: python:3.11
connection: duckdb-default

materialization:
  type: table
  strategy: append

columns:
  - name: pickup_datetime
    type: timestamp
    description: "When the meter was engaged"
  - name: dropoff_datetime
    type: timestamp
    description: "When the meter was disengaged"
  - name: vendor_id
    type: integer
    description: "TPEP provider code"
  - name: passenger_count
    type: integer
    description: "Number of passengers in the vehicle"
  - name: trip_distance
    type: float
    description: "Elapsed trip distance in miles"
  - name: fare_amount
    type: float
    description: "Time-and-distance fare calculated by the meter"
@bruin"""

import os
import json
import pandas as pd

def materialize():
    # 1. RETRIEVE PARAMETERS INJECTED BY BRUIN
    # Start and End dates are standard environment variables in Bruin
    start_date = os.environ["BRUIN_START_DATE"]
    end_date = os.environ["BRUIN_END_DATE"]
    
    # Custom variables are packed into a JSON string inside BRUIN_VARS
    vars_dict = json.loads(os.environ["BRUIN_VARS"])
    taxi_types = vars_dict.get("taxi_types", ["yellow"])

    # 2. PREPARE THE DATE PARAMETERS
    # We extract year and month to build the filename (e.g., 2023-01)
    year = start_date[:4]
    month = start_date[5:7]
    
    all_data = []
    
    # 3. LOOP THROUGH TAXI TYPES AND FETCH DATA
    for taxi in taxi_types:
        # Building the URL for the NYC Taxi Data (hosted on Cloudfront)
        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{taxi}_tripdata_{year}-{month}.parquet"
        
        print(f"Fetching {taxi} taxi data for {year}-{month} from: {url}")
        
        try:
            # pandas reads the remote parquet file directly from the URL
            df = pd.read_parquet(url)
            
            # Optional: add a column to identify the taxi type
            df['taxi_type'] = taxi
            
            all_data.append(df)
        except Exception as e:
            print(f"Error downloading data for {taxi}: {e}")

    # 4. CONSOLIDATE AND RETURN THE RESULTS
    if not all_data:
      # If downloads fail, return empty dataframe with expected schema to avoid failing downstream
      expected_cols = [
        'pickup_datetime', 'dropoff_datetime', 'tpep_pickup_datetime', 'tpep_dropoff_datetime',
        'vendor_id', 'passenger_count', 'trip_distance', 'fare_amount', 'payment_type', 'taxi_type',
        'extracted_at', 'pickup_locationid', 'dropoff_locationid'
      ]
      empty = pd.DataFrame({c: pd.Series(dtype='float') for c in expected_cols})
      return empty

    # Combine all individual dataframes into one large table
    final_dataframe = pd.concat(all_data, ignore_index=True)

    # Normalize common column names so downstream SQL can rely on a stable schema
    col_map = {}
    # If raw data uses tpep_* timestamp names, map them to friendly names and back
    if 'tpep_pickup_datetime' in final_dataframe.columns:
      col_map['tpep_pickup_datetime'] = 'tpep_pickup_datetime'
      if 'pickup_datetime' not in final_dataframe.columns:
        final_dataframe['pickup_datetime'] = final_dataframe['tpep_pickup_datetime']
    if 'tpep_dropoff_datetime' in final_dataframe.columns:
      col_map['tpep_dropoff_datetime'] = 'tpep_dropoff_datetime'
      if 'dropoff_datetime' not in final_dataframe.columns:
        final_dataframe['dropoff_datetime'] = final_dataframe['tpep_dropoff_datetime']
    if 'pickup_datetime' in final_dataframe.columns and 'tpep_pickup_datetime' not in final_dataframe.columns:
      final_dataframe['tpep_pickup_datetime'] = final_dataframe['pickup_datetime']
    if 'dropoff_datetime' in final_dataframe.columns and 'tpep_dropoff_datetime' not in final_dataframe.columns:
      final_dataframe['tpep_dropoff_datetime'] = final_dataframe['dropoff_datetime']

    # Location id aliases
    for src in ('PULocationID', 'pu_location_id', 'pickup_location_id', 'pickup_locationid'):
      if src in final_dataframe.columns:
        final_dataframe['pickup_locationid'] = final_dataframe[src]
        final_dataframe['pickup_location_id'] = final_dataframe[src]
        break
    for src in ('DOLocationID', 'do_location_id', 'dropoff_location_id', 'dropoff_locationid'):
      if src in final_dataframe.columns:
        final_dataframe['dropoff_locationid'] = final_dataframe[src]
        final_dataframe['dropoff_location_id'] = final_dataframe[src]
        break

    # Ensure the common columns exist even if source omitted them
    for col in ('vendor_id', 'passenger_count', 'trip_distance', 'fare_amount', 'payment_type', 'taxi_type'):
      if col not in final_dataframe.columns:
        final_dataframe[col] = pd.Series(dtype='float')

    return final_dataframe