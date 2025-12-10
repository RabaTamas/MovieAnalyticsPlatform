import pandas as pd
import numpy as np
from datetime import datetime
import os

print("=" * 80)
print("🧹 Movie Analytics Platform - Data Cleaning")
print("=" * 80)

# Paths
raw_csv = 'data/raw/movies.csv'
cleaned_csv = 'data/processed/movies_cleaned.csv'

# Create processed directory if it doesn't exist
os.makedirs('data/processed', exist_ok=True)

# Load data
print(f"\n⏳ Loading raw data from: {raw_csv}")
print("   (Loading ALL 700k+ rows - this will take 30-60 seconds...)")

try:
    df = pd.read_csv(raw_csv)
    print(f"✅ Loaded {len(df):,} movies")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    exit()

# Initial stats
print(f"\n📊 INITIAL DATASET:")
print(f"   Total rows: {len(df):,}")
print(f"   Total columns: {len(df.columns)}")
print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**3:.2f} GB")

# =============================================================================
# STEP 1: Date Cleaning
# =============================================================================
print("\n" + "=" * 80)
print("📅 STEP 1: Date Cleaning")
print("=" * 80)

# Convert release_date to datetime
df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')

# Count invalid dates
invalid_dates = df['release_date'].isna().sum()
print(f"   Invalid dates: {invalid_dates:,}")

# Filter: Only movies from 1900 onwards
print(f"   Filtering: release_date >= 1900-01-01")
before_date_filter = len(df)
df = df[df['release_date'] >= '1900-01-01']
removed_old = before_date_filter - len(df)
print(f"   Removed {removed_old:,} movies before 1900")

# Filter: No future movies beyond 2025
print(f"   Filtering: release_date <= 2025-12-31")
df = df[df['release_date'] <= '2025-12-31']
removed_future = before_date_filter - removed_old - len(df)
print(f"   Removed {removed_future:,} future movies")

print(f"   ✅ Remaining after date filter: {len(df):,}")

# =============================================================================
# STEP 2: Budget & Revenue Cleaning
# =============================================================================
print("\n" + "=" * 80)
print("💰 STEP 2: Budget & Revenue Cleaning")
print("=" * 80)

# Count zero/null values
zero_budget = (df['budget'] == 0).sum()
zero_revenue = (df['revenue'] == 0).sum()
print(f"   Movies with budget = 0: {zero_budget:,} ({zero_budget/len(df)*100:.1f}%)")
print(f"   Movies with revenue = 0: {zero_revenue:,} ({zero_revenue/len(df)*100:.1f}%)")

# Filter: Only movies with budget > 0 AND revenue > 0
print(f"\n   Filtering: budget > 0 AND revenue > 0")
before_financial_filter = len(df)
df = df[(df['budget'] > 0) & (df['revenue'] > 0)]
removed_financial = before_financial_filter - len(df)
print(f"   Removed {removed_financial:,} movies without budget/revenue data")
print(f"   ✅ Remaining: {len(df):,}")

# Remove extreme outliers (budget > 1 billion, revenue > 5 billion)
print(f"\n   Removing extreme outliers...")
before_outliers = len(df)
df = df[(df['budget'] <= 1_000_000_000) & (df['revenue'] <= 5_000_000_000)]
removed_outliers = before_outliers - len(df)
print(f"   Removed {removed_outliers:,} extreme outliers")
print(f"   ✅ Remaining: {len(df):,}")

# =============================================================================
# STEP 3: Handle Missing Values
# =============================================================================
print("\n" + "=" * 80)
print("🔧 STEP 3: Handle Missing Values")
print("=" * 80)

# Fill missing genres with "Unknown"
missing_genres = df['genres'].isna().sum()
if missing_genres > 0:
    df['genres'] = df['genres'].fillna('Unknown')
    print(f"   Filled {missing_genres:,} missing genres with 'Unknown'")

# Fill missing production_companies with "Unknown"
missing_companies = df['production_companies'].isna().sum()
if missing_companies > 0:
    df['production_companies'] = df['production_companies'].fillna('Unknown')
    print(f"   Filled {missing_companies:,} missing production companies with 'Unknown'")

# Fill missing overview with empty string
missing_overview = df['overview'].isna().sum()
if missing_overview > 0:
    df['overview'] = df['overview'].fillna('')
    print(f"   Filled {missing_overview:,} missing overviews with empty string")

# Fill missing runtime with median
if 'runtime' in df.columns:
    missing_runtime = df['runtime'].isna().sum()
    if missing_runtime > 0:
        median_runtime = df['runtime'].median()
        df['runtime'] = df['runtime'].fillna(median_runtime)
        print(f"   Filled {missing_runtime:,} missing runtimes with median ({median_runtime:.0f} min)")

# Fill missing ratings with 0
for col in ['vote_average', 'vote_count']:
    if col in df.columns:
        missing = df[col].isna().sum()
        if missing > 0:
            df[col] = df[col].fillna(0)
            print(f"   Filled {missing:,} missing {col} with 0")

print(f"   ✅ Missing values handled")

# =============================================================================
# STEP 4: Create Calculated Fields
# =============================================================================
print("\n" + "=" * 80)
print("📐 STEP 4: Create Calculated Fields")
print("=" * 80)

# Profit = revenue - budget
df['profit'] = df['revenue'] - df['budget']
print(f"   ✅ Created 'profit' column")

# ROI = (revenue - budget) / budget
df['roi'] = (df['revenue'] - df['budget']) / df['budget']
print(f"   ✅ Created 'roi' column")

# Release year, month
df['release_year'] = df['release_date'].dt.year
df['release_month'] = df['release_date'].dt.month
print(f"   ✅ Created 'release_year' and 'release_month' columns")

# =============================================================================
# STEP 5: Data Type Optimization
# =============================================================================
print("\n" + "=" * 80)
print("🔧 STEP 5: Data Type Optimization")
print("=" * 80)

# Convert IDs to integers
df['id'] = df['id'].astype('int64')

# Convert year/month to integers
df['release_year'] = df['release_year'].astype('int32')
df['release_month'] = df['release_month'].astype('int8')

# Convert financial columns to float64
for col in ['budget', 'revenue', 'profit', 'roi', 'popularity', 'vote_average', 'vote_count']:
    if col in df.columns:
        df[col] = df[col].astype('float64')

print(f"   ✅ Data types optimized")

# =============================================================================
# STEP 6: Final Validation
# =============================================================================
print("\n" + "=" * 80)
print("✅ STEP 6: Final Validation")
print("=" * 80)

# Check for any remaining nulls in critical columns
critical_cols = ['id', 'title', 'release_date', 'budget', 'revenue', 'genres']
print(f"\n   Checking critical columns for nulls:")
for col in critical_cols:
    if col in df.columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            print(f"   ⚠️  {col}: {null_count:,} nulls remaining")
        else:
            print(f"   ✅ {col}: No nulls")

# Final statistics
print(f"\n📊 FINAL CLEANED DATASET:")
print(f"   Total movies: {len(df):,}")
print(f"   Date range: {df['release_date'].min().date()} to {df['release_date'].max().date()}")
print(f"   Budget range: ${df['budget'].min():,.0f} to ${df['budget'].max():,.0f}")
print(f"   Revenue range: ${df['revenue'].min():,.0f} to ${df['revenue'].max():,.0f}")
print(f"   ROI range: {df['roi'].min():.2f} to {df['roi'].max():.2f}")
print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Top genres
print(f"\n🎭 TOP 10 GENRES IN CLEANED DATA:")
all_genres = df['genres'].str.split('-').explode()
genre_counts = all_genres.value_counts().head(10)
for genre, count in genre_counts.items():
    print(f"   {genre:25s}: {count:,} movies")

# =============================================================================
# STEP 7: Save Cleaned Data
# =============================================================================
print("\n" + "=" * 80)
print("💾 STEP 7: Saving Cleaned Data")
print("=" * 80)

print(f"\n⏳ Saving to: {cleaned_csv}")
try:
    df.to_csv(cleaned_csv, index=False)
    file_size_mb = os.path.getsize(cleaned_csv) / (1024 ** 2)
    print(f"✅ Saved successfully!")
    print(f"   File size: {file_size_mb:.2f} MB")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
except Exception as e:
    print(f"❌ Error saving CSV: {e}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 80)
print("📋 CLEANING SUMMARY")
print("=" * 80)

print(f"\n   Original dataset: {before_date_filter:,} movies")
print(f"   After date filter: {before_financial_filter:,} movies (-{removed_old + removed_future:,})")
print(f"   After financial filter: {before_outliers:,} movies (-{removed_financial:,})")
print(f"   After outlier removal: {len(df):,} movies (-{removed_outliers:,})")
print(f"\n   ✅ Final cleaned dataset: {len(df):,} movies")
print(f"   📉 Data reduction: {(1 - len(df)/before_date_filter)*100:.1f}%")
print(f"   ✅ Quality data retained for analysis!")

print("\n" + "=" * 80)
print("🎉 Data cleaning complete!")
print("=" * 80)