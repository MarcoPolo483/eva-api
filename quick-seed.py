"""Quick seed script using demo-data.json"""
import json
import requests
import uuid

API_BASE = "http://127.0.0.1:8000"
API_KEY = "demo-api-key"
DEMO_USER_ID = str(uuid.uuid4())

# Load demo data
with open("chat-ui/demo-data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

spaces = [
    {
        "name": "Service Canada / Service Canada",
        "description": "Employment Insurance, Canada Pension Plan | Assurance-emploi, Régime de pensions du Canada",
        "owner_id": DEMO_USER_ID,
        "owner_email": "demo@canada.ca"
    },
    {
        "name": "EVA RAG Documentation",
        "description": "Technical documentation for the EVA RAG system architecture",
        "owner_id": DEMO_USER_ID,
        "owner_email": "demo@canada.ca"
    }
]

print("🌱 Seeding demo spaces...")
print(f"API: {API_BASE}")

for space in spaces:
    try:
        response = requests.post(
            f"{API_BASE}/api/v1/spaces",
            headers=headers,
            json=space
        )
        if response.status_code == 201:
            print(f"✅ Created: {space['name']}")
        elif response.status_code == 409:
            print(f"ℹ️  Already exists: {space['name']}")
        else:
            print(f"❌ Failed: {space['name']} - {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error creating {space['name']}: {e}")

print("\n✅ Done! Refresh your browser to see the spaces.")
