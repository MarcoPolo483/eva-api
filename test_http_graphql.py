"""Test GraphQL via HTTP client to debug 500 errors."""
import sys
sys.path.insert(0, 'src')

from fastapi.testclient import TestClient
from eva_api.main import app

client = TestClient(app)

# Test introspection
response = client.post(
    "/graphql",
    json={"query": "{ __typename }"}
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code != 200:
    print("\n❌ Failed!")
else:
    print("\n✅ Success!")
