"""
Locust load testing for EVA API.

Tests API performance under load with realistic scenarios.
"""

from locust import HttpUser, task, between, TaskSet
import random
import string
from uuid import uuid4


def random_string(length=10):
    """Generate random string for test data."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class SpaceOperations(TaskSet):
    """Task set for space-related operations."""
    
    def on_start(self):
        """Setup: Create a test space."""
        response = self.client.post(
            "/api/v1/spaces",
            json={
                "name": f"Load Test Space {random_string()}",
                "description": "Created by load testing",
                "tenant_id": "load-test",
                "created_by": "locust",
            },
            headers={"Authorization": f"Bearer {self.user.api_key}"},
        )
        if response.status_code == 201:
            self.space_id = response.json()["id"]
        else:
            self.space_id = None
    
    @task(10)
    def list_spaces(self):
        """List spaces with pagination."""
        self.client.get(
            "/api/v1/spaces",
            params={"limit": 20, "offset": 0},
            headers={"Authorization": f"Bearer {self.user.api_key}"},
            name="/api/v1/spaces [LIST]",
        )
    
    @task(5)
    def get_space(self):
        """Get specific space details."""
        if self.space_id:
            self.client.get(
                f"/api/v1/spaces/{self.space_id}",
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id} [GET]",
            )
    
    @task(3)
    def update_space(self):
        """Update space metadata."""
        if self.space_id:
            self.client.patch(
                f"/api/v1/spaces/{self.space_id}",
                json={
                    "name": f"Updated Space {random_string(5)}",
                    "tags": ["load-test", "updated"],
                },
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id} [PATCH]",
            )


class DocumentOperations(TaskSet):
    """Task set for document-related operations."""
    
    def on_start(self):
        """Setup: Create space and upload document."""
        # Create space
        response = self.client.post(
            "/api/v1/spaces",
            json={
                "name": f"Doc Test Space {random_string()}",
                "description": "For document testing",
                "tenant_id": "load-test",
                "created_by": "locust",
            },
            headers={"Authorization": f"Bearer {self.user.api_key}"},
        )
        if response.status_code == 201:
            self.space_id = response.json()["id"]
        else:
            self.space_id = None
            return
        
        # Upload document
        files = {
            "file": (f"test-{random_string()}.txt", b"Load test document content"),
        }
        response = self.client.post(
            f"/api/v1/spaces/{self.space_id}/documents",
            files=files,
            headers={"Authorization": f"Bearer {self.user.api_key}"},
        )
        if response.status_code == 201:
            self.document_id = response.json()["id"]
        else:
            self.document_id = None
    
    @task(8)
    def list_documents(self):
        """List documents in space."""
        if self.space_id:
            self.client.get(
                f"/api/v1/spaces/{self.space_id}/documents",
                params={"limit": 20},
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id}/documents [LIST]",
            )
    
    @task(5)
    def get_document(self):
        """Get document metadata."""
        if self.space_id and self.document_id:
            self.client.get(
                f"/api/v1/spaces/{self.space_id}/documents/{self.document_id}",
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id}/documents/{doc_id} [GET]",
            )
    
    @task(2)
    def download_document(self):
        """Download document content."""
        if self.space_id and self.document_id:
            self.client.get(
                f"/api/v1/spaces/{self.space_id}/documents/{self.document_id}/download",
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id}/documents/{doc_id}/download [GET]",
            )


class QueryOperations(TaskSet):
    """Task set for query-related operations."""
    
    def on_start(self):
        """Setup: Create space for queries."""
        response = self.client.post(
            "/api/v1/spaces",
            json={
                "name": f"Query Test Space {random_string()}",
                "description": "For query testing",
                "tenant_id": "load-test",
                "created_by": "locust",
            },
            headers={"Authorization": f"Bearer {self.user.api_key}"},
        )
        if response.status_code == 201:
            self.space_id = response.json()["id"]
        else:
            self.space_id = None
    
    @task(5)
    def submit_query(self):
        """Submit a query for processing."""
        if self.space_id:
            queries = [
                "What is this document about?",
                "Summarize the main points",
                "What are the key findings?",
                "Explain the methodology",
                "What are the conclusions?",
            ]
            self.client.post(
                f"/api/v1/spaces/{self.space_id}/queries",
                json={
                    "query": random.choice(queries),
                    "created_by": "locust",
                },
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id}/queries [POST]",
            )
    
    @task(10)
    def list_queries(self):
        """List queries in space."""
        if self.space_id:
            self.client.get(
                f"/api/v1/spaces/{self.space_id}/queries",
                params={"limit": 20},
                headers={"Authorization": f"Bearer {self.user.api_key}"},
                name="/api/v1/spaces/{id}/queries [LIST]",
            )


class GraphQLOperations(TaskSet):
    """Task set for GraphQL operations."""
    
    @task(5)
    def query_spaces(self):
        """Query spaces via GraphQL."""
        query = """
        query ListSpaces($limit: Int!) {
            spaces(limit: $limit) {
                items {
                    id
                    name
                    documentCount
                }
                hasMore
            }
        }
        """
        self.client.post(
            "/graphql",
            json={"query": query, "variables": {"limit": 10}},
            headers={"Authorization": f"Bearer {self.user.api_key}"},
            name="/graphql [spaces query]",
        )
    
    @task(3)
    def mutation_create_space(self):
        """Create space via GraphQL mutation."""
        mutation = """
        mutation CreateSpace($input: CreateSpaceInput!) {
            createSpace(input: $input) {
                id
                name
            }
        }
        """
        self.client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "name": f"GraphQL Space {random_string()}",
                        "description": "Created via GraphQL",
                        "tenantId": "load-test",
                        "createdBy": "locust",
                    }
                },
            },
            headers={"Authorization": f"Bearer {self.user.api_key}"},
            name="/graphql [createSpace mutation]",
        )


class APIUser(HttpUser):
    """
    Simulated API user with mixed workload.
    
    Weight distribution:
    - 40% Space operations (read-heavy)
    - 30% Document operations (balanced)
    - 20% Query operations (write-heavy)
    - 10% GraphQL operations
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    tasks = {
        SpaceOperations: 40,
        DocumentOperations: 30,
        QueryOperations: 20,
        GraphQLOperations: 10,
    }
    
    def on_start(self):
        """Setup: Get API key from environment."""
        import os
        self.api_key = os.getenv("EVA_API_KEY", "test-api-key")


class HealthCheckUser(HttpUser):
    """
    Lightweight user that only hits health endpoints.
    Used for baseline performance testing.
    """
    
    wait_time = between(0.5, 1)
    
    @task
    def health_check(self):
        """Check API health."""
        self.client.get("/health", name="/health [GET]")
