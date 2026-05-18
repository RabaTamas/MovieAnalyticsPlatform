import pandas as pd
import os

# Load
df = pd.read_csv('data/processed/movies_cleaned.csv')
print(f"Total rows: {len(df)}")

# Output folder
os.makedirs('data/chunks', exist_ok=True)

# Split into 4 chunks
chunks = 4
chunk_size = len(df) // chunks

for i in range(chunks):
    start = i * chunk_size
    end = start + chunk_size if i < chunks - 1 else len(df)
    chunk = df.iloc[start:end]
    path = f'data/chunks/movies_chunk_{i+1}.csv'
    chunk.to_csv(path, index=False)
    print(f"chunk_{i+1}: {len(chunk)} rows → {path}")

print("Done!")