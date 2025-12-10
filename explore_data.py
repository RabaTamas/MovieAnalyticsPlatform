import pandas as pd
import os

print("=" * 70)
print("🎬 TMDB Movies Dataset - Initial Exploration")
print("=" * 70)

# CSV file path
csv_path = 'data/raw/movies.csv'

# Check if file exists
if not os.path.exists(csv_path):
    print(f"\n❌ Error: File not found at {csv_path}")
    print("\nPlease download the dataset and place it in data/raw/ folder")
    exit()

# Get file size
file_size_mb = os.path.getsize(csv_path) / (1024 ** 2)
print(f"\n📁 File size: {file_size_mb:.2f} MB")

# Load CSV with progress
print(f"\n⏳ Loading CSV (this may take 10-30 seconds)...")

try:
    # Load only first 100k rows for initial exploration (faster)
    df = pd.read_csv(csv_path, nrows=100000)
    print(f"✅ Loaded first 100,000 rows for quick exploration")
    
    # If you want to load ALL data, comment out above and uncomment below:
    # df = pd.read_csv(csv_path)
    # print(f"✅ Full dataset loaded!")
    
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    exit()

# Basic info
print("\n" + "=" * 70)
print("📊 DATASET OVERVIEW")
print("=" * 70)

print(f"\n🎥 Movies in sample: {len(df):,}")
print(f"📋 Total columns: {len(df.columns)}")
print(f"💾 Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# Column names and data types
print("\n📋 COLUMNS:")
for i, col in enumerate(df.columns, 1):
    dtype = df[col].dtype
    non_null = df[col].notna().sum()
    null_pct = (df[col].isna().sum() / len(df)) * 100
    unique = df[col].nunique()
    print(f"   {i:2d}. {col:25s} | {str(dtype):12s} | Non-null: {non_null:6,} ({100-null_pct:5.1f}%) | Unique: {unique:7,}")

# First few rows
print("\n🔍 FIRST 5 MOVIES:")
display_cols = [col for col in ['title', 'release_date', 'budget', 'revenue', 'popularity'] if col in df.columns]
print(df[display_cols].head().to_string(index=False))

# Missing values summary
print("\n🚨 MISSING VALUES (Top 10):")
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({
    'Column': missing.index,
    'Missing': missing.values,
    'Percentage': missing_pct.values
})
missing_df = missing_df[missing_df['Missing'] > 0].sort_values('Missing', ascending=False).head(10)

if len(missing_df) > 0:
    for idx, row in missing_df.iterrows():
        print(f"   {row['Column']:25s}: {row['Missing']:7,} ({row['Percentage']:5.1f}%)")
else:
    print("   No missing values found!")

# Numeric statistics
print("\n💰 BUDGET & REVENUE STATISTICS:")
numeric_cols = [col for col in ['budget', 'revenue'] if col in df.columns]
if numeric_cols:
    print(df[numeric_cols].describe().to_string())

# Date range
print("\n📅 RELEASE DATE RANGE:")
if 'release_date' in df.columns:
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    print(f"   Earliest: {df['release_date'].min()}")
    print(f"   Latest: {df['release_date'].max()}")
    
    # Year distribution
    df['year'] = df['release_date'].dt.year
    year_counts = df['year'].value_counts().sort_index()
    print(f"\n   Movies by decade:")
    for decade in range(1900, 2030, 10):
        decade_count = year_counts[(year_counts.index >= decade) & (year_counts.index < decade + 10)].sum()
        if decade_count > 0:
            print(f"      {decade}s: {decade_count:,} movies")

# Top movies by revenue
print("\n💎 TOP 10 HIGHEST GROSSING MOVIES (in sample):")
if 'revenue' in df.columns and 'title' in df.columns:
    top_movies = df.nlargest(10, 'revenue')[['title', 'release_date', 'revenue', 'budget']]
    for idx, row in top_movies.iterrows():
        revenue_b = row['revenue'] / 1e9 if pd.notna(row['revenue']) else 0
        budget_m = row['budget'] / 1e6 if pd.notna(row['budget']) else 0
        print(f"   {row['title'][:45]:45s} | ${revenue_b:.2f}B | Budget: ${budget_m:.0f}M")

# Genre distribution (if available)
if 'genres' in df.columns:
    print("\n🎭 TOP 10 GENRES:")
    # Assuming genres are separated by '-' or '|'
    all_genres = df['genres'].dropna().str.split('-').explode()
    genre_counts = all_genres.value_counts().head(10)
    for genre, count in genre_counts.items():
        print(f"   {genre:30s}: {count:,} movies")

print("\n" + "=" * 70)
print("✅ Exploration complete!")
print("\n💡 Note: Loaded first 100k rows for speed.")
print("   To load full dataset, modify the script (see comments in code)")
print("=" * 70)