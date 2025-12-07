# EVA API Client SDKs

This directory contains generated client SDKs for the EVA API Platform.

## Available SDKs

### Python SDK
- **Location**: `python/`
- **Package**: `eva-api-client`
- **Installation**: `pip install eva-api-client`
- **Generator**: openapi-python-client

### TypeScript SDK
- **Location**: `typescript/`
- **Package**: `@eva/api-client`
- **Installation**: `npm install @eva/api-client`
- **Generator**: openapi-typescript-codegen

### .NET SDK
- **Location**: `dotnet/`
- **Package**: `Eva.ApiClient`
- **Installation**: `dotnet add package Eva.ApiClient`
- **Generator**: NSwag

## Generating SDKs

### Prerequisites

1. **Python SDK**:
   ```bash
   pip install openapi-python-client
   ```

2. **TypeScript SDK**:
   ```bash
   npm install -g @openapitools/openapi-generator-cli
   ```

3. **.NET SDK**:
   ```bash
   dotnet tool install -g NSwag.ConsoleCore
   ```

### Generation Scripts

Run the generation scripts from the repo root:

```bash
# Generate all SDKs
./scripts/generate-sdks.ps1

# Or generate individually
./scripts/generate-python-sdk.ps1
./scripts/generate-typescript-sdk.ps1
./scripts/generate-dotnet-sdk.ps1
```

### Manual Generation

#### Python
```bash
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output-path sdks/python \
  --custom-template-path templates/python
```

#### TypeScript
```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o sdks/typescript \
  --additional-properties=npmName=@eva/api-client,supportsES6=true
```

#### .NET
```bash
nswag openapi2csclient \
  /input:http://localhost:8000/openapi.json \
  /output:sdks/dotnet/src/Eva.ApiClient/ApiClient.cs \
  /namespace:Eva.ApiClient \
  /className:EvaApiClient
```

## SDK Usage Examples

### Python
```python
from eva_api_client import Client
from eva_api_client.api.spaces import create_space
from eva_api_client.models import SpaceCreate

client = Client(base_url="https://api.eva.com", token="your-jwt-token")

space = create_space.sync(
    client=client,
    json_body=SpaceCreate(
        name="My Space",
        description="Example space",
    ),
)
print(f"Created space: {space.id}")
```

### TypeScript
```typescript
import { Configuration, SpacesApi } from '@eva/api-client';

const config = new Configuration({
  basePath: 'https://api.eva.com',
  accessToken: 'your-jwt-token',
});

const spacesApi = new SpacesApi(config);

const space = await spacesApi.createSpace({
  name: 'My Space',
  description: 'Example space',
});
console.log(`Created space: ${space.data.id}`);
```

### .NET
```csharp
using Eva.ApiClient;

var client = new EvaApiClient("https://api.eva.com");
client.SetBearerToken("your-jwt-token");

var space = await client.CreateSpaceAsync(new SpaceCreate
{
    Name = "My Space",
    Description = "Example space"
});
Console.WriteLine($"Created space: {space.Id}");
```

## Customization

SDK generation templates are located in `templates/`:
- `templates/python/` - Python SDK templates
- `templates/typescript/` - TypeScript SDK templates
- `templates/dotnet/` - .NET SDK templates

Modify these templates to customize generated code structure, add utilities, or adjust naming conventions.

## Publishing

### Python (PyPI)
```bash
cd sdks/python
python setup.py sdist bdist_wheel
twine upload dist/*
```

### TypeScript (npm)
```bash
cd sdks/typescript
npm publish --access public
```

### .NET (NuGet)
```bash
cd sdks/dotnet
dotnet pack -c Release
dotnet nuget push bin/Release/Eva.ApiClient.*.nupkg --source https://api.nuget.org/v3/index.json
```

## Continuous Integration

SDKs are automatically regenerated and published on API version releases via GitHub Actions.
See `.github/workflows/sdk-generation.yml` for details.
