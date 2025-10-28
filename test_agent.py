import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock, mock_open
from main import (
    DeepAgent, CodeAnalysisRequest, CodeGenerationRequest, CodeTestGenerationRequest, 
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
        
        request = CodeTestGenerationRequest(
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
        # Create mock items
        mock_file = Mock()
        mock_file.name = "file1.py"
        mock_file.is_file.return_value = True
        mock_file.is_dir.return_value = False
        mock_file.stat.return_value = Mock(st_size=100, st_mtime=1234567890)
        
        mock_dir = Mock()
        mock_dir.name = "dir1"
        mock_dir.is_file.return_value = False
        mock_dir.is_dir.return_value = True
        mock_dir.stat.return_value = Mock(st_size=None, st_mtime=1234567890)
        
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.iterdir.return_value = [mock_file, mock_dir]
        mock_path.__str__ = Mock(return_value="test_dir")
        
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
        
        with patch("main.asyncio.create_subprocess_shell", return_value=mock_process):
            with patch("main.asyncio.wait_for", side_effect=mock_wait_for):
                with patch("main.Path") as mock_path_class:
                    mock_path = Mock()
                    mock_path.exists.return_value = True
                    mock_path.__str__ = Mock(return_value="/workspace")
                    mock_path_class.return_value = mock_path
                    
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
                    # Use valid API response data
                    mock_data = {
                        "status_code": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": {"message": "success"}
                    }
                    result = await self.agent.create_mock("api_response", mock_data)
                    
                    assert result.success is True
                    assert "created successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_create_websocket_mock(self):
        """Test WebSocket mock creation"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    mock_data = {
                        "connection_url": "ws://localhost:8000",
                        "message_types": ["text", "binary"],
                        "ping_interval": 30
                    }
                    result = await self.agent.create_mock("websocket", mock_data)
                    
                    assert result.success is True
                    assert result.data["mock_type"] == "websocket"
                    assert "ws://localhost:8000" in str(result.data["mock_data"])
    
    @pytest.mark.asyncio
    async def test_create_authentication_mock(self):
        """Test authentication mock creation"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    mock_data = {
                        "token": "test_token_123",
                        "user_id": "user_456",
                        "roles": ["admin", "user"]
                    }
                    result = await self.agent.create_mock("authentication", mock_data)
                    
                    assert result.success is True
                    assert result.data["mock_type"] == "authentication"
                    assert "test_token_123" in str(result.data["mock_data"])
    
    @pytest.mark.asyncio
    async def test_create_file_upload_mock(self):
        """Test file upload mock creation"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    mock_data = {
                        "max_file_size": 10485760,
                        "allowed_extensions": [".txt", ".pdf"],
                        "upload_path": "/tmp/uploads"
                    }
                    result = await self.agent.create_mock("file_upload", mock_data)
                    
                    assert result.success is True
                    assert result.data["mock_type"] == "file_upload"
                    assert result.data["mock_data"]["max_file_size"] == 10485760
    
    @pytest.mark.asyncio
    async def test_mock_validation_failure(self):
        """Test mock validation failure"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    # Invalid API response - missing required fields
                    result = await self.agent.create_mock("api_response", {"invalid": "data"})
                    
                    assert result.success is False
                    assert "validation failed" in result.message
    
    @pytest.mark.asyncio
    async def test_mock_validation_success(self):
        """Test successful mock validation"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump"):
                    # Valid API response
                    mock_data = {
                        "status_code": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": {"message": "success"}
                    }
                    result = await self.agent.create_mock("api_response", mock_data)
                    
                    assert result.success is True
                    assert result.data["validation"]["valid"] is True

class TestErrorHandling:
    """Test error handling scenarios"""
    
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
    async def test_read_file_permission_error(self):
        """Test file reading with permission error"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                request = FileReadRequest(file_path="protected_file.txt")
                result = await self.agent.read_file(request)
                
                assert result.success is False
                assert "Failed to read file" in result.message
                assert "Permission denied" in result.error
    
    @pytest.mark.asyncio
    async def test_write_file_disk_full(self):
        """Test file writing with disk full error"""
        with patch("pathlib.Path.parent") as mock_parent:
            mock_parent.mkdir = Mock()
            with patch("pathlib.Path.exists", return_value=False):
                with patch("builtins.open", side_effect=OSError("No space left on device")):
                    request = FileWriteRequest(file_path="test.txt", content="test content")
                    result = await self.agent.write_file(request)
                    
                    assert result.success is False
                    assert "Failed to write file" in result.message
                    assert "No space left" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_command_timeout(self):
        """Test command execution timeout"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"output", b""))
        
        async def mock_wait_for_timeout(coro, timeout):
            raise asyncio.TimeoutError("Command timed out")
        
        with patch("main.asyncio.create_subprocess_shell", return_value=mock_process):
            with patch("main.asyncio.wait_for", side_effect=mock_wait_for_timeout):
                with patch("main.Path") as mock_path_class:
                    mock_path = Mock()
                    mock_path.exists.return_value = True
                    mock_path.__str__ = Mock(return_value="/workspace")
                    mock_path_class.return_value = mock_path
                    
                    request = TerminalRequest(command="sleep 100", timeout=1)
                    result = await self.agent.execute_command(request)
                    
                    assert result.success is False
                    assert "timed out" in result.message
    
    @pytest.mark.asyncio
    async def test_search_text_unicode_error(self):
        """Test text search with unicode decode error"""
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_file = Mock()
            mock_file.is_file.return_value = True
            mock_file.__str__ = Mock(return_value="binary_file.bin")
            mock_rglob.return_value = [mock_file]
            
            with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")):
                request = SearchRequest(pattern="test")
                result = await self.agent.search_text(request)
                
                assert result.success is True  # Should skip problematic files
                assert "results" in result.data
    
    @pytest.mark.asyncio
    async def test_analyze_code_api_error(self):
        """Test code analysis with API error"""
        self.agent.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )
        
        request = CodeAnalysisRequest(
            code="def test(): pass",
            language="python"
        )
        result = await self.agent.analyze_code(request)
        
        assert result.success is False
        assert "Failed to analyze code" in result.message
        assert "API rate limit exceeded" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_code_invalid_language(self):
        """Test code generation with invalid language"""
        self.agent.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Unsupported language: invalid_lang")
        )
        
        request = CodeGenerationRequest(
            description="Create a function",
            language="invalid_lang"
        )
        result = await self.agent.generate_code(request)
        
        assert result.success is False
        assert "Failed to generate code" in result.message
        assert "Unsupported language" in result.error
    
    @pytest.mark.asyncio
    async def test_replace_text_file_not_found(self):
        """Test text replacement with non-existent file"""
        with patch("pathlib.Path.exists", return_value=False):
            request = ReplaceRequest(
                file_path="nonexistent.txt",
                old_text="old",
                new_text="new"
            )
            result = await self.agent.replace_text(request)
            
            assert result.success is False
            assert "not found" in result.message
    
    @pytest.mark.asyncio
    async def test_list_directory_permission_error(self):
        """Test directory listing with permission error"""
        with patch("main.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.iterdir.side_effect = PermissionError("Permission denied")
            mock_path.__str__ = Mock(return_value="/protected")
            mock_path_class.return_value = mock_path
            
            result = await self.agent.list_directory("/protected")
            
            assert result.success is False
            assert "Failed to list directory" in result.message
            assert "Permission denied" in result.error
    
    @pytest.mark.asyncio
    async def test_plan_task_invalid_constraints(self):
        """Test task planning with invalid constraints"""
        self.agent.client.chat.completions.create = AsyncMock(
            side_effect=Exception("Invalid constraint format")
        )
        
        request = PlanningRequest(
            task="Test task",
            constraints=["invalid constraint format"]
        )
        result = await self.agent.plan_task(request)
        
        assert result.success is False
        assert "Failed to plan task" in result.message
        assert "Invalid constraint format" in result.error
    
    @pytest.mark.asyncio
    async def test_create_mock_invalid_data_type(self):
        """Test mock creation with invalid data type"""
        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()):
                with patch("json.dump", side_effect=TypeError("Object of type 'function' is not JSON serializable")):
                    result = await self.agent.create_mock("api_response", {
                        "status_code": 200,
                        "headers": {},
                        "body": {"func": lambda x: x}  # Non-serializable
                    })
                    
                    assert result.success is False
                    assert "Failed to create mock" in result.message
                    assert "not JSON serializable" in result.error

class TestSimulationScenarios:
    """Test simulation scenarios for various edge cases"""
    
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
    async def test_large_file_handling(self):
        """Test handling of large files"""
        large_content = "x" * (10 * 1024 * 1024)  # 10MB content
        
        with patch("pathlib.Path.parent") as mock_parent:
            mock_parent.mkdir = Mock()
            with patch("pathlib.Path.exists", return_value=False):
                with patch("builtins.open", mock_open()):
                    request = FileWriteRequest(file_path="large_file.txt", content=large_content)
                    result = await self.agent.write_file(request)
                    
                    assert result.success is True
                    assert "written successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self):
        """Test network timeout simulation"""
        # Simulate slow API response
        async def slow_api_call(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate network delay
            return self.mock_response
        
        self.agent.client.chat.completions.create = slow_api_call
        
        request = CodeAnalysisRequest(
            code="def test(): pass",
            language="python"
        )
        
        start_time = time.time()
        result = await self.agent.analyze_code(request)
        end_time = time.time()
        
        assert result.success is True
        assert (end_time - start_time) >= 0.1  # Should take at least 100ms
    
    @pytest.mark.asyncio
    async def test_memory_pressure_simulation(self):
        """Test handling under memory pressure"""
        # Simulate memory pressure by creating many large objects
        large_objects = []
        try:
            for i in range(1000):
                large_objects.append("x" * 1024)  # 1KB each
            
            request = CodeAnalysisRequest(
                code="def test(): pass",
                language="python"
            )
            result = await self.agent.analyze_code(request)
            
            assert result.success is True
        finally:
            del large_objects  # Clean up
    
    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self):
        """Test concurrent file operations"""
        async def write_file_task(file_num):
            with patch("pathlib.Path.parent") as mock_parent:
                mock_parent.mkdir = Mock()
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("builtins.open", mock_open()):
                        request = FileWriteRequest(
                            file_path=f"concurrent_file_{file_num}.txt",
                            content=f"Content {file_num}"
                        )
                        return await self.agent.write_file(request)
        
        # Run 10 concurrent file write operations
        tasks = [write_file_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_api_rate_limit_simulation(self):
        """Test API rate limit handling"""
        call_count = 0
        
        async def rate_limited_api(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Rate limit exceeded")
            return self.mock_response
        
        self.agent.client.chat.completions.create = rate_limited_api
        
        # First two calls should fail
        for i in range(2):
            request = CodeAnalysisRequest(
                code=f"def test{i}(): pass",
                language="python"
            )
            result = await self.agent.analyze_code(request)
            assert result.success is False
            assert "Rate limit exceeded" in result.error
        
        # Third call should succeed
        request = CodeAnalysisRequest(
            code="def test3(): pass",
            language="python"
        )
        result = await self.agent.analyze_code(request)
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_disk_space_simulation(self):
        """Test handling of disk space issues"""
        with patch("pathlib.Path.parent") as mock_parent:
            mock_parent.mkdir = Mock()
            with patch("pathlib.Path.exists", return_value=False):
                with patch("builtins.open", side_effect=OSError("No space left on device")):
                    request = FileWriteRequest(file_path="test.txt", content="test")
                    result = await self.agent.write_file(request)
                    
                    assert result.success is False
                    assert "No space left" in result.error
    
    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self):
        """Test handling of corrupted files"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")):
                request = FileReadRequest(file_path="corrupted.txt")
                result = await self.agent.read_file(request)
                
                assert result.success is False
                assert "Failed to read file" in result.message
    
    @pytest.mark.asyncio
    async def test_system_resource_exhaustion(self):
        """Test handling when system resources are exhausted"""
        # Simulate file descriptor exhaustion
        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=OSError("Too many open files")):
                request = FileReadRequest(file_path="test.txt")
                result = await self.agent.read_file(request)
                
                assert result.success is False
                assert "Too many open files" in result.error
    
    @pytest.mark.asyncio
    async def test_partial_network_failure(self):
        """Test partial network failure simulation"""
        failure_count = 0
        
        async def intermittent_api(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count % 3 == 0:  # Every third call fails
                raise Exception("Network connection lost")
            return self.mock_response
        
        self.agent.client.chat.completions.create = intermittent_api
        
        # Test multiple calls - some should fail, some succeed
        results = []
        for i in range(6):
            request = CodeAnalysisRequest(
                code=f"def test{i}(): pass",
                language="python"
            )
            result = await self.agent.analyze_code(request)
            results.append(result)
        
        # Should have mix of successes and failures
        successes = sum(1 for r in results if r.success)
        failures = sum(1 for r in results if not r.success)
        
        assert successes > 0
        assert failures > 0
        assert successes + failures == 6

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
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        async def make_request():
            request = CodeAnalysisRequest(
                code="def test(): pass",
                language="python"
            )
            return await self.agent.analyze_code(request)
        
        # Run 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_response_time_measurement(self):
        """Test response time measurement"""
        async def measure_response_time():
            start_time = time.time()
            request = CodeAnalysisRequest(
                code="def test(): pass",
                language="python"
            )
            result = await self.agent.analyze_code(request)
            end_time = time.time()
            
            return result, end_time - start_time
        
        result, response_time = await measure_response_time()
        
        assert result.success is True
        assert response_time >= 0  # Should be non-negative
        assert response_time < 1.0  # Should be reasonably fast (mocked)
    
    @pytest.mark.asyncio
    async def test_load_testing(self):
        """Test system under load"""
        async def load_test_task(task_id):
            request = CodeAnalysisRequest(
                code=f"def test{task_id}(): pass",
                language="python"
            )
            return await self.agent.analyze_code(request)
        
        # Run 20 concurrent tasks
        start_time = time.time()
        tasks = [load_test_task(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All should succeed
        for result in results:
            assert result.success is True
        
        # Should complete in reasonable time
        assert total_time < 5.0  # 20 tasks in under 5 seconds
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run many operations
        tasks = []
        for i in range(50):
            request = CodeAnalysisRequest(
                code=f"def test{i}(): pass",
                language="python"
            )
            tasks.append(self.agent.analyze_code(request))
        
        results = await asyncio.gather(*tasks)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # All should succeed
        for result in results:
            assert result.success is True
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024
    
    @pytest.mark.asyncio
    async def test_file_operations_performance(self):
        """Test file operations performance"""
        async def file_operation_task(file_num):
            with patch("pathlib.Path.parent") as mock_parent:
                mock_parent.mkdir = Mock()
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("builtins.open", mock_open()):
                        request = FileWriteRequest(
                            file_path=f"perf_test_{file_num}.txt",
                            content=f"Content {file_num}" * 1000  # 1KB content
                        )
                        return await self.agent.write_file(request)
        
        # Run 10 concurrent file operations
        start_time = time.time()
        tasks = [file_operation_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All should succeed
        for result in results:
            assert result.success is True
        
        # Should complete quickly
        assert total_time < 2.0
    
    @pytest.mark.asyncio
    async def test_api_call_performance(self):
        """Test API call performance"""
        # Simulate different response times
        response_times = [0.01, 0.05, 0.1, 0.2, 0.5]  # Different delays
        
        async def api_call_with_delay(delay):
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(delay)
                return self.mock_response
            
            self.agent.client.chat.completions.create = delayed_response
            
            request = CodeAnalysisRequest(
                code="def test(): pass",
                language="python"
            )
            
            start_time = time.time()
            result = await self.agent.analyze_code(request)
            end_time = time.time()
            
            return result, end_time - start_time
        
        # Test different response times
        for expected_delay in response_times:
            result, actual_delay = await api_call_with_delay(expected_delay)
            
            assert result.success is True
            assert actual_delay >= expected_delay
            assert actual_delay < expected_delay + 0.1  # Allow small margin
    
    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self):
        """Test concurrent mixed operations"""
        async def mixed_operation(operation_type, data):
            if operation_type == "analyze":
                request = CodeAnalysisRequest(
                    code=data,
                    language="python"
                )
                return await self.agent.analyze_code(request)
            elif operation_type == "generate":
                request = CodeGenerationRequest(
                    description=data,
                    language="python"
                )
                return await self.agent.generate_code(request)
            elif operation_type == "plan":
                request = PlanningRequest(
                    task=data,
                    constraints=[]
                )
                return await self.agent.plan_task(request)
        
        # Mix of different operations
        operations = [
            ("analyze", "def test1(): pass"),
            ("generate", "Create a calculator function"),
            ("plan", "Implement user authentication"),
            ("analyze", "def test2(): pass"),
            ("generate", "Create a data parser"),
            ("plan", "Design database schema"),
            ("analyze", "def test3(): pass"),
            ("generate", "Create a web scraper"),
            ("plan", "Implement caching system"),
            ("analyze", "def test4(): pass"),
        ]
        
        start_time = time.time()
        tasks = [mixed_operation(op_type, data) for op_type, data in operations]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # All should succeed
        for result in results:
            assert result.success is True
        
        # Should complete in reasonable time
        assert total_time < 3.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])