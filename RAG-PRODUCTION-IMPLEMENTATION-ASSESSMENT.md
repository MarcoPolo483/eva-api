# RAG Production Implementation Assessment
**Project:** EVA API - Production RAG Integration  
**Date:** December 9, 2025  
**Status:** Current = Demo Mode → Target = Production RAG  
**Assigned To:** P02-REQ (Requirements & Architecture Agent)

---

## 🎯 Executive Summary

The EVA API currently operates in **demo mode** with mock responses. This assessment outlines the requirements to implement **production-grade RAG (Retrieval-Augmented Generation)** using Azure OpenAI, Azure AI Search, and real document processing.

**Current State:** ✅ Working demo with 15 knowledge spaces, 14 documents, deployed to Azure  
**Target State:** 🎯 Full RAG pipeline with vector search, document retrieval, and Azure OpenAI synthesis

---

## 📊 Current System Analysis

### Working Components ✅
1. **API Infrastructure**
   - FastAPI backend deployed to Azure App Service (`eva-api-marco-prod.azurewebsites.net`)
   - Cosmos DB with `eva-core` database (15 spaces, 14 documents)
   - Blob Storage for document uploads
   - CORS configured for static website
   - GraphQL + REST endpoints operational

2. **Demo RAG Flow**
   ```python
   # Current: query_service.py (_process_query)
   1. User submits query → POST /api/v1/queries
   2. Query stored in Cosmos DB with status="pending"
   3. Background task returns mock French response
   4. Status changes: pending → processing → completed
   5. Result includes demo answer + dummy sources
   ```

3. **Authentication & Authorization**
   - API key authentication working
   - JWT token validation ready (Azure Entra ID configured)
   - Multi-tenant isolation via space_id

4. **Frontend UI**
   - Bilingual chat interface (EN/FR) deployed
   - Language toggle slider functional
   - Query submission and result display working
   - Holiday-themed UI with snowflakes 🎄

### Missing Components 🔴

1. **Azure AI Search Integration**
   - No vector index created
   - No document ingestion pipeline
   - No embedding generation
   - No semantic/hybrid search implementation

2. **Real Document Processing**
   - Documents uploaded but not chunked
   - No text extraction from PDFs
   - No embedding generation
   - No indexing into search service

3. **Azure OpenAI RAG Pipeline**
   - Client initialized but not used (mock_mode=True)
   - No document retrieval logic
   - No context building from retrieved chunks
   - No answer synthesis with citations

4. **Document Ingestion Pipeline**
   - No Azure Function for blob triggers
   - No chunking engine (LangChain configured but unused)
   - No metadata extraction
   - No error handling for malformed docs

---

## 🏗️ Architecture Requirements

### High-Level RAG Flow (Production)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DOCUMENT INGESTION (Azure Function + Blob Trigger)       │
│    • User uploads document → Blob Storage                    │
│    • Function triggered automatically                        │
│    • Extract text (PDFs, Office docs, HTML)                  │
│    • Chunk text (1000 tokens, 200 overlap)                   │
│    • Generate embeddings (text-embedding-3-small)            │
│    • Store chunks + embeddings in Azure AI Search            │
│    • Update document status in Cosmos DB                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. QUERY PROCESSING (query_service.py)                      │
│    • User asks question in chat UI                          │
│    • POST /api/v1/queries → Create query record             │
│    • Background task starts (_process_query)                │
│    • Generate query embedding                                │
│    • Vector search in Azure AI Search:                       │
│      - Index: knowledge-index-{space_id}                     │
│      - Filter: space_id = current space                      │
│      - Top K results (default: 10)                           │
│      - Score threshold: 0.7                                  │
│    • Retrieve document chunks with metadata                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ANSWER SYNTHESIS (Azure OpenAI)                          │
│    • Build context from top chunks:                          │
│      [1] Title: {doc_title}                                  │
│      Source: {doc_name} (Page {page_num})                    │
│      Content: {chunk_text}                                   │
│                                                              │
│    • System prompt:                                          │
│      "You are EVA, a bilingual assistant. Answer using       │
│       ONLY the context below. Cite sources using [1], [2].   │
│       If info not in context, say 'I don't have that info.'" │
│                                                              │
│    • User prompt: Query + Context                            │
│    • Call Azure OpenAI Chat Completion (GPT-4)               │
│    • Extract citations from response                         │
│    • Store result in Cosmos DB                               │
│    • Return answer with source attribution                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Requirements

### 1. Azure AI Search Setup

**Service Configuration:**
```json
{
  "name": "eva-search-service",
  "location": "canadacentral",
  "sku": "standard",
  "partition_count": 1,
  "replica_count": 1
}
```

**Index Schema:**
```json
{
  "name": "knowledge-index",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true},
    {"name": "space_id", "type": "Edm.String", "filterable": true},
    {"name": "document_id", "type": "Edm.String", "filterable": true},
    {"name": "chunk_id", "type": "Edm.String"},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "embedding", "type": "Collection(Edm.Single)", "dimensions": 1536, "vectorSearchProfile": "default"},
    {"name": "title", "type": "Edm.String", "searchable": true},
    {"name": "page_number", "type": "Edm.Int32"},
    {"name": "metadata", "type": "Edm.ComplexType"},
    {"name": "created_at", "type": "Edm.DateTimeOffset"}
  ],
  "vectorSearch": {
    "profiles": [{"name": "default", "algorithm": "hnsw"}],
    "algorithms": [{"name": "hnsw", "kind": "hnsw"}]
  }
}
```

### 2. Document Ingestion Pipeline

**Azure Function (Blob Trigger):**
```python
# functions/document-ingestion/function_app.py

@app.blob_trigger(
    arg_name="myblob",
    path="documents/{space_id}/{document_id}",
    connection="AzureWebJobsStorage"
)
async def document_ingestion(myblob: func.InputStream):
    """
    Triggered when document uploaded to Blob Storage.
    
    Steps:
    1. Extract text from PDF/Office/HTML
    2. Chunk text (1000 tokens, 200 overlap) using LangChain
    3. Generate embeddings via Azure OpenAI
    4. Upload chunks to Azure AI Search
    5. Update document status in Cosmos DB
    """
    pass
```

**Chunking Strategy:**
- Use LangChain `RecursiveCharacterTextSplitter`
- Chunk size: 1000 tokens (~750 words)
- Overlap: 200 tokens (preserve context)
- Respect sentence boundaries
- Preserve metadata (page numbers, sections)

### 3. Query Service Updates

**File:** `src/eva_api/services/query_service.py`

**Required Changes:**
```python
class QueryService:
    def __init__(self, settings, cosmos_service, blob_service):
        # ADD: Azure AI Search client
        self.search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name="knowledge-index",
            credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        )
    
    async def _process_query(self, query_id: UUID):
        """
        REPLACE: Current mock implementation
        WITH: Real RAG pipeline
        """
        # 1. Generate query embedding
        embedding = await self._generate_embedding(question)
        
        # 2. Vector search in Azure AI Search
        results = await self._vector_search(
            embedding=embedding,
            space_id=space_id,
            top_k=10,
            score_threshold=0.7
        )
        
        # 3. Build context from chunks
        context = self._build_context(results)
        
        # 4. Call Azure OpenAI
        answer = await self._generate_answer(
            question=question,
            context=context,
            language=query.get("language", "en")
        )
        
        # 5. Extract citations
        citations = self._extract_citations(answer, results)
        
        # 6. Store result
        result = {
            "answer": answer["text"],
            "sources": citations,
            "metadata": {
                "processing_time": time.time() - start_time,
                "tokens_used": answer["tokens"],
                "model": "gpt-4",
                "chunks_retrieved": len(results)
            }
        }
```

### 4. Configuration Updates

**File:** `src/eva_api/config.py`

**Add Settings:**
```python
class Settings(BaseSettings):
    # Existing...
    
    # Azure AI Search
    azure_search_endpoint: str = ""
    azure_search_key: str = ""
    azure_search_index_name: str = "knowledge-index"
    
    # RAG Configuration
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k_results: int = 10
    rag_score_threshold: float = 0.7
    rag_max_context_tokens: int = 3000
    
    # Azure OpenAI Embeddings
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_embedding_dimensions: int = 1536
```

---

## 📋 Implementation Checklist

### Phase 1: Infrastructure Setup (POD-I - Infrastructure)
- [ ] Create Azure AI Search service in Canada Central
- [ ] Configure search index with vector field
- [ ] Set up Azure Function App for document processing
- [ ] Configure Blob Storage event triggers
- [ ] Update Azure Key Vault with new credentials
- [ ] Add AZURE_SEARCH_* environment variables to App Service

### Phase 2: Document Ingestion (POD-L - Libraries & Services)
- [ ] Implement document text extraction (PDFs, Office, HTML)
- [ ] Set up LangChain chunking pipeline
- [ ] Create embedding generation service
- [ ] Build Azure AI Search upload logic
- [ ] Add error handling and retry logic
- [ ] Implement batch processing for existing documents

### Phase 3: RAG Query Processing (POD-L - Libraries & Services)
- [ ] Replace mock logic in `_process_query()`
- [ ] Implement `_generate_embedding()` method
- [ ] Implement `_vector_search()` with filters
- [ ] Build `_build_context()` with source attribution
- [ ] Update `_generate_answer()` to use real Azure OpenAI
- [ ] Add `_extract_citations()` logic
- [ ] Implement bilingual prompt templates (EN/FR)

### Phase 4: Testing & Validation (POD-T - Testing)
- [ ] Unit tests for chunking logic
- [ ] Integration tests for search queries
- [ ] End-to-end tests for full RAG flow
- [ ] Load testing (25+ concurrent users)
- [ ] Bilingual accuracy validation
- [ ] Source citation verification
- [ ] Performance benchmarks (<5s query response time)

### Phase 5: Deployment & Monitoring (POD-D - Deployment)
- [ ] Deploy updated code to Azure
- [ ] Run document ingestion for 15 existing spaces
- [ ] Update UI to show real sources
- [ ] Configure Application Insights monitoring
- [ ] Set up cost alerts (Azure OpenAI tokens)
- [ ] Enable query analytics dashboard

---

## 🎯 Acceptance Criteria

### Functional Requirements
1. ✅ User can upload a PDF document to a knowledge space
2. ✅ Document is automatically processed and indexed within 2 minutes
3. ✅ User can ask a question in English or French
4. ✅ System retrieves relevant document chunks (top 10, score >0.7)
5. ✅ System generates accurate answer with [1], [2] citations
6. ✅ Sources displayed with document name, page number, snippet
7. ✅ Bilingual support: French question → French answer
8. ✅ Query completes in <5 seconds (p95 latency)

### Non-Functional Requirements
1. ✅ Support 25+ concurrent users
2. ✅ Handle documents up to 50MB (PDFs with 200+ pages)
3. ✅ 99.9% uptime SLA
4. ✅ PII detection and redaction (future phase)
5. ✅ Audit trail for all queries (Cosmos DB)
6. ✅ Cost monitoring: <$50/month for 1000 queries
7. ✅ Multi-tenant isolation (space_id filtering)

---

## 💰 Cost Estimate

### Azure Services (Monthly)
- **Azure AI Search (Standard):** ~$250/month
- **Azure OpenAI (GPT-4 + Embeddings):** ~$100/month (1000 queries)
- **Cosmos DB (Serverless):** ~$10/month
- **Blob Storage:** ~$5/month
- **App Service (B1):** ~$13/month
- **Function App (Consumption):** ~$5/month

**Total Estimated:** ~$383/month for 1000 queries/month

**Optimization Options:**
- Use GPT-3.5-turbo instead of GPT-4: -$60/month
- Use Basic AI Search tier: -$100/month
- Reduce top_k from 10 to 5: -20% token costs

---

## 🔐 Security & Compliance

### Data Protection
- All data in Canada Central region
- Encryption at rest (Azure Storage, Cosmos DB)
- Encryption in transit (HTTPS, TLS 1.2+)
- API key rotation every 90 days
- JWT token expiration: 1 hour

### Access Control
- Azure Entra ID for employee authentication
- API keys for service-to-service
- Space-level isolation (users can only query their spaces)
- Admin role for space management
- Audit logs for all operations

### Protected B Readiness
- Network isolation (VNet integration)
- Private endpoints for Azure services
- Azure Policy compliance
- Conditional access policies
- Multi-factor authentication

---

## 📚 Dependencies

### Python Packages (Already Installed)
```txt
langchain==0.2.5              # Document chunking
langchain-openai==0.1.8       # OpenAI integrations
openai==1.35.0                # Azure OpenAI client
azure-search-documents==11.4.0  # AI Search client
tiktoken==0.7.0               # Token counting
PyPDF2==3.0.1                 # PDF text extraction
python-docx==1.1.0            # Word doc processing
beautifulsoup4==4.12.3        # HTML parsing
```

### Azure Resources (Existing)
- ✅ Azure App Service (eva-api-marco-prod)
- ✅ Azure Cosmos DB (eva-suite-cosmos-dev / eva-core)
- ✅ Azure Blob Storage (evasuitestoragedev)
- ✅ Azure OpenAI (canadacentral endpoint)
- 🔴 Azure AI Search (NEEDS CREATION)
- 🔴 Azure Function App (NEEDS CREATION)

---

## 🚀 Implementation Timeline

### Week 1: Infrastructure & Ingestion
- **Days 1-2:** Create Azure AI Search service, configure index
- **Days 3-5:** Build document ingestion Azure Function
- **Days 6-7:** Test ingestion with 15 existing spaces

### Week 2: RAG Query Processing
- **Days 1-3:** Implement vector search and context building
- **Days 4-5:** Integrate Azure OpenAI with real prompts
- **Days 6-7:** Add citation extraction and result formatting

### Week 3: Testing & Deployment
- **Days 1-3:** Unit and integration tests
- **Days 4-5:** Load testing and performance tuning
- **Days 6-7:** Production deployment and monitoring setup

**Total Duration:** 3 weeks (15 business days)

---

## 🎓 Knowledge Transfer

### Documentation Required
1. **Developer Guide:** How to add new document types
2. **Operations Guide:** Monitoring, alerting, troubleshooting
3. **API Guide:** RAG endpoint usage examples
4. **Architecture Diagrams:** Updated with RAG flow
5. **Cost Management:** Azure OpenAI token optimization

### Training Sessions
1. **For Developers:** RAG architecture and code walkthrough
2. **For Admins:** Azure resource management
3. **For Users:** How to upload documents and ask questions

---

## 📞 Stakeholders

**Product Owner:** Marco Presta  
**Scrum Master:** GitHub Copilot  
**POD-I (Infrastructure):** Azure resource provisioning  
**POD-L (Libraries & Services):** RAG implementation  
**POD-T (Testing):** Quality assurance  
**POD-D (Deployment):** Production rollout  
**POD-F (Frontend):** UI updates for source display

---

## 🎯 Success Metrics

### After 1 Month of Production Use
- [ ] 500+ real queries processed
- [ ] <5s average query response time
- [ ] >90% user satisfaction (source relevance)
- [ ] <$50/month Azure OpenAI costs
- [ ] 0 security incidents
- [ ] 99.9% uptime achieved

---

## 📝 Next Steps

1. **Review this assessment** with Marco Presta
2. **Request P02 to generate role-specific implementation docs:**
   - POD-I: Infrastructure setup guide
   - POD-L: RAG service implementation spec
   - POD-T: Test plan and acceptance tests
   - POD-D: Deployment runbook
3. **Assign each document to respective agent** via GitHub Issues
4. **Monitor execution** and validate outputs
5. **Deploy to production** once all acceptance criteria met

---

**Document Version:** 1.0  
**Last Updated:** December 9, 2025  
**Status:** 📋 Ready for P02 Review
