"""
Populate EVA API with demo spaces from ingested data
Creates spaces and uploads documents for ESDC demo
"""
import asyncio
import json
from pathlib import Path
import httpx

API_BASE = "http://127.0.0.1:8000"
API_KEY = "demo-api-key"
TENANT_ID = "demo-tenant"

# Data source paths
RAG_DATA = Path(r"C:\Users\marco\Documents\_AI Dev\EVA Suite\eva-rag\data\ingested")

async def create_space(client: httpx.AsyncClient, name: str, description: str) -> dict:
    """Create a knowledge space"""
    response = await client.post(
        f"{API_BASE}/api/v1/spaces",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "name": name,
            "description": description,
            "tenant_id": TENANT_ID
        }
    )
    response.raise_for_status()
    return response.json()["data"]

async def upload_document(client: httpx.AsyncClient, space_id: str, file_path: Path, metadata: dict = None) -> dict:
    """Upload a document to a space"""
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'application/octet-stream')}
        data = {
            'space_id': space_id,
            'tenant_id': TENANT_ID
        }
        if metadata:
            data['metadata'] = json.dumps(metadata)
        
        response = await client.post(
            f"{API_BASE}/api/v1/documents",
            headers={"X-API-Key": API_KEY},
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()["data"]

async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        print("🎄 Creating EVA Demo Spaces for ESDC\n")
        
        # 1. Canada Life Benefits
        print("📚 Creating Canada Life Benefits space...")
        canadalife_space = await create_space(
            client,
            "Canada Life Benefits",
            "PSHCP and PSDCP member booklets, FAQs, and implementation guides"
        )
        print(f"   ✅ Space created: {canadalife_space['id']}")
        
        # Note: Canada Life documents need to be found in ingested data
        # The actual files would be uploaded here if available
        
        # 2. Employment Analytics
        print("\n📊 Creating Employment Analytics space...")
        employment_space = await create_space(
            client,
            "Employment Analytics",
            "Statistics Canada employment trends and labour force data"
        )
        print(f"   ✅ Space created: {employment_space['id']}")
        
        # Upload employment CSVs if they exist
        employment_dir = RAG_DATA / "employment"
        if employment_dir.exists():
            for json_file in employment_dir.glob("*.json"):
                print(f"   📄 Loading: {json_file.name}")
                # These are JSON metadata files from ingestion
                # Would need to find original CSV files
        
        # 3. Jurisprudence (Supreme Court Cases)
        print("\n⚖️ Creating Jurisprudence space...")
        legal_space = await create_space(
            client,
            "Supreme Court Jurisprudence",
            "Supreme Court of Canada case law and legal precedents"
        )
        print(f"   ✅ Space created: {legal_space['id']}")
        
        legal_dir = RAG_DATA / "legal"
        if legal_dir.exists():
            print(f"   📂 Found legal documents directory")
        
        # 4. Canada.ca Government Content
        print("\n🇨🇦 Creating Canada.ca Government Content space...")
        canada_space = await create_space(
            client,
            "Canada.ca Government Services",
            "Bilingual government services information (EN/FR) - 1,257 pages"
        )
        print(f"   ✅ Space created: {canada_space['id']}")
        
        canada_dir = RAG_DATA / "canada_ca"
        if canada_dir.exists():
            json_files = list(canada_dir.glob("*.json"))
            print(f"   📂 Found {len(json_files)} metadata files")
        
        # 5. IT Collective Agreement
        print("\n💼 Creating IT Collective Agreement space...")
        it_agreement_space = await create_space(
            client,
            "IT Collective Agreement",
            "Treasury Board IT collective agreement (EN/FR) - pay scales, benefits, leave"
        )
        print(f"   ✅ Space created: {it_agreement_space['id']}")
        
        # 6. Employment Equity Act
        print("\n📜 Creating Employment Equity Act space...")
        equity_space = await create_space(
            client,
            "Employment Equity Act",
            "Official legislation S.C. 1995, c. 44 (EN/FR bilingual)"
        )
        print(f"   ✅ Space created: {equity_space['id']}")
        
        # 7. Employment Standards & Workplace Rights
        print("\n📋 Creating Employment Standards space...")
        standards_space = await create_space(
            client,
            "Employment Standards & Workplace Rights",
            "AssistMe legal guidance - hours, wages, holidays, workplace rights"
        )
        print(f"   ✅ Space created: {standards_space['id']}")
        
        print("\n" + "="*60)
        print("✨ Demo spaces created successfully!")
        print("="*60)
        print("\n📌 Next Steps:")
        print("   1. Documents need to be uploaded to each space")
        print("   2. EVA-RAG ingestion pipeline needs to connect to eva-api")
        print("   3. Alternative: Create a script to sync ingested data → API spaces")
        print("\n💡 For now, the spaces exist and the UI will show them!")
        print("   Visit: http://127.0.0.1:5500")

if __name__ == "__main__":
    asyncio.run(main())
