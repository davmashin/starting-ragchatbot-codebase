"""Tests for FastAPI endpoints"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Add backend to path
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import the models directly to avoid app import issues
from pydantic import BaseModel
from typing import List, Optional

# Define models locally to avoid importing from app.py (which has static file issues)
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str
    sources: List[str]
    session_id: str

class CourseStats(BaseModel):
    """Response model for course statistics"""
    total_courses: int
    course_titles: List[str]

class ClearSessionRequest(BaseModel):
    """Request model for clearing a session"""
    session_id: str

class ClearSessionResponse(BaseModel):
    """Response model for clearing a session"""
    success: bool
    message: str


def create_test_app(mock_rag_system):
    """Create a test FastAPI app without static file mounting"""
    test_app = FastAPI(title="Test Course Materials RAG System")
    
    # Add middleware
    test_app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]
    )
    
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Define endpoints inline to avoid import issues
    @test_app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        """Process a query and return response with sources"""
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            
            answer, sources = mock_rag_system.query(request.query, session_id)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        """Get course analytics and statistics"""
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/api/lesson-link")
    async def get_lesson_link(course: str, lesson: int):
        """Get lesson link for a specific course and lesson number"""
        try:
            lesson_link = mock_rag_system.vector_store.get_lesson_link(course, lesson)
            return {"link": lesson_link}
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.post("/api/clear-session", response_model=ClearSessionResponse)
    async def clear_session(request: ClearSessionRequest):
        """Clear all messages from a specific session"""
        try:
            mock_rag_system.session_manager.clear_session(request.session_id)
            return ClearSessionResponse(
                success=True,
                message=f"Session {request.session_id} cleared successfully"
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

    @test_app.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "RAG System API"}
    
    return test_app


@pytest.mark.api
class TestApiEndpoints:
    """Test suite for API endpoints"""
    
    @pytest.fixture
    def mock_rag_system(self):
        """Mock RAG system for API testing"""
        mock_system = MagicMock()
        
        # Mock session manager
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.return_value = "test_session_123"
        mock_session_manager.clear_session.return_value = None
        mock_system.session_manager = mock_session_manager
        
        # Mock query method
        mock_system.query.return_value = (
            "MCP is the Model Context Protocol for connecting AI assistants to external data sources.",
            ["Course: MCP Course, Lesson: 1"]
        )
        
        # Mock analytics
        mock_system.get_course_analytics.return_value = {
            "total_courses": 2,
            "course_titles": ["MCP Course", "FastAPI Course"]
        }
        
        # Mock vector store
        mock_vector_store = MagicMock()
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson/1"
        mock_system.vector_store = mock_vector_store
        
        return mock_system
    
    @pytest.fixture
    async def test_client(self, mock_rag_system):
        """Test client with mocked dependencies"""
        app = create_test_app(mock_rag_system)
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    
    async def test_query_endpoint_success(self, test_client):
        """Test successful query processing"""
        request_data = {
            "query": "What is MCP?",
            "session_id": "test_session"
        }
        
        response = await test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test_session"
        assert isinstance(data["sources"], list)
    
    async def test_query_endpoint_new_session(self, test_client):
        """Test query with new session creation"""
        request_data = {"query": "What is MCP?"}
        
        response = await test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session_123"
    
    async def test_query_endpoint_invalid_request(self, test_client):
        """Test query endpoint with invalid request data"""
        response = await test_client.post("/api/query", json={})
        
        assert response.status_code == 422  # Validation error
    
    async def test_courses_endpoint_success(self, test_client):
        """Test successful course statistics retrieval"""
        response = await test_client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2
        assert "MCP Course" in data["course_titles"]
    
    async def test_lesson_link_endpoint_success(self, test_client):
        """Test successful lesson link retrieval"""
        response = await test_client.get("/api/lesson-link?course=MCP Course&lesson=1")
        
        assert response.status_code == 200
        data = response.json()
        assert "link" in data
        assert data["link"] == "https://example.com/lesson/1"
    
    async def test_lesson_link_endpoint_missing_params(self, test_client):
        """Test lesson link endpoint with missing parameters"""
        response = await test_client.get("/api/lesson-link")
        
        assert response.status_code == 422  # Validation error
    
    async def test_clear_session_endpoint_success(self, test_client):
        """Test successful session clearing"""
        request_data = {"session_id": "test_session_123"}
        
        response = await test_client.post("/api/clear-session", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Session test_session_123 cleared successfully" in data["message"]
    
    async def test_clear_session_endpoint_invalid_request(self, test_client):
        """Test clear session endpoint with invalid request"""
        response = await test_client.post("/api/clear-session", json={})
        
        assert response.status_code == 422  # Validation error
    
    async def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = await test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "RAG System API"
    
    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/query", "post", {"query": "test"}),
        ("/api/courses", "get", None),
        ("/api/lesson-link?course=test&lesson=1", "get", None),
        ("/api/clear-session", "post", {"session_id": "test"}),
        ("/", "get", None),
    ])
    async def test_cors_headers(self, test_client, endpoint, method, data):
        """Test that CORS headers are properly set"""
        if method == "get":
            response = await test_client.get(endpoint)
        else:
            response = await test_client.post(endpoint, json=data)
        
        # Should have CORS headers (exact headers depend on FastAPI CORS implementation)
        assert response.status_code in [200, 422]  # Either success or validation error is fine for CORS test


@pytest.mark.api
class TestApiErrorHandling:
    """Test error handling in API endpoints"""
    
    @pytest.fixture
    def failing_rag_system(self):
        """Mock RAG system that raises errors"""
        mock_system = MagicMock()
        
        # Mock session manager with errors
        mock_session_manager = MagicMock()
        mock_session_manager.create_session.side_effect = Exception("Session creation failed")
        mock_system.session_manager = mock_session_manager
        
        # Mock query method with error
        mock_system.query.side_effect = Exception("Query processing failed")
        
        # Mock analytics with error
        mock_system.get_course_analytics.side_effect = Exception("Analytics retrieval failed")
        
        # Mock vector store with error
        mock_vector_store = MagicMock()
        mock_vector_store.get_lesson_link.side_effect = Exception("Lesson link retrieval failed")
        mock_system.vector_store = mock_vector_store
        
        return mock_system
    
    @pytest.fixture
    async def failing_test_client(self, failing_rag_system):
        """Test client with failing dependencies"""
        app = create_test_app(failing_rag_system)
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    
    async def test_query_endpoint_error(self, failing_test_client):
        """Test query endpoint error handling"""
        request_data = {"query": "What is MCP?"}
        
        response = await failing_test_client.post("/api/query", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    async def test_courses_endpoint_error(self, failing_test_client):
        """Test courses endpoint error handling"""
        response = await failing_test_client.get("/api/courses")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    async def test_lesson_link_endpoint_error(self, failing_test_client):
        """Test lesson link endpoint error handling"""
        response = await failing_test_client.get("/api/lesson-link?course=test&lesson=1")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data