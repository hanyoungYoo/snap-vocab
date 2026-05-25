# Development Environment Setup

## Prerequisites
- Python 3.13+
- PostgreSQL 14+
- Git
- UV package manager (optional but recommended)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/hanyoungYoo/snap-vocab.git
cd snap-vocab
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

#### Using UV (Recommended)
```bash
uv sync
```

#### Using Pip
```bash
pip install -e ".[dev]"
```

### 4. Configure Environment Variables
Copy the example env file and update with your settings:
```bash
cp .env.example .env
```

### 5. Run Migrations
```bash
# Navigate to migrations directory and apply them
cd migrations
# Run migration script as per your setup
```

### 6. Start Development Server
```bash
cd api
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Running Tests
```bash
pytest tests/
```

## Deactivating Virtual Environment
```bash
deactivate
```

## Project Structure
- `api/` - FastAPI application
- `bot/` - Telegram bot
- `llm/` - LLM integration
- `notification/` - Notification service
- `prompts/` - Prompt templates
- `extension/` - Browser extension
- `migrations/` - Database migrations
- `tests/` - Test suite

## Additional Resources
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- See [CLAUDE.md](CLAUDE.md) for development context
