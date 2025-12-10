import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

load_dotenv()

print("=" * 70)
print("📦 Azure Blob Storage - Create Containers")
print("=" * 70)

# Get connection string
conn_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Create BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(conn_string)

# Containers to create
containers = [
    ('raw', 'Raw data from Kaggle and TMDB API'),
    ('processed', 'Cleaned and processed data'),
    ('ml-models', 'Machine learning model outputs')
]

print("\n🔨 Creating containers...\n")

for container_name, description in containers:
    try:
        # Check if container exists
        container_client = blob_service_client.get_container_client(container_name)
        
        if not container_client.exists():
            # Create container
            blob_service_client.create_container(container_name)
            print(f"✅ Created: '{container_name}' - {description}")
        else:
            print(f"ℹ️  Already exists: '{container_name}'")
            
    except Exception as e:
        print(f"❌ Error creating '{container_name}': {e}")

print("\n📋 Listing all containers:")
print("-" * 70)

containers = blob_service_client.list_containers()
for container in containers:
    print(f"   📁 {container.name}")

print("\n" + "=" * 70)
print("✅ Blob containers ready!")
print("=" * 70)