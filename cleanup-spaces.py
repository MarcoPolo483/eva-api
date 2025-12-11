"""Delete all spaces"""
import requests

API_BASE = "http://127.0.0.1:8000"
API_KEY = "demo-api-key"

headers = {"X-API-Key": API_KEY}

response = requests.get(f"{API_BASE}/api/v1/spaces", headers=headers)
spaces = response.json()["data"]["items"]

print(f"Found {len(spaces)} spaces to delete...")
for space in spaces:
    requests.delete(f"{API_BASE}/api/v1/spaces/{space['id']}", headers=headers)
    print(f"✅ Deleted: {space['name']}")

print("✅ All spaces deleted")
