# Deep Agent - AI Coding Assistant Backend

Deep Agent to zaawansowany backend agenta kodującego, który komunikuje się przez WebSocket z pluginami IDE (jak IntelliJ). Agent wykorzystuje LangChain i OpenAI do analizy kodu, generowania, pisania testów i refaktoryzacji.

## Funkcjonalności

- 🔍 **Analiza kodu** - Ocena jakości, wykrywanie błędów, sugestie optymalizacji
- ⚡ **Generowanie kodu** - Tworzenie kodu na podstawie opisu
- 🧪 **Generowanie testów** - Automatyczne tworzenie testów jednostkowych
- 🔧 **Refaktoryzacja** - Ulepszanie i optymalizacja istniejącego kodu
- 🌐 **WebSocket API** - Komunikacja w czasie rzeczywistym z IDE
- 🐍 **Wielojęzyczność** - Obsługa Python, JavaScript, TypeScript, Java, C# i innych

## Instalacja

1. **Sklonuj repozytorium:**
```bash
git clone <repository-url>
cd deep-agent
```

2. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

3. **Skonfiguruj zmienne środowiskowe:**
```bash
cp .env.example .env
# Edytuj .env i dodaj swój klucz OpenAI API
```

4. **Uruchom serwer:**
```bash
python main.py
```

Serwer będzie dostępny na `http://localhost:8000` z WebSocket na `ws://localhost:8000/ws`

## Konfiguracja

### Zmienne środowiskowe (.env)

```env
OPENAI_API_KEY=your_openai_api_key_here
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Wymagania systemowe

- Python 3.8+
- OpenAI API key
- Połączenie internetowe

## API WebSocket

### Format wiadomości

```json
{
  "action": "analyze_code|generate_code|generate_tests|refactor_code",
  "data": {
    // Dane specyficzne dla akcji
  }
}
```

### Dostępne akcje

#### 1. Analiza kodu (`analyze_code`)

```json
{
  "action": "analyze_code",
  "data": {
    "code": "def hello(): return 'world'",
    "language": "python",
    "context": "Opcjonalny kontekst"
  }
}
```

#### 2. Generowanie kodu (`generate_code`)

```json
{
  "action": "generate_code",
  "data": {
    "description": "Funkcja obliczająca silnię",
    "language": "python",
    "context": "Opcjonalny kontekst",
    "existing_code": "Opcjonalny istniejący kod"
  }
}
```

#### 3. Generowanie testów (`generate_tests`)

```json
{
  "action": "generate_tests",
  "data": {
    "code": "def add(a, b): return a + b",
    "language": "python",
    "test_framework": "pytest"
  }
}
```

#### 4. Refaktoryzacja (`refactor_code`)

```json
{
  "action": "refactor_code",
  "data": {
    "code": "def old_function(): ...",
    "language": "python",
    "refactoring_type": "optimize|clean|restructure"
  }
}
```

### Format odpowiedzi

```json
{
  "success": true,
  "message": "Opis operacji",
  "data": {
    // Dane wynikowe
  },
  "error": null
}
```

## Testowanie

### Uruchomienie testów

```bash
# Wszystkie testy
python run_tests.py

# Tylko testy jednostkowe
pytest test_agent.py -v

# Test WebSocket (wymaga uruchomionego serwera)
python test_websocket_client.py
```

### Tryb interaktywny

```bash
python test_websocket_client.py interactive
```

## Integracja z IntelliJ

Agent jest zaprojektowany do pracy z pluginem IntelliJ. Plugin powinien:

1. Łączyć się z WebSocket na `ws://localhost:8000/ws`
2. Wysyłać żądania w formacie JSON
3. Obsługiwać odpowiedzi asynchronicznie

### Przykład integracji (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    // Wysyłanie żądania analizy kodu
    ws.send(JSON.stringify({
        action: 'analyze_code',
        data: {
            code: 'function test() { return 42; }',
            language: 'javascript'
        }
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('Odpowiedź:', response);
};
```

## Architektura

```
┌─────────────────┐    WebSocket    ┌──────────────────┐
│   IntelliJ      │◄──────────────►│   Deep Agent     │
│   Plugin        │                 │   Backend        │
└─────────────────┘                 └──────────────────┘
                                            │
                                            ▼
                                    ┌──────────────────┐
                                    │   LangChain +    │
                                    │   OpenAI API     │
                                    └──────────────────┘
```

## Rozwój

### Struktura projektu

```
deep-agent/
├── main.py                 # Główny serwer FastAPI + WebSocket
├── test_agent.py          # Testy jednostkowe
├── test_websocket_client.py # Klient testowy WebSocket
├── run_tests.py           # Skrypt uruchamiający testy
├── requirements.txt       # Zależności Python
├── .env.example          # Przykład konfiguracji
└── README.md             # Dokumentacja
```

### Dodawanie nowych funkcji

1. Dodaj nową metodę do klasy `DeepAgent`
2. Zaktualizuj `handle_websocket_message`
3. Dodaj testy w `test_agent.py`
4. Zaktualizuj dokumentację

## Licencja

MIT License

## Wsparcie

W przypadku problemów lub pytań, utwórz issue w repozytorium.
