# POD-T: RAG Testing and Quality Assurance Plan
**Role:** POD-T (Testing)  
**Priority:** High  
**Estimated Effort:** 3-4 days  
**Dependencies:** POD-I (infrastructure), POD-L (service implementation)  
**Source:** RAG-PRODUCTION-IMPLEMENTATION-ASSESSMENT.md

---

## 🎯 Objective

Validate production RAG implementation with comprehensive test coverage: unit tests for individual components, integration tests for end-to-end flows, load tests for performance, and bilingual accuracy tests for quality assurance.

**Success Criteria:** All tests pass with >80% code coverage, response time <5s (95th percentile), bilingual accuracy >90%.

---

## 📊 Context

RAG system has multiple failure points:
- PDF text extraction errors
- Chunking creating incoherent segments
- Embedding generation failures
- Vector search returning irrelevant results
- Context building exceeding token limits
- GPT-4 hallucinating or missing citations
- Bilingual responses in wrong language

**Testing Pyramid:**
```
           /\
          /  \  E2E Tests (5)
         /    \
        / Integration Tests (15)
       /        \
      / Unit Tests (30)
     /            \
    /______________\
```

---

## 🔧 Technical Requirements

### Input
- Test document corpus (PDF files in EN/FR)
- Test queries with expected answers
- Azure AI Search test index
- Mock Azure OpenAI responses (for unit tests)
- Performance benchmarks (latency, throughput)

### Output
1. **Test Report** with pass/fail status, coverage metrics, performance results
2. **Test Artifacts** (logs, screenshots, performance graphs)
3. **Bug Reports** for any failures (GitHub Issues)
4. **Sign-off Document** certifying production readiness

### Constraints
- Tests must run in CI/CD pipeline (GitHub Actions)
- Use pytest framework (existing in project)
- Isolate tests (no shared state, idempotent)
- Test data must not use real sensitive documents
- Performance tests run in staging environment only

---

## 📝 Test Categories

### 1. Unit Tests (30 tests, ~8 hours)

#### 1.1 Document Processing (`test_document_processing.py`)

**Test: PDF Text Extraction**
```python
# tests/unit/test_document_processing.py
import pytest
from functions.document_ingestion import extract_text_from_pdf

def test_extract_text_from_single_page_pdf():
    """Verify text extraction from 1-page PDF."""
    with open("tests/fixtures/single_page.pdf", "rb") as f:
        pages = extract_text_from_pdf(f)
    
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert "expected text content" in pages[0]["text"].lower()

def test_extract_text_from_multi_page_pdf():
    """Verify text extraction from 10-page PDF."""
    with open("tests/fixtures/multi_page.pdf", "rb") as f:
        pages = extract_text_from_pdf(f)
    
    assert len(pages) == 10
    assert all(p["page_number"] == i+1 for i, p in enumerate(pages))
    assert all(len(p["text"]) > 0 for p in pages)

def test_extract_text_handles_corrupted_pdf():
    """Verify graceful failure on corrupted PDF."""
    with open("tests/fixtures/corrupted.pdf", "rb") as f:
        with pytest.raises(Exception) as exc_info:
            extract_text_from_pdf(f)
    
    assert "PDF" in str(exc_info.value)

def test_extract_text_handles_scanned_pdf():
    """Verify OCR not supported message for scanned PDFs."""
    with open("tests/fixtures/scanned_image.pdf", "rb") as f:
        pages = extract_text_from_pdf(f)
    
    # Scanned PDFs return empty or minimal text without OCR
    assert len(pages) > 0
    assert all(len(p["text"]) < 50 for p in pages)  # Very little text extracted
```

**Expected Results:**
- Single-page PDF: 1 page extracted with correct content
- Multi-page PDF: 10 pages extracted in correct order
- Corrupted PDF: Raises exception with "PDF" in message
- Scanned PDF: Returns minimal text (OCR not implemented)

---

#### 1.2 Text Chunking (`test_chunking.py`)

**Test: Chunking with Overlap**
```python
# tests/unit/test_chunking.py
from functions.document_ingestion import chunk_text
import tiktoken

def test_chunk_respects_token_limit():
    """Verify chunks do not exceed specified token size."""
    pages = [{"page_number": 1, "text": "word " * 2000}]  # 2000 tokens
    chunks = chunk_text(pages, chunk_size=500, overlap=100)
    
    encoding = tiktoken.get_encoding("cl100k_base")
    for chunk in chunks:
        token_count = len(encoding.encode(chunk["content"]))
        assert token_count <= 500, f"Chunk exceeded limit: {token_count} tokens"

def test_chunk_overlap_preserves_context():
    """Verify adjacent chunks share overlapping content."""
    pages = [{"page_number": 1, "text": " ".join([f"word{i}" for i in range(1000)])}]
    chunks = chunk_text(pages, chunk_size=200, overlap=50)
    
    encoding = tiktoken.get_encoding("cl100k_base")
    for i in range(len(chunks) - 1):
        chunk1_tokens = encoding.encode(chunks[i]["content"])[-50:]
        chunk2_tokens = encoding.encode(chunks[i+1]["content"])[:50]
        
        # Some overlap should exist
        overlap_exists = any(t in chunk2_tokens for t in chunk1_tokens)
        assert overlap_exists, f"No overlap between chunk {i} and {i+1}"

def test_chunk_preserves_page_numbers():
    """Verify chunks correctly track source page."""
    pages = [
        {"page_number": 1, "text": "page one " * 500},
        {"page_number": 2, "text": "page two " * 500}
    ]
    chunks = chunk_text(pages, chunk_size=300, overlap=50)
    
    page1_chunks = [c for c in chunks if c["page_number"] == 1]
    page2_chunks = [c for c in chunks if c["page_number"] == 2]
    
    assert len(page1_chunks) > 0
    assert len(page2_chunks) > 0
    assert all("page one" in c["content"] for c in page1_chunks)
    assert all("page two" in c["content"] for c in page2_chunks)

def test_chunk_handles_empty_pages():
    """Verify empty pages are skipped gracefully."""
    pages = [
        {"page_number": 1, "text": "content"},
        {"page_number": 2, "text": ""},
        {"page_number": 3, "text": "more content"}
    ]
    chunks = chunk_text(pages, chunk_size=100, overlap=20)
    
    # Should have chunks from pages 1 and 3 only
    assert all(c["page_number"] in [1, 3] for c in chunks)
```

**Expected Results:**
- All chunks ≤500 tokens
- Adjacent chunks share ~50 tokens of content
- Page numbers correctly assigned to chunks
- Empty pages skipped without errors

---

#### 1.3 Embedding Generation (`test_embeddings.py`)

**Test: Azure OpenAI Embedding API**
```python
# tests/unit/test_embeddings.py
import pytest
from unittest.mock import AsyncMock, patch
from functions.document_ingestion import generate_embeddings

@pytest.mark.asyncio
async def test_generate_embeddings_returns_correct_dimensions():
    """Verify embeddings are 1536 dimensions (text-embedding-3-small)."""
    chunks = [
        {"chunk_id": "chunk-0001", "content": "Test content for embedding", "page_number": 1}
    ]
    
    with patch("azure.ai.openai.AsyncAzureOpenAI") as mock_client:
        # Mock response
        mock_client.return_value.embeddings.create = AsyncMock(return_value={
            "data": [{"embedding": [0.1] * 1536}]
        })
        
        embeddings = await generate_embeddings(chunks)
    
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1536

@pytest.mark.asyncio
async def test_generate_embeddings_handles_batch():
    """Verify multiple chunks generate multiple embeddings."""
    chunks = [
        {"chunk_id": f"chunk-{i:04d}", "content": f"Content {i}", "page_number": 1}
        for i in range(5)
    ]
    
    with patch("azure.ai.openai.AsyncAzureOpenAI") as mock_client:
        mock_client.return_value.embeddings.create = AsyncMock(return_value={
            "data": [{"embedding": [0.1] * 1536}]
        })
        
        embeddings = await generate_embeddings(chunks)
    
    assert len(embeddings) == 5
    assert all(len(e) == 1536 for e in embeddings)

@pytest.mark.asyncio
async def test_generate_embeddings_handles_api_failure():
    """Verify graceful handling of Azure OpenAI API errors."""
    chunks = [{"chunk_id": "chunk-0001", "content": "Test", "page_number": 1}]
    
    with patch("azure.ai.openai.AsyncAzureOpenAI") as mock_client:
        mock_client.return_value.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception) as exc_info:
            await generate_embeddings(chunks)
        
        assert "API Error" in str(exc_info.value)
```

**Expected Results:**
- Embeddings are 1536-dimensional vectors
- Batch of 5 chunks returns 5 embeddings
- API errors propagate with clear error message

---

#### 1.4 Vector Search (`test_vector_search.py`)

**Test: Azure AI Search Query**
```python
# tests/unit/test_vector_search.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.eva_api.services.query_service import QueryService

@pytest.mark.asyncio
async def test_vector_search_returns_top_k_results():
    """Verify search returns requested number of results."""
    service = QueryService(config=mock_config)
    query_embedding = [0.1] * 1536
    
    with patch("azure.search.documents.SearchClient") as mock_client:
        # Mock search results
        mock_results = [
            MagicMock(
                id=f"doc-{i}",
                title=f"Document {i}",
                content=f"Content {i}",
                page_number=i,
                **{"@search.score": 0.9 - (i * 0.05)}
            )
            for i in range(10)
        ]
        mock_client.return_value.search.return_value = mock_results
        
        results = await service._vector_search(query_embedding, "test-space", top_k=10)
    
    assert len(results) == 10
    assert all(r["score"] >= 0.7 for r in results)  # Above threshold

@pytest.mark.asyncio
async def test_vector_search_filters_by_space_id():
    """Verify search respects tenant isolation."""
    service = QueryService(config=mock_config)
    query_embedding = [0.1] * 1536
    
    with patch("azure.search.documents.SearchClient") as mock_client:
        await service._vector_search(query_embedding, "space-abc", top_k=5)
        
        # Verify filter was applied
        call_args = mock_client.return_value.search.call_args
        assert "filter" in call_args.kwargs
        assert "space-abc" in call_args.kwargs["filter"]

@pytest.mark.asyncio
async def test_vector_search_filters_by_score_threshold():
    """Verify low-score results are excluded."""
    service = QueryService(config=mock_config)
    service.config.azure_search_score_threshold = 0.8
    query_embedding = [0.1] * 1536
    
    with patch("azure.search.documents.SearchClient") as mock_client:
        # Return results with varying scores
        mock_results = [
            MagicMock(id="doc-1", **{"@search.score": 0.95}),
            MagicMock(id="doc-2", **{"@search.score": 0.85}),
            MagicMock(id="doc-3", **{"@search.score": 0.75}),  # Below threshold
            MagicMock(id="doc-4", **{"@search.score": 0.60})   # Below threshold
        ]
        for r in mock_results:
            r.get = MagicMock(side_effect=lambda k, d=None: r.__dict__.get(k, d))
        
        mock_client.return_value.search.return_value = mock_results
        
        results = await service._vector_search(query_embedding, "test-space", top_k=10)
    
    # Should only return docs with score >= 0.8
    assert len(results) == 2
    assert all(r["score"] >= 0.8 for r in results)
```

**Expected Results:**
- Returns exactly 10 results when top_k=10
- Applies space_id filter in search query
- Excludes results below score threshold (0.7 or 0.8)

---

#### 1.5 Context Building (`test_context_building.py`)

**Test: Token Limit Enforcement**
```python
# tests/unit/test_context_building.py
from src.eva_api.services.query_service import QueryService
import tiktoken

def test_build_context_respects_token_limit():
    """Verify context doesn't exceed max_tokens parameter."""
    service = QueryService(config=mock_config)
    
    # Create chunks that would exceed 2000 tokens if all included
    search_results = [
        {
            "title": f"Doc {i}",
            "content": "word " * 300,  # ~300 tokens per chunk
            "page_number": i,
            "score": 0.9
        }
        for i in range(10)  # 10 chunks * 300 = 3000 tokens total
    ]
    
    context = service._build_context(search_results, max_tokens=2000)
    
    encoding = tiktoken.get_encoding("cl100k_base")
    actual_tokens = len(encoding.encode(context))
    
    assert actual_tokens <= 2000, f"Context exceeded limit: {actual_tokens} tokens"

def test_build_context_includes_citations():
    """Verify context includes [Document N] markers."""
    service = QueryService(config=mock_config)
    
    search_results = [
        {"title": "Policy Guide", "content": "Important policy details", "page_number": 5, "score": 0.95},
        {"title": "FAQ", "content": "Frequently asked questions", "page_number": 2, "score": 0.85}
    ]
    
    context = service._build_context(search_results, max_tokens=5000)
    
    assert "[Document 1: Policy Guide, Page 5" in context
    assert "[Document 2: FAQ, Page 2" in context
    assert "Important policy details" in context
    assert "Frequently asked questions" in context

def test_build_context_handles_empty_results():
    """Verify graceful handling when no search results."""
    service = QueryService(config=mock_config)
    
    context = service._build_context([], max_tokens=5000)
    
    assert context == "No relevant documents found."
```

**Expected Results:**
- Context ≤2000 tokens when max_tokens=2000
- Includes [Document N] citation markers with page numbers
- Returns "No relevant documents found" for empty results

---

#### 1.6 Answer Generation (`test_answer_generation.py`)

**Test: Bilingual Prompts**
```python
# tests/unit/test_answer_generation.py
import pytest
from unittest.mock import AsyncMock, patch
from src.eva_api.services.query_service import QueryService

@pytest.mark.asyncio
async def test_generate_answer_in_english():
    """Verify English prompt and response."""
    service = QueryService(config=mock_config)
    question = "What is the policy?"
    context = "[Document 1] The policy states..."
    
    with patch.object(service, "openai_client") as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="The policy states that..."))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        answer = await service._generate_answer(question, context, language="en")
        
        # Verify English system prompt used
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "EVA (Enhanced Virtual Assistant)" in messages[0]["content"]
        assert "official documents" in messages[0]["content"].lower()
    
    assert len(answer) > 0

@pytest.mark.asyncio
async def test_generate_answer_in_french():
    """Verify French prompt and response."""
    service = QueryService(config=mock_config)
    question = "Quelle est la politique?"
    context = "[Document 1] La politique indique..."
    
    with patch.object(service, "openai_client") as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="La politique indique que..."))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        answer = await service._generate_answer(question, context, language="fr")
        
        # Verify French system prompt used
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert "EVA (Assistant Virtuel Amélioré)" in messages[0]["content"]
        assert "documents officiels" in messages[0]["content"].lower()
    
    assert len(answer) > 0

@pytest.mark.asyncio
async def test_generate_answer_handles_api_error():
    """Verify error handling returns user-friendly message."""
    service = QueryService(config=mock_config)
    
    with patch.object(service, "openai_client") as mock_client:
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Rate limit exceeded"))
        
        answer = await service._generate_answer("Test question", "Context", language="en")
    
    assert "error" in answer.lower() or "apologize" in answer.lower()
```

**Expected Results:**
- English language parameter uses English system prompt
- French language parameter uses French system prompt
- API errors return user-friendly error message in requested language

---

#### 1.7 Citation Extraction (`test_citation_extraction.py`)

**Test: Regex Pattern Matching**
```python
# tests/unit/test_citation_extraction.py
from src.eva_api.services.query_service import QueryService

def test_extract_citations_from_answer():
    """Verify [Document N] patterns extracted correctly."""
    service = QueryService(config=mock_config)
    
    search_results = [
        {"title": "Doc A", "page_number": 1, "score": 0.95, "document_id": "doc-a", "chunk_id": "chunk-1"},
        {"title": "Doc B", "page_number": 5, "score": 0.90, "document_id": "doc-b", "chunk_id": "chunk-2"},
        {"title": "Doc C", "page_number": 3, "score": 0.85, "document_id": "doc-c", "chunk_id": "chunk-3"}
    ]
    
    answer = "According to [Document 1], the policy... Furthermore, [Document 3] states..."
    
    sources = service._extract_citations(search_results, answer)
    
    assert len(sources) == 2
    assert sources[0]["title"] == "Doc A"
    assert sources[0]["page"] == 1
    assert sources[1]["title"] == "Doc C"
    assert sources[1]["page"] == 3

def test_extract_citations_handles_no_citations():
    """Verify fallback to top 3 sources when no citations found."""
    service = QueryService(config=mock_config)
    
    search_results = [
        {"title": f"Doc {i}", "page_number": i, "score": 0.9, "document_id": f"doc-{i}", "chunk_id": f"chunk-{i}"}
        for i in range(5)
    ]
    
    answer = "This answer has no citation markers."
    
    sources = service._extract_citations(search_results, answer)
    
    assert len(sources) == 3  # Top 3 sources included as fallback
    assert sources[0]["title"] == "Doc 0"

def test_extract_citations_handles_invalid_indices():
    """Verify out-of-range citation numbers are skipped."""
    service = QueryService(config=mock_config)
    
    search_results = [
        {"title": "Doc A", "page_number": 1, "score": 0.95, "document_id": "doc-a", "chunk_id": "chunk-1"}
    ]
    
    answer = "According to [Document 1] and [Document 99], the policy..."
    
    sources = service._extract_citations(search_results, answer)
    
    assert len(sources) == 1  # Only Document 1 (valid index)
    assert sources[0]["title"] == "Doc A"
```

**Expected Results:**
- Cited documents extracted with correct page numbers
- No citations → fallback to top 3 sources
- Invalid indices (>= len(search_results)) skipped gracefully

---

### 2. Integration Tests (15 tests, ~16 hours)

#### 2.1 End-to-End Query Flow (`test_e2e_query.py`)

**Test: Submit Query → Retrieve Result**
```python
# tests/integration/test_e2e_query.py
import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_submit_query_and_retrieve_result():
    """Verify complete query lifecycle."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Submit query
        response = await client.post(
            "/api/v1/queries",
            headers={"X-API-Key": "demo-api-key"},
            json={
                "space_id": "test-space",
                "question": "What is the main policy objective?",
                "language": "en"
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        query_id = data["query_id"]
        assert data["status"] == "pending"
        
        # Wait for processing (max 10 seconds)
        for _ in range(20):
            await asyncio.sleep(0.5)
            
            status_response = await client.get(
                f"/api/v1/queries/{query_id}",
                headers={"X-API-Key": "demo-api-key"}
            )
            
            status_data = status_response.json()
            if status_data["status"] == "completed":
                break
        
        # Retrieve result
        result_response = await client.get(
            f"/api/v1/queries/{query_id}/result",
            headers={"X-API-Key": "demo-api-key"}
        )
        
        assert result_response.status_code == 200
        result = result_response.json()
        
        assert result["status"] == "completed"
        assert "answer" in result
        assert len(result["answer"]) > 0
        assert "sources" in result
        assert len(result["sources"]) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_bilingual_response():
    """Verify English and French queries return correct languages."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # English query
        en_response = await client.post(
            "/api/v1/queries",
            headers={"X-API-Key": "demo-api-key"},
            json={"space_id": "test-space", "question": "What is this?", "language": "en"}
        )
        en_query_id = en_response.json()["query_id"]
        await asyncio.sleep(8)
        en_result = await client.get(f"/api/v1/queries/{en_query_id}/result", headers={"X-API-Key": "demo-api-key"})
        
        # French query
        fr_response = await client.post(
            "/api/v1/queries",
            headers={"X-API-Key": "demo-api-key"},
            json={"space_id": "test-space", "question": "Qu'est-ce que c'est?", "language": "fr"}
        )
        fr_query_id = fr_response.json()["query_id"]
        await asyncio.sleep(8)
        fr_result = await client.get(f"/api/v1/queries/{fr_query_id}/result", headers={"X-API-Key": "demo-api-key"})
        
        # Verify language markers (simple heuristic)
        en_answer = en_result.json()["answer"]
        fr_answer = fr_result.json()["answer"]
        
        # French text typically has accents
        assert any(char in fr_answer for char in "àâäéèêëïîôùûüÿœæç")
```

**Expected Results:**
- Query submitted (202 Accepted)
- Status changes from pending → processing → completed
- Result contains answer and sources
- English query returns English answer
- French query returns French answer with accents

---

#### 2.2 Document Upload and Indexing (`test_document_upload.py`)

**Test: Upload PDF → Function Triggers → Index Updated**
```python
# tests/integration/test_document_upload.py
import pytest
import time
from azure.storage.blob import BlobServiceClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

@pytest.mark.integration
def test_upload_pdf_triggers_indexing():
    """Verify document upload triggers Azure Function and indexes chunks."""
    # Upload test PDF
    blob_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
    container_client = blob_client.get_container_client("spaces")
    
    with open("tests/fixtures/test_policy.pdf", "rb") as f:
        blob_client = container_client.upload_blob(
            name="test-space/documents/test-doc-123.pdf",
            data=f,
            overwrite=True
        )
    
    # Wait for function to process (max 60 seconds)
    time.sleep(60)
    
    # Query search index for chunks
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name="knowledge-index",
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    results = search_client.search(
        search_text="*",
        filter="document_id eq 'test-doc-123'"
    )
    
    chunks = list(results)
    
    assert len(chunks) > 0, "No chunks found in index after upload"
    assert all("embedding" in chunk for chunk in chunks)
    assert all(len(chunk["embedding"]) == 1536 for chunk in chunks)
```

**Expected Results:**
- PDF uploaded to Blob Storage successfully
- After 60 seconds, chunks appear in search index
- All chunks have 1536-dimensional embeddings

---

### 3. Load Tests (5 tests, ~8 hours)

#### 3.1 Concurrent Query Handling (`test_load_queries.py`)

**Test: 25 Concurrent Queries**
```python
# tests/load/test_load_queries.py
import pytest
import asyncio
import time
from httpx import AsyncClient

@pytest.mark.load
@pytest.mark.asyncio
async def test_25_concurrent_queries():
    """Verify system handles 25 concurrent queries within 10 seconds."""
    queries = [
        {"space_id": "test-space", "question": f"Question {i}", "language": "en"}
        for i in range(25)
    ]
    
    start_time = time.time()
    
    async with AsyncClient(base_url="http://localhost:8000", timeout=30.0) as client:
        # Submit all queries concurrently
        tasks = [
            client.post("/api/v1/queries", headers={"X-API-Key": "demo-api-key"}, json=q)
            for q in queries
        ]
        responses = await asyncio.gather(*tasks)
        
        query_ids = [r.json()["query_id"] for r in responses]
        assert len(query_ids) == 25
        
        # Wait for all to complete
        await asyncio.sleep(10)
        
        # Check results
        result_tasks = [
            client.get(f"/api/v1/queries/{qid}/result", headers={"X-API-Key": "demo-api-key"})
            for qid in query_ids
        ]
        results = await asyncio.gather(*result_tasks)
        
        completed = [r.json() for r in results if r.json()["status"] == "completed"]
    
    elapsed = time.time() - start_time
    
    assert len(completed) >= 20, f"Only {len(completed)}/25 queries completed"
    assert elapsed < 15, f"Load test took {elapsed}s (should be <15s)"
```

**Expected Results:**
- 25 queries accepted (202 status)
- At least 20 queries complete within 15 seconds
- No 500 errors or timeouts

---

### 4. Bilingual Accuracy Tests (5 tests, ~4 hours)

#### 4.1 English Query Accuracy (`test_accuracy_english.py`)

**Test: Validate Answers with Gold Standard**
```python
# tests/accuracy/test_accuracy_english.py
import pytest
from httpx import AsyncClient
import asyncio

ENGLISH_TEST_CASES = [
    {
        "question": "What is the purpose of the telework policy?",
        "expected_keywords": ["flexibility", "work-life balance", "productivity"],
        "expected_source": "Telework Policy 2024"
    },
    {
        "question": "How many vacation days do employees receive?",
        "expected_keywords": ["15 days", "annual", "vacation"],
        "expected_source": "Employee Handbook"
    }
]

@pytest.mark.accuracy
@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", ENGLISH_TEST_CASES)
async def test_english_answer_accuracy(test_case):
    """Verify English answers contain expected keywords and cite correct sources."""
    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/api/v1/queries",
            headers={"X-API-Key": "demo-api-key"},
            json={"space_id": "test-space", "question": test_case["question"], "language": "en"}
        )
        
        query_id = response.json()["query_id"]
        await asyncio.sleep(8)
        
        result = await client.get(f"/api/v1/queries/{query_id}/result", headers={"X-API-Key": "demo-api-key"})
        data = result.json()
        
        answer = data["answer"].lower()
        sources = [s["title"] for s in data["sources"]]
        
        # Check keywords present
        for keyword in test_case["expected_keywords"]:
            assert keyword.lower() in answer, f"Expected keyword '{keyword}' not found in answer"
        
        # Check source cited
        assert any(test_case["expected_source"].lower() in s.lower() for s in sources), \
            f"Expected source '{test_case['expected_source']}' not cited"
```

**Expected Results:**
- All expected keywords present in answers
- Correct source documents cited
- 90%+ accuracy across test cases

---

## ✅ Acceptance Criteria

- [ ] Unit tests: 30 tests, >80% code coverage, all passing
- [ ] Integration tests: 15 tests, all passing (E2E, upload, indexing)
- [ ] Load tests: 25 concurrent queries complete in <15s
- [ ] Bilingual tests: English and French responses accurate (>90% keyword match)
- [ ] Performance: p95 latency <5 seconds
- [ ] CI/CD: All tests run in GitHub Actions on every PR
- [ ] Test report generated with coverage metrics and screenshots
- [ ] Zero high-severity bugs found

---

## 🧪 Test Execution

**Local Testing:**
```powershell
# Run unit tests only
pytest tests/unit/ -v

# Run integration tests (requires local API running)
pytest tests/integration/ -v --integration

# Run load tests (requires staging environment)
pytest tests/load/ -v --load

# Run accuracy tests with gold standard data
pytest tests/accuracy/ -v --accuracy

# Generate coverage report
pytest --cov=src/eva_api --cov-report=html
```

**CI/CD Pipeline (GitHub Actions):**
```yaml
# .github/workflows/test.yml
name: Test RAG Implementation

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/unit/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
  
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose up -d
      - run: pytest tests/integration/ --integration
  
  load-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/load/ --load
```

---

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Azure Load Testing](https://learn.microsoft.com/azure/load-testing/)
- [HTTPX Async Client](https://www.python-httpx.org/async/)
- [Test Coverage with pytest-cov](https://pytest-cov.readthedocs.io/)

---

## 🚨 Risks & Mitigation

**Risk 1: Integration Tests Require Real Azure Resources**  
**Impact:** High - Tests can't run without Azure AI Search/OpenAI  
**Mitigation:** Use Azure CLI to provision test environment, mock services for unit tests

**Risk 2: Load Tests May Incur High Costs**  
**Impact:** Medium - 25 concurrent queries = 25 OpenAI API calls  
**Mitigation:** Run load tests in staging only, use smaller test corpus

**Risk 3: Bilingual Accuracy Hard to Measure**  
**Impact:** Medium - Subjective assessment  
**Mitigation:** Use keyword matching and human review of 10% sample

---

## 📞 Handoff to POD-D

Once all tests pass, provide POD-D:
1. **Test Report** (HTML coverage report, pass/fail summary)
2. **Performance Metrics** (p50, p95, p99 latencies)
3. **Sign-off Document** certifying production readiness
4. **Known Issues** (if any) with workaround steps

---

**Created:** December 9, 2025  
**Assigned To:** POD-T (Testing)  
**Status:** 📋 Ready for Implementation  
**Estimated Completion:** 3-4 business days  
**Blocks:** POD-D (Deployment)  
**Blocked By:** POD-L (Service implementation required first)
