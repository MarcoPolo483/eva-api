import { useState } from 'react'

interface Endpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  path: string
  description: string
  requiresAuth: boolean
  requestBody?: string
  responseExample?: string
}

const endpoints: Record<string, Endpoint[]> = {
  'Authentication': [
    {
      method: 'POST',
      path: '/auth/api-keys',
      description: 'Create a new API key for programmatic access',
      requiresAuth: true,
      requestBody: `{
  "name": "My API Key",
  "description": "Production key",
  "scopes": ["read", "write"]
}`,
      responseExample: `{
  "success": true,
  "data": {
    "key_id": "key_abc123",
    "api_key": "eva_live_xyz789...",
    "name": "My API Key",
    "created_at": "2025-12-07T10:00:00Z"
  }
}`
    },
    {
      method: 'GET',
      path: '/auth/api-keys',
      description: 'List all API keys for authenticated tenant',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": [
    {
      "key_id": "key_abc123",
      "name": "My API Key",
      "created_at": "2025-12-07T10:00:00Z",
      "last_used": "2025-12-07T12:30:00Z"
    }
  ]
}`
    },
    {
      method: 'DELETE',
      path: '/auth/api-keys/{key_id}',
      description: 'Revoke an API key',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "message": "API key revoked successfully"
}`
    }
  ],
  'Spaces': [
    {
      method: 'POST',
      path: '/api/v1/spaces',
      description: 'Create a new knowledge space',
      requiresAuth: true,
      requestBody: `{
  "name": "Product Documentation",
  "description": "All product docs and guides",
  "metadata": {
    "department": "Engineering"
  }
}`,
      responseExample: `{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Product Documentation",
    "description": "All product docs and guides",
    "document_count": 0,
    "created_at": "2025-12-07T10:00:00Z"
  }
}`
    },
    {
      method: 'GET',
      path: '/api/v1/spaces',
      description: 'List all spaces with cursor-based pagination',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Product Documentation",
        "document_count": 42
      }
    ],
    "cursor": "next_page_token",
    "has_more": true
  }
}`
    },
    {
      method: 'GET',
      path: '/api/v1/spaces/{space_id}',
      description: 'Get details of a specific space',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Product Documentation",
    "description": "All product docs and guides",
    "document_count": 42,
    "created_at": "2025-12-07T10:00:00Z",
    "updated_at": "2025-12-07T15:30:00Z"
  }
}`
    },
    {
      method: 'PUT',
      path: '/api/v1/spaces/{space_id}',
      description: 'Update space details',
      requiresAuth: true,
      requestBody: `{
  "name": "Updated Name",
  "description": "New description"
}`,
      responseExample: `{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Updated Name",
    "updated_at": "2025-12-07T16:00:00Z"
  }
}`
    },
    {
      method: 'DELETE',
      path: '/api/v1/spaces/{space_id}',
      description: 'Delete a space and all its documents',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "message": "Space deleted successfully"
}`
    }
  ],
  'Documents': [
    {
      method: 'POST',
      path: '/api/v1/spaces/{space_id}/documents',
      description: 'Upload a document to a space (multipart/form-data)',
      requiresAuth: true,
      requestBody: `FormData:
  file: <binary>
  metadata: {"tags": ["manual", "v2.0"]}`,
      responseExample: `{
  "success": true,
  "data": {
    "id": "doc_abc123",
    "filename": "user-guide.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1048576,
    "space_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-12-07T11:00:00Z"
  }
}`
    },
    {
      method: 'GET',
      path: '/api/v1/spaces/{space_id}/documents',
      description: 'List documents in a space with pagination',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": {
    "items": [
      {
        "id": "doc_abc123",
        "filename": "user-guide.pdf",
        "size_bytes": 1048576,
        "created_at": "2025-12-07T11:00:00Z"
      }
    ],
    "cursor": "next_page_token",
    "has_more": false
  }
}`
    },
    {
      method: 'GET',
      path: '/api/v1/documents/{document_id}',
      description: 'Get document metadata',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": {
    "id": "doc_abc123",
    "filename": "user-guide.pdf",
    "content_type": "application/pdf",
    "size_bytes": 1048576,
    "space_id": "550e8400-e29b-41d4-a716-446655440000",
    "download_url": "https://...",
    "created_at": "2025-12-07T11:00:00Z"
  }
}`
    },
    {
      method: 'DELETE',
      path: '/api/v1/documents/{document_id}',
      description: 'Delete a document',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "message": "Document deleted successfully"
}`
    }
  ],
  'Queries': [
    {
      method: 'POST',
      path: '/api/v1/queries',
      description: 'Submit a RAG query against a space',
      requiresAuth: true,
      requestBody: `{
  "space_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What are the installation requirements?",
  "parameters": {
    "max_results": 5,
    "temperature": 0.7
  }
}`,
      responseExample: `{
  "success": true,
  "data": {
    "id": "query_xyz789",
    "status": "pending",
    "submitted_at": "2025-12-07T12:00:00Z"
  },
  "message": "Query submitted. Use GET /queries/{id} to check status."
}`
    },
    {
      method: 'GET',
      path: '/api/v1/queries/{query_id}',
      description: 'Get query status',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": {
    "id": "query_xyz789",
    "status": "completed",
    "submitted_at": "2025-12-07T12:00:00Z",
    "completed_at": "2025-12-07T12:00:03Z"
  }
}`
    },
    {
      method: 'GET',
      path: '/api/v1/queries/{query_id}/result',
      description: 'Get query result and answer',
      requiresAuth: true,
      responseExample: `{
  "success": true,
  "data": {
    "query_id": "query_xyz789",
    "answer": "The installation requires Python 3.9+, 4GB RAM...",
    "confidence": 0.92,
    "sources": [
      {
        "document_id": "doc_abc123",
        "filename": "install-guide.pdf",
        "relevance": 0.95
      }
    ],
    "processing_time_ms": 2847
  }
}`
    }
  ],
  'Health': [
    {
      method: 'GET',
      path: '/health',
      description: 'Basic health check endpoint',
      requiresAuth: false,
      responseExample: `{
  "status": "healthy",
  "timestamp": "2025-12-07T12:00:00Z"
}`
    },
    {
      method: 'GET',
      path: '/health/ready',
      description: 'Detailed readiness check with service status',
      requiresAuth: false,
      responseExample: `{
  "status": "ready",
  "services": {
    "cosmos_db": "healthy",
    "blob_storage": "healthy",
    "openai": "healthy"
  },
  "version": "1.0.0",
  "environment": "production"
}`
    }
  ]
}

const methodColors: Record<string, string> = {
  GET: 'bg-blue-500',
  POST: 'bg-green-500',
  PUT: 'bg-yellow-500',
  DELETE: 'bg-red-500'
}

export default function Documentation() {
  const [activeCategory, setActiveCategory] = useState('Authentication')
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null)

  const toggleEndpoint = (path: string) => {
    setExpandedEndpoint(expandedEndpoint === path ? null : path)
  }

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '3rem 1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          API Documentation
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#6B7280' }}>
          Complete reference for EVA API Platform endpoints
        </p>
      </div>

      {/* Base URL */}
      <div style={{ 
        background: 'linear-gradient(to right, #3B82F6, #8B5CF6)', 
        padding: '1.5rem',
        borderRadius: '0.5rem',
        marginBottom: '2rem',
        color: 'white'
      }}>
        <div style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '0.5rem' }}>
          BASE URL
        </div>
        <code style={{ fontSize: '1.125rem', fontFamily: 'monospace' }}>
          https://api.eva-platform.com
        </code>
      </div>

      {/* Authentication Info */}
      <div style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        border: '1px solid #E5E7EB',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          🔐 Authentication
        </h2>
        <p style={{ color: '#6B7280', marginBottom: '1rem' }}>
          Most endpoints require authentication. Include your API key in the Authorization header:
        </p>
        <div style={{
          background: '#1F2937',
          padding: '1rem',
          borderRadius: '0.375rem',
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          color: '#F9FAFB'
        }}>
          Authorization: Bearer eva_live_your_api_key_here
        </div>
      </div>

      {/* API Categories */}
      <div style={{ display: 'flex', gap: '2rem' }}>
        {/* Sidebar */}
        <div style={{ width: '200px', flexShrink: 0 }}>
          <div style={{
            background: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '0.5rem',
            padding: '0.5rem',
            position: 'sticky',
            top: '2rem'
          }}>
            {Object.keys(endpoints).map(category => (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.375rem',
                  background: activeCategory === category ? '#3B82F6' : 'transparent',
                  color: activeCategory === category ? 'white' : '#374151',
                  fontWeight: activeCategory === category ? '600' : '400',
                  cursor: 'pointer',
                  border: 'none',
                  marginBottom: '0.25rem',
                  transition: 'all 0.2s'
                }}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Endpoints */}
        <div style={{ flex: 1 }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
            {activeCategory}
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {endpoints[activeCategory].map(endpoint => {
              const isExpanded = expandedEndpoint === endpoint.path
              return (
                <div
                  key={endpoint.path}
                  style={{
                    background: 'white',
                    border: '1px solid #E5E7EB',
                    borderRadius: '0.5rem',
                    overflow: 'hidden'
                  }}
                >
                  {/* Endpoint Header */}
                  <button
                    onClick={() => toggleEndpoint(endpoint.path)}
                    style={{
                      width: '100%',
                      padding: '1.5rem',
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem'
                    }}
                  >
                    <span
                      className={methodColors[endpoint.method]}
                      style={{
                        padding: '0.25rem 0.75rem',
                        borderRadius: '0.25rem',
                        color: 'white',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        minWidth: '70px',
                        textAlign: 'center'
                      }}
                    >
                      {endpoint.method}
                    </span>
                    <code style={{
                      fontFamily: 'monospace',
                      fontSize: '0.875rem',
                      color: '#1F2937',
                      flex: 1
                    }}>
                      {endpoint.path}
                    </code>
                    {endpoint.requiresAuth && (
                      <span style={{
                        fontSize: '0.75rem',
                        color: '#6B7280',
                        background: '#F3F4F6',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '0.25rem'
                      }}>
                        🔒 Auth
                      </span>
                    )}
                    <span style={{ color: '#9CA3AF', fontSize: '1.25rem' }}>
                      {isExpanded ? '−' : '+'}
                    </span>
                  </button>

                  {/* Endpoint Details */}
                  {isExpanded && (
                    <div style={{
                      padding: '0 1.5rem 1.5rem 1.5rem',
                      borderTop: '1px solid #E5E7EB'
                    }}>
                      <p style={{ color: '#374151', marginBottom: '1.5rem', paddingTop: '1rem' }}>
                        {endpoint.description}
                      </p>

                      {endpoint.requestBody && (
                        <div style={{ marginBottom: '1.5rem' }}>
                          <div style={{
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            color: '#374151',
                            marginBottom: '0.5rem'
                          }}>
                            Request Body
                          </div>
                          <pre style={{
                            background: '#1F2937',
                            padding: '1rem',
                            borderRadius: '0.375rem',
                            overflow: 'auto',
                            fontSize: '0.875rem',
                            color: '#F9FAFB',
                            margin: 0
                          }}>
                            {endpoint.requestBody}
                          </pre>
                        </div>
                      )}

                      {endpoint.responseExample && (
                        <div>
                          <div style={{
                            fontSize: '0.875rem',
                            fontWeight: '600',
                            color: '#374151',
                            marginBottom: '0.5rem'
                          }}>
                            Response Example
                          </div>
                          <pre style={{
                            background: '#1F2937',
                            padding: '1rem',
                            borderRadius: '0.375rem',
                            overflow: 'auto',
                            fontSize: '0.875rem',
                            color: '#F9FAFB',
                            margin: 0
                          }}>
                            {endpoint.responseExample}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* GraphQL Section */}
      <div style={{ marginTop: '4rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          GraphQL API
        </h2>
        <div style={{
          background: 'white',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          border: '1px solid #E5E7EB'
        }}>
          <p style={{ color: '#6B7280', marginBottom: '1rem' }}>
            GraphQL endpoint for flexible queries:
          </p>
          <code style={{
            display: 'block',
            background: '#1F2937',
            padding: '1rem',
            borderRadius: '0.375rem',
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            color: '#F9FAFB',
            marginBottom: '1rem'
          }}>
            POST /graphql
          </code>
          <p style={{ color: '#6B7280', fontSize: '0.875rem' }}>
            Visit the <a href="/graphql" style={{ color: '#3B82F6', textDecoration: 'underline' }}>GraphQL Playground</a> for interactive schema exploration.
          </p>
        </div>
      </div>
    </div>
  )
}
