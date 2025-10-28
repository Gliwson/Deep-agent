# LangGraph Agent Backend

Agent zbudowany w Pythonie z LangGraph, który oferuje funkcje planowania i wykonywania zadań.

## 🚀 Funkcjonalności

### Główne komponenty:
- **LangGraph Agent** - główny agent z funkcjami planowania i wykonywania
- **FastAPI Backend** - REST API dla komunikacji z agentem
- **WebSocket** - komunikacja w czasie rzeczywistym
- **Narzędzia** - zestaw narzędzi do operacji na plikach, terminalu, wyszukiwania

### Workflow agenta:
1. **Planowanie** - agent analizuje zadanie i tworzy szczegółowy plan
2. **Wykonywanie** - agent wykonuje kroki planu używając dostępnych narzędzi
3. **Przegląd** - agent ocenia wyniki i decyduje o następnych krokach
4. **Zakończenie** - agent kończy gdy zadanie jest ukończone

## 🛠️ Narzędzia dostępne dla agenta

- `read_file_tool` - czytanie plików
- `write_file_tool` - zapisywanie plików
- `search_text_tool` - wyszukiwanie tekstu w plikach
- `execute_command_tool` - wykonywanie komend terminala
- `list_directory_tool` - listowanie zawartości katalogów

## 📡 API Endpoints

### REST API:
- `GET /` - informacje o serwerze
- `GET /health` - sprawdzenie stanu serwera
- `POST /agent/execute` - wykonanie zadania przez agenta
- `POST /agent/analyze-code` - analiza kodu
- `POST /agent/generate-code` - generowanie kodu

### WebSocket:
- `WS /ws` - komunikacja w czasie rzeczywistym

## 🚀 Uruchomienie

1. **Zainstaluj zależności:**
```bash
pip3 install -r requirements.txt
```

2. **Skonfiguruj zmienne środowiskowe:**
```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

3. **Uruchom serwer:**
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

4. **Przetestuj agenta:**
```bash
python3 test_agent_structure.py  # Test struktury
python3 test_api.py              # Test API
python3 test_websocket_client.py # Test WebSocket
```

## 📝 Przykład użycia

### Przez API:
```python
import requests

# Wykonaj zadanie
response = requests.post("http://localhost:8000/agent/execute", json={
    "task": "Stwórz prosty skrypt Python",
    "context": {"workspace": "/workspace"},
    "constraints": ["Użyj Python 3", "Zachowaj prostotę"]
})

result = response.json()
print(f"Status: {result['success']}")
print(f"Wynik: {result['data']}")
```

### Przez WebSocket:
```python
import asyncio
import websockets
import json

async def send_task():
    async with websockets.connect("ws://localhost:8000/ws") as websocket:
        await websocket.send(json.dumps({
            "type": "task",
            "task": "Lista plików w katalogu",
            "context": {"directory": "/workspace"}
        }))
        
        response = await websocket.recv()
        result = json.loads(response)
        print(f"Wynik: {result['data']}")

asyncio.run(send_task())
```

## 🧪 Testy

- `test_agent_structure.py` - test struktury agenta
- `test_api.py` - test endpointów API
- `test_websocket_client.py` - test WebSocket
- `test_langgraph_agent.py` - pełny test agenta (wymaga prawdziwego klucza API)

## 📊 Status

✅ **Zakończone:**
- Instalacja zależności (LangGraph, FastAPI, OpenAI)
- Implementacja agenta LangGraph z funkcjami planowania i wykonywania
- REST API endpoints
- WebSocket komunikacja
- Narzędzia do operacji na plikach i terminalu
- Testy struktury i API

🚀 **Agent jest gotowy do użycia!**

## 🔧 Konfiguracja

Aby agent działał w pełni, potrzebujesz:
1. Prawdziwego klucza OpenAI API w pliku `.env`
2. Dostępu do internetu dla wywołań API
3. Uprawnień do operacji na plikach w workspace

## 📈 Rozszerzenia

Agent jest zaprojektowany modularnie, więc można łatwo:
- Dodać nowe narzędzia
- Rozszerzyć funkcje planowania
- Dodać nowe typy zadań
- Zintegrować z innymi systemami
