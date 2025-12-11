import { useState } from 'react'

const templates = [
  {
    name: 'Create Space',
    language: 'python',
    code: `import requests

response = requests.post(
    "https://api.eva-platform.com/api/v1/spaces",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={
        "name": "My Workspace",
        "description": "Project documentation"
    }
)

print(response.json())`
  },
  {
    name: 'Submit Query',
    language: 'javascript',
    code: `const response = await fetch(
  'https://api.eva-platform.com/api/v1/queries',
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      space_id: '550e8400-e29b-41d4-a716-446655440000',
      question: 'What are the requirements?'
    })
  }
);

const data = await response.json();
console.log(data);`
  },
  {
    name: 'Upload Document',
    language: 'curl',
    code: `curl -X POST \\
  https://api.eva-platform.com/api/v1/spaces/{space_id}/documents \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "file=@document.pdf" \\
  -F 'metadata={"tags":["manual"]}'`
  }
]

export default function Sandbox() {
  const [selectedTemplate, setSelectedTemplate] = useState(templates[0])
  const [code, setCode] = useState(templates[0].code)
  const [output, setOutput] = useState('')
  const [running, setRunning] = useState(false)

  const handleTemplateChange = (template: typeof templates[0]) => {
    setSelectedTemplate(template)
    setCode(template.code)
    setOutput('')
  }

  const handleRun = () => {
    setRunning(true)
    setOutput('Note: Sandbox execution requires backend integration.\n\nExpected output:\n{\n  "success": true,\n  "data": {...}\n}')
    setTimeout(() => setRunning(false), 1000)
  }

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '3rem 1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          API Sandbox
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#6B7280' }}>
          Try the API with live code examples - no setup required
        </p>
      </div>

      {/* Info Banner */}
      <div style={{
        background: '#DBEAFE',
        border: '1px solid #93C5FD',
        padding: '1rem',
        borderRadius: '0.5rem',
        marginBottom: '1.5rem',
        fontSize: '0.875rem',
        color: '#1E40AF'
      }}>
        💡 <strong>Tip:</strong> Replace YOUR_API_KEY with your actual API key to run live requests
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '1.5rem' }}>
        {/* Template Selector */}
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
              Code Templates
            </div>
            {templates.map((template, idx) => (
              <button
                key={idx}
                onClick={() => handleTemplateChange(template)}
                style={{
                  width: '100%',
                  padding: '1rem',
                  textAlign: 'left',
                  border: 'none',
                  borderBottom: '1px solid #E5E7EB',
                  background: selectedTemplate === template ? '#EFF6FF' : 'white',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
              >
                <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827', marginBottom: '0.25rem' }}>
                  {template.name}
                </div>
                <div style={{
                  fontSize: '0.75rem',
                  color: '#6B7280',
                  textTransform: 'uppercase',
                  fontFamily: 'monospace'
                }}>
                  {template.language}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Code Editor */}
        <div>
          <div style={{
            background: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '0.5rem',
            overflow: 'hidden',
            marginBottom: '1.5rem'
          }}>
            <div style={{
              padding: '1rem',
              borderBottom: '1px solid #E5E7EB',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontWeight: '600', fontSize: '0.875rem' }}>Code Editor</span>
                <span style={{
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  background: '#F3F4F6',
                  fontSize: '0.75rem',
                  fontFamily: 'monospace',
                  color: '#6B7280'
                }}>
                  {selectedTemplate.language}
                </span>
              </div>
              <button
                onClick={handleRun}
                disabled={running}
                style={{
                  padding: '0.5rem 1.5rem',
                  background: running ? '#9CA3AF' : '#10B981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  fontWeight: '600',
                  cursor: running ? 'not-allowed' : 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                {running ? '▶ Running...' : '▶ Run Code'}
              </button>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              rows={16}
              style={{
                width: '100%',
                padding: '1.5rem',
                border: 'none',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                background: '#1F2937',
                color: '#F9FAFB',
                resize: 'vertical',
                outline: 'none'
              }}
            />
          </div>

          {/* Output */}
          {output && (
            <div style={{
              background: 'white',
              border: '1px solid #E5E7EB',
              borderRadius: '0.5rem',
              overflow: 'hidden'
            }}>
              <div style={{
                padding: '1rem',
                borderBottom: '1px solid #E5E7EB',
                fontWeight: '600',
                fontSize: '0.875rem',
                background: '#F9FAFB'
              }}>
                Output
              </div>
              <pre style={{
                margin: 0,
                padding: '1.5rem',
                background: '#111827',
                color: '#10B981',
                fontSize: '0.875rem',
                fontFamily: 'monospace',
                overflow: 'auto'
              }}>
                {output}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
