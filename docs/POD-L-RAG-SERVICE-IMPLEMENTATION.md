# POD-L: RAG Query Service Implementation
**Role:** POD-L (Libraries & Services)  
**Priority:** High (Core Feature)  
**Estimated Effort:** 24 hours (3 days)  
**Dependencies:** POD-I Azure AI Search setup must be completed first

---

## 🎯 Objective
Replace mock RAG logic with production Azure OpenAI + Azure AI Search integration to enable real document retrieval and answer synthesis.

## 📊 Context
Current `query_service.py` returns demo responses. Need to implement:
1. Query embedding generation
2. Vector search in Azure AI Search
3. Context building from retrieved chunks
4. Answer synthesis with Azure OpenAI GPT-4
5. Citation extraction and source attribution

**Current Code:** `src/eva_api/services/query_service.py` (432 lines)  
**Mock Implementation:** Lines 166-220 (`_process_query`)

---

## 🔧 Technical Requirements

### Input
- Query from user (via POST /api/v1/queries)
- space_id for tenant isolation
- User's language preference (en/fr)
- Azure AI Search endpoint + credentials
- Azure OpenAI endpoint + credentials

### Output
- Answer text (bilingual)
- Source citations with [1], [2] numbering
- Metadata: tokens used, processing time, confidence score
- Documents: title, page number, snippet

### Constraints
- <5 second p95 latency
- <3000 tokens context window
- Top 10 document chunks (configurable)
- Score threshold: 0.7 (configurable)
- Bilingual prompts (EN/FR)

---

## 📝 Implementation Steps

### 1. Update QueryService __init__
```python
# File: src/eva_api/services/query_service.py

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
import tiktoken

class QueryService:
    def __init__(
        self,
        settings: Settings,
        cosmos_service=None,
        blob_service=None,
    ):
        self.settings = settings
        self.cosmos = cosmos_service
        self.blob = blob_service
        self.mock_mode = settings.mock_mode
        
        # Initialize Azure OpenAI client
        if not self.mock_mode and settings.AZURE_OPENAI_ENDPOINT:
            self.openai_client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                timeout=settings.azure_timeout,
            )
            self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
            self.embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            
            # ADD: Azure AI Search client
            self.search_client = SearchClient(
                endpoint=settings.AZURE_SEARCH_ENDPOINT,
                index_name=settings.AZURE_SEARCH_INDEX_NAME,
                credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY)
            )
            
            # Token counter for context management
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
            
            logger.info("✅ Azure OpenAI + AI Search clients initialized")
        else:
            self.openai_client = None
            self.search_client = None
            self.tokenizer = None
            logger.warning("⚠️  Running in MOCK MODE - no real AI calls")
```

### 2. Implement _generate_embedding()
```python
async def _generate_embedding(self, text: str) -> list[float]:
    """
    Generate embedding vector for query text.
    
    Args:
        text: User's question
        
    Returns:
        1536-dimension embedding vector
    """
    if not self.openai_client:
        # Mock embedding for testing
        return [0.1] * 1536
    
    try:
        response = await self.openai_client.embeddings.create(
            model=self.embedding_deployment,
            input=text
        )
        embedding = response.data[0].embedding
        logger.info(f"✅ Generated embedding: {len(embedding)} dimensions")
        return embedding
    
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate query embedding: {str(e)}"
        )
```

**Validation:**
```python
# Test embedding generation
embedding = await query_service._generate_embedding("What is CPP?")
assert len(embedding) == 1536
assert all(isinstance(x, float) for x in embedding)
```

### 3. Implement _vector_search()
```python
async def _vector_search(
    self,
    embedding: list[float],
    space_id: UUID,
    top_k: int = 10,
    score_threshold: float = 0.7
) -> list[dict]:
    """
    Perform vector search in Azure AI Search.
    
    Args:
        embedding: Query embedding vector
        space_id: Knowledge space filter
        top_k: Number of results to return
        score_threshold: Minimum relevance score
        
    Returns:
        List of document chunks with metadata
    """
    if not self.search_client:
        # Mock results for testing
        return [{
            "id": "demo-chunk-1",
            "content": "Demo content about CPP eligibility...",
            "title": "Canada Pension Plan Guide",
            "document_name": "CPP-Guide-2024.pdf",
            "page_number": 5,
            "score": 0.85
        }]
    
    try:
        # Build vector query
        vector_query = VectorizedQuery(
            vector=embedding,
            k_nearest_neighbors=top_k,
            fields="embedding"
        )
        
        # Execute hybrid search (vector + keyword)
        results = await asyncio.to_thread(
            self.search_client.search,
            search_text="*",  # Use * for vector-only, or add query text for hybrid
            vector_queries=[vector_query],
            filter=f"space_id eq '{space_id}'",
            select=["id", "content", "title", "document_name", "page_number"],
            top=top_k
        )
        
        # Filter by score threshold and format results
        filtered_results = []
        for result in results:
            score = result.get("@search.score", 0)
            if score >= score_threshold:
                filtered_results.append({
                    "id": result["id"],
                    "content": result["content"],
                    "title": result.get("title", "Untitled"),
                    "document_name": result.get("document_name", "Unknown"),
                    "page_number": result.get("page_number", 0),
                    "score": score
                })
        
        logger.info(f"✅ Vector search: {len(filtered_results)}/{top_k} chunks above threshold {score_threshold}")
        return filtered_results
    
    except Exception as e:
        logger.error(f"❌ Vector search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Document search failed: {str(e)}"
        )
```

**Validation:**
```python
# Test vector search
results = await query_service._vector_search(
    embedding=[0.1] * 1536,
    space_id=UUID("test-space-id"),
    top_k=10,
    score_threshold=0.7
)
assert len(results) <= 10
assert all(r["score"] >= 0.7 for r in results)
```

### 4. Implement _build_context()
```python
def _build_context(
    self,
    results: list[dict],
    max_tokens: int = 3000
) -> tuple[str, list[dict]]:
    """
    Build context string from search results with token limit.
    
    Args:
        results: Search results from _vector_search()
        max_tokens: Maximum context size
        
    Returns:
        (context_string, sources_list)
    """
    context_parts = []
    sources = []
    total_tokens = 0
    
    for i, result in enumerate(results, start=1):
        # Format chunk with citation number
        chunk_text = f"[{i}] Title: {result['title']}\n"
        chunk_text += f"Source: {result['document_name']} (Page {result['page_number']})\n"
        chunk_text += f"Content: {result['content']}\n"
        
        # Count tokens
        chunk_tokens = len(self.tokenizer.encode(chunk_text)) if self.tokenizer else len(chunk_text) // 4
        
        # Check if adding this chunk exceeds limit
        if total_tokens + chunk_tokens > max_tokens:
            logger.warning(f"⚠️  Context limit reached at {i-1} chunks ({total_tokens} tokens)")
            break
        
        context_parts.append(chunk_text)
        sources.append({
            "citation": i,
            "title": result['title'],
            "document_name": result['document_name'],
            "page_number": result['page_number'],
            "relevance_score": result['score'],
            "snippet": result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
        })
        total_tokens += chunk_tokens
    
    context = "\n\n".join(context_parts)
    logger.info(f"✅ Built context: {len(sources)} chunks, {total_tokens} tokens")
    
    return context, sources
```

### 5. Update _generate_answer() with Bilingual Prompts
```python
async def _generate_answer(
    self,
    question: str,
    context: str,
    language: str = "en",
    parameters: dict = None,
) -> dict:
    """
    Generate answer using Azure OpenAI with RAG context.
    
    Args:
        question: User's question
        context: Retrieved document context
        language: Response language (en/fr)
        parameters: Query parameters (temperature, max_tokens)
    
    Returns:
        {
            "text": "Answer text with citations [1], [2]",
            "tokens": 450,
            "model": "gpt-4"
        }
    """
    if not self.openai_client:
        return {
            "text": "Mock answer (OpenAI not configured)",
            "tokens": 0,
            "model": "mock"
        }
    
    # Bilingual system prompts
    system_prompts = {
        "en": """You are EVA (Enterprise Virtual Assistant), a helpful bilingual AI assistant for Canadian public servants.

INSTRUCTIONS:
1. Answer the user's question using ONLY the context provided below
2. Cite your sources using [1], [2], etc. when referencing information
3. If the context doesn't contain relevant information, say: "I don't have information about that in the available documents."
4. Be concise but thorough
5. Use professional, accessible language
6. Maintain accuracy - never make up information

CONTEXT:
{context}""",
        
        "fr": """Vous êtes EVA (Assistant Virtuel d'Entreprise), un assistant IA bilingue serviable pour les fonctionnaires canadiens.

INSTRUCTIONS :
1. Répondez à la question de l'utilisateur en utilisant UNIQUEMENT le contexte fourni ci-dessous
2. Citez vos sources en utilisant [1], [2], etc. lorsque vous référencez des informations
3. Si le contexte ne contient pas d'informations pertinentes, dites : "Je n'ai pas d'informations à ce sujet dans les documents disponibles."
4. Soyez concis mais complet
5. Utilisez un langage professionnel et accessible
6. Maintenez l'exactitude - n'inventez jamais d'informations

CONTEXTE :
{context}"""
    }
    
    system_prompt = system_prompts.get(language, system_prompts["en"]).format(context=context)
    
    # Get parameters with defaults
    params = parameters or {}
    temperature = params.get("temperature", 0.3)  # Low temp for factual accuracy
    max_tokens = params.get("max_tokens", 1000)
    
    try:
        response = await self.openai_client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        answer_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        logger.info(f"✅ Answer generated: {tokens_used} tokens, {len(answer_text)} chars")
        
        return {
            "text": answer_text,
            "tokens": tokens_used,
            "model": self.deployment_name,
            "finish_reason": response.choices[0].finish_reason
        }
    
    except Exception as e:
        logger.error(f"❌ Answer generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )
```

### 6. Replace _process_query() with Production Logic
```python
async def _process_query(self, query_id: UUID) -> None:
    """
    PRODUCTION: Process query using RAG pipeline.
    
    Steps:
    1. Generate query embedding
    2. Vector search in Azure AI Search
    3. Build context from top chunks
    4. Call Azure OpenAI for answer synthesis
    5. Extract citations and store result
    """
    start_time = time.time()
    
    try:
        # Get query from Cosmos DB
        query = await self.get_query_status(query_id)
        if not query:
            logger.error(f"Query {query_id} not found")
            return
        
        question = query["question"]
        space_id = UUID(query["space_id"])
        language = query.get("language", "en")
        
        logger.info(f"🔍 Processing query {query_id}: '{question}' (space: {space_id}, lang: {language})")
        
        # Update status to PROCESSING
        await self._update_query_status(query_id, QueryStatus.PROCESSING)
        
        # STEP 1: Generate query embedding
        embedding = await self._generate_embedding(question)
        
        # STEP 2: Vector search
        search_results = await self._vector_search(
            embedding=embedding,
            space_id=space_id,
            top_k=self.settings.rag_top_k_results,
            score_threshold=self.settings.rag_score_threshold
        )
        
        if not search_results:
            # No relevant documents found
            await self._update_query_status(
                query_id,
                QueryStatus.COMPLETED,
                error_message="No relevant documents found"
            )
            logger.warning(f"⚠️  No documents above threshold for query {query_id}")
            return
        
        # STEP 3: Build context
        context, sources = self._build_context(
            search_results,
            max_tokens=self.settings.rag_max_context_tokens
        )
        
        # STEP 4: Generate answer with Azure OpenAI
        answer_data = await self._generate_answer(
            question=question,
            context=context,
            language=language,
            parameters=query.get("parameters")
        )
        
        # STEP 5: Build result object
        processing_time = time.time() - start_time
        result = {
            "answer": answer_data["text"],
            "sources": sources,
            "metadata": {
                "processing_time": round(processing_time, 2),
                "tokens_used": answer_data["tokens"],
                "model": answer_data["model"],
                "chunks_retrieved": len(search_results),
                "chunks_used": len(sources),
                "language": language,
                "finish_reason": answer_data.get("finish_reason"),
                "is_demo": False
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # STEP 6: Store result in Cosmos DB
        query["status"] = QueryStatus.COMPLETED.value
        query["result"] = result
        query["updated_at"] = datetime.utcnow().isoformat()
        
        await asyncio.to_thread(
            self.cosmos.queries_container.upsert_item,
            body=query
        )
        
        logger.info(f"✅ Query {query_id} completed: {processing_time:.2f}s, {answer_data['tokens']} tokens")
    
    except Exception as e:
        logger.error(f"❌ Query {query_id} failed: {e}", exc_info=True)
        await self._update_query_status(
            query_id,
            QueryStatus.FAILED,
            error_message=str(e)
        )
```

---

## ✅ Acceptance Criteria
- [ ] `_generate_embedding()` returns 1536-dim vector
- [ ] `_vector_search()` filters by space_id correctly
- [ ] `_vector_search()` respects score_threshold
- [ ] `_build_context()` stays under max_tokens limit
- [ ] `_generate_answer()` supports EN and FR prompts
- [ ] `_generate_answer()` includes [1], [2] citations
- [ ] `_process_query()` completes in <5 seconds (p95)
- [ ] Result includes sources with page numbers
- [ ] Unit tests pass for all methods
- [ ] Integration test: end-to-end query flow
- [ ] Mock mode still works (for testing without Azure)
- [ ] Bilingual test: FR question → FR answer

---

## 🧪 Validation

### Unit Tests
```python
# tests/test_query_service_rag.py

@pytest.mark.asyncio
async def test_generate_embedding():
    service = QueryService(settings, cosmos, blob)
    embedding = await service._generate_embedding("Test question")
    assert len(embedding) == 1536
    assert all(-1 <= x <= 1 for x in embedding)

@pytest.mark.asyncio
async def test_vector_search_with_filter():
    service = QueryService(settings, cosmos, blob)
    results = await service._vector_search(
        embedding=[0.1] * 1536,
        space_id=UUID("test-space"),
        top_k=5
    )
    assert len(results) <= 5
    assert all(r["score"] >= 0.7 for r in results)

def test_build_context_token_limit():
    service = QueryService(settings, cosmos, blob)
    mock_results = [
        {"content": "x" * 5000, "title": "Doc1", "document_name": "test.pdf", "page_number": 1, "score": 0.9}
        for _ in range(10)
    ]
    context, sources = service._build_context(mock_results, max_tokens=1000)
    tokens = len(service.tokenizer.encode(context))
    assert tokens <= 1000

@pytest.mark.asyncio
async def test_generate_answer_bilingual():
    service = QueryService(settings, cosmos, blob)
    
    # English
    answer_en = await service._generate_answer("What is CPP?", "CPP is...", language="en")
    assert "Mock" not in answer_en["text"] or settings.mock_mode
    
    # French
    answer_fr = await service._generate_answer("Qu'est-ce que le RPC?", "Le RPC est...", language="fr")
    assert answer_fr["tokens"] > 0
```

### Integration Test
```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_rag_pipeline():
    """End-to-end RAG test with real Azure services."""
    service = QueryService(settings, cosmos, blob)
    
    # Submit query
    query = await service.submit_query(
        space_id=UUID("test-space-with-docs"),
        question="What are the CPP eligibility requirements?",
        user_id="test-user"
    )
    query_id = query["id"]
    
    # Wait for processing
    await asyncio.sleep(10)
    
    # Check result
    result = await service.get_query_result(query_id)
    assert result is not None
    assert "CPP" in result["answer"] or "eligibility" in result["answer"]
    assert len(result["sources"]) > 0
    assert result["metadata"]["is_demo"] is False
    assert result["metadata"]["processing_time"] < 10.0
```

---

## 📚 Resources

**Code Files:**
- Main implementation: `src/eva_api/services/query_service.py`
- Config updates: `src/eva_api/config.py`
- Tests: `tests/test_query_service_rag.py`

**Azure Documentation:**
- [Azure OpenAI Chat Completion](https://learn.microsoft.com/azure/ai-services/openai/reference)
- [Azure AI Search Python SDK](https://learn.microsoft.com/python/api/overview/azure/search-documents-readme)
- [Vector Search Guide](https://learn.microsoft.com/azure/search/vector-search-how-to-query)

**Dependencies:**
```python
# Add to requirements.txt if missing
azure-search-documents==11.4.0
tiktoken==0.7.0
```

---

## 🚨 Risks & Mitigation

**Risk:** Azure OpenAI rate limits (10 RPM on free tier)  
**Impact:** High (service degradation)  
**Mitigation:** Request quota increase to 60 RPM, implement exponential backoff retry

**Risk:** Vector search returns no results above threshold  
**Impact:** Medium (user experience)  
**Mitigation:** Lower threshold to 0.6 temporarily, log queries with no results for analysis

**Risk:** Context exceeds max tokens  
**Impact:** Low (truncation)  
**Mitigation:** Implement token counting before OpenAI call, truncate smartly at sentence boundaries

**Risk:** Bilingual prompt engineering needs tuning  
**Impact:** Medium (answer quality)  
**Mitigation:** A/B test prompts, collect user feedback, iterate based on examples

---

**Created:** December 9, 2025  
**Assigned To:** POD-L (Libraries & Services Team)  
**Status:** 📋 Ready for Implementation  
**Estimated Time:** 24 hours (3 days)
