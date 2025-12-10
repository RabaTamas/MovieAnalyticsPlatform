import pandas as pd
import requests
import os

print("=" * 60)
print("🔧 Movie Analytics Platform - Setup Test")
print("=" * 60)

# Test pandas
print("\n✅ Pandas version:", pd.__version__)

# TMDB API key - IDEIGLENESEN ide írd be a kulcsot!
# KÉSŐBB ezt a .env fájlba tesszük!
api_key = "IDE_ÍRD_BE_A_TMDB_API_KULCSOD"  # <--- Cseréld le!

if api_key and api_key != "IDE_ÍRD_BE_A_TMDB_API_KULCSOD":
    print("✅ TMDB API key set")
    print(f"   Key length: {len(api_key)} characters")
else:
    print("❌ TMDB API key not set!")
    print("   Írd be az API key-t a test_setup.py fájlba!")
    exit()

# Test TMDB API connection
print("\n⏳ Testing TMDB API connection...")
url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"

try:
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        print("✅ TMDB API connection successful!")
        data = response.json()
        print(f"   Retrieved {len(data['results'])} popular movies")
        print(f"   First movie: {data['results'][0]['title']}")
    elif response.status_code == 401:
        print("❌ TMDB API authentication failed")
        print("   Ellenőrizd az API key-t a TMDB weboldalon!")
    else:
        print(f"❌ TMDB API connection failed: HTTP {response.status_code}")
        
except requests.exceptions.Timeout:
    print("❌ Connection timeout - check your internet connection")
except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")

print("\n" + "=" * 60)
print("✅ Setup test complete!")
print("=" * 60)