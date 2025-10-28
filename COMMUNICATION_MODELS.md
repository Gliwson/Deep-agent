# Modele Komunikacji - Deep Agent Backend

## 🏗️ Architektura Systemu

### Komponenty
1. **Deep Agent Backend** - serwer z narzędziami
2. **WebSocket Server** - komunikacja w czasie rzeczywistym
3. **Plugin** - klient wywołujący narzędzia
4. **OpenAI Integration** - analiza i generowanie kodu

### Diagram Architektury
```
┌─────────────────┐    WebSocket    ┌──────────────────┐
│     Plugin      │◄──────────────►│  Deep Agent      │
│                 │                 │  Backend         │
│ - UI Interface  │                 │                  │
│ - Tool Manager  │                 │ - File Operations│
│ - Error Handler │                 │ - Search/Replace │
└─────────────────┘                 │ - Terminal Ops   │
                                    │ - AI Operations  │
                                    │ - Planning       │
                                    │ - Mock Creation  │
                                    └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   OpenAI API     │
                                    │   (GPT-4)        │
                                    └──────────────────┘
```

## 📡 Protokół WebSocket

### Format Wiadomości

#### Żądanie (Request)
```json
{
  "action": "string",     // Nazwa akcji do wykonania
  "data": {               // Dane specyficzne dla akcji
    "param1": "value1",
    "param2": "value2"
  }
}
```

#### Odpowiedź (Response)
```json
{
  "success": boolean,     // Czy operacja się powiodła
  "message": "string",    // Opis wyniku
  "data": {               // Dane wynikowe (jeśli success=true)
    "result": "value"
  },
  "error": "string"       // Opis błędu (jeśli success=false)
}
```

### Typy Akcji

#### 1. Operacje na Plikach
- `read_file` - odczyt pliku
- `write_file` - zapis pliku
- `list_directory` - listowanie katalogu

#### 2. Wyszukiwanie i Zamiana
- `search_text` - wyszukiwanie tekstu
- `replace_text` - zamiana tekstu

#### 3. Wykonywanie Komend
- `execute_command` - wykonanie komendy terminalowej

#### 4. Operacje AI
- `analyze_code` - analiza kodu
- `generate_code` - generowanie kodu
- `generate_tests` - generowanie testów
- `refactor_code` - refaktoryzacja kodu

#### 5. Planowanie
- `plan_task` - planowanie zadania

#### 6. Mocki
- `create_mock` - tworzenie mocka

## 🔧 Modele Danych

### FileReadRequest
```json
{
  "file_path": "string",    // Ścieżka do pliku
  "encoding": "string"      // Kodowanie (domyślnie: utf-8)
}
```

### FileWriteRequest
```json
{
  "file_path": "string",    // Ścieżka do pliku
  "content": "string",      // Zawartość pliku
  "encoding": "string",     // Kodowanie (domyślnie: utf-8)
  "backup": boolean         // Czy utworzyć backup (domyślnie: true)
}
```

### SearchRequest
```json
{
  "pattern": "string",      // Wzorzec wyszukiwania
  "file_path": "string",    // Ścieżka do pliku (opcjonalne)
  "directory": "string",    // Katalog do przeszukania (opcjonalne)
  "case_sensitive": boolean, // Czy rozróżniać wielkość liter
  "regex": boolean          // Czy używać regex
}
```

### ReplaceRequest
```json
{
  "file_path": "string",    // Ścieżka do pliku
  "old_text": "string",     // Tekst do zamiany
  "new_text": "string",     // Nowy tekst
  "count": integer,         // Liczba zamian (-1 = wszystkie)
  "backup": boolean         // Czy utworzyć backup
}
```

### TerminalRequest
```json
{
  "command": "string",      // Komenda do wykonania
  "working_directory": "string", // Katalog roboczy (opcjonalne)
  "timeout": integer        // Timeout w sekundach (domyślnie: 30)
}
```

### CodeAnalysisRequest
```json
{
  "code": "string",         // Kod do analizy
  "language": "string",     // Język programowania
  "context": "string"       // Kontekst (opcjonalne)
}
```

### CodeGenerationRequest
```json
{
  "description": "string",  // Opis kodu do wygenerowania
  "language": "string",     // Język programowania
  "context": "string",      // Kontekst (opcjonalne)
  "existing_code": "string" // Istniejący kod (opcjonalne)
}
```

### TestGenerationRequest
```json
{
  "code": "string",         // Kod do przetestowania
  "language": "string",     // Język programowania
  "test_framework": "string" // Framework testowy (opcjonalne)
}
```

### RefactoringRequest
```json
{
  "code": "string",         // Kod do refaktoryzacji
  "language": "string",     // Język programowania
  "refactoring_type": "string" // Typ refaktoryzacji
}
```

### PlanningRequest
```json
{
  "task": "string",         // Zadanie do zaplanowania
  "context": "string",      // Kontekst (opcjonalne)
  "constraints": ["string"] // Ograniczenia (opcjonalne)
}
```

### MockRequest
```json
{
  "mock_type": "string",    // Typ mocka (api_response, database, file_system)
  "mock_data": {            // Dane mocka
    "key": "value"
  }
}
```

## 🔄 Przepływ Komunikacji

### 1. Inicjalizacja
```
Plugin → WebSocket Connect → Backend
Backend → Connection Accepted → Plugin
```

### 2. Wykonanie Narzędzia
```
Plugin → Request Message → Backend
Backend → Process Tool → Backend
Backend → Response Message → Plugin
```

### 3. Obsługa Błędów
```
Plugin → Request Message → Backend
Backend → Error Occurred → Backend
Backend → Error Response → Plugin
```

### 4. Zamknięcie Połączenia
```
Plugin → WebSocket Close → Backend
Backend → Connection Closed → Plugin
```

## 🚨 Kody Błędów

### Błędy Połączenia
- `CONNECTION_FAILED` - Nie można połączyć z serwerem
- `CONNECTION_LOST` - Utracono połączenie
- `TIMEOUT` - Przekroczono timeout

### Błędy Walidacji
- `INVALID_JSON` - Nieprawidłowy format JSON
- `MISSING_ACTION` - Brak akcji w wiadomości
- `INVALID_ACTION` - Nieznana akcja
- `MISSING_DATA` - Brak wymaganych danych

### Błędy Operacji
- `FILE_NOT_FOUND` - Plik nie istnieje
- `PERMISSION_DENIED` - Brak uprawnień
- `COMMAND_FAILED` - Komenda się nie powiodła
- `AI_API_ERROR` - Błąd API OpenAI

## 🔐 Bezpieczeństwo

### Walidacja Wejścia
- Wszystkie dane są walidowane przez Pydantic
- Sprawdzanie ścieżek plików
- Walidacja komend terminalowych

### Timeouty
- Domyślny timeout: 30 sekund
- Konfigurowalny per operacja
- Automatyczne przerywanie długich operacji

### Backup
- Automatyczne tworzenie kopii zapasowych
- Możliwość wyłączenia dla operacji masowych
- Przechowywanie w katalogu tymczasowym

## 📊 Monitoring i Logi

### Poziomy Logowania
- `INFO` - Informacje o operacjach
- `WARNING` - Ostrzeżenia
- `ERROR` - Błędy operacji
- `DEBUG` - Szczegółowe informacje debugowania

### Metryki
- Liczba aktywnych połączeń
- Czas wykonywania operacji
- Liczba błędów
- Wykorzystanie zasobów

## 🔧 Konfiguracja

### Zmienne Środowiskowe
```bash
OPENAI_API_KEY=sk-...          # Klucz API OpenAI
WORKSPACE_ROOT=/workspace      # Katalog roboczy
LOG_LEVEL=INFO                 # Poziom logowania
MAX_CONNECTIONS=100            # Maksymalna liczba połączeń
DEFAULT_TIMEOUT=30             # Domyślny timeout
```

### Ustawienia Serwera
```python
HOST = "0.0.0.0"              # Adres serwera
PORT = 8000                    # Port serwera
WORKSPACE = "/workspace"       # Katalog roboczy
TEMP_DIR = "/tmp/deep_agent"   # Katalog tymczasowy
```

## 🚀 Optymalizacja

### Równoległe Operacje
- Asynchroniczne przetwarzanie
- Obsługa wielu połączeń
- Kolejkowanie żądań

### Caching
- Cache wyników wyszukiwania
- Cache analizy kodu
- Cache planów zadań

### Limity Zasobów
- Maksymalna wielkość pliku: 100MB
- Maksymalny czas komendy: 300s
- Maksymalna liczba połączeń: 100

## 📈 Skalowanie

### Poziome Skalowanie
- Wiele instancji serwera
- Load balancer
- Rozdzielenie obciążenia

### Pionowe Skalowanie
- Zwiększenie pamięci
- Więcej CPU
- Szybsze dyski

### Monitoring
- Health checks
- Metryki wydajności
- Alerty błędów

## 🔄 Wersjonowanie

### Wersja API
- Obecna: 2.0.0
- Format: MAJOR.MINOR.PATCH
- Kompatybilność wsteczna

### Migracje
- Automatyczne migracje
- Dokumentacja zmian
- Narzędzia migracyjne

## 📚 Przykłady Implementacji

### JavaScript/TypeScript
```typescript
interface DeepAgentClient {
  connect(): Promise<void>;
  disconnect(): void;
  sendRequest<T>(action: string, data: any): Promise<T>;
}
```

### Python
```python
class DeepAgentClient:
    async def connect(self) -> None:
        pass
    
    async def disconnect(self) -> None:
        pass
    
    async def send_request(self, action: str, data: dict) -> dict:
        pass
```

### Go
```go
type DeepAgentClient struct {
    conn *websocket.Conn
}

func (c *DeepAgentClient) Connect() error {
    // Implementation
}

func (c *DeepAgentClient) SendRequest(action string, data map[string]interface{}) (map[string]interface{}, error) {
    // Implementation
}
```

## 🎯 Najlepsze Praktyki

1. **Zawsze sprawdzaj status odpowiedzi**
2. **Używaj timeoutów**
3. **Obsługuj błędy gracefully**
4. **Zamykaj połączenia**
5. **Używaj backupów**
6. **Monitoruj wydajność**
7. **Testuj połączenie**
8. **Używaj logowania**
9. **Implementuj retry logic**
10. **Cache'uj wyniki**

## 🔮 Przyszłe Rozszerzenia

### Planowane Funkcje
- Obsługa więcej języków programowania
- Integracja z innymi AI modelami
- Rozszerzone API
- Więcej typów mocków
- Automatyczne testowanie
- CI/CD integracja

### Roadmap
- Q1 2024: Więcej języków
- Q2 2024: AI modele
- Q3 2024: Rozszerzone API
- Q4 2024: Automatyzacja