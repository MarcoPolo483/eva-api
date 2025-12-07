# EVA API - .NET SDK Generation Script
#
# Generates a C#/.NET client SDK from the OpenAPI specification.
#
# Requirements:
#   dotnet tool install -g NSwag.ConsoleCore
#
# Usage:
#   .\scripts\generate-dotnet-sdk.ps1

Write-Host "🔵 Generating .NET SDK..." -ForegroundColor Cyan

# Ensure API is running
Write-Host "Checking if API is running on http://localhost:8000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -ErrorAction Stop
    if ($response.StatusCode -ne 200) {
        Write-Host "❌ API is not responding. Please start the API first:" -ForegroundColor Red
        Write-Host "   uvicorn eva_api.main:app --reload" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ API is not running. Please start the API first:" -ForegroundColor Red
    Write-Host "   uvicorn eva_api.main:app --reload" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ API is running" -ForegroundColor Green

# Remove old SDK
if (Test-Path "sdks\dotnet") {
    Write-Host "Removing old .NET SDK..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "sdks\dotnet"
}

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "sdks\dotnet\src\Eva.ApiClient" | Out-Null

# Download OpenAPI spec
Write-Host "Downloading OpenAPI spec..." -ForegroundColor Cyan
$specPath = "sdks\dotnet\openapi.json"
Invoke-WebRequest -Uri "http://localhost:8000/openapi.json" -OutFile $specPath

# Generate SDK
Write-Host "Generating .NET SDK from OpenAPI spec..." -ForegroundColor Cyan
try {
    & nswag openapi2csclient `
        /input:$specPath `
        /output:"sdks\dotnet\src\Eva.ApiClient\ApiClient.cs" `
        /namespace:Eva.ApiClient `
        /className:EvaApiClient `
        /generateClientInterfaces:true `
        /generateDtoTypes:true `
        /injectHttpClient:true `
        /useBaseUrl:true
    
    if ($LASTEXITCODE -ne 0) {
        throw "nswag failed"
    }
} catch {
    Write-Host "❌ Failed to generate .NET SDK: $_" -ForegroundColor Red
    exit 1
}

# Create .csproj file
Write-Host "Creating project file..." -ForegroundColor Cyan
$csproj = @"
<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <GeneratePackageOnBuild>true</GeneratePackageOnBuild>
    <PackageId>Eva.ApiClient</PackageId>
    <Version>1.0.0</Version>
    <Authors>EVA Suite</Authors>
    <Company>EVA Suite</Company>
    <Description>Official .NET client SDK for EVA API Platform</Description>
    <PackageTags>eva;api;client;sdk</PackageTags>
    <RepositoryUrl>https://github.com/eva-suite/eva-api</RepositoryUrl>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
    <PackageReference Include="System.ComponentModel.Annotations" Version="5.0.0" />
  </ItemGroup>

</Project>
"@
$csproj | Out-File -FilePath "sdks\dotnet\src\Eva.ApiClient\Eva.ApiClient.csproj" -Encoding UTF8

# Build SDK
Write-Host "Building .NET SDK..." -ForegroundColor Cyan
Push-Location "sdks\dotnet\src\Eva.ApiClient"
try {
    dotnet build
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet build failed"
    }
} finally {
    Pop-Location
}

Write-Host "✅ .NET SDK generated successfully at sdks\dotnet" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review generated code in sdks\dotnet\src\Eva.ApiClient\ApiClient.cs" -ForegroundColor White
Write-Host "  2. Build SDK: cd sdks\dotnet\src\Eva.ApiClient && dotnet build" -ForegroundColor White
Write-Host "  3. Run tests: cd sdks\dotnet && dotnet test" -ForegroundColor White
Write-Host "  4. Pack: cd sdks\dotnet\src\Eva.ApiClient && dotnet pack -c Release" -ForegroundColor White
Write-Host "  5. Publish: dotnet nuget push bin/Release/Eva.ApiClient.*.nupkg --source https://api.nuget.org/v3/index.json" -ForegroundColor White
