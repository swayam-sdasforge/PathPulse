# Powering PathPulse with Exasol 🚀

This document serves as a technical deep dive into how the **MindSpark** team leveraged the Exasol Analytics Database to build PathPulse for the Exasol AI Build Challenge 2026.

## 1. Why We Chose Exasol over Traditional RDBMS
When processing 30 frames per second of live traffic footage through a YOLOv8 computer vision model, the sheer volume of telemetry data generated is staggering. Every single frame can contain dozens of detected objects (pedestrians, vehicles, potholes, speed bumps). 

A traditional transactional database (like PostgreSQL or MySQL) would quickly choke on the rapid micro-batch insertions while simultaneously trying to serve complex analytical queries to our Streamlit dashboard. 

**Exasol’s in-memory, columnar architecture** was the silver bullet. It allowed us to write vast amounts of inference data in real-time while instantaneously querying aggregate metrics (like average severity scores and incident distributions) without a millisecond of UI lag.

## 2. Bypassing ORM Bottlenecks with `pyexasol`
Most hackathon projects rely on ORMs like SQLAlchemy. However, ORMs introduce significant serialization overhead. To maximize Exasol's capabilities, we utilized the native `pyexasol` driver, which operates over highly optimized WebSockets.

In our architecture, the YOLOv8 engine pushes raw detections into a local buffer. Once the buffer hits a micro-batch threshold, a background thread fires a raw parameterized SQL `INSERT` statement via `pyexasol` directly into our `CIVIC.ROAD_INCIDENTS` schema. This completely decoupled our ML inference speed from our database ingestion speed.

## 3. The `exasol-nano` Edge Computing Advantage
As first-year students, we wanted to build something architecturally innovative. We hypothesized: *What if we wanted to deploy PathPulse directly onto the onboard computer of a city garbage truck?*

Cloud databases are useless if the garbage truck drives through a dead zone without internet connectivity. 

By deploying Exasol locally via the `exasol-nano` Docker container, we achieved a true **Edge-Computing Architecture**. The AI infers locally, and Exasol processes the analytics locally. No internet required. When the truck returns to the depot and connects to Wi-Fi, the local Exasol instance can batch-sync its analytics to a centralized cloud server.

## 4. The Database Schema
We designed a lightweight, highly-indexed schema to track incidents:
```sql
CREATE TABLE CIVIC.ROAD_INCIDENTS (
    INCIDENT_ID VARCHAR(50),
    CLASS_NAME VARCHAR(50),
    CONFIDENCE DOUBLE,
    SEVERITY INT,
    TIMESTAMP TIMESTAMP
);
```
Streamlit constantly queries this table using fast aggregations:
```sql
SELECT CLASS_NAME, COUNT(*) as Count, AVG(CONFIDENCE) as AvgConf
FROM CIVIC.ROAD_INCIDENTS 
GROUP BY CLASS_NAME;
```
Because of Exasol's columnar storage, these `GROUP BY` operations over thousands of rows execute in sub-millisecond timeframes, allowing our dashboard to feel entirely real-time.

## Summary
Exasol wasn't just a storage bin for our project; it was the engine that made real-time Edge-AI possible. It handled the massive throughput of our computer vision model with zero lag, proving that Exasol is the ultimate analytics backend for the future of Smart City infrastructure.
