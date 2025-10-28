# Instrukcje dla Pluginu - Komunikacja z Deep Agent Backend

## 🚀 Przegląd Systemu

Deep Agent Backend to zaawansowany system narzędzi dostępny przez WebSocket, który eliminuje wszystkie symulacje i moki. Plugin może wywoływać rzeczywiste narzędzia do:

- **Operacji na plikach** (odczyt, zapis, listowanie)
- **Wyszukiwania i zamiany tekstu** (z obsługą regex)
- **Wykonywania komend terminalowych**
- **Analizy i generowania kodu** (z AI)
- **Planowania zadań**
- **Tworzenia mocków i symulacji**

## 📡 Protokół Komunikacji WebSocket

### Połączenie
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Format Wiadomości
Wszystkie wiadomości muszą być w formacie JSON:
```json
{
  "action": "nazwa_akcji",
  "data": {
    // parametry specyficzne dla akcji
  }
}
```

### Format Odpowiedzi
```json
{
  "success": true/false,
  "message": "Opis wyniku",
  "data": {
    // dane wynikowe
  },
  "error": "Opis błędu (jeśli success=false)"
}
```

## 🛠️ Dostępne Narzędzia

### 1. Operacje na Plikach

#### Odczytywanie Pliku
```json
{
  "action": "read_file",
  "data": {
    "file_path": "/ścieżka/do/pliku.py",
    "encoding": "utf-8"
  }
}
```

#### Zapisywanie Pliku
```json
{
  "action": "write_file",
  "data": {
    "file_path": "/ścieżka/do/pliku.py",
    "content": "zawartość pliku",
    "encoding": "utf-8",
    "backup": true
  }
}
```

#### Listowanie Katalogu
```json
{
  "action": "list_directory",
  "data": {
    "directory": "/ścieżka/do/katalogu"
  }
}
```

### 2. Wyszukiwanie i Zamiana

#### Wyszukiwanie Tekstu
```json
{
  "action": "search_text",
  "data": {
    "pattern": "wzorzec_wyszukiwania",
    "file_path": "/ścieżka/do/pliku.py",
    "directory": "/ścieżka/do/katalogu",
    "case_sensitive": false,
    "regex": false
  }
}
```

#### Zamiana Tekstu
```json
{
  "action": "replace_text",
  "data": {
    "file_path": "/ścieżka/do/pliku.py",
    "old_text": "stary_tekst",
    "new_text": "nowy_tekst",
    "count": -1,
    "backup": true
  }
}
```

### 3. Wykonywanie Komend

#### Wykonanie Komendy Terminalowej
```json
{
  "action": "execute_command",
  "data": {
    "command": "ls -la",
    "working_directory": "/workspace",
    "timeout": 30
  }
}
```

### 4. Analiza i Generowanie Kodu (Wymaga OpenAI API Key)

#### Analiza Kodu
```json
{
  "action": "analyze_code",
  "data": {
    "code": "def hello(): return 'world'",
    "language": "python",
    "context": "Prosta funkcja"
  }
}
```

#### Generowanie Kodu
```json
{
  "action": "generate_code",
  "data": {
    "description": "Stwórz funkcję obliczającą silnię",
    "language": "python",
    "context": "Funkcja matematyczna",
    "existing_code": "istniejący_kod"
  }
}
```

#### Generowanie Testów
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

#### Refaktoryzacja Kodu
```json
{
  "action": "refactor_code",
  "data": {
    "code": "def add(a, b): return a + b",
    "language": "python",
    "refactoring_type": "optimize"
  }
}
```

### 5. Planowanie Zadań

#### Planowanie Zadania
```json
{
  "action": "plan_task",
  "data": {
    "task": "Stwórz aplikację webową z autentykacją",
    "context": "Python FastAPI + React",
    "constraints": ["Musi używać PostgreSQL", "Musi mieć JWT"]
  }
}
```

### 6. Tworzenie Mocków

#### Tworzenie Mocka
```json
{
  "action": "create_mock",
  "data": {
    "mock_type": "api_response",
    "mock_data": {
      "status_code": 200,
      "headers": {"Content-Type": "application/json"},
      "body": {"message": "Success"}
    }
  }
}
```

## 🔧 Implementacja w Pluginie

### Przykład Implementacji JavaScript

```javascript
class DeepAgentPlugin {
    constructor(wsUrl = 'ws://localhost:8000/ws') {
        this.wsUrl = wsUrl;
        this.ws = null;
        this.messageId = 0;
        this.pendingRequests = new Map();
    }

    async connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                console.log('Połączono z Deep Agent Backend');
                resolve();
            };
            
            this.ws.onmessage = (event) => {
                const response = JSON.parse(event.data);
                this.handleResponse(response);
            };
            
            this.ws.onerror = (error) => {
                console.error('Błąd WebSocket:', error);
                reject(error);
            };
            
            this.ws.onclose = () => {
                console.log('Rozłączono z Deep Agent Backend');
            };
        });
    }

    async sendRequest(action, data) {
        return new Promise((resolve, reject) => {
            const message = {
                action: action,
                data: data
            };
            
            const messageId = ++this.messageId;
            this.pendingRequests.set(messageId, { resolve, reject });
            
            this.ws.send(JSON.stringify(message));
            
            // Timeout po 30 sekundach
            setTimeout(() => {
                if (this.pendingRequests.has(messageId)) {
                    this.pendingRequests.delete(messageId);
                    reject(new Error('Timeout'));
                }
            }, 30000);
        });
    }

    handleResponse(response) {
        // W tym prostym przykładzie zakładamy, że odpowiedzi przychodzą w kolejności
        // W rzeczywistej implementacji powinieneś używać ID wiadomości
        const pendingRequest = this.pendingRequests.values().next().value;
        if (pendingRequest) {
            this.pendingRequests.delete(this.pendingRequests.keys().next().value);
            pendingRequest.resolve(response);
        }
    }

    // Metody narzędzi
    async readFile(filePath, encoding = 'utf-8') {
        return await this.sendRequest('read_file', {
            file_path: filePath,
            encoding: encoding
        });
    }

    async writeFile(filePath, content, encoding = 'utf-8', backup = true) {
        return await this.sendRequest('write_file', {
            file_path: filePath,
            content: content,
            encoding: encoding,
            backup: backup
        });
    }

    async listDirectory(directory = null) {
        return await this.sendRequest('list_directory', {
            directory: directory
        });
    }

    async searchText(pattern, options = {}) {
        return await this.sendRequest('search_text', {
            pattern: pattern,
            file_path: options.filePath,
            directory: options.directory,
            case_sensitive: options.caseSensitive || false,
            regex: options.regex || false
        });
    }

    async replaceText(filePath, oldText, newText, options = {}) {
        return await this.sendRequest('replace_text', {
            file_path: filePath,
            old_text: oldText,
            new_text: newText,
            count: options.count || -1,
            backup: options.backup !== false
        });
    }

    async executeCommand(command, options = {}) {
        return await this.sendRequest('execute_command', {
            command: command,
            working_directory: options.workingDirectory,
            timeout: options.timeout || 30
        });
    }

    async analyzeCode(code, language, context = null) {
        return await this.sendRequest('analyze_code', {
            code: code,
            language: language,
            context: context
        });
    }

    async generateCode(description, language, context = null, existingCode = null) {
        return await this.sendRequest('generate_code', {
            description: description,
            language: language,
            context: context,
            existing_code: existingCode
        });
    }

    async generateTests(code, language, testFramework = null) {
        return await this.sendRequest('generate_tests', {
            code: code,
            language: language,
            test_framework: testFramework
        });
    }

    async refactorCode(code, language, refactoringType) {
        return await this.sendRequest('refactor_code', {
            code: code,
            language: language,
            refactoring_type: refactoringType
        });
    }

    async planTask(task, context = null, constraints = []) {
        return await this.sendRequest('plan_task', {
            task: task,
            context: context,
            constraints: constraints
        });
    }

    async createMock(mockType, mockData) {
        return await this.sendRequest('create_mock', {
            mock_type: mockType,
            mock_data: mockData
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Przykład użycia
async function example() {
    const plugin = new DeepAgentPlugin();
    
    try {
        await plugin.connect();
        
        // Odczytywanie pliku
        const fileContent = await plugin.readFile('/workspace/main.py');
        console.log('Zawartość pliku:', fileContent.data.content);
        
        // Wyszukiwanie tekstu
        const searchResults = await plugin.searchText('def ', {
            directory: '/workspace',
            regex: true
        });
        console.log('Wyniki wyszukiwania:', searchResults.data.results);
        
        // Wykonanie komendy
        const commandResult = await plugin.executeCommand('ls -la');
        console.log('Wynik komendy:', commandResult.data.stdout);
        
    } catch (error) {
        console.error('Błąd:', error);
    } finally {
        plugin.disconnect();
    }
}
```

## 🔑 Konfiguracja

### Wymagane Zmienne Środowiskowe
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Ustawienia Serwera
- **Port**: 8000 (domyślnie)
- **Host**: 0.0.0.0
- **Workspace**: /workspace (domyślnie)

## 🚨 Obsługa Błędów

### Typowe Błędy
1. **Brak połączenia WebSocket** - sprawdź czy serwer działa
2. **Nieprawidłowy format JSON** - sprawdź składnię wiadomości
3. **Nieznana akcja** - sprawdź nazwę akcji
4. **Błąd OpenAI API** - sprawdź klucz API
5. **Timeout** - zwiększ timeout dla długich operacji

### Przykład Obsługi Błędów
```javascript
try {
    const result = await plugin.readFile('/nieistniejący/plik.py');
    if (result.success) {
        console.log('Sukces:', result.data);
    } else {
        console.error('Błąd:', result.error);
    }
} catch (error) {
    console.error('Błąd połączenia:', error);
}
```

## 📊 Przykłady Użycia

### 1. Analiza Projektu
```javascript
// Pobierz listę plików
const files = await plugin.listDirectory('/workspace');

// Przeanalizuj każdy plik Python
for (const file of files.data.items) {
    if (file.name.endsWith('.py')) {
        const content = await plugin.readFile(file.path);
        const analysis = await plugin.analyzeCode(content.data.content, 'python');
        console.log(`Analiza ${file.name}:`, analysis.data.analysis);
    }
}
```

### 2. Refaktoryzacja Kodu
```javascript
// Znajdź wszystkie funkcje
const functions = await plugin.searchText('def ', { regex: true });

// Refaktoryzuj każdą funkcję
for (const result of functions.data.results) {
    for (const match of result.matches) {
        const content = await plugin.readFile(result.file_path);
        const refactored = await plugin.refactorCode(content.data.content, 'python', 'optimize');
        await plugin.writeFile(result.file_path, refactored.data.refactored_code);
    }
}
```

### 3. Automatyczne Testowanie
```javascript
// Wygeneruj testy dla wszystkich funkcji
const functions = await plugin.searchText('def ', { regex: true });

for (const result of functions.data.results) {
    const content = await plugin.readFile(result.file_path);
    const tests = await plugin.generateTests(content.data.content, 'python', 'pytest');
    
    const testFileName = result.file_path.replace('.py', '_test.py');
    await plugin.writeFile(testFileName, tests.data.test_code);
}
```

## 🎯 Najlepsze Praktyki

1. **Zawsze sprawdzaj `success`** w odpowiedzi
2. **Używaj timeoutów** dla długich operacji
3. **Obsługuj błędy** gracefully
4. **Zamykaj połączenia** po zakończeniu
5. **Używaj backupów** przy modyfikacji plików
6. **Testuj połączenie** przed rozpoczęciem pracy

## 🔄 Status Systemu

System jest w pełni funkcjonalny i gotowy do użycia:
- ✅ WebSocket komunikacja
- ✅ Operacje na plikach
- ✅ Wyszukiwanie i zamiana
- ✅ Wykonywanie komend
- ✅ Tworzenie mocków
- ✅ Planowanie zadań
- ⚠️ Operacje AI (wymagają klucza OpenAI)

**Wszystkie symulacje i moki zostały wyeliminowane - system używa prawdziwych narzędzi!**