/* @bruin
name: staging.trips
type: duckdb.sql

depends:
  - ingestion.trips
  - ingestion.payment_lookup

materialization:
  type: table
  strategy: create+replace

columns:
  - name: tpep_pickup_datetime
    type: timestamp
    primary_key: true
    checks:
      - name: not_null
  - name: tpep_dropoff_datetime
    type: timestamp
    primary_key: true
  - name: passenger_count
    type: integer
    primary_key: true
  - name: trip_distance
    type: float
    primary_key: true
  - name: fare_amount
    type: float
    primary_key: true
  - name: payment_type
    type: integer
  - name: taxi_type
    type: string
  - name: payment_type_name
    type: string

custom_checks:
  - name: row_count_greater_than_zero
    query: |
      SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
      FROM staging.trips 
    value: 1
@bruin */

SELECT DISTINCT
    t.tpep_pickup_datetime,
    t.tpep_dropoff_datetime,
    t.passenger_count,
    t.trip_distance,
    t.fare_amount,
    t.payment_type,
    t.taxi_type,
    p.payment_type_name
FROM ingestion.trips t
LEFT JOIN ingestion.payment_lookup p
    ON t.payment_type = p.payment_type_id
WHERE t.tpep_pickup_datetime >= '{{ start_datetime }}'
  AND t.tpep_pickup_datetime < '{{ end_datetime }}'
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY t.tpep_pickup_datetime, t.tpep_dropoff_datetime,
                 t.passenger_count, t.trip_distance, t.fare_amount
    ORDER BY t.tpep_pickup_datetime
) = 1
