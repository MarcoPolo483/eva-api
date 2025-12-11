"""
Integration tests for GraphQL API with full stack.

Tests GraphQL queries and mutations against real Azure services.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from eva_api.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphql_create_and_query_space():
    """Test GraphQL space creation and querying."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create space via GraphQL
        mutation = """
        mutation CreateSpace($input: CreateSpaceInput!) {
            createSpace(input: $input) {
                id
                name
                description
                tenantId
                documentCount
                createdAt
            }
        }
        """

        variables = {
            "input": {
                "name": "GraphQL Integration Test",
                "description": "Created via GraphQL mutation",
                "tenantId": "test-tenant",
                "createdBy": "integration-test",
                "tags": ["graphql", "integration"]
            }
        }

        response = await client.post(
            "/graphql",
            json={"query": mutation, "variables": variables},
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "createSpace" in data["data"]

        space = data["data"]["createSpace"]
        space_id = space["id"]
        assert space["name"] == "GraphQL Integration Test"
        assert space["documentCount"] == 0

        # Query the created space
        query = """
        query GetSpace($id: ID!) {
            space(id: $id) {
                id
                name
                description
                documentCount
                tags
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={"query": query, "variables": {"id": space_id}},
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        queried_space = data["data"]["space"]
        assert queried_space["id"] == space_id
        assert "graphql" in queried_space["tags"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphql_list_spaces_pagination():
    """Test GraphQL space listing with pagination."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        query = """
        query ListSpaces($limit: Int!, $cursor: String) {
            spaces(limit: $limit, cursor: $cursor) {
                items {
                    id
                    name
                    documentCount
                }
                cursor
                hasMore
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={"query": query, "variables": {"limit": 5}},
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "spaces" in data["data"]

        spaces = data["data"]["spaces"]
        assert "items" in spaces
        assert "hasMore" in spaces
        assert isinstance(spaces["items"], list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphql_update_space():
    """Test GraphQL space update mutation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create space first
        create_mutation = """
        mutation CreateSpace($input: CreateSpaceInput!) {
            createSpace(input: $input) {
                id
                name
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={
                "query": create_mutation,
                "variables": {
                    "input": {
                        "name": "Original Name",
                        "description": "Original",
                        "tenantId": "test-tenant",
                        "createdBy": "integration-test"
                    }
                }
            },
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        space_id = response.json()["data"]["createSpace"]["id"]

        # Update space
        update_mutation = """
        mutation UpdateSpace($id: ID!, $input: UpdateSpaceInput!) {
            updateSpace(id: $id, input: $input) {
                id
                name
                description
                tags
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={
                "query": update_mutation,
                "variables": {
                    "id": space_id,
                    "input": {
                        "name": "Updated Name",
                        "description": "Updated via GraphQL",
                        "tags": ["updated"]
                    }
                }
            },
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        updated_space = data["data"]["updateSpace"]
        assert updated_space["name"] == "Updated Name"
        assert "updated" in updated_space["tags"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphql_query_submission():
    """Test GraphQL query submission and status tracking."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create space
        create_mutation = """
        mutation CreateSpace($input: CreateSpaceInput!) {
            createSpace(input: $input) {
                id
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={
                "query": create_mutation,
                "variables": {
                    "input": {
                        "name": "Query Test Space",
                        "description": "For testing queries",
                        "tenantId": "test-tenant",
                        "createdBy": "integration-test"
                    }
                }
            },
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        space_id = response.json()["data"]["createSpace"]["id"]

        # Submit query
        query_mutation = """
        mutation SubmitQuery($input: SubmitQueryInput!) {
            submitQuery(input: $input) {
                id
                queryText
                status
                spaceId
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={
                "query": query_mutation,
                "variables": {
                    "input": {
                        "spaceId": space_id,
                        "queryText": "What is this space about?",
                        "createdBy": "integration-test"
                    }
                }
            },
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        query_data = data["data"]["submitQuery"]
        assert query_data["queryText"] == "What is this space about?"
        assert query_data["status"] in ["PENDING", "PROCESSING"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphql_subscription_connection():
    """Test GraphQL subscription WebSocket connection."""
    # Note: Full WebSocket testing requires additional setup
    # This test verifies the subscription is defined
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Introspection query to check subscription exists
        query = """
        query IntrospectionQuery {
            __schema {
                subscriptionType {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={"query": query},
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        subscription_type = data["data"]["__schema"]["subscriptionType"]
        assert subscription_type is not None

        # Check queryUpdates subscription exists
        fields = {f["name"] for f in subscription_type["fields"]}
        assert "queryUpdates" in fields


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graphql_error_handling():
    """Test GraphQL error responses."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Query non-existent space
        query = """
        query GetSpace($id: ID!) {
            space(id: $id) {
                id
                name
            }
        }
        """

        response = await client.post(
            "/graphql",
            json={"query": query, "variables": {"id": str(uuid4())}},
            headers={"Authorization": f"Bearer {settings.jwt_secret}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Should return null for non-existent space, not error
        assert data["data"]["space"] is None
