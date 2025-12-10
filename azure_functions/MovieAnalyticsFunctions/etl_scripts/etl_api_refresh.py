import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import pyodbc
from sqlalchemy import create_engine, text
from email_notifier import send_email_alert

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'

# Azure SQL Database
SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
SQL_DATABASE = os.getenv('AZURE_SQL_DATABASE')
SQL_USERNAME = os.getenv('AZURE_SQL_USERNAME')
SQL_PASSWORD = os.getenv('AZURE_SQL_PASSWORD')

# Rate limiting
REQUEST_DELAY = 0.25  # 250ms between requests (4 requests/sec, TMDB limit: 50/sec)
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# How many movies to fetch
MOVIES_TO_FETCH = 500  # Top 500 popular movies

print("=" * 80)
print("TMDB API Refresh ETL Job")
print("=" * 80)

# =============================================================================
# DATABASE CONNECTION
# =============================================================================
print("\nConnecting to Azure SQL Database...")

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
job_name = 'API_Refresh'
start_time = datetime.now()

print(f"\nStarting ETL Job: {job_name}")
print(f"   Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def api_request_with_retry(url, params, max_retries=MAX_RETRIES):
    """Make API request with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                print(f"Rate limit hit, waiting {RETRY_DELAY * (attempt + 1)}s...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                print(f"API error {response.status_code}, attempt {attempt + 1}/{max_retries}")
                time.sleep(RETRY_DELAY)
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, attempt {attempt + 1}/{max_retries}")
            time.sleep(RETRY_DELAY)
    
    return None

def get_existing_movie_ids():
    """Get list of movie IDs already in Staging_Movies"""
    query = "SELECT DISTINCT movie_id FROM Staging_Movies WHERE movie_id IS NOT NULL"
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            existing_ids = {row[0] for row in result}
            return existing_ids
    except Exception as e:
        print(f"Error getting existing IDs: {e}")
        return set()

# =============================================================================
# STEP 1: FETCH POPULAR MOVIES FROM TMDB API
# =============================================================================
print("\n" + "=" * 80)
print("Step 1: Fetching popular movies from TMDB API")
print("=" * 80)

movies_data = []
pages_to_fetch = (MOVIES_TO_FETCH // 20) + 1  # TMDB returns 20 movies per page

print(f"\n   Fetching {MOVIES_TO_FETCH} movies ({pages_to_fetch} pages)...")

for page in range(1, pages_to_fetch + 1):
    print(f"Fetching page {page}/{pages_to_fetch}...", end=" ")
    
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
        'page': page
    }
    
    data = api_request_with_retry(url, params)
    
    if data and 'results' in data:
        movies_data.extend(data['results'])
        print(f"Got {len(data['results'])} movies")
    else:
        print(f"Failed")
    
    # Rate limiting
    time.sleep(REQUEST_DELAY)

print(f"\nTotal movies fetched: {len(movies_data)}")

# =============================================================================
# STEP 2: FETCH DETAILED INFO FOR EACH MOVIE
# =============================================================================
print("\n" + "=" * 80)
print("Step 2: Fetching detailed info for each movie")
print("=" * 80)

detailed_movies = []
failed_count = 0

print(f"\n   Processing {len(movies_data)} movies...")

for i, movie in enumerate(movies_data, 1):
    movie_id = movie.get('id')
    
    if i % 50 == 0:
        print(f"   Progress: {i}/{len(movies_data)} ({(i/len(movies_data)*100):.1f}%)")
    
    # Fetch detailed movie info
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US'
    }
    
    details = api_request_with_retry(url, params)
    
    if details:
        detailed_movies.append(details)
    else:
        failed_count += 1
    
    # Rate limiting
    time.sleep(REQUEST_DELAY)

print(f"\nSuccessfully fetched: {len(detailed_movies)} movies")
print(f"Failed: {failed_count} movies")

# =============================================================================
# STEP 3: PARSE JSON AND PREPARE DATA
# =============================================================================
print("\n" + "=" * 80)
print("Step 3: Parsing JSON and preparing data")
print("=" * 80)

parsed_data = []

for movie in detailed_movies:
    try:
        # Extract genres
        genres = '-'.join([g['name'] for g in movie.get('genres', [])])
        if not genres:
            genres = 'Unknown'
        
        # Extract production companies
        companies = '-'.join([c['name'] for c in movie.get('production_companies', [])])
        if not companies:
            companies = 'Unknown'
        
        # Extract production countries
        countries = '-'.join([c['iso_3166_1'] for c in movie.get('production_countries', [])])
        if not countries:
            countries = 'US'
        
        parsed_movie = {
            'movie_id': movie.get('id'),
            'title': movie.get('title', ''),
            'genres': genres,
            'original_language': movie.get('original_language', 'en'),
            'overview': movie.get('overview', ''),
            'popularity': movie.get('popularity', 0),
            'production_companies': companies,
            'release_date': movie.get('release_date', None),
            'budget': movie.get('budget', 0),
            'revenue': movie.get('revenue', 0),
            'runtime': movie.get('runtime', None),
            'vote_average': movie.get('vote_average', 0),
            'vote_count': movie.get('vote_count', 0),
            'source': 'TMDB_API',
            'load_date': datetime.now()
        }
        
        # Calculate profit and ROI
        if parsed_movie['budget'] > 0 and parsed_movie['revenue'] > 0:
            parsed_movie['profit'] = parsed_movie['revenue'] - parsed_movie['budget']
            parsed_movie['roi'] = parsed_movie['profit'] / parsed_movie['budget']
        else:
            parsed_movie['profit'] = None
            parsed_movie['roi'] = None
        
        # Extract year and month
        if parsed_movie['release_date']:
            try:
                release_dt = pd.to_datetime(parsed_movie['release_date'])
                parsed_movie['release_year'] = release_dt.year
                parsed_movie['release_month'] = release_dt.month
            except:
                parsed_movie['release_year'] = None
                parsed_movie['release_month'] = None
        else:
            parsed_movie['release_year'] = None
            parsed_movie['release_month'] = None
        
        parsed_data.append(parsed_movie)
        
    except Exception as e:
        print(f"Error parsing movie {movie.get('id')}: {e}")
        continue

print(f"\nParsed {len(parsed_data)} movies successfully")

# =============================================================================
# STEP 4: DELTA LOAD - FILTER ONLY NEW MOVIES
# =============================================================================
print("\n" + "=" * 80)
print("Step 4: Delta Load - Filtering new movies only")
print("=" * 80)

print("\n   Getting existing movie IDs from Staging_Movies...")
existing_ids = get_existing_movie_ids()
print(f"   Found {len(existing_ids)} existing movies in database")

# Filter new movies
df = pd.DataFrame(parsed_data)
df_new = df[~df['movie_id'].isin(existing_ids)]

print(f"\n   Total movies from API: {len(df)}")
print(f"   Existing movies in DB: {len(df) - len(df_new)}")
print(f"New movies to insert: {len(df_new)}")

# =============================================================================
# STEP 5: INSERT NEW MOVIES INTO STAGING_MOVIES
# =============================================================================
print("\n" + "=" * 80)
print("Step 5: Inserting new movies into Staging_Movies")
print("=" * 80)

rows_inserted = 0
rows_failed = 0

if len(df_new) > 0:
    print(f"\n   Inserting {len(df_new)} new movies...")
    
    try:
        # Insert to Staging_Movies
        df_new.to_sql(
            'Staging_Movies',
            engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=100
        )
        
        rows_inserted = len(df_new)
        print(f"Successfully inserted {rows_inserted} movies")
        
    except Exception as e:
        print(f"Error inserting data: {e}")
        rows_failed = len(df_new)
else:
    print("\n   No new movies to insert (all movies already in database)")

# =============================================================================
# STEP 6: ETL LOG - END
# =============================================================================
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

status = 'SUCCESS' if rows_failed == 0 else 'PARTIAL_SUCCESS' if rows_inserted > 0 else 'FAILED'
error_message = f"Failed to insert {rows_failed} rows" if rows_failed > 0 else None

print("\n" + "=" * 80)
print("Step 6: Logging ETL job to ETL_Log table")
print("=" * 80)

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
            'rows_processed': rows_inserted,
            'rows_failed': rows_failed,
            'status': status,
            'error_message': error_message
        })
        conn.commit()
    
    print("ETL log entry created")
except Exception as e:
    print(f"Warning: Could not log to ETL_Log: {e}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print("ETL Job Summary")
print("=" * 80)

print(f"\n   Job Name: {job_name}")
print(f"   Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
print(f"   Status: {status}")
print(f"\n   Movies fetched from API: {len(detailed_movies)}")
print(f"   Movies parsed: {len(parsed_data)}")
print(f"   New movies inserted: {rows_inserted}")
print(f"   Failed insertions: {rows_failed}")

print("\n" + "=" * 80)
print("ETL Job Complete!")
print("=" * 80)

# =============================================================================
# EMAIL ALERT (if failed)
# =============================================================================
if status != 'SUCCESS':
    print("\n" + "=" * 80)
    print("Sending failure email alert...")
    print("=" * 80)
    
    send_email_alert(
        job_name=job_name,
        error_message=f"ETL job failed with status: {status}",
        error_details=f"Rows failed: {rows_failed}\nError: {error_message}"
    )
