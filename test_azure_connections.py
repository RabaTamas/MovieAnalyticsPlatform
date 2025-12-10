import os
from dotenv import load_dotenv
import pyodbc
from azure.storage.blob import BlobServiceClient

load_dotenv()

print("=" * 70)
print("🔌 Azure Connection Tests")
print("=" * 70)

# =============================================================================
# TEST 1: Azure SQL Database
# =============================================================================
print("\n📊 TEST 1: Azure SQL Database")
print("-" * 70)

try:
    server = os.getenv('AZURE_SQL_SERVER')
    database = os.getenv('AZURE_SQL_DATABASE')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    conn_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    
    print(f"⏳ Connecting to: {server}/{database}")
    conn = pyodbc.connect(conn_string, timeout=10)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    
    print(f"✅ Connection successful!")
    print(f"   SQL Server version: {version[:50]}...")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Check firewall rules in Azure Portal")
    print("   2. Verify credentials in .env file")
    print("   3. Make sure 'Allow Azure services' is enabled")

# =============================================================================
# TEST 2: Azure Blob Storage
# =============================================================================
print("\n📦 TEST 2: Azure Blob Storage")
print("-" * 70)

try:
    conn_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    
    print(f"⏳ Connecting to Blob Storage...")
    blob_service_client = BlobServiceClient.from_connection_string(conn_string)
    
    # List containers
    containers = list(blob_service_client.list_containers())
    
    print(f"✅ Connection successful!")
    print(f"   Existing containers: {len(containers)}")
    
    if len(containers) == 0:
        print("   (No containers yet - we'll create them in the next step)")
    else:
        for container in containers[:5]:
            print(f"   - {container.name}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Check connection string in .env file")
    print("   2. Verify storage account name and key")

print("\n" + "=" * 70)
print("✅ Connection tests complete!")
print("=" * 70)