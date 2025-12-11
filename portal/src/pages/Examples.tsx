import { useState } from 'react'

const examples = [
  {
    title: 'Getting Started',
    description: 'Basic setup and authentication',
    language: 'python',
    code: `from eva_sdk import EVAClient

# Initialize client with API key
client = EVAClient(api_key="eva_live_your_key")

# Check API status
health = client.health.check()
print(f"API Status: {health.status}")

# Create your first space
space = client.spaces.create(
    name="Documentation Hub",
    description="All product documentation"
)
print(f"Created space: {space.id}")`
  },
  {
    title: 'Document Upload & Processing',
    description: 'Upload documents and manage spaces',
    language: 'typescript',
    code: `import { EVAClient } from '@eva-suite/sdk';

const client = new EVAClient({
  apiKey: process.env.EVA_API_KEY
});

// Upload a document
const document = await client.documents.upload({
  spaceId: 'space-123',
  file: './user-guide.pdf',
  metadata: {
    tags: ['manual', 'v2.0'],
    department: 'Engineering'
  }
});

console.log('Document uploaded:', document.id);

// List all documents in space
const docs = await client.documents.list({
  spaceId: 'space-123',
  limit: 50
});

console.log(\`Found \${docs.items.length} documents\`);`
  },
  {
    title: 'RAG Query with Citations',
    description: 'Submit queries and retrieve AI-generated answers',
    language: 'python',
    code: `from eva_sdk import EVAClient

client = EVAClient(api_key="eva_live_your_key")

# Submit a query
query = client.queries.submit(
    space_id="space-123",
    question="What are the system requirements?",
    parameters={
        "max_results": 5,
        "temperature": 0.7
    }
)

print(f"Query ID: {query.id}")
print(f"Status: {query.status}")

# Poll for result
import time
while query.status == "pending":
    time.sleep(2)
    query = client.queries.get(query.id)

# Get the result
if query.status == "completed":
    result = client.queries.get_result(query.id)
    print(f"Answer: {result.answer}")
    print(f"Confidence: {result.confidence}")
    
    # Show sources
    for source in result.sources:
        print(f"  - {source.filename} (relevance: {source.relevance})")`
  },
  {
    title: 'GraphQL Query',
    description: 'Use GraphQL for flexible data fetching',
    language: 'typescript',
    code: `import { EVAClient } from '@eva-suite/sdk';

const client = new EVAClient({ apiKey: process.env.EVA_API_KEY });

const query = \`
  query GetSpaceWithDocuments($spaceId: UUID!) {
    space(id: $spaceId) {
      id
      name
      documentCount
      documents(limit: 10) {
        items {
          id
          filename
          sizeBytes
          createdAt
        }
      }
    }
  }
\`;

const result = await client.graphql.query(query, {
  spaceId: 'space-123'
});

console.log(result.data.space);`
  },
  {
    title: 'Batch Operations',
    description: 'Efficiently process multiple operations',
    language: 'csharp',
    code: `using EVA.SDK;

var client = new EVAClient("eva_live_your_key");

// Create multiple spaces in parallel
var spaceNames = new[] { "Sales", "Marketing", "Support" };

var tasks = spaceNames.Select(name => 
    client.Spaces.CreateAsync(new CreateSpaceRequest
    {
        Name = name,
        Description = $"{name} department documents"
    })
);

var spaces = await Task.WhenAll(tasks);

Console.WriteLine($"Created {spaces.Length} spaces");

// Batch document upload
foreach (var space in spaces)
{
    var files = Directory.GetFiles($"./docs/{space.Name}");
    
    var uploadTasks = files.Select(file =>
        client.Documents.UploadAsync(
            spaceId: space.Id,
            file: file
        )
    );
    
    await Task.WhenAll(uploadTasks);
    Console.WriteLine($"Uploaded {files.Length} files to {space.Name}");
}`
  },
  {
    title: 'Error Handling & Retries',
    description: 'Handle errors gracefully with retry logic',
    language: 'python',
    code: `from eva_sdk import EVAClient, EVAError, RateLimitError
import time

client = EVAClient(api_key="eva_live_your_key")

def upload_with_retry(space_id, file_path, max_retries=3):
    """Upload document with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return client.documents.upload(
                space_id=space_id,
                file=file_path
            )
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
        except EVAError as e:
            print(f"Error: {e.message}")
            if e.status_code >= 500:  # Retry on server errors
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            raise

# Usage
try:
    doc = upload_with_retry("space-123", "large-file.pdf")
    print(f"Uploaded: {doc.id}")
except EVAError as e:
    print(f"Failed after retries: {e}")`
  }
]

const languageColors: Record<string, string> = {
  python: '#3776AB',
  typescript: '#3178C6',
  javascript: '#F7DF1E',
  csharp: '#239120',
  curl: '#073551'
}

export default function Examples() {
  const [activeLanguage, setActiveLanguage] = useState<string | null>(null)

  const filteredExamples = activeLanguage
    ? examples.filter(ex => ex.language === activeLanguage)
    : examples

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '3rem 1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.25rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Code Examples
        </h1>
        <p style={{ fontSize: '1.125rem', color: '#6B7280' }}>
          Real-world examples to get you started quickly
        </p>
      </div>

      {/* Language Filter */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveLanguage(null)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            border: '1px solid #E5E7EB',
            background: !activeLanguage ? '#3B82F6' : 'white',
            color: !activeLanguage ? 'white' : '#374151',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: '500'
          }}
        >
          All
        </button>
        {['python', 'typescript', 'csharp'].map(lang => (
          <button
            key={lang}
            onClick={() => setActiveLanguage(lang)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.375rem',
              border: '1px solid #E5E7EB',
              background: activeLanguage === lang ? '#3B82F6' : 'white',
              color: activeLanguage === lang ? 'white' : '#374151',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              textTransform: 'capitalize'
            }}
          >
            {lang === 'csharp' ? 'C#' : lang}
          </button>
        ))}
      </div>

      {/* Examples Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {filteredExamples.map((example, idx) => (
          <div key={idx} style={{
            background: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '0.5rem',
            overflow: 'hidden'
          }}>
            {/* Example Header */}
            <div style={{
              padding: '1.5rem',
              borderBottom: '1px solid #E5E7EB'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#111827' }}>
                  {example.title}
                </h3>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '0.25rem',
                  fontSize: '0.75rem',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  color: 'white',
                  background: languageColors[example.language] || '#6B7280'
                }}>
                  {example.language === 'csharp' ? 'C#' : example.language}
                </span>
              </div>
              <p style={{ color: '#6B7280', fontSize: '0.875rem' }}>
                {example.description}
              </p>
            </div>

            {/* Code Block */}
            <pre style={{
              margin: 0,
              padding: '1.5rem',
              background: '#1F2937',
              color: '#F9FAFB',
              fontSize: '0.875rem',
              fontFamily: 'monospace',
              overflow: 'auto',
              lineHeight: '1.6'
            }}>
              {example.code}
            </pre>
          </div>
        ))}
      </div>

      {/* SDK Links */}
      <div style={{
        marginTop: '3rem',
        padding: '2rem',
        background: 'linear-gradient(to right, #3B82F6, #8B5CF6)',
        borderRadius: '0.5rem',
        color: 'white'
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          SDK Documentation
        </h2>
        <p style={{ marginBottom: '1.5rem', opacity: 0.9 }}>
          Explore complete SDK documentation and API references
        </p>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <a href="#" style={{
            padding: '0.75rem 1.5rem',
            background: 'white',
            color: '#3B82F6',
            borderRadius: '0.375rem',
            fontWeight: '600',
            textDecoration: 'none'
          }}>
            Python SDK →
          </a>
          <a href="#" style={{
            padding: '0.75rem 1.5rem',
            background: 'white',
            color: '#3B82F6',
            borderRadius: '0.375rem',
            fontWeight: '600',
            textDecoration: 'none'
          }}>
            TypeScript SDK →
          </a>
          <a href="#" style={{
            padding: '0.75rem 1.5rem',
            background: 'white',
            color: '#3B82F6',
            borderRadius: '0.375rem',
            fontWeight: '600',
            textDecoration: 'none'
          }}>
            .NET SDK →
          </a>
        </div>
      </div>
    </div>
  )
}
