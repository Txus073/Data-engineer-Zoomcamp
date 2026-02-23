"""@bruin

name: ingestion.trips

type: python

image: python:3.11

connection: duckdb-default

materialization:
  type: table
  strategy: append

columns:
  - name: tpep_pickup_datetime
    type: timestamp
    primary_key: true
  - name: tpep_dropoff_datetime
    type: timestamp
    primary_key: true
  - name: passenger_count
    type: integer
  - name: trip_distance
    type: float
  - name: fare_amount
    type: float
  - name: payment_type
    type: integer
  - name: taxi_type
    type: string
  - name: extracted_at
    type: timestamp

@bruin"""
"""@bruin

name: ingestion.trips

type: python

image: python:3.11

connection: duckdb-default

materialization:
  type: table
  strategy: append

columns:
  - name: tpep_pickup_datetime
    type: timestamp
    primary_key: true
  - name: tpep_dropoff_datetime
    type: timestamp
    primary_key: true
  - name: passenger_count
    type: integer
  - name: trip_distance
    type: float
  - name: fare_amount
    type: float
  - name: payment_type
    type: integer
  - name: taxi_type
    type: string
  - name: extracted_at
    type: timestamp

@bruin"""

import os
import json
from datetime import datetime
import pandas as pd
from dateutil import parser as date_parser


def materialize():
    start_date_str = os.getenv('BRUIN_START_DATE', '2022-01-01')
    end_date_str = os.getenv('BRUIN_END_DATE', '2022-01-31')

    start_date = date_parser.parse(start_date_str).date()
    end_date = date_parser.parse(end_date_str).date()

    bruin_vars = os.getenv('BRUIN_VARS', '{}')
    vars_dict = json.loads(bruin_vars)
    taxi_types = vars_dict.get('taxi_types', ['yellow'])

    base_url = 'https://d37ci6vzurychx.cloudfront.net/trip-data'
    extracted_at = datetime.utcnow()
    all_data = []

    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        for taxi_type in taxi_types:
            file_name = f'{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet'
            url = f'{base_url}/{file_name}'
            try:
                print(f'Fetching: {url}')
                df = pd.read_parquet(url)
                df['taxi_type'] = taxi_type
                df['extracted_at'] = extracted_at
                all_data.append(df)
                print(f'Loaded {len(df)} rows from {file_name}')
            except Exception as e:
                print(f'Warning: Could not fetch {url}: {e}')
                continue
        if month == 12:
            current_date = current_date.replace(year=year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=month + 1, day=1)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
      # Normalize common column names so downstream SQL can rely on a stable schema
      # Create canonical names and some aliases that pipelines may expect
      col_map = {}
      # pickup timestamps
      if 'tpep_pickup_datetime' in final_df.columns:
        col_map['tpep_pickup_datetime'] = 'tpep_pickup_datetime'
      if 'pickup_datetime' in final_df.columns:
        # ensure both names exist, prefer tpep_ name
        col_map['pickup_datetime'] = 'tpep_pickup_datetime'
      # dropoff timestamps
      if 'tpep_dropoff_datetime' in final_df.columns:
        col_map['tpep_dropoff_datetime'] = 'tpep_dropoff_datetime'
      if 'dropoff_datetime' in final_df.columns:
        col_map['dropoff_datetime'] = 'tpep_dropoff_datetime'
      # location ids
      for src in ('PULocationID', 'pu_location_id', 'pickup_location_id', 'pickup_locationid'):
        if src in final_df.columns:
          col_map[src] = 'pickup_locationid'
          break
      for src in ('DOLocationID', 'do_location_id', 'dropoff_location_id', 'dropoff_locationid'):
        if src in final_df.columns:
          col_map[src] = 'dropoff_locationid'
          break

      # Apply renames (only for columns that exist)
      if col_map:
        # build inverse mapping for rename where values are desired canonical names
        rename_map = {k: v for k, v in col_map.items()}
        final_df = final_df.rename(columns=rename_map)

      # Ensure both canonical and friendly names exist to satisfy different pipelines
      if 'tpep_pickup_datetime' in final_df.columns and 'pickup_datetime' not in final_df.columns:
        final_df['pickup_datetime'] = final_df['tpep_pickup_datetime']
      if 'tpep_dropoff_datetime' in final_df.columns and 'dropoff_datetime' not in final_df.columns:
        final_df['dropoff_datetime'] = final_df['tpep_dropoff_datetime']
      if 'pickup_locationid' in final_df.columns and 'pickup_location_id' not in final_df.columns:
        final_df['pickup_location_id'] = final_df['pickup_locationid']
      if 'dropoff_locationid' in final_df.columns and 'dropoff_location_id' not in final_df.columns:
        final_df['dropoff_location_id'] = final_df['dropoff_locationid']

      return final_df
    else:
      # If downloads failed entirely, return an empty dataframe with expected columns
      expected_cols = [
        'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'pickup_datetime', 'dropoff_datetime',
        'passenger_count', 'trip_distance', 'fare_amount', 'payment_type', 'taxi_type',
        'extracted_at', 'pickup_locationid', 'dropoff_locationid', 'pickup_location_id', 'dropoff_location_id'
      ]
      empty = pd.DataFrame({c: pd.Series(dtype='float') for c in expected_cols})
      return empty


