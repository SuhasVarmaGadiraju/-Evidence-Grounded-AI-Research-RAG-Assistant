# Evidence-Grounded AI Research Assistant (RAG)

> **Enterprise-grade Production Retrieval-Augmented Generation (RAG) system for intelligent academic document search, dense vector retrieval, sparse lexical matching, cross-encoder re-ranking, and grounded LLM synthesis.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.all/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20DB-00599C?style=for-the-badge&logo=meta&logoColor=white)](https://github.com/facebookresearch/faiss)
[![Firebase](https://img.shields.io/badge/Firebase-Auth-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![Railway](https://img.shields.io/badge/Railway-Backend-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app/)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

---

## 🎯 Project Overview

The **Evidence-Grounded AI Research Assistant** is an open-source, full-stack Retrieval-Augmented Generation (RAG) application engineered to solve hallucination and context limitations in Large Language Models (LLMs). By indexing multi-page academic research PDFs into dense vector embeddings and sparse lexical tokens, the platform provides exact page-level source citations and verifiably grounded answers.

### 💡 The Problem It Solves
Standard LLMs suffer from two critical limitations:
1. **Hallucinations & Untraceability**: Models generate plausible-sounding answers without verifiable source documentation.
2. **Knowledge Cutoffs & Context Constraints**: Generalist LLMs lack access to private, domain-specific research PDFs and recent literature.

### ⚡ Why Retrieval-Augmented Generation (RAG)?
RAG bridges parametric LLM intelligence with non-parametric external document knowledge. By fetching relevant passages *before* calling the LLM, the system forces the model to synthesize answers strictly from retrieved evidence, producing fully citeable responses.

### 🏢 Real-World Use Cases
- **Academic Research**: Rapidly query hundreds of multi-page PDF papers for methodologies, formulas, and baseline results.
- **Legal & Compliance**: Search contract clauses, privacy regulations (GDPR/HIPAA), and statutory requirements with exact page attribution.
- **Enterprise Knowledge Base**: Query internal technical specifications, product documentation, and whitepapers with strict zero-hallucination constraints.

---

## ✨ Features

- 📄 **Multi-Page PDF Ingestion**: Drag-and-drop PDF upload with automatic text cleaning, paragraph normalization, and metadata extraction.
- ⚙️ **Configurable Chunking Strategies**: Support for both Fixed-Size boundary chunking and Recursive Structure segmentation.
- 🔐 **Firebase Authentication**: Secure user authentication with Email/Password and Google OAuth sign-in.
- 🧠 **Dense Semantic Vector Search**: High-dimensional cosine similarity matching powered by 384d `all-MiniLM-L6-v2` embeddings in FAISS (`IndexFlatIP`).
- 🔤 **Sparse Lexical BM25 Search**: Okapi BM25 index for exact keyword matching, technical acronyms, and specialized term recall.
- 🔀 **Hybrid Search (Reciprocal Rank Fusion)**: Combines dense vector similarity with sparse BM25 keyword scores using Reciprocal Rank Fusion (RRF).
- 🎯 **CrossEncoder Re-ranking**: Deep transformer-based cross-attention re-ranking to elevate highly relevant passages to top-K contexts.
- 💬 **Interactive AI Research Chat**: Multi-turn conversation sessions with real-time response generation and expandable evidence drawer.
- 🛠️ **Interactive Prompt Builder**: Customize RAG system prompts, temperature, top-K thresholds, and chunking parameters in real time.
- 📊 **RAG Evaluation Diagnostics**: Metric evaluation calculating Retrieval Precision, Recall, Mean Reciprocal Rank (MRR), and Groundedness Scores.
- 📈 **Analytics Dashboard**: Real-time visualization of library statistics, total document chunks, average latency, and search algorithm distribution.
- 🌗 **Dark / Light Theme**: Premium Tailwind CSS theme switcher with seamless glassmorphism UI.
- 📱 **Fully Responsive Interface**: Mobile-friendly sidebar drawer and optimized desktop workspace layouts.
- 📍 **Page-Level Source Citations**: Inline clickable badge citations linking directly to exact PDF source pages.
- 🗄️ **Relational Metadata Storage**: PostgreSQL database (Neon) for tracking users, document libraries, chunk indices, and chat session histories.

---

## 🏗️ Project Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Vercel)"]
        User(["👤 Researcher"])
        ReactApp["⚛️ React 19 + Vite Frontend"]
    end

    subgraph API ["API & Routing Layer (Railway)"]
        FlaskServer["🐍 Flask Backend Gateway"]
        FirebaseAuth["🔥 Firebase Auth Validation"]
    end

    subgraph Processing ["Ingestion & Pipeline"]
        PDFParser["📄 PyMuPDF / Text Normalizer"]
        Chunker["✂️ Fixed / Recursive Chunker"]
        Embedder["🧠 SentenceTransformer (all-MiniLM-L6-v2)"]
    end

    subgraph Storage ["Storage & Indexing (Neon PostgreSQL)"]
        PostgresDB[("🐘 Neon PostgreSQL DB")]
        FAISSStore[("⚡ FAISS IndexFlatIP Vector DB")]
        BM25Store[("🔤 BM25 Lexical Index")]
    end

    subgraph Retrieval ["Hybrid Retrieval & Reranking"]
        VectorSearch["Semantic Search (FAISS)"]
        LexicalSearch["Lexical Search (BM25)"]
        RRFEngine["🔀 Reciprocal Rank Fusion (RRF)"]
        CrossEncoder["🎯 Cross-Encoder Reranker"]
    end

    subgraph Inference ["LLM Inference Layer"]
        LlamaAPI["🤖 NVIDIA Llama 3.1 8B Instruct API"]
    end

    User -->|Queries / Uploads| ReactApp
    ReactApp -->|REST API Request + JWT| FlaskServer
    FlaskServer -->|Validate Token| FirebaseAuth
    
    FlaskServer -->|PDF Upload| PDFParser
    PDFParser --> Chunker
    Chunker --> Embedder
    Embedder --> FAISSStore
    Chunker --> BM25Store
    Chunker --> PostgresDB

    FlaskServer -->|Search / Chat Query| VectorSearch & LexicalSearch
    FAISSStore --> VectorSearch
    BM25Store --> LexicalSearch
    VectorSearch & LexicalSearch --> RRFEngine
    RRFEngine --> CrossEncoder
    CrossEncoder -->|Top-K Context + Prompt| LlamaAPI
    LlamaAPI -->|Grounded Response + Sources| FlaskServer
    FlaskServer -->|JSON Response| ReactApp
```

---

## 🔬 Complete RAG Pipeline

<details>
<summary><strong>🔍 Click to expand the 15-stage RAG Pipeline details</strong></summary>

1. **Upload PDF**: User uploads raw academic PDF documents via the drag-and-drop frontend interface.
2. **Text Extraction**: PyMuPDF parses raw PDF stream, extracting text content along with page numbers and structural headers.
3. **Cleaning & Normalization**: Strips invalid UTF-8 encodings, removes redundant whitespace, normalizes hyphenated linebreaks, and formats equations.
4. **Paragraph Chunking**: Segments documents into chunks using Fixed-size (500 chars) or Recursive Structure boundaries with overlapping windows (50 chars) to prevent context loss across boundaries.
5. **Embedding Generation**: Converts each chunk into a 384-dimensional dense vector using the `sentence-transformers/all-MiniLM-L6-v2` embedding model.
6. **FAISS Indexing**: Ingests 384d normalized vectors into FAISS `IndexFlatIP` (Inner Product) for lightning-fast cosine similarity vector search.
7. **BM25 Lexical Indexing**: Tokenizes chunks into term-frequency matrices using `rank_bm25` (Okapi BM25 algorithm) for exact keyword and acronym indexing.
8. **Query Embedding**: User chat or diagnostic query is encoded into a 384d vector using the exact same embedding pipeline.
9. **Semantic Vector Retrieval**: Performs $k$-nearest neighbor cosine similarity search in FAISS, retrieving top-N dense vector candidates.
10. **BM25 Lexical Retrieval**: Scores chunks using term frequency-inverse document frequency weighting, retrieving top-N sparse keyword candidates.
11. **Hybrid Reciprocal Rank Fusion (RRF)**: Combines dense semantic rank $R_{\text{semantic}}$ and sparse BM25 rank $R_{\text{BM25}}$ using:
    $$\text{RRF Score}(d) = \frac{1}{60 + R_{\text{semantic}}(d)} + \frac{1}{60 + R_{\text{BM25}}(d)}$$
12. **Cross-Encoder Re-ranking**: Passes top candidates through `ms-marco-MiniLM-L-6-v2` cross-attention model to compute query-chunk relevance scores and filter out irrelevant passages.
13. **Prompt Construction**: Injects retrieved top-K passages into a strict system prompt instructing the model to rely exclusively on provided evidence.
14. **LLM Synthesis**: Calls NVIDIA Llama 3.1 8B Instruct API to generate a precise, factual answer.
15. **Source Citation**: Appends exact document names and page numbers (`[Paper_Title.pdf, Page X]`) for inline UI attribution.

</details>

---

## 🛠️ Tech Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend** | React 19, Vite 6, Tailwind CSS v4, React Router DOM v7, Axios, Lucide Icons |
| **Backend** | Python 3.12, Flask 3.0, SQLAlchemy ORM, Alembic Migrations |
| **AI / Machine Learning** | SentenceTransformers (`all-MiniLM-L6-v2`), FAISS Vector Engine, Rank-BM25, Cross-Encoder (`ms-marco-MiniLM-L-6-v2`), NVIDIA Llama 3.1 8B API |
| **Authentication** | Firebase Authentication (JWT Tokens, Google OAuth 2.0) |
| **Database** | Neon PostgreSQL (Serverless Cloud Database) |
| **Infrastructure / Deployment** | Vercel (Frontend CDN), Railway (Backend Container), Docker |

---

## 📁 Folder Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (auth, documents, search, chat, eval)
│   │   ├── core/            # Config, security, database initialization
│   │   ├── models/          # SQLAlchemy ORM models (User, Document, Chunk)
│   │   └── services/        # RAG pipeline (chunking, embedding, FAISS, BM25, rerank, LLM)
│   ├── database/            # Database connection & session setup
│   ├── migrations/          # Alembic database migration scripts
│   ├── Dockerfile           # Backend container specification
│   ├── requirements.txt     # Python dependency manifest
│   ├── run.py               # Flask application entry point
│   └── runtime.txt          # Python runtime version lock
│
├── frontend/
│   ├── public/              # Static assets & favicon
│   ├── src/
│   │   ├── assets/          # SVG icons & branding graphics
│   │   ├── components/      # UI components (Header, Sidebar, AppLayout, ProtectedRoute)
│   │   ├── context/         # React Contexts (AuthContext, ThemeContext)
│   │   ├── pages/           # Application views (Home, Chat, Upload, Documents, Searches)
│   │   ├── services/        # Axios API client configured with Bearer token interceptor
│   │   ├── App.jsx          # Main application routing & lazy suspense boundaries
│   │   └── main.jsx         # React application entry root
│   ├── package.json         # Node.js dependencies & scripts
│   ├── vercel.json          # Single-page application SPA rewrite rules
│   └── vite.config.js       # Vite build & chunking configuration
│
├── .vercelignore            # Excludes backend & non-frontend files from Vercel deployments
├── README.md                # Project documentation
└── runtime.txt              # Project level Python specification
```

---

## 🚀 Installation & Local Setup

### Prerequisites
- **Node.js** >= 18.x
- **Python** >= 3.11
- **PostgreSQL** instance (local or Neon PostgreSQL cloud)
- **NVIDIA API Key** (for Llama 3.1 inference)
- **Firebase Project** (for client authentication)

### 1. Clone the Repository
```bash
git clone https://github.com/SuhasVarmaGadiraju/-Evidence-Grounded-AI-Research-RAG-Assistant.git
cd -Evidence-Grounded-AI-Research-RAG-Assistant
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate
# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file in backend directory (see Environment Variables section)
# Run database migrations
flask db upgrade

# Start Flask dev server
python run.py
```
*Backend server will start at `http://localhost:5000`.*

### 3. Frontend Setup
```bash
# Navigate to frontend directory (from project root)
cd ../frontend

# Install dependencies
npm install

# Create .env file in frontend directory (see Environment Variables section)
# Start Vite dev server
npm run dev
```
*Frontend application will start at `http://localhost:5173`.*

---

## 🔐 Environment Variables

### Backend Environment Variables (`backend/.env`)

| Variable Name | Scope | Description | Sample Format |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Backend | PostgreSQL connection string | `postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require` |
| `NVIDIA_API_KEY` | Backend | NVIDIA AI Foundation Endpoint Key | `nvapi-xxxxxxxxxxxxxxxxxxxxxxxx` |
| `SECRET_KEY` | Backend | Flask session & JWT secret | `your-super-secret-random-key` |
| `FLASK_ENV` | Backend | Execution environment | `development` / `production` |
| `PORT` | Backend | Server port | `5000` |

### Frontend Environment Variables (`frontend/.env`)

| Variable Name | Scope | Description | Sample Format |
| :--- | :--- | :--- | :--- |
| `VITE_API_URL` | Frontend | Flask Backend API Base URL | `http://localhost:5000` or `https://your-backend.up.railway.app` |
| `VITE_FIREBASE_API_KEY` | Frontend | Firebase API Key | `AIzaSyXxxxxxxxxxxxxxxxxx` |
| `VITE_FIREBASE_AUTH_DOMAIN` | Frontend | Firebase Auth Domain | `your-app.firebaseapp.com` |
| `VITE_FIREBASE_PROJECT_ID` | Frontend | Firebase Project ID | `your-app-id` |
| `VITE_FIREBASE_STORAGE_BUCKET`| Frontend | Firebase Storage Bucket | `your-app.appspot.com` |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Frontend | Firebase Sender ID | `123456789012` |
| `VITE_FIREBASE_APP_ID` | Frontend | Firebase App ID | `1:123456789012:web:abcdef` |

---

## 🖼️ Application Screenshots

| Page View | Screenshot Preview |
| :--- | :--- |
| **Landing Page** | ![Landing Page](https://via.placeholder.com/800x450.png?text=Landing+Page+View) |
| **Dashboard Analytics** | ![Dashboard](https://via.placeholder.com/800x450.png?text=Dashboard+Analytics+View) |
| **Upload Documents** | ![Upload Documents](https://via.placeholder.com/800x450.png?text=Upload+Documents+View) |
| **Document Library** | ![Document Library](https://via.placeholder.com/800x450.png?text=Document+Library+View) |
| **Semantic Search** | ![Semantic Search](https://via.placeholder.com/800x450.png?text=Semantic+FAISS+Search+View) |
| **BM25 Lexical Search** | ![BM25 Search](https://via.placeholder.com/800x450.png?text=BM25+Search+View) |
| **Hybrid Search (RRF)** | ![Hybrid Search](https://via.placeholder.com/800x450.png?text=Hybrid+Search+RRF+View) |
| **AI Research Chat** | ![AI Chat](https://via.placeholder.com/800x450.png?text=AI+Research+Chat+View) |
| **RAG Evaluation** | ![Evaluation](https://via.placeholder.com/800x450.png?text=RAG+Evaluation+Metrics+View) |
| **Settings** | ![Settings](https://via.placeholder.com/800x450.png?text=Settings+Panel+View) |

---

## 📡 API Endpoints Specification

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/upload` | Yes | Uploads PDF files, performs chunking, embedding, FAISS & BM25 indexing |
| `GET` | `/api/documents` | Yes | Lists all ingested documents with chunk counts and metadata |
| `DELETE`| `/api/documents/:id` | Yes | Deletes document and removes associated vectors/chunks |
| `GET` | `/api/documents/:id/chunks`| Yes | Retrieves chunk previews for a specific document |
| `POST` | `/api/retrieval/search` | Yes | Executes FAISS dense semantic similarity vector search |
| `POST` | `/api/retrieval/bm25` | Yes | Executes Okapi BM25 sparse keyword search |
| `POST` | `/api/retrieval/hybrid` | Yes | Executes Hybrid Search combining FAISS + BM25 via Reciprocal Rank Fusion |
| `POST` | `/api/retrieval/rerank` | Yes | Runs Cross-Encoder re-ranking on candidate passages |
| `POST` | `/api/chat` | Yes | Generates grounded answer using retrieved contexts + Llama 3.1 |
| `GET` | `/api/sessions` | Yes | Fetches user chat session history |
| `GET` | `/api/evaluation` | Yes | Returns RAG pipeline evaluation metrics (Precision, Recall, MRR) |

---

## 🗄️ Database Schema Design

```
  +------------------+         +--------------------+         +-------------------+
  |      Users       |         |     Documents      |         |      Chunks       |
  +------------------+         +--------------------+         +-------------------+
  | id (PK)          |<-------1| id (PK)            |<-------1| id (PK)           |
  | email            |        || user_id (FK)       |        || document_id (FK) |
  | firebase_uid     |        || filename           |        || chunk_index      |
  | created_at       |        || total_chunks       |        || text_content     |
  +------------------+        N| created_at         |        N| page_number       |
                               +--------------------+         | embedding_id      |
                                                              +-------------------+
```

- **Users**: Manages user profiles synchronized with Firebase UID.
- **Documents**: Tracks uploaded PDF files, file sizes, chunk quantities, and user ownership.
- **Chunks**: Stores individual text segments, page numbers, character offsets, and references to FAISS vector IDs.

---

## 🔍 Search Algorithms & Comparisons

| Algorithm | Type | Strengths | Weaknesses |
| :--- | :--- | :--- | :--- |
| **Semantic Search (FAISS)** | Dense Vector | Captures conceptual intent and synonyms without exact keyword matches. | Can miss exact technical acronyms, part numbers, or unique code names. |
| **Lexical Search (BM25)** | Sparse Term Frequency | Highly accurate for exact word matches, proper nouns, and acronyms. | Fails when query uses synonyms or paraphrased wording. |
| **Hybrid Search (RRF)** | Multi-Retrieval Fusion | Combines advantages of both dense vector recall and sparse keyword precision. | Adds minimal aggregation latency (~10ms). |
| **Cross-Encoder Reranking** | Deep Transformer Attention | Jointly cross-attends query and document text for maximum relevance ordering. | Computationally heavier (~30-50ms) than bi-encoder matrix dot product. |

---

## ⚡ Why Hybrid Search Improves Retrieval

In single-retrieval RAG architectures, relying purely on dense vector embeddings can cause failures when users query specific terms (e.g., `"Equation 4.2"` or `"ResNet-50"`). Conversely, sparse BM25 keyword matching fails on semantic conceptual queries (e.g., `"How does the model prevent overfitting?"`).

By merging dense cosine similarity with sparse BM25 scores via **Reciprocal Rank Fusion (RRF)**:
1. Candidate documents are retrieved from both index structures in parallel.
2. Documents appearing in both result sets receive a reciprocal boost.
3. The combined candidate set provides significantly higher Recall@K before entering the LLM context window.

---

## 📊 Performance & Optimization

- **Embedding Speed**: SentenceTransformer `all-MiniLM-L6-v2` processes ~150 chunks/sec on CPU.
- **Vector Search Latency**: FAISS `IndexFlatIP` retrieves top-5 matches in $< 2\text{ms}$.
- **BM25 Lookup**: Okapi BM25 index returns matches in $< 5\text{ms}$.
- **Cross-Encoder Reranking**: `ms-marco-MiniLM-L-6-v2` re-ranks 25 candidates in $\sim 35\text{ms}$.
- **End-to-End Search Latency**: Complete Hybrid + Rerank search completes in $< 100\text{ms}$ (excluding LLM generation time).
- **Vite Bundle Optimization**: Code-split into `vendor-react` (224kB), `vendor-firebase` (114kB), and `vendor-icons` (23kB) for rapid CDN caching.

---

## 🛡️ Security

- **Firebase Token Verification**: Flask backend validates incoming Firebase Bearer JWT tokens on every protected endpoint.
- **CORS Protection**: Restricted Cross-Origin Resource Sharing headers configured to allow only authorized frontend origins.
- **Database Security**: Serverless Neon PostgreSQL database accessed strictly via TLS/SSL encrypted connections (`sslmode=require`).
- **Environment Isolation**: Secrets (`NVIDIA_API_KEY`, `DATABASE_URL`) are kept isolated on backend servers and never exposed to the client bundle.

---

## 🌐 Deployment Architecture

- **Frontend (React + Vite)**: Deployed to **Vercel** with single-page application rewrite routing (`vercel.json`).
- **Backend (Flask)**: Deployed on **Railway** via Docker container with Gunicorn WSGI HTTP server.
- **Database (PostgreSQL)**: Hosted on **Neon Serverless PostgreSQL**.

---

## 🔮 Future Improvements

- 🌊 **Streaming LLM Responses**: Implement Server-Sent Events (SSE) / WebSockets for token-by-token response streaming.
- ⚡ **Asynchronous Background Processing**: Offload PDF processing and vector indexing to Celery + Redis queues.
- 🛡️ **Role-Based Access Control (RBAC)**: Team workspaces with granular viewer, editor, and admin permissions.
- 🖼️ **OCR & Multi-Modal RAG**: Integrate Tesseract / AWS Textract to parse images, scans, and tables inside PDF documents.
- 📦 **Redis Caching**: Cache frequent semantic search vector queries to reduce backend computation.

---

## 👨‍💻 Author

**Suhas Varma Gadiraju**
- **GitHub**: [@SuhasVarmaGadiraju](https://github.com/SuhasVarmaGadiraju)
- **LinkedIn**: [Suhas Varma Gadiraju](https://linkedin.com/in/)
- **Portfolio**: [suhasvarma.dev](https://suhasvarma.dev)

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
