# Deep Agent Backend - Kompleksowe Narzędzie do Analizy Kodu

Zaawansowane narzędzie do analizy kodu z funkcjami podobnymi do Cursor/Kite, ale w pełni funkcjonalne w Pythonie z obsługą WebSocket i REST API.

## 🚀 Funkcje

### 📁 Operacje na Plikach
- **Odczytywanie plików** - pełna obsługa różnych kodowań
- **Zapisywanie plików** - z automatycznym tworzeniem katalogów i backupów
- **Listowanie katalogów** - szczegółowe informacje o plikach i folderach

### 🔍 Wyszukiwanie i Zamiana
- **Wyszukiwanie tekstu** - z obsługą regex i wyszukiwania case-sensitive
- **Zamiana tekstu** - z kontrolą liczby zamian i backupami
- **Wyszukiwanie w katalogach** - rekurencyjne przeszukiwanie

### 💻 Wykonywanie Komend
- **Terminal** - wykonywanie komend systemowych z timeout
- **Obsługa błędów** - szczegółowe logi i komunikaty

### 🤖 Analiza i Generowanie Kodu
- **Analiza kodu** - jakość, błędy, wydajność, bezpieczeństwo
- **Generowanie kodu** - na podstawie opisu z kontekstem
- **Generowanie testów** - kompletne testy jednostkowe
- **Refaktoryzacja** - optymalizacja i poprawa kodu

### 🧠 Planowanie i Myślenie
- **Planowanie zadań** - szczegółowe plany z zależnościami
- **Analiza ryzyka** - ocena i alternatywne podejścia

### 🎭 Mocki i Symulacje
- **Tworzenie mocków** - API, bazy danych, system plików
- **Symulacje** - testowanie bez rzeczywistych zależności

## 🛠️ Instalacja

```bash
# Klonowanie repozytorium
git clone <repository-url>
cd deep-agent-backend

# Instalacja zależności
pip install -r requirements.txt

# Konfiguracja środowiska
cp .env.example .env
# Edytuj .env i dodaj swój klucz OpenAI API
```

## 🚀 Uruchomienie

### Serwer Backend
```bash
python main.py
```

### Testy
```bash
# Wszystkie testy
python -m pytest test_agent.py -v

# Konkretne testy
python -m pytest test_agent.py::TestDeepAgent::test_analyze_code_success -v
```

### Klient WebSocket
```bash
# Tryb automatyczny
python test_websocket_client.py

# Tryb interaktywny
python test_websocket_client.py interactive
```

## 📡 API

### REST Endpoints

#### Analiza Kodu
```http
POST /api/analyze
Content-Type: application/json

{
  "code": "def hello(): return 'world'",
  "language": "python",
  "context": "Simple function"
}
```

#### Generowanie Kodu
```http
POST /api/generate
Content-Type: application/json

{
  "description": "Create a function that calculates factorial",
  "language": "python",
  "context": "Mathematical function"
}
```

#### Operacje na Plikach
```http
POST /api/read-file
Content-Type: application/json

{
  "file_path": "/path/to/file.py",
  "encoding": "utf-8"
}
```

#### Wyszukiwanie
```http
POST /api/search
Content-Type: application/json

{
  "pattern": "function_name",
  "directory": "/path/to/search",
  "case_sensitive": false,
  "regex": false
}
```

#### Wykonywanie Komend
```http
POST /api/execute
Content-Type: application/json

{
  "command": "ls -la",
  "working_directory": "/workspace",
  "timeout": 30
}
```

### WebSocket API

#### Połączenie
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

#### Format Wiadomości
```json
{
  "action": "analyze_code",
  "data": {
    "code": "def hello(): return 'world'",
    "language": "python",
    "context": "Simple function"
  }
}
```

#### Dostępne Akcje
- `analyze_code` - analiza kodu
- `generate_code` - generowanie kodu
- `generate_tests` - generowanie testów
- `refactor_code` - refaktoryzacja
- `read_file` - odczyt pliku
- `write_file` - zapis pliku
- `list_directory` - listowanie katalogu
- `search_text` - wyszukiwanie tekstu
- `replace_text` - zamiana tekstu
- `execute_command` - wykonywanie komend
- `plan_task` - planowanie zadań
- `create_mock` - tworzenie mocków

## 🔧 Konfiguracja

### Zmienne Środowiskowe
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Ustawienia Aplikacji
- **Port**: 8000 (domyślnie)
- **Host**: 0.0.0.0
- **Workspace**: /workspace (domyślnie)

## 📊 Przykłady Użycia

### Analiza Kodu
```python
import requests

response = requests.post('http://localhost:8000/api/analyze', json={
    "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """,
    "language": "python",
    "context": "Recursive Fibonacci implementation"
})

print(response.json())
```

### Wyszukiwanie w Kodzie
```python
response = requests.post('http://localhost:8000/api/search', json={
    "pattern": "def.*fibonacci",
    "directory": "/workspace",
    "regex": True
})

print(response.json())
```

### Wykonywanie Komend
```python
response = requests.post('http://localhost:8000/api/execute', json={
    "command": "python --version",
    "timeout": 10
})

print(response.json())
```

## 🧪 Testowanie

### Testy Jednostkowe
```bash
python -m pytest test_agent.py -v
```

### Testy Integracyjne
```bash
python test_websocket_client.py
```

### Testy Wydajnościowe
```bash
python -m pytest test_agent.py::TestPerformance -v
```

## 🏗️ Architektura

### Komponenty
- **DeepAgent** - główna klasa z logiką biznesową
- **ConnectionManager** - zarządzanie połączeniami WebSocket
- **FastAPI** - framework REST API
- **OpenAI** - integracja z modelem AI

### Struktura Plików
```
├── main.py                 # Główna aplikacja
├── test_agent.py          # Testy jednostkowe
├── test_websocket_client.py # Klient testowy
├── requirements.txt       # Zależności
├── .env.example          # Przykład konfiguracji
└── README.md             # Dokumentacja
```

## 🔒 Bezpieczeństwo

- **Walidacja wejścia** - wszystkie dane są walidowane
- **Timeout komend** - ochrona przed zawieszeniem
- **Backup plików** - automatyczne kopie zapasowe
- **Izolacja procesów** - bezpieczne wykonywanie komend

## 🚀 Rozwój

### Dodawanie Nowych Funkcji
1. Dodaj nową metodę do klasy `DeepAgent`
2. Dodaj endpoint REST API
3. Dodaj obsługę WebSocket
4. Napisz testy jednostkowe
5. Zaktualizuj dokumentację

### Wsparcie Języków
Aplikacja obsługuje:
- Python
- JavaScript/TypeScript
- Java
- C#
- Go
- Rust
- PHP
- Ruby

## 📈 Wydajność

- **Asynchroniczność** - obsługa wielu żądań jednocześnie
- **Caching** - optymalizacja powtarzających się operacji
- **Timeout** - kontrola czasu wykonywania
- **Monitoring** - szczegółowe logi

## 🤝 Wsparcie

### Zgłaszanie Problemów
1. Sprawdź logi aplikacji
2. Uruchom testy
3. Sprawdź konfigurację
4. Utwórz issue z szczegółami

### Funkcje na Żądanie
- Dodatkowe języki programowania
- Nowe typy analizy kodu
- Integracje z zewnętrznymi narzędziami
- Rozszerzone API

## 📄 Licencja

MIT License - zobacz plik LICENSE dla szczegółów.

## 🙏 Podziękowania

- OpenAI za API GPT-4
- FastAPI za framework webowy
- Pydantic za walidację danych
- Wszystkim kontrybutorom

---

**Deep Agent Backend** - Twój inteligentny asystent do analizy i generowania kodu! 🚀
