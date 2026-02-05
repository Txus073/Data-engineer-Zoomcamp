
Create external table:

CREATE OR REPLACE EXTERNAL TABLE `kestra-taxi-zoomcamp.zoomcamp.external_yellow_tripdata` 
OPTIONS ( format = 'PARQUET', uris = ['gs://txus-module-3-homework/yellow_tripdata_2024-*.parquet'] );

Create materialised table:

CREATE OR REPLACE TABLE `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_non_partitioned` AS
SELECT * FROM `kestra-taxi-zoomcamp.zoomcamp.external_yellow_tripdata`;


1-   20,332,093

2-  
SELECT COUNT(DISTINCT PULocationID) 
FROM `kestra-taxi-zoomcamp.zoomcamp.external_yellow_tripdata`;
 	0MB
SELECT COUNT(DISTINCT PULocationID) 
FROM `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_non_partitioned`;
	155.12
0 MB for the External Table and 155.12 MB for the Materialized Table


3- 
SELECT PULocationID
FROM `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_non_partitioned`;

SELECT PULocationID, DOLocationID
FROM `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_non_partitioned`;

BigQuery is a columnar database, and it only scans the specific columns requested in the query. Querying two columns (PULocationID, DOLocationID) requires reading more data than querying one column (PULocationID), leading to a higher estimated number of bytes processed.

4-
SELECT count(*)
FROM `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_non_partitioned`
WHERE fare_amount = 0;

		8,333

5-
CREATE OR REPLACE TABLE `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_partitioned_clustered`
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID AS
SELECT * FROM `kestra-taxi-zoomcamp.zoomcamp.external_yellow_tripdata`;

Partition by tpep_dropoff_datetime and Cluster on VendorID

6-
SELECT DISTINCT(VendorID)
FROM `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_non_partitioned`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01' AND '2024-03-15';

		310.24 MB

SELECT DISTINCT(VendorID)
FROM `kestra-taxi-zoomcamp.zoomcamp.yellow_tripdata_partitioned_clustered`
WHERE tpep_dropoff_datetime BETWEEN '2024-03-01' AND '2024-03-15';
		26.84 MB

310.24 MB for non-partitioned table and 26.84 MB for the partitioned table

7-  GCP Bucket

8- Flase

9- 0 MB Because BigQuery already has the schema and the details like number of rows
