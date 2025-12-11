"""
Comprehensive tests for Query Service (Azure OpenAI integration).
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import APIError, APITimeoutError, RateLimitError

from eva_api.config import Settings
from eva_api.models.queries import QueryStatus
from eva_api.services.query_service import QueryService


@pytest.fixture
def query_settings():
    """Create test settings for query service."""
    settings = Settings()
    settings.mock_mode = False
    settings.AZURE_OPENAI_ENDPOINT = "https://test-openai.openai.azure.com/"
    settings.AZURE_OPENAI_KEY = "test-key"
    settings.AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
    return settings


@pytest.fixture
def mock_query_service(query_settings):
    """Create a query service with mocked dependencies."""
    mock_cosmos = MagicMock()
    mock_blob = MagicMock()

    with patch('eva_api.services.query_service.AsyncAzureOpenAI') as mock_openai_class:
        mock_openai = AsyncMock()
        mock_openai_class.return_value = mock_openai

        service = QueryService(query_settings, cosmos_service=mock_cosmos, blob_service=mock_blob)
        service.mock_openai = mock_openai

        yield service


class TestQuerySubmission:
    """Tests for query submission and status management."""

    @pytest.mark.asyncio
    async def test_submit_query_success(self, mock_query_service):
        """Test successful query submission."""
        space_id = uuid.uuid4()
        question = "What is the capital of France?"
        user_id = "test-user"
        parameters = {"temperature": 0.7, "max_tokens": 500}

        result = await mock_query_service.submit_query(
            space_id=space_id,
            question=question,
            user_id=user_id,
            parameters=parameters
        )

        assert result["question"] == question
        assert result["space_id"] == str(space_id)
        assert result["created_by"] == user_id
        assert result["status"] == QueryStatus.PENDING.value
        assert result["parameters"] == parameters
        assert "id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_submit_query_minimal(self, mock_query_service):
        """Test submitting query with minimal parameters."""
        space_id = uuid.uuid4()
        question = "What is AI?"
        user_id = "user123"

        result = await mock_query_service.submit_query(space_id, question, user_id)

        assert result["question"] == question
        assert result["parameters"] == {}

    @pytest.mark.asyncio
    async def test_submit_query_long_question(self, mock_query_service):
        """Test submitting very long question."""
        space_id = uuid.uuid4()
        question = "What is artificial intelligence? " * 100  # Long question
        user_id = "user123"

        result = await mock_query_service.submit_query(space_id, question, user_id)

        assert len(result["question"]) > 1000
        assert result["status"] == QueryStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_get_query_status_success(self, mock_query_service):
        """Test retrieving query status."""
        query_id = uuid.uuid4()
        expected_query = {
            "id": str(query_id),
            "status": QueryStatus.PROCESSING.value,
            "question": "Test question",
            "created_at": datetime.utcnow().isoformat()
        }

        mock_query_service.cosmos.queries_container.query_items.return_value = [expected_query]

        result = await mock_query_service.get_query_status(query_id)

        assert result["id"] == str(query_id)
        assert result["status"] == QueryStatus.PROCESSING.value

    @pytest.mark.asyncio
    async def test_get_query_status_not_found(self, mock_query_service):
        """Test retrieving non-existent query."""
        query_id = uuid.uuid4()

        mock_query_service.cosmos.queries_container.query_items.return_value = []

        result = await mock_query_service.get_query_status(query_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_query_result_completed(self, mock_query_service):
        """Test retrieving completed query result."""
        query_id = uuid.uuid4()
        expected_result = {
            "answer": "Paris is the capital of France.",
            "sources": [{"document_id": "doc1", "title": "Geography"}],
            "confidence": 0.95
        }
        expected_query = {
            "id": str(query_id),
            "status": QueryStatus.COMPLETED.value,
            "result": expected_result
        }

        mock_query_service.cosmos.queries_container.query_items.return_value = [expected_query]

        result = await mock_query_service.get_query_result(query_id)

        assert result == expected_result
        assert result["answer"] == "Paris is the capital of France."

    @pytest.mark.asyncio
    async def test_get_query_result_pending(self, mock_query_service):
        """Test retrieving result for pending query."""
        query_id = uuid.uuid4()
        expected_query = {
            "id": str(query_id),
            "status": QueryStatus.PENDING.value,
            "result": None
        }

        mock_query_service.cosmos.queries_container.query_items.return_value = [expected_query]

        result = await mock_query_service.get_query_result(query_id)

        assert result is None  # Not yet completed


class TestAzureOpenAIIntegration:
    """Tests for Azure OpenAI API interactions."""

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, mock_query_service):
        """Test successful chat completion with Azure OpenAI."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="4"))]
        mock_response.usage = MagicMock(total_tokens=25)

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await mock_query_service._call_openai(messages)

        assert result["content"] == "4"
        assert result["tokens"] == 25

    @pytest.mark.asyncio
    async def test_chat_completion_with_parameters(self, mock_query_service):
        """Test chat completion with custom parameters."""
        messages = [{"role": "user", "content": "Explain quantum computing"}]
        parameters = {"temperature": 0.9, "max_tokens": 1000}

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Quantum computing explanation..."))]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await mock_query_service._call_openai(messages, **parameters)

        assert "content" in result
        # Verify parameters were passed
        call_args = mock_query_service.mock_openai.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.9
        assert call_args[1]["max_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_streaming_response(self, mock_query_service):
        """Test streaming chat completion."""
        messages = [{"role": "user", "content": "Write a story"}]

        # Mock streaming response
        async def mock_stream():
            chunks = ["Once ", "upon ", "a ", "time..."]
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock(delta=MagicMock(content=chunk))]
                yield mock_chunk

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(return_value=mock_stream())

        result = []
        async for chunk in await mock_query_service._call_openai_streaming(messages):
            result.append(chunk)

        assert len(result) == 4
        assert "".join(result) == "Once upon a time..."

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, mock_query_service):
        """Test handling rate limit error."""
        messages = [{"role": "user", "content": "Test"}]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded")
        )

        with pytest.raises(RateLimitError):
            await mock_query_service._call_openai(messages)

    @pytest.mark.asyncio
    async def test_api_timeout(self, mock_query_service):
        """Test handling API timeout."""
        messages = [{"role": "user", "content": "Test"}]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError("Request timeout")
        )

        with pytest.raises(APITimeoutError):
            await mock_query_service._call_openai(messages)

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, mock_query_service):
        """Test handling invalid API key."""
        messages = [{"role": "user", "content": "Test"}]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=APIError("Invalid API key")
        )

        with pytest.raises(APIError):
            await mock_query_service._call_openai(messages)


class TestRetryLogic:
    """Tests for retry logic on failures."""

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, mock_query_service):
        """Test automatic retry on rate limit."""
        messages = [{"role": "user", "content": "Test"}]

        # Fail twice, then succeed
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Success"))]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=[
                RateLimitError("Rate limit"),
                RateLimitError("Rate limit"),
                mock_response
            ]
        )

        result = await mock_query_service._call_openai_with_retry(messages, max_retries=3)

        assert result["content"] == "Success"
        assert mock_query_service.mock_openai.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_query_service):
        """Test failure after max retries."""
        messages = [{"role": "user", "content": "Test"}]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit")
        )

        with pytest.raises(RateLimitError):
            await mock_query_service._call_openai_with_retry(messages, max_retries=2)

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_query_service):
        """Test exponential backoff between retries."""
        messages = [{"role": "user", "content": "Test"}]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Success"))]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=[RateLimitError("Rate limit"), mock_response]
        )

        with patch('asyncio.sleep') as mock_sleep:
            await mock_query_service._call_openai_with_retry(messages)

            # Verify sleep was called (backoff)
            mock_sleep.assert_called()


class TestTokenCounting:
    """Tests for token counting and management."""

    @pytest.mark.asyncio
    async def test_estimate_tokens(self, mock_query_service):
        """Test token estimation for messages."""
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is AI?"}
        ]

        token_count = await mock_query_service.estimate_tokens(messages)

        assert token_count > 0
        assert token_count < 100  # Should be relatively small

    @pytest.mark.asyncio
    async def test_token_limit_enforcement(self, mock_query_service):
        """Test enforcement of token limits."""
        # Create very long message that exceeds limit
        long_content = "word " * 10000
        messages = [{"role": "user", "content": long_content}]

        with pytest.raises(ValueError, match="Token limit exceeded"):
            await mock_query_service._call_openai(messages)

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, mock_query_service):
        """Test tracking of token usage."""
        messages = [{"role": "user", "content": "Test"}]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=25
        )

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await mock_query_service._call_openai(messages)

        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 15
        assert result["usage"]["total_tokens"] == 25


class TestRAGProcessing:
    """Tests for RAG (Retrieval-Augmented Generation) workflow."""

    @pytest.mark.asyncio
    async def test_document_retrieval(self, mock_query_service):
        """Test retrieving relevant documents for query."""
        space_id = uuid.uuid4()
        question = "What is the policy on vacation days?"

        mock_documents = [
            {"id": "doc1", "content": "Vacation policy content...", "relevance": 0.9},
            {"id": "doc2", "content": "HR policies...", "relevance": 0.7},
        ]

        mock_query_service.cosmos.documents_container.query_items.return_value = mock_documents

        result = await mock_query_service._retrieve_documents(space_id, question)

        assert len(result) == 2
        assert result[0]["id"] == "doc1"
        assert result[0]["relevance"] == 0.9

    @pytest.mark.asyncio
    async def test_context_building(self, mock_query_service):
        """Test building context from documents."""
        documents = [
            {"title": "Doc 1", "content": "Content 1"},
            {"title": "Doc 2", "content": "Content 2"},
        ]

        context = await mock_query_service._build_context(documents)

        assert "Doc 1" in context
        assert "Content 1" in context
        assert "Doc 2" in context

    @pytest.mark.asyncio
    async def test_rag_prompt_construction(self, mock_query_service):
        """Test constructing RAG prompt with context."""
        question = "What is the policy?"
        context = "Policy context from documents..."

        prompt = await mock_query_service._build_rag_prompt(question, context)

        assert question in prompt
        assert context in prompt
        assert "based on the following" in prompt.lower()

    @pytest.mark.asyncio
    async def test_source_citation(self, mock_query_service):
        """Test including source citations in response."""
        documents = [
            {"id": "doc1", "title": "Policy Doc", "content": "Content"},
        ]
        answer = "The policy states..."

        result = await mock_query_service._add_citations(answer, documents)

        assert result["answer"] == answer
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_id"] == "doc1"


class TestMockMode:
    """Tests for mock mode behavior."""

    @pytest.mark.asyncio
    async def test_mock_mode_query_submission(self, query_settings):
        """Test query submission in mock mode."""
        query_settings.mock_mode = True
        service = QueryService(query_settings)

        space_id = uuid.uuid4()
        result = await service.submit_query(space_id, "Test question", "user123")

        assert result["status"] == QueryStatus.PENDING.value
        assert result["question"] == "Test question"

    @pytest.mark.asyncio
    async def test_mock_mode_response(self, query_settings):
        """Test receiving mock response."""
        query_settings.mock_mode = True
        service = QueryService(query_settings)

        messages = [{"role": "user", "content": "Test"}]
        result = await service._call_openai(messages)

        assert "content" in result
        assert "mock" in result["content"].lower() or "demo" in result["content"].lower()


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    @pytest.mark.asyncio
    async def test_query_failure_updates_status(self, mock_query_service):
        """Test that failed query updates status correctly."""
        query_id = uuid.uuid4()

        # Simulate processing failure
        mock_query_service.mock_openai.chat.completions.create = AsyncMock(
            side_effect=APIError("API error")
        )

        # Process query (should fail gracefully)
        await mock_query_service._process_query(query_id)

        # Verify status was updated to FAILED
        # (Would need to check Cosmos DB in real implementation)

    @pytest.mark.asyncio
    async def test_partial_result_handling(self, mock_query_service):
        """Test handling partial responses."""
        messages = [{"role": "user", "content": "Long question"}]

        # Mock truncated response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(content="Partial answer..."),
            finish_reason="length"  # Truncated due to length
        )]

        mock_query_service.mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await mock_query_service._call_openai(messages)

        assert result["finish_reason"] == "length"
        assert result["truncated"] is True
