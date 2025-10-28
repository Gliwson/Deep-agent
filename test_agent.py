import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from main import DeepAgent, CodeAnalysisRequest, CodeGenerationRequest, TestGenerationRequest, RefactoringRequest

class TestDeepAgent:
    def setup_method(self):
        """Setup for each test method"""
        self.agent = DeepAgent()
        self.agent.client = Mock()
        
    @pytest.mark.asyncio
    async def test_analyze_code_success(self):
        """Test successful code analysis"""
        # Mock OpenAI response
        mock_choice = Mock()
        mock_choice.message.content = '{"quality": "good", "bugs": [], "performance": "optimized"}'
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        self.agent.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Test data
        request = CodeAnalysisRequest(
            code="def hello(): return 'world'",
            language="python",
            context="Simple function"
        )
        
        # Execute
        result = await self.agent.analyze_code(request)
        
        # Assertions
        assert result.success is True
        assert "analysis" in result.data
        assert result.error is None
        self.agent.llm.agenerate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_code_failure(self):
        """Test code analysis failure"""
        # Mock LLM to raise exception
        self.agent.llm.agenerate = AsyncMock(side_effect=Exception("API Error"))
        
        request = CodeAnalysisRequest(
            code="def hello(): return 'world'",
            language="python"
        )
        
        result = await self.agent.analyze_code(request)
        
        assert result.success is False
        assert "API Error" in result.error
        assert result.data is None
    
    @pytest.mark.asyncio
    async def test_generate_code_success(self):
        """Test successful code generation"""
        mock_generation = Mock()
        mock_generation.text = "def calculate_sum(a, b):\n    return a + b"
        
        mock_response = Mock()
        mock_response.generations = [[mock_generation]]
        
        self.agent.llm.agenerate = AsyncMock(return_value=mock_response)
        
        request = CodeGenerationRequest(
            description="Create a function that adds two numbers",
            language="python"
        )
        
        result = await self.agent.generate_code(request)
        
        assert result.success is True
        assert "generated_code" in result.data
        assert "def calculate_sum" in result.data["generated_code"]
    
    @pytest.mark.asyncio
    async def test_generate_tests_success(self):
        """Test successful test generation"""
        mock_generation = Mock()
        mock_generation.text = "def test_calculate_sum():\n    assert calculate_sum(2, 3) == 5"
        
        mock_response = Mock()
        mock_response.generations = [[mock_generation]]
        
        self.agent.llm.agenerate = AsyncMock(return_value=mock_response)
        
        request = TestGenerationRequest(
            code="def calculate_sum(a, b):\n    return a + b",
            language="python",
            test_framework="pytest"
        )
        
        result = await self.agent.generate_tests(request)
        
        assert result.success is True
        assert "test_code" in result.data
        assert result.data["test_framework"] == "pytest"
    
    @pytest.mark.asyncio
    async def test_refactor_code_success(self):
        """Test successful code refactoring"""
        mock_generation = Mock()
        mock_generation.text = "def calculate_sum(a: int, b: int) -> int:\n    \"\"\"Add two integers.\"\"\"\n    return a + b"
        
        mock_response = Mock()
        mock_response.generations = [[mock_generation]]
        
        self.agent.llm.agenerate = AsyncMock(return_value=mock_response)
        
        request = RefactoringRequest(
            code="def calculate_sum(a, b):\n    return a + b",
            language="python",
            refactoring_type="optimize"
        )
        
        result = await self.agent.refactor_code(request)
        
        assert result.success is True
        assert "refactored_code" in result.data
        assert result.data["refactoring_type"] == "optimize"
    
    def test_get_default_test_framework(self):
        """Test default test framework selection"""
        assert self.agent._get_default_test_framework("python") == "pytest"
        assert self.agent._get_default_test_framework("javascript") == "jest"
        assert self.agent._get_default_test_framework("java") == "junit"
        assert self.agent._get_default_test_framework("unknown") == "pytest"

class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self):
        """Test WebSocket message handling"""
        from main import handle_websocket_message, manager
        
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        # Test analyze_code message
        message = json.dumps({
            "action": "analyze_code",
            "data": {
                "code": "def test(): pass",
                "language": "python"
            }
        })
        
        # Mock the agent
        with patch('main.agent') as mock_agent:
            mock_response = Mock()
            mock_response.dict.return_value = {"success": True, "message": "Test"}
            mock_agent.analyze_code = AsyncMock(return_value=mock_response)
            
            await handle_websocket_message(mock_websocket, message)
            
            # Verify WebSocket send was called
            mock_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalid_json_handling(self):
        """Test handling of invalid JSON messages"""
        from main import handle_websocket_message
        
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        # Test with invalid JSON
        await handle_websocket_message(mock_websocket, "invalid json")
        
        # Should send error response
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        response = json.loads(call_args)
        assert response["success"] is False
        assert "Invalid JSON" in response["message"]
    
    @pytest.mark.asyncio
    async def test_unknown_action_handling(self):
        """Test handling of unknown actions"""
        from main import handle_websocket_message
        
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        message = json.dumps({
            "action": "unknown_action",
            "data": {}
        })
        
        await handle_websocket_message(mock_websocket, message)
        
        # Should send error response
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        response = json.loads(call_args)
        assert response["success"] is False
        assert "Unknown action" in response["message"]

class TestConnectionManager:
    """Test WebSocket connection management"""
    
    def test_connection_management(self):
        """Test connection manager functionality"""
        from main import ConnectionManager
        
        manager = ConnectionManager()
        mock_websocket = Mock()
        
        # Test initial state
        assert len(manager.active_connections) == 0
        
        # Test adding connection
        manager.active_connections.append(mock_websocket)
        assert len(manager.active_connections) == 1
        
        # Test removing connection
        manager.disconnect(mock_websocket)
        assert len(manager.active_connections) == 0

# Test data fixtures
@pytest.fixture
def sample_python_code():
    return """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
"""

@pytest.fixture
def sample_javascript_code():
    return """
function calculateSum(a, b) {
    return a + b;
}

function findMax(arr) {
    return Math.max(...arr);
}
"""

# Performance tests
class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        agent = DeepAgent()
        agent.llm = Mock()
        
        # Mock LLM response
        mock_generation = Mock()
        mock_generation.text = "Test response"
        mock_response = Mock()
        mock_response.generations = [[mock_generation]]
        agent.llm.agenerate = AsyncMock(return_value=mock_response)
        
        # Create multiple concurrent requests
        requests = [
            CodeAnalysisRequest(code=f"def test{i}(): pass", language="python")
            for i in range(5)
        ]
        
        # Execute concurrently
        tasks = [agent.analyze_code(req) for req in requests]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(result.success for result in results)
        assert len(results) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])