import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from datetime import datetime

load_dotenv()

print("=" * 70)
print("☁️  Upload Data to Azure Blob Storage")
print("=" * 70)

# Connection
conn_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
blob_service_client = BlobServiceClient.from_connection_string(conn_string)

# Files to upload
files_to_upload = [
    {
        'local_path': 'data/raw/movies.csv',
        'container': 'raw',
        'blob_name': 'movies/movies_full.csv',
        'description': 'Full raw dataset (722k movies)'
    },
    {
        'local_path': 'data/processed/movies_cleaned.csv',
        'container': 'processed',
        'blob_name': 'movies/movies_cleaned.csv',
        'description': 'Cleaned dataset (10k+ movies)'
    }
]

print("\n📤 Uploading files to Blob Storage...\n")

for file_info in files_to_upload:
    local_path = file_info['local_path']
    container_name = file_info['container']
    blob_name = file_info['blob_name']
    description = file_info['description']
    
    print(f"📁 {description}")
    print(f"   Local: {local_path}")
    print(f"   Blob: {container_name}/{blob_name}")
    
    try:
        # Check if file exists locally
        if not os.path.exists(local_path):
            print(f"   ❌ File not found locally: {local_path}")
            continue
        
        # Get file size
        file_size_mb = os.path.getsize(local_path) / (1024 ** 2)
        print(f"   📊 File size: {file_size_mb:.2f} MB")
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Upload file
        print(f"   ⏳ Uploading...")
        with open(local_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"   ✅ Uploaded successfully!")
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
    
    print()

print("=" * 70)
print("✅ Upload complete!")
print("=" * 70)

# List uploaded blobs
print("\n📋 Uploaded files in 'processed' container:")
print("-" * 70)

container_client = blob_service_client.get_container_client('processed')
blob_list = container_client.list_blobs()

for blob in blob_list:
    size_mb = blob.size / (1024 ** 2)
    print(f"   📄 {blob.name} ({size_mb:.2f} MB)")

print()