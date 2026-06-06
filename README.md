# Movie Analytics Platform

Teljes körű data engineering és üzleti intelligencia pipeline a filmipar adatainak elemzésére. A projekt az Üzleti Intelligencia tárgy (2025 ősz) házi feladatának kiterjesztett verziója, amelyet a Data Engineering a gyakorlatban tárgy követelményeinek megfelelően bővítettük Apache Airflow orkesztrációval és dbt transzformációs réteggel.

## Technológiai stack

| Réteg | Eszköz |
|---|---|
| Adatforrás | Kaggle TMDB CSV, TMDB REST API |
| Landing zone | Azure Blob Storage |
| ETL / ingestálás | Python 3.12, Pandas, SQLAlchemy, pyodbc |
| Transzformáció | dbt (SQL modellek + tesztek) |
| Adattárház | Azure SQL Database (Star Schema) |
| Orchestration | Apache Airflow 2.8.1 (Docker Compose) |
| Reporting | Power BI Desktop/Service |
| ML / predikció | scikit-learn (Linear Regression) |
| Idősoros elemzés | Prophet (Meta) |
| Tesztelés | Pytest, dbt tests |

## Projekt struktúra

```
MovieAnalyticsPlatform/
├── airflow/
│   └── dags/
│       └── movie_analytics_dag.py      # Airflow DAG (8 task)
├── azure_functions/                    # Régi HTTP-triggered ETL (BI tárgy előzmény)
├── dbt/
│   ├── models/
│   │   ├── staging/stg_movies.sql
│   │   ├── dimensions/dim_genre.sql
│   │   ├── facts/fact_movies.sql
│   │   └── aggregations/agg_by_genre.sql
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/schema.yml               # dbt tesztek
├── data/
│   ├── processed/movies_cleaned.csv
│   └── chunks/                         # CSV chunk fájlok (4 db)
├── tests/                              # Pytest tesztek
├── etl_csv_chunk_to_staging.py         # Chunk-alapú CSV betöltés
├── etl_api_refresh.py                  # TMDB API delta load
├── etl_load_dimensions.py              # Dim táblák betöltése
├── etl_load_fact.py                    # Fact tábla betöltése
├── etl_load_aggregations.py            # Aggregációk betöltése
├── etl_data_quality_validation.py      # 19 validációs szabály
├── ml_revenue_prediction.py            # Linear Regression modell
├── prophet_forecast.py                 # Prophet idősoros előrejelzés
├── split_csv.py                        # CSV felvágó script
├── clean_staging.py                    # Staging tábla tisztítása
├── Dockerfile.airflow                  # Custom Airflow image (ODBC Driver 17)
├── docker-compose.yml                  # Airflow + Postgres
└── MovieAnalytics_PowerBI.pbix         # Power BI dashboardok
```

## Előfeltételek

- Python 3.12
- Docker Desktop
- Azure SQL Database (connection string a `.env` fájlban)
- Azure Blob Storage (connection string a `.env` fájlban)
- Power BI Desktop (opcionális, dashboard megtekintéséhez)

## Telepítés és futtatás

### 1. Repository klónozása

```bash
git clone https://github.com/RabaTamas/MovieAnalyticsPlatform.git
cd MovieAnalyticsPlatform
```

### 2. `.env` fájl létrehozása

Hozz létre egy `.env` fájlt a projekt gyökerében:

```env
AZURE_SQL_SERVER=<your-server>.database.windows.net
AZURE_SQL_DATABASE=<your-database>
AZURE_SQL_USERNAME=<your-username>
AZURE_SQL_PASSWORD=<your-password>
AZURE_STORAGE_CONNECTION_STRING=<your-blob-connection-string>
TMDB_API_KEY=<your-tmdb-api-key>
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-email>
SMTP_PASSWORD=<your-app-password>
ALERT_RECIPIENTS=<your-email>
```

### 3. Python függőségek telepítése

```bash
pip install pandas pyodbc sqlalchemy python-dotenv requests scikit-learn prophet matplotlib seaborn pytest
pip install dbt-core dbt-sqlserver
```

### 4. CSV felvágása (első futtatás előtt)

```bash
python split_csv.py
```

Ez létrehozza a `data/chunks/` mappában a 4 CSV chunkot.

### 5. Airflow indítása Docker Compose-szal

```bash
docker-compose up airflow-init
docker-compose up airflow-webserver airflow-scheduler -d
```

Airflow UI: **http://localhost:8080** (admin / admin)

Az Airflow image automatikusan buildelődik a `Dockerfile.airflow`-ból, amely tartalmazza az ODBC Driver 17 for SQL Server-t.

### 6. Azure SQL tűzfalbeállítás

Az Azure Portalon add hozzá a saját IP-det és a Docker container IP-jét a tűzfalszabályokhoz:
- Azure Portal → SQL Server → Hálózatkezelés → Tűzfalszabályok

### 7. Airflow DAG futtatása

1. Nyisd meg: http://localhost:8080
2. Kapcsold be a `movie_analytics_pipeline` DAG-ot (toggle)
3. Kattints a ▶ (Trigger DAG) gombra

A DAG napi 02:00-kor fut automatikusan, vagy manuálisan triggerelhető.

### 8. dbt futtatása (opcionális – manuálisan)

```bash
cd dbt
# Környezeti változók beállítása (PowerShell)
$env:AZURE_SQL_SERVER="<server>"; $env:AZURE_SQL_DATABASE="<db>"; $env:AZURE_SQL_USERNAME="<user>"; $env:AZURE_SQL_PASSWORD="<password>"

# Kapcsolat tesztelése
dbt debug --profiles-dir .

# Modellek futtatása
dbt run --profiles-dir .

# Tesztek futtatása
dbt test --profiles-dir .
```

### 9. ML modellek futtatása (opcionális)

```bash
# Linear Regression (bevétel-predikció)
python ml_revenue_prediction.py

# Prophet (idősoros előrejelzés)
python prophet_forecast.py
```

### 10. Pytest tesztek futtatása

```bash
python -m pytest tests/ -v
```

## Airflow DAG – Pipeline lépései

| # | Task | Leírás |
|---|---|---|
| 1 | ingest_csv_chunk_1 | Kaggle CSV 1. részlet (2,708 film) → Azure Blob |
| 2 | ingest_csv_chunk_2 | Kaggle CSV 2. részlet (2,708 film) → Azure Blob |
| 3 | ingest_csv_chunk_3 | Kaggle CSV 3. részlet (2,708 film) → Azure Blob |
| 4 | ingest_csv_chunk_4 | Kaggle CSV 4. részlet (2,710 film) → Azure Blob |
| 5 | load_dimensions | Staging → Dim táblák (SCD Type 1) |
| 6 | load_fact | Staging + Dim → Fact_Movies (profit/ROI) |
| 7 | load_aggregations | Fact → Agg táblák (műfaj/év) |
| 8 | data_quality_validation | 19 validációs szabály ellenőrzése |

A DAG **idempotens**: minden task újrafuttatható duplikáció nélkül (UPSERT logika, source mező ellenőrzés).

## Data Warehouse séma

**Star Schema – 9 tábla:**

```
Staging_Movies          → nyers adatok (4 CSV chunk)
Dim_Genre (20)          → műfajok
Dim_Time (40,359)       → időbeli dimenziók
Dim_Studio (10,284)     → produkciós stúdiók
Dim_Country (70)        → országok
Fact_Movies (25,051)    → ténytábla (multi-genre design)
Agg_Genre_Performance   → műfajonkénti aggregációk
Agg_Yearly_Trends       → évenkénti trendek
ETL_Log                 → ETL futtatások naplója
```

## Főbb eredmények

- **10,834 film** feldolgozva (Kaggle CSV + TMDB API delta load)
- **Data Quality:** 0.10% invalid records – EXCELLENT minősítés
- **Linear Regression:** R²=0.70, CV Mean R²=0.70 (KFold shuffle=True)
- **Prophet forecast:** 2025–2029, 95% konfidencia intervallum
- **Pytest:** 28/28 PASSED
- **dbt tesztek:** 11/11 PASSED

## Szerző

Rába Tamás – CRLJQ8

BME Üzleti Intelligencia Laboratórium / Data Engineering a gyakorlatban – 2025/2026 tavasz
