# QueryForge

A powerful natural language to SQL/NoSQL query generator built with Python, FastAPI, and Streamlit. Convert plain English questions into database queries for MySQL, PostgreSQL, MongoDB, and more.

## Features

- **Multi-Database Support**: MySQL, PostgreSQL, SQL Server, SQLite, Oracle, MongoDB
- **Schema Management**: Save and reuse database schemas
- **Safety First**: Built-in query validation to prevent unsafe operations
- **Multiple Interfaces**: Both REST API and web UI
- **OpenAI Integration**: Powered by GPT models for accurate query generation

## Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: Streamlit
- **AI**: OpenAI GPT models
- **Storage**: JSON file-based schema storage
- **Validation**: Pydantic models with safety checks

## 📦 Installation

1. Clone the repository:
```bash
git clone 
cd queryforge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 🚀 Quick Start

### 1. Set up your environment
```bash
# Install dependencies (handled automatically in Replit)
pip install -r requirements.txt

# Set your OpenAI API key in Settings or .env
export OPENAI_API_KEY="sk-..."
```

### 2. Run the application
```bash
python run.py both
```

## 📚 API Documentation

Once the server is running, visit `http://localhost:5000/docs` for interactive API documentation.

### Key Endpoints

- `POST /api/generate-query` - Generate SQL from natural language
- `GET /api/schemas` - List saved schemas
- `POST /api/schemas` - Save a new schema
- `GET /api/health` - Health check

### Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `ROW_LIMIT_DEFAULT` - Default row limit for queries (optional, default: 100)

## 🤝 Contributing
Contributions are welcome! Please feel to submit a Pull Request.