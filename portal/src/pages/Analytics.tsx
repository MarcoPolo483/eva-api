import { useState } from 'react'

interface MetricCard {
  label: string
  value: string
  change: string
  trend: 'up' | 'down'
}

const metrics: MetricCard[] = [
  { label: 'Total Requests', value: '2.4M', change: '+12.5%', trend: 'up' },
  { label: 'Avg Response Time', value: '142ms', change: '-8.3%', trend: 'down' },
  { label: 'Success Rate', value: '99.8%', change: '+0.2%', trend: 'up' },
  { label: 'Active API Keys', value: '1,247', change: '+5.1%', trend: 'up' }
]

const topEndpoints = [
  { path: '/api/v1/queries', count: '847K', percent: 35 },
  { path: '/api/v1/spaces', count: '612K', percent: 25 },
  { path: '/api/v1/documents', count: '489K', percent: 20 },
  { path: '/graphql', count: '367K', percent: 15 },
  { path: '/health', count: '122K', percent: 5 }
]

const recentActivity = [
  { time: '2m ago', event: 'Query processed', user: 'user@company.com', status: 'success' },
  { time: '5m ago', event: 'Space created', user: 'dev@startup.io', status: 'success' },
  { time: '8m ago', event: 'Document uploaded', user: 'admin@corp.com', status: 'success' },
  { time: '12m ago', event: 'API key created', user: 'test@example.com', status: 'success' },
  { time: '15m ago', event: 'Query failed', user: 'user@company.com', status: 'error' }
]

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('7d')

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '3rem 1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            API Analytics
          </h1>
          <p style={{ fontSize: '1.125rem', color: '#6B7280' }}>
            Monitor your API usage and performance
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['24h', '7d', '30d', '90d'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '0.375rem',
                border: '1px solid #E5E7EB',
                background: timeRange === range ? '#3B82F6' : 'white',
                color: timeRange === range ? 'white' : '#374151',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {metrics.map((metric, idx) => (
          <div key={idx} style={{
            background: 'white',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #E5E7EB'
          }}>
            <div style={{ fontSize: '0.875rem', color: '#6B7280', marginBottom: '0.5rem' }}>
              {metric.label}
            </div>
            <div style={{ display: 'flex', alignItems: 'end', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#111827' }}>
                {metric.value}
              </div>
              <div style={{
                fontSize: '0.875rem',
                fontWeight: '600',
                color: metric.trend === 'up' ? '#10B981' : '#EF4444'
              }}>
                {metric.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        {/* Request Chart */}
        <div style={{
          background: 'white',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          border: '1px solid #E5E7EB'
        }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
            Request Volume
          </h2>
          <div style={{ height: '300px', display: 'flex', alignItems: 'end', gap: '0.5rem' }}>
            {[85, 92, 78, 95, 88, 90, 87, 94, 89, 96, 91, 93, 88, 95].map((height, idx) => (
              <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'end', height: '100%' }}>
                <div style={{
                  background: 'linear-gradient(to top, #3B82F6, #60A5FA)',
                  height: `${height}%`,
                  borderRadius: '0.25rem 0.25rem 0 0',
                  transition: 'all 0.3s'
                }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem', fontSize: '0.75rem', color: '#6B7280' }}>
            <span>Mon</span>
            <span>Tue</span>
            <span>Wed</span>
            <span>Thu</span>
            <span>Fri</span>
            <span>Sat</span>
            <span>Sun</span>
          </div>
        </div>

        {/* Top Endpoints */}
        <div style={{
          background: 'white',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          border: '1px solid #E5E7EB'
        }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
            Top Endpoints
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {topEndpoints.map((endpoint, idx) => (
              <div key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                  <code style={{ color: '#374151', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                    {endpoint.path}
                  </code>
                  <span style={{ color: '#6B7280', fontWeight: '600' }}>{endpoint.count}</span>
                </div>
                <div style={{ background: '#F3F4F6', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    background: '#3B82F6',
                    height: '100%',
                    width: `${endpoint.percent}%`,
                    transition: 'width 0.3s'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div style={{
        background: 'white',
        padding: '1.5rem',
        borderRadius: '0.5rem',
        border: '1px solid #E5E7EB',
        marginTop: '1.5rem'
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>
          Recent Activity
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {recentActivity.map((activity, idx) => (
            <div key={idx} style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              padding: '1rem',
              background: '#F9FAFB',
              borderRadius: '0.375rem'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: activity.status === 'success' ? '#10B981' : '#EF4444'
              }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#111827' }}>
                  {activity.event}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#6B7280' }}>
                  {activity.user}
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#9CA3AF' }}>
                {activity.time}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
