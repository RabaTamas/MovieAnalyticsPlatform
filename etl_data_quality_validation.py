import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

if os.getenv('AZURE_FUNCTIONS_ENVIRONMENT'):
    OUTPUT_DIR = "/tmp"
elif os.getenv('AIRFLOW_HOME'):
    # Running in Airflow Docker container
    OUTPUT_DIR = "/opt/airflow/project/data/processed"
else:
    # Running locally
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Azure SQL Database
SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE')
SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')

print("=" * 80)
print("Data Quality Validation - ETL Job")
print("=" * 80)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================
print("\n Connecting to Azure SQL Database...")

connection_string = (
    f"mssql+pyodbc://{SQL_USERNAME}:{SQL_PASSWORD}@{SQL_SERVER}/"
    f"{SQL_DATABASE}?driver=ODBC+Driver+17+for+SQL+Server"
)

engine = create_engine(connection_string)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")
    exit(1)

# =============================================================================
# ETL LOG - START
# =============================================================================
job_name = 'Data_Quality_Validation'
start_time = datetime.now()

print(f"\n Starting ETL Job: {job_name}")
print(f"   Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# VALIDATION RESULTS STORAGE
# =============================================================================
validation_results = []
total_issues = 0

def add_validation_result(table, validation_type, invalid_count, total_count, description):
    """Add validation result to results list"""
    global total_issues
    
    invalid_pct = (invalid_count / total_count * 100) if total_count > 0 else 0
    status = 'PASS' if invalid_pct < 0.5 else 'WARNING' if invalid_pct < 5 else 'FAIL'
    
    validation_results.append({
        'table': table,
        'validation_type': validation_type,
        'total_records': total_count,
        'invalid_records': invalid_count,
        'invalid_percentage': invalid_pct,
        'status': status,
        'description': description,
        'timestamp': datetime.now()
    })
    
    total_issues += invalid_count
    
    # Print result
    status_icon = '[OK]' if status == 'PASS' else '[WARN]' if status == 'WARNING' else '[FAIL]'
    print(f"   {status_icon} {validation_type}: {invalid_count}/{total_count} invalid ({invalid_pct:.2f}%) - {status}")

# =============================================================================
# VALIDATION 1: STAGING_MOVIES
# =============================================================================
print("\n" + "=" * 80)
print("Validation 1: Staging_Movies Table")
print("=" * 80)

print("\n Running validations on Staging_Movies...")

# Get total count
query_total = "SELECT COUNT(*) FROM Staging_Movies"
with engine.connect() as conn:
    total_staging = conn.execute(text(query_total)).scalar()

print(f"\n   Total records in Staging_Movies: {total_staging:,}")

# Validation 1.1: NULL movie_id
query = "SELECT COUNT(*) FROM Staging_Movies WHERE movie_id IS NULL"
with engine.connect() as conn:
    null_movie_id = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies', 
    'NULL movie_id', 
    null_movie_id, 
    total_staging,
    'Movies with NULL movie_id (primary identifier)'
)

# Validation 1.2: NULL or empty title
query = "SELECT COUNT(*) FROM Staging_Movies WHERE title IS NULL OR title = ''"
with engine.connect() as conn:
    null_title = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'NULL/Empty title',
    null_title,
    total_staging,
    'Movies with NULL or empty title'
)

# Validation 1.3: Negative budget
query = "SELECT COUNT(*) FROM Staging_Movies WHERE budget < 0"
with engine.connect() as conn:
    negative_budget = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'Negative budget',
    negative_budget,
    total_staging,
    'Movies with negative budget (invalid)'
)

# Validation 1.4: Negative revenue
query = "SELECT COUNT(*) FROM Staging_Movies WHERE revenue < 0"
with engine.connect() as conn:
    negative_revenue = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'Negative revenue',
    negative_revenue,
    total_staging,
    'Movies with negative revenue (invalid)'
)

# Validation 1.5: Rating out of range (0-10)
query = "SELECT COUNT(*) FROM Staging_Movies WHERE vote_average < 0 OR vote_average > 10"
with engine.connect() as conn:
    invalid_rating = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'Rating out of range',
    invalid_rating,
    total_staging,
    'Movies with vote_average not in 0-10 range'
)

# Validation 1.6: Future release dates
query = "SELECT COUNT(*) FROM Staging_Movies WHERE release_date > GETDATE()"
with engine.connect() as conn:
    future_dates = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'Future release dates',
    future_dates,
    total_staging,
    'Movies with release date in the future'
)

# Validation 1.7: Negative runtime
query = "SELECT COUNT(*) FROM Staging_Movies WHERE runtime < 0"
with engine.connect() as conn:
    negative_runtime = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'Negative runtime',
    negative_runtime,
    total_staging,
    'Movies with negative runtime (invalid)'
)

# Validation 1.8: Extremely high runtime (>600 minutes = 10 hours)
query = "SELECT COUNT(*) FROM Staging_Movies WHERE runtime > 600"
with engine.connect() as conn:
    extreme_runtime = conn.execute(text(query)).scalar()

add_validation_result(
    'Staging_Movies',
    'Extreme runtime (>10h)',
    extreme_runtime,
    total_staging,
    'Movies with runtime over 10 hours (suspicious)'
)

# =============================================================================
# VALIDATION 2: FACT_MOVIES
# =============================================================================
print("\n" + "=" * 80)
print(" Validation 2: Fact_Movies Table")
print("=" * 80)

print("\n Running validations on Fact_Movies...")

# Get total count
query_total = "SELECT COUNT(*) FROM Fact_Movies"
with engine.connect() as conn:
    total_fact = conn.execute(text(query_total)).scalar()

print(f"\n   Total records in Fact_Movies: {total_fact:,}")

# Validation 2.1: NULL genre_id
query = "SELECT COUNT(*) FROM Fact_Movies WHERE genre_id IS NULL"
with engine.connect() as conn:
    null_genre = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'NULL genre_id',
    null_genre,
    total_fact,
    'Movies with NULL genre_id (broken FK)'
)

# Validation 2.2: NULL time_id
query = "SELECT COUNT(*) FROM Fact_Movies WHERE time_id IS NULL"
with engine.connect() as conn:
    null_time = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'NULL time_id',
    null_time,
    total_fact,
    'Movies with NULL time_id (broken FK)'
)

# Validation 2.3: NULL studio_id
query = "SELECT COUNT(*) FROM Fact_Movies WHERE studio_id IS NULL"
with engine.connect() as conn:
    null_studio = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'NULL studio_id',
    null_studio,
    total_fact,
    'Movies with NULL studio_id (broken FK)'
)

# Validation 2.4: Negative budget
query = "SELECT COUNT(*) FROM Fact_Movies WHERE budget < 0"
with engine.connect() as conn:
    negative_budget_fact = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Negative budget',
    negative_budget_fact,
    total_fact,
    'Movies with negative budget'
)

# Validation 2.5: Negative revenue
query = "SELECT COUNT(*) FROM Fact_Movies WHERE revenue < 0"
with engine.connect() as conn:
    negative_revenue_fact = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Negative revenue',
    negative_revenue_fact,
    total_fact,
    'Movies with negative revenue'
)

# Validation 2.6: Rating out of range
query = "SELECT COUNT(*) FROM Fact_Movies WHERE vote_average < 0 OR vote_average > 10"
with engine.connect() as conn:
    invalid_rating_fact = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Rating out of range',
    invalid_rating_fact,
    total_fact,
    'Movies with invalid vote_average'
)

# Validation 2.7: Duplicate movies (same movie_id multiple times)
# query = """
#     SELECT COUNT(*) FROM (
#         SELECT movie_id, COUNT(*) as cnt
#         FROM Fact_Movies
#         GROUP BY movie_id
#         HAVING COUNT(*) > 1
#     ) as duplicates
# """

# Validation 2.7: Duplicate movies - INFORMATIONAL (multi-genre design)
query = """
    SELECT COUNT(*) FROM (
        SELECT movie_id, COUNT(*) as cnt
        FROM Fact_Movies
        GROUP BY movie_id
        HAVING COUNT(*) > 1
    ) as duplicates
"""
with engine.connect() as conn:
    duplicate_movies = conn.execute(text(query)).scalar()

# This is by design (multi-genre), not an error
print(f"    Multi-genre movies: {duplicate_movies:,} movies appear multiple times (by design)")

# =============================================================================
# VALIDATION 3: REFERENTIAL INTEGRITY
# =============================================================================
print("\n" + "=" * 80)
print(" Validation 3: Referential Integrity")
print("=" * 80)

print("\n Checking foreign key relationships...")

# Validation 3.1: Orphaned genre_id
query = """
    SELECT COUNT(*) 
    FROM Fact_Movies f
    WHERE f.genre_id NOT IN (SELECT genre_id FROM Dim_Genre)
    AND f.genre_id IS NOT NULL
"""
with engine.connect() as conn:
    orphaned_genres = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Orphaned genre_id',
    orphaned_genres,
    total_fact,
    'Movies with genre_id not in Dim_Genre'
)

# Validation 3.2: Orphaned time_id
query = """
    SELECT COUNT(*) 
    FROM Fact_Movies f
    WHERE f.time_id NOT IN (SELECT time_id FROM Dim_Time)
    AND f.time_id IS NOT NULL
"""
with engine.connect() as conn:
    orphaned_times = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Orphaned time_id',
    orphaned_times,
    total_fact,
    'Movies with time_id not in Dim_Time'
)

# Validation 3.3: Orphaned studio_id
query = """
    SELECT COUNT(*) 
    FROM Fact_Movies f
    WHERE f.studio_id NOT IN (SELECT studio_id FROM Dim_Studio)
    AND f.studio_id IS NOT NULL
"""
with engine.connect() as conn:
    orphaned_studios = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Orphaned studio_id',
    orphaned_studios,
    total_fact,
    'Movies with studio_id not in Dim_Studio'
)

# =============================================================================
# VALIDATION 4: BUSINESS LOGIC
# =============================================================================
print("\n" + "=" * 80)
print(" Validation 4: Business Logic Checks")
print("=" * 80)

print("\n Running business logic validations...")

# Validation 4.1: Revenue less than budget (but both > 0) = Loss-making
query = """
    SELECT COUNT(*) 
    FROM Fact_Movies
    WHERE budget > 0 AND revenue > 0 AND revenue < budget
"""
with engine.connect() as conn:
    loss_making = conn.execute(text(query)).scalar()

# This is informational, not an error
print(f"   Loss-making films: {loss_making:,}/{total_fact:,} ({loss_making/total_fact*100:.2f}%)")

# Validation 4.2: Extremely high ROI (>1000x = suspicious)
query = """
    SELECT COUNT(*) 
    FROM Fact_Movies
    WHERE roi > 1000
"""
with engine.connect() as conn:
    extreme_roi = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Extreme ROI (>1000x)',
    extreme_roi,
    total_fact,
    'Movies with ROI over 1000 (suspicious data)'
)

# Validation 4.3: Zero budget but has revenue (data quality issue)
query = """
    SELECT COUNT(*) 
    FROM Fact_Movies
    WHERE budget = 0 AND revenue > 0
"""
with engine.connect() as conn:
    zero_budget = conn.execute(text(query)).scalar()

add_validation_result(
    'Fact_Movies',
    'Zero budget with revenue',
    zero_budget,
    total_fact,
    'Movies with $0 budget but positive revenue (missing data)'
)

# =============================================================================
# CALCULATE OVERALL STATISTICS
# =============================================================================
print("\n" + "=" * 80)
print(" Overall Data Quality Statistics")
print("=" * 80)

total_records = total_staging + total_fact
invalid_pct_overall = (total_issues / total_records * 100) if total_records > 0 else 0

print(f"\n   Total records checked: {total_records:,}")
print(f"   Total invalid records: {total_issues:,}")
print(f"   Invalid percentage: {invalid_pct_overall:.2f}%")

if invalid_pct_overall < 0.5:
    overall_status = 'EXCELLENT'
    status_icon = '[OK]'
elif invalid_pct_overall < 2:
    overall_status = 'GOOD'
    status_icon = '[OK]'
elif invalid_pct_overall < 5:
    overall_status = 'ACCEPTABLE'
    status_icon = '[WARN]'
else:
    overall_status = 'POOR'
    status_icon = '[FAIL]'

print(f"   Overall status: {status_icon} {overall_status}")

# =============================================================================
# SAVE VALIDATION REPORT
# =============================================================================
print("\n" + "=" * 80)
print(" Saving Validation Report")
print("=" * 80)

# Create DataFrame
df_report = pd.DataFrame(validation_results)

# Save to CSV
# report_file = f'data/processed/data_quality_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
report_file = os.path.join(
    OUTPUT_DIR,
    f"data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)
df_report.to_csv(report_file, index=False)

print(f"\n Validation report saved to: {report_file}")
print(f"   Total validations: {len(validation_results)}")

# =============================================================================
# LOG TO ETL_LOG TABLE
# =============================================================================
print("\n" + "=" * 80)
print(" Logging to ETL_Log table")
print("=" * 80)

end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

# Determine job status
if invalid_pct_overall < 0.5:
    job_status = 'SUCCESS'
elif invalid_pct_overall < 5:
    job_status = 'SUCCESS_WITH_WARNINGS'
else:
    job_status = 'FAILED'

error_message = f"Data quality: {invalid_pct_overall:.2f}% invalid records" if invalid_pct_overall > 0 else None

log_query = text("""
    INSERT INTO ETL_Log (job_name, start_time, end_time, rows_processed, rows_failed, status, error_message)
    VALUES (:job_name, :start_time, :end_time, :rows_processed, :rows_failed, :status, :error_message)
""")

try:
    with engine.connect() as conn:
        conn.execute(log_query, {
            'job_name': job_name,
            'start_time': start_time,
            'end_time': end_time,
            'rows_processed': total_records,
            'rows_failed': total_issues,
            'status': job_status,
            'error_message': error_message
        })
        conn.commit()
    
    print(" ETL log entry created")
except Exception as e:
    print(f"  Warning: Could not log to ETL_Log: {e}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print(" Validation Job Summary")
print("=" * 80)

print(f"\n   Job Name: {job_name}")
print(f"   Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Duration: {duration:.2f} seconds")
print(f"   Status: {job_status}")
print(f"\n   Total validations run: {len(validation_results)}")
print(f"   Total records checked: {total_records:,}")
print(f"   Invalid records found: {total_issues:,}")
print(f"   Invalid percentage: {invalid_pct_overall:.2f}%")
print(f"   Overall quality: {overall_status}")
print(f"\n   Report saved: {report_file}")

# Print top issues
print(f"\n   Top 5 Issues:")
df_sorted = df_report.sort_values('invalid_records', ascending=False)
for idx, row in df_sorted.head(5).iterrows():
    if row['invalid_records'] > 0:
        print(f"      {row['invalid_records']:>6,} - {row['table']}.{row['validation_type']}")

print("\n" + "=" * 80)
print(" Data Quality Validation Complete!")
print("=" * 80)