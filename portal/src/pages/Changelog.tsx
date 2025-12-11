const releases = [
  {
    version: '1.2.0',
    date: '2025-12-01',
    type: 'minor',
    changes: [
      { type: 'added', description: 'GraphQL API now supports cursor-based pagination for all list queries' },
      { type: 'added', description: 'New /health/ready endpoint with detailed service status checks' },
      { type: 'improved', description: 'Query processing speed improved by 35% through caching optimization' },
      { type: 'fixed', description: 'Fixed race condition in document upload when processing large files' }
    ]
  },
  {
    version: '1.1.0',
    date: '2025-11-15',
    type: 'minor',
    changes: [
      { type: 'added', description: 'Support for batch document operations (upload up to 50 files at once)' },
      { type: 'added', description: 'New metadata filtering in document list endpoints' },
      { type: 'improved', description: 'Rate limiting now includes burst allowance for API keys' },
      { type: 'deprecated', description: 'Legacy /api/v1/search endpoint - use /api/v1/queries instead' }
    ]
  },
  {
    version: '1.0.1',
    date: '2025-11-01',
    type: 'patch',
    changes: [
      { type: 'fixed', description: 'Resolved authentication token expiration edge case' },
      { type: 'fixed', description: 'Corrected OpenAPI schema for document upload response' },
      { type: 'improved', description: 'Error messages now include request IDs for easier debugging' }
    ]
  },
  {
    version: '1.0.0',
    date: '2025-10-15',
    type: 'major',
    changes: [
      { type: 'added', description: '🎉 Initial stable release of EVA API Platform' },
      { type: 'added', description: 'Complete REST API with Spaces, Documents, and Queries endpoints' },
      { type: 'added', description: 'GraphQL API with full schema introspection' },
      { type: 'added', description: 'Azure AD B2C and Entra ID authentication support' },
      { type: 'added', description: 'Python, TypeScript, and .NET SDKs available' },
      { type: 'added', description: 'Rate limiting and API key management' }
    ]
  },
  {
    version: '0.9.0-beta',
    date: '2025-09-20',
    type: 'prerelease',
    changes: [
      { type: 'added', description: 'Beta release - RAG query engine with citation support' },
      { type: 'added', description: 'Document processing pipeline with Azure AI' },
      { type: 'breaking', description: 'Authentication now requires JWT tokens (API keys deprecated in v0.8)' }
    ]
  }
]

const changeTypeColors: Record<string, { bg: string; text: string; label: string }> = {
  added: { bg: '#D1FAE5', text: '#065F46', label: 'Added' },
  improved: { bg: '#DBEAFE', text: '#1E40AF', label: 'Improved' },
  fixed: { bg: '#FEF3C7', text: '#92400E', label: 'Fixed' },
  deprecated: { bg: '#FEE2E2', text: '#991B1B', label: 'Deprecated' },
  breaking: { bg: '#FEE2E2', text: '#991B1B', label: '⚠️ Breaking' }
}

const versionTypeColors: Record<string, string> = {
  major: '#EF4444',
  minor: '#3B82F6',
  patch: '#10B981',
  prerelease: '#F59E0B'
}

export default function Changelog() {
  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '3rem 1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          API Changelog
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#6B7280' }}>
          Track updates, new features, and breaking changes
        </p>
      </div>

      {/* Subscribe Banner */}
      <div style={{
        background: 'linear-gradient(to right, #3B82F6, #8B5CF6)',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        color: 'white',
        marginBottom: '3rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{ fontSize: '1.125rem', fontWeight: 'bold', marginBottom: '0.25rem' }}>
            Stay Updated
          </div>
          <div style={{ fontSize: '0.875rem', opacity: 0.9 }}>
            Get notified about new releases and breaking changes
          </div>
        </div>
        <button style={{
          padding: '0.75rem 1.5rem',
          background: 'white',
          color: '#3B82F6',
          border: 'none',
          borderRadius: '0.375rem',
          fontWeight: '600',
          cursor: 'pointer',
          fontSize: '0.875rem'
        }}>
          Subscribe →
        </button>
      </div>

      {/* Releases */}
      <div style={{ position: 'relative' }}>
        {/* Timeline Line */}
        <div style={{
          position: 'absolute',
          left: '23px',
          top: '20px',
          bottom: '20px',
          width: '2px',
          background: '#E5E7EB'
        }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {releases.map((release, idx) => (
            <div key={idx} style={{ position: 'relative', paddingLeft: '4rem' }}>
              {/* Timeline Dot */}
              <div style={{
                position: 'absolute',
                left: '16px',
                top: '8px',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: versionTypeColors[release.type],
                border: '3px solid white',
                boxShadow: '0 0 0 2px ' + versionTypeColors[release.type]
              }} />

              {/* Release Card */}
              <div style={{
                background: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '0.5rem',
                overflow: 'hidden'
              }}>
                {/* Release Header */}
                <div style={{
                  padding: '1.5rem',
                  borderBottom: '1px solid #E5E7EB',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#111827' }}>
                      v{release.version}
                    </h2>
                    <span style={{
                      padding: '0.25rem 0.75rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                      textTransform: 'uppercase',
                      color: 'white',
                      background: versionTypeColors[release.type]
                    }}>
                      {release.type}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#6B7280' }}>
                    {new Date(release.date).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </div>
                </div>

                {/* Changes */}
                <div style={{ padding: '1.5rem' }}>
                  <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {release.changes.map((change, changeIdx) => (
                      <li key={changeIdx} style={{ display: 'flex', gap: '1rem', alignItems: 'start' }}>
                        <span style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '0.25rem',
                          fontSize: '0.75rem',
                          fontWeight: '600',
                          background: changeTypeColors[change.type].bg,
                          color: changeTypeColors[change.type].text,
                          flexShrink: 0
                        }}>
                          {changeTypeColors[change.type].label}
                        </span>
                        <span style={{ color: '#374151', fontSize: '0.875rem', lineHeight: '1.5' }}>
                          {change.description}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Migration Guide CTA */}
      <div style={{
        marginTop: '3rem',
        padding: '2rem',
        background: '#F9FAFB',
        border: '1px solid #E5E7EB',
        borderRadius: '0.5rem',
        textAlign: 'center'
      }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#111827' }}>
          Need Help Migrating?
        </h3>
        <p style={{ color: '#6B7280', marginBottom: '1rem', fontSize: '0.875rem' }}>
          Check our migration guides for step-by-step instructions on upgrading between versions
        </p>
        <a href="/docs" style={{
          display: 'inline-block',
          padding: '0.75rem 1.5rem',
          background: '#3B82F6',
          color: 'white',
          borderRadius: '0.375rem',
          fontWeight: '600',
          textDecoration: 'none',
          fontSize: '0.875rem'
        }}>
          View Migration Guides →
        </a>
      </div>
    </div>
  )
}
