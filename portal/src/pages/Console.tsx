import { useState } from 'react'

const endpoints = [
  { category: 'Auth', method: 'POST', path: '/auth/api-keys', name: 'Create API Key' },
  { category: 'Auth', method: 'GET', path: '/auth/api-keys', name: 'List API Keys' },
  { category: 'Spaces', method: 'POST', path: '/api/v1/spaces', name: 'Create Space' },
  { category: 'Spaces', method: 'GET', path: '/api/v1/spaces', name: 'List Spaces' },
  { category: 'Spaces', method: 'GET', path: '/api/v1/spaces/{space_id}', name: 'Get Space' },
  { category: 'Spaces', method: 'PUT', path: '/api/v1/spaces/{space_id}', name: 'Update Space' },
  { category: 'Spaces', method: 'DELETE', path: '/api/v1/spaces/{space_id}', name: 'Delete Space' },
  { category: 'Documents', method: 'POST', path: '/api/v1/spaces/{space_id}/documents', name: 'Upload Document' },
  { category: 'Documents', method: 'GET', path: '/api/v1/spaces/{space_id}/documents', name: 'List Documents' },
  { category: 'Documents', method: 'GET', path: '/api/v1/documents/{document_id}', name: 'Get Document' },
  { category: 'Documents', method: 'DELETE', path: '/api/v1/documents/{document_id}', name: 'Delete Document' },
  { category: 'Queries', method: 'POST', path: '/api/v1/queries', name: 'Submit Query' },
  { category: 'Queries', method: 'GET', path: '/api/v1/queries/{query_id}', name: 'Get Query Status' },
  { category: 'Queries', method: 'GET', path: '/api/v1/queries/{query_id}/result', name: 'Get Query Result' },
  { category: 'Health', method: 'GET', path: '/health', name: 'Health Check' },
  { category: 'Health', method: 'GET', path: '/health/ready', name: 'Readiness Check' },
]

const exampleBodies: Record<string, string> = {
  'POST /auth/api-keys': `{
  "name": "My API Key",
  "description": "Production key",
  "scopes": ["read", "write"]
}`,
  'POST /api/v1/spaces': `{
  "name": "My Workspace",
  "description": "Project documentation",
  "metadata": {
    "department": "Engineering"
  }
}`,
  'PUT /api/v1/spaces/{space_id}': `{
  "name": "Updated Name",
  "description": "Updated description"
}`,
  'POST /api/v1/queries': `{
  "space_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What are the installation requirements?",
  "parameters": {
    "max_results": 5,
    "temperature": 0.7
  }
}`
}

const methodColors: Record<string, string> = {
  GET: '#3B82F6',
  POST: '#10B981',
  PUT: '#F59E0B',
  DELETE: '#EF4444'
}

export default function Console() {
  const [selectedEndpoint, setSelectedEndpoint] = useState(endpoints[0])
  const [apiKey, setApiKey] = useState('eva_live_...')
  const [requestBody, setRequestBody] = useState('')
  const [response, setResponse] = useState('')
  const [loading, setLoading] = useState(false)
  const [statusCode, setStatusCode] = useState<number | null>(null)

  const handleEndpointChange = (endpoint: typeof endpoints[0]) => {
    setSelectedEndpoint(endpoint)
    const key = `${endpoint.method} ${endpoint.path}`
    setRequestBody(exampleBodies[key] || '')
    setResponse('')
    setStatusCode(null)
  }

  const handleSendRequest = async () => {
    setLoading(true)
    setResponse('')
    setStatusCode(null)

    try {
      const url = `http://localhost:8000${selectedEndpoint.path.replace(/\{[^}]+\}/g, '550e8400-e29b-41d4-a716-446655440000')}`
      const options: RequestInit = {
        method: selectedEndpoint.method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        }
      }

      if (['POST', 'PUT'].includes(selectedEndpoint.method) && requestBody) {
        options.body = requestBody
      }

      const res = await fetch(url, options)
      const data = await res.json()
      setStatusCode(res.status)
      setResponse(JSON.stringify(data, null, 2))
    } catch (error: any) {
      setStatusCode(500)
      setResponse(JSON.stringify({
        error: 'Request failed',
        message: error.message
      }, null, 2))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '3rem 1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          API Console
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#6B7280' }}>
          Test EVA API endpoints directly from your browser
        </p>
      </div>

      {/* API Key Input */}
      <div style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        border: '1px solid #E5E7EB',
        marginBottom: '1.5rem'
      }}>
        <label style={{
          display: 'block',
          fontSize: '0.875rem',
          fontWeight: '600',
          color: '#374151',
          marginBottom: '0.5rem'
        }}>
          API Key (Authorization Header)
        </label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="eva_live_your_api_key"
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #D1D5DB',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            fontFamily: 'monospace'
          }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
        {/* Endpoint Selector */}
        <div>
          <div style={{
            background: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '0.5rem',
            overflow: 'hidden'
          }}>
            <div style={{
              padding: '1rem',
              borderBottom: '1px solid #E5E7EB',
              background: '#F9FAFB',
              fontWeight: '600',
              fontSize: '0.875rem'
            }}>
              Select Endpoint
            </div>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {endpoints.map((endpoint, idx) => (
                <button
                  key={idx}
                  onClick={() => handleEndpointChange(endpoint)}
                  style={{
                    width: '100%',
                    padding: '1rem',
                    textAlign: 'left',
                    border: 'none',
                    borderBottom: '1px solid #E5E7EB',
                    background: selectedEndpoint === endpoint ? '#EFF6FF' : 'white',
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                >
                  <div style={{
                    display: 'inline-block',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    color: 'white',
                    background: methodColors[endpoint.method],
                    marginBottom: '0.25rem'
                  }}>
                    {endpoint.method}
                  </div>
                  <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>
                    {endpoint.name}
                  </div>
                  <code style={{ fontSize: '0.75rem', color: '#6B7280', fontFamily: 'monospace' }}>
                    {endpoint.path}
                  </code>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Request/Response Panel */}
        <div>
          {/* Request Section */}
          <div style={{
            background: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '0.5rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              padding: '1rem',
              borderBottom: '1px solid #E5E7EB',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem'
            }}>
              <div style={{
                padding: '0.5rem 1rem',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: 'white',
                background: methodColors[selectedEndpoint.method]
              }}>
                {selectedEndpoint.method}
              </div>
              <code style={{
                flex: 1,
                fontSize: '0.875rem',
                fontFamily: 'monospace',
                color: '#1F2937'
              }}>
                {selectedEndpoint.path}
              </code>
              <button
                onClick={handleSendRequest}
                disabled={loading}
                style={{
                  padding: '0.5rem 1.5rem',
                  background: loading ? '#9CA3AF' : '#3B82F6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  fontWeight: '600',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                {loading ? 'Sending...' : 'Send Request'}
              </button>
            </div>

            {['POST', 'PUT'].includes(selectedEndpoint.method) && (
              <div style={{ padding: '1rem' }}>
                <label style={{
                  display: 'block',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: '#374151',
                  marginBottom: '0.5rem'
                }}>
                  Request Body (JSON)
                </label>
                <textarea
                  value={requestBody}
                  onChange={(e) => setRequestBody(e.target.value)}
                  rows={12}
                  style={{
                    width: '100%',
                    padding: '1rem',
                    border: '1px solid #D1D5DB',
                    borderRadius: '0.375rem',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    background: '#1F2937',
                    color: '#F9FAFB',
                    resize: 'vertical'
                  }}
                />
              </div>
            )}
          </div>

          {/* Response Section */}
          {response && (
            <div style={{
              background: 'white',
              border: '1px solid #E5E7EB',
              borderRadius: '0.5rem'
            }}>
              <div style={{
                padding: '1rem',
                borderBottom: '1px solid #E5E7EB',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <span style={{ fontWeight: '600', fontSize: '0.875rem' }}>Response</span>
                {statusCode && (
                  <span style={{
                    padding: '0.25rem 0.75rem',
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    background: statusCode < 300 ? '#D1FAE5' : '#FEE2E2',
                    color: statusCode < 300 ? '#065F46' : '#991B1B'
                  }}>
                    {statusCode}
                  </span>
                )}
              </div>
              <div style={{ padding: '1rem' }}>
                <pre style={{
                  margin: 0,
                  padding: '1rem',
                  background: '#1F2937',
                  color: '#F9FAFB',
                  borderRadius: '0.375rem',
                  overflow: 'auto',
                  fontSize: '0.875rem',
                  fontFamily: 'monospace',
                  maxHeight: '400px'
                }}>
                  {response}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
