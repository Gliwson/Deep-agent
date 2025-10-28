import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, mock_open
from main import (
    DeepAgent, CodeAnalysisRequest, CodeGenerationRequest, TestGenerationRequest, 
    RefactoringRequest, FileReadRequest, FileWriteRequest, SearchRequest, 
    ReplaceRequest, TerminalRequest, PlanningRequest
)

class TestDeepAgent:
    def setup_method(self):
        """Setup for each test method"""
        self.agent = DeepAgent()
        self.agent.client = Mock()
        # Mock OpenAI response
        self.mock_choice = Mock()
        self.mock_choice.message.content = '{"quality": "good", "bugs": [], "performance": "optimized"}'
        self.mock_response = Mock()
        self.mock_response.choices = [self.mock_choice]
        self.agent.client.chat.completions.create = AsyncMock(return_value=self.mock_response)
        
    @pytest.mark.asyncio
    async def test_analyze_code_success(self):
        """Test successful code analysis"""
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
        self.agent.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_code_failure(self):
        """Test code analysis failure"""
        # Mock client to raise exception
        self.agent.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
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
        self.mock_choice.message.content = "def calculate_sum(a, b):\n    return a + b"
        
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
        self.mock_choice.message.content = "def test_calculate_sum():\n    assert calculate_sum(2, 3) == 5"
        
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
        self.mock_choice.message.content = "def calculate_sum(a: int, b: int) -> int:\n    \"\"\"Add two integers.\"\"\"\n    return a + b"
        
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
        assert self.agent._get_default_test_framework("rust") == "cargo test"
        assert self.agent._get_default_test_framework("unknown") == "pytest"
    
    @pytest.mark.asyncio
    async def test_read_file_success(self):
        """Test successful file reading"""
        with patch("builtins.open", mock_open(read_data="test content")):
            with patch("pathlib.Path.exists", return_value=True):
                request = FileReadRequest(file_path="test.py")
                result = await self.agent.read_file(request)
                
                assert result.success is True
                assert "content" in result.data
                assert result.data["content"] == "test content"
    
    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        """Test file reading when file doesn't exist"""
        with patch("pathlib.Path.exists", return_value=False):
            request = FileReadRequest(file_path="nonexistent.py")
            result = await self.agent.read_file(request)
            
            assert result.success is False
            assert "not found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_write_file_success(self):
        """Test successful file writing"""
        with patch("builtins.open", mock_open()):
            with patch("pathlib.Path.parent") as mock_parent:
                mock_parent.mkdir = Mock()
                with patch("pathlib.Path.exists", return_value=False):
                    request = FileWriteRequest(file_path="test.py", content="test content")
                    result = await self.agent.write_file(request)
                    
                    assert result.success is True
                    assert "written successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_list_directory_success(self):
        """Test successful directory listing"""
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.iterdir.return_value = [
            Mock(name="file1.py", is_file=Mock(return_value=True), is_dir=Mock(return_value=False), stat=Mock(return_value=Mock(st_size=100, st_mtime=1234567890))),
            Mock(name="dir1", is_file=Mock(return_value=False), is_dir=Mock(return_value=True), stat=Mock(return_value=Mock(st_size=None, st_mtime=1234567890)))
        ]
        
        with patch("main.Path") as mock_path_class:
            mock_path_class.return_value = mock_path
            result = await self.agent.list_directory("test_dir")
            
            assert result.success is True
            assert len(result.data["items"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_text_success(self):
        """Test successful text search"""
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_file.__str__ = Mock(return_value="test.py")
            mock_rglob.return_value = [mock_file]
            
            with patch("builtins.open", mock_open(read_data="def test_function():\n    pass")):
                request = SearchRequest(pattern="test_function")
                result = await self.agent.search_text(request)
                
                assert result.success is True
                assert "results" in result.data
    
    @pytest.mark.asyncio
    async def test_replace_text_success(self):
        """Test successful text replacement"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="old text")):
                with patch("shutil.copy2"):
                    request = ReplaceRequest(file_path="test.py", old_text="old", new_text="new")
                    result = await self.agent.replace_text(request)
                    
                    assert result.success is True
                    assert "replaced successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_command_success(self):
        """Test successful command execution"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        async def mock_wait_for(coro, timeout):
            return await coro
            
        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            with patch("asyncio.wait_for", side_effect=mock_wait_for):
                with patch("pathlib.Path.exists", return_value=True):
                    # Mock the workspace_root
                    self.agent.workspace_root = Mock()
                    self.agent.workspace_root.exists.return_value = True
                    request = TerminalRequest(command="ls")
                    result = await self.agent.execute_command(request)
                    
                    assert result.success is True
                    assert "executed" in result.message
    
    @pytest.mark.asyncio
    async def test_plan_task_success(self):
        """Test successful task planning"""
        self.mock_choice.message.content = '{"plan": "detailed plan"}'
        
        request = PlanningRequest(task="test task", context="test context")
        result = await self.agent.plan_task(request)
        
        assert result.success is True
        assert "plan" in result.data
        self.agent.client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_mock_success(self):
        """Test successful mock creation"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    result = await self.agent.create_mock("api_response", {"test": "data"})
                    
                    assert result.success is True
                    assert "created successfully" in result.message

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
        agent.client = Mock()
        
        # Mock OpenAI response
        mock_choice = Mock()
        mock_choice.message.content = "Test response"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        agent.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
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