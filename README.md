# Demo Video: https://youtu.be/ltRvZQI0IEk 

# 🚀 GitXeek

> **Seek the hidden story behind every GitHub repository.**

GitXeek is an AI-powered repository intelligence platform that goes beyond traditional code search. Instead of only indexing files, it understands **commits, pull requests, documentation, code structure, and project evolution**, building a persistent knowledge graph that can answer questions such as:

* Who implemented this feature?
* Why was this architecture introduced?
* Which PR changed this module?
* When did this API appear?
* How are different components related?
* What decisions shaped the project?

GitXeek combines **FastAPI**, **LLMs**, **Cognee**, and **knowledge graphs** to continuously learn from repositories and answer natural language questions with contextual understanding.

---

# ✨ Features

* 📂 GitHub repository indexing
* 🧠 AI-powered repository understanding
* 🔍 Semantic search over commits, PRs, files, and documentation
* 🌐 Knowledge Graph generation using Cognee
* 🤖 LLM enrichment for repository metadata
* ⚡ Background processing for repository indexing
* 📖 README understanding
* 🔗 Relationship extraction between features, modules, authors, and commits
* 💬 Natural language querying
* 📊 Repository understanding progress tracking

---

# 🏗️ Architecture

```
                  GitHub Repository
                          │
                          ▼
               Repository Cloning
                          │
                          ▼
                 Repository Scanner
                          │
         ┌────────────────┴───────────────┐
         │                                │
         ▼                                ▼
 Manual Normalization             Code Analysis
         │                                │
         └──────────────┬─────────────────┘
                        ▼
                LLM Enrichment
                        │
                        ▼
                Merged Knowledge
                        │
                        ▼
               Cognee Knowledge Graph
                        │
                        ▼
          Semantic Retrieval & Reasoning
                        │
                        ▼
                Natural Language Answers
```

---

# 🧠 How GitXeek Works

## 1. Repository Analysis

GitXeek clones the repository and extracts information from:

* Source code
* README
* Pull Requests
* Commits
* Issues (optional)
* Repository metadata
* Folder structure

---

## 2. Manual Normalization

Every artifact is converted into a standard schema.

Example:

```json
{
  "artifact_type": "commit",
  "title": "Added JWT Authentication",
  "module": "authentication",
  "author": "John",
  "summary": "Implemented login flow"
}
```

---

## 3. LLM Enrichment

The normalized data is enriched using an LLM.

The model extracts:

* feature names
* architectural decisions
* implementation reasons
* impacted modules
* technical concepts
* hidden relationships

---

## 4. Knowledge Merging

Manual metadata and AI-generated insights are merged into a richer representation before indexing.

---

## 5. Cognee Knowledge Graph

The merged knowledge is stored in Cognee.

Instead of plain vector search, GitXeek stores:

* entities
* relationships
* facts
* domain concepts
* project memory

Example relationships:

```
JWT Authentication
      │
      ├── implemented_by → Commit
      │
      ├── reviewed_in → Pull Request
      │
      ├── belongs_to → Authentication Module
      │
      └── documented_in → README
```

---

## 6. Querying

Users ask natural language questions like:

> Who introduced JWT?

> Why was Redis added?

> Which PR refactored authentication?

GitXeek retrieves the relevant knowledge graph context and generates an accurate answer.

---

# 📁 Project Structure

```
GitXeek/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── workers/
│   ├── utils/
│   ├── schemas/
│   └── main.py
│
├── alembic/
├── tests/
├── .env
├── pyproject.toml
├── uv.lock
└── README.md
```

---

# 🛠️ Tech Stack

### Backend

* FastAPI
* Uvicorn
* SQLAlchemy
* Async PostgreSQL
* Alembic

### AI

* Cognee
* Gemini / OpenAI compatible LLM
* Knowledge Graphs
* Embeddings
* Semantic Retrieval

### Infrastructure

* uv
* Git
* GitHub API

---

# 📦 Installation

## Clone the repository

```bash
git clone https://github.com/your-username/gitxeek.git

cd gitxeek
```

---

## Install uv

If you don't already have **uv** installed:

### Linux / macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or visit:

https://docs.astral.sh/uv/

---

## Install dependencies

```bash
uv sync
```

---

# ⚙️ Environment Variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/gitxeek

SECRET_KEY=your-secret-key


#github
GITHUB_CLIENT_ID=your-github-token
GITHUB_CLIENT_SECRET=secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback
GITHUB_OAUTH_SCOPES=repo read:user user:email

REPOS_CLONE_DIR=path
FRONTEND_URL=http://localhost:3000

# cognee
COGNEE_SERVICE_URL=tenant.url
COGNEE_API_KEY=key

# #LLM config for Cognee
# openrouter
LLM_API_KEY=your-key
LLM_PROVIDER=gemini/custom/openai
LLM_MODEL=model
```

Adjust the variables according to your local setup.

---

# 🚀 Running the Project

Start the FastAPI server using **uv**:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

---

# 📖 API Documentation

Interactive Swagger UI:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

---

# 🔄 Typical Workflow

1. Add a GitHub repository.
2. GitXeek clones the repository.
3. Background workers begin indexing.
4. README, commits, pull requests, and source code are analyzed.
5. LLM enriches repository knowledge.
6. Cognee builds and updates the knowledge graph.
7. Users ask questions.
8. GitXeek retrieves context and generates intelligent answers.

---

# 💡 Example Questions

* Who implemented OAuth?
* Why was Redis introduced?
* Which PR added dark mode?
* What does the authentication flow look like?
* Which commits modified payment services?
* Explain the repository architecture.
* What is the purpose of this repository?
* How has this project evolved over time?

---

# 🔮 Future Improvements

* GitHub Webhooks
* Incremental repository indexing
* Multi-repository querying
* Architecture diagrams
* Agentic code exploration
* Slack/Discord integrations
* VS Code Extension
* Repository timeline visualization
* PR review assistant
* Code ownership analysis

---

# 🧪 Development

Run the development server:

```bash
uv run uvicorn app.main:app --reload
```

Run tests:

```bash
uv run pytest
```

Run database migrations:

```bash
uv run alembic upgrade head
```

Create a new migration:

```bash
uv run alembic revision --autogenerate -m "migration message"
```

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/my-feature
```

3. Commit your changes

```bash
git commit -m "Add awesome feature"
```

4. Push

```bash
git push origin feature/my-feature
```

5. Open a Pull Request

---

# 📜 License

This project is licensed under the MIT License.

---

# ❤️ Acknowledgements

Special thanks to the open-source community and the projects that made GitXeek possible:

* FastAPI
* Cognee
* Uvicorn
* SQLAlchemy
* Alembic
* GitHub API
* Google Gemini / OpenAI-compatible LLMs

---

# ⭐ Support

If you found GitXeek useful:

* ⭐ Star the repository
* 🍴 Fork it
* 🐛 Report issues
* 💡 Suggest new features

Together, let's make Git repositories truly understandable.
