# HR Screening Agent MVP

An agentic HR screening system that evaluates candidate fit against job requirements using LLM-assisted extraction, deterministic scoring, and an agent loop for clarification questions.

## Features

### Candidate Management
- **Contact Information Extraction**: Automatically extracts email, phone, Telegram, and WhatsApp from CVs
- **Multi-Channel Communication**: Send review results via email (with support for phone, Telegram, WhatsApp in future)
- **CV Storage**: All uploaded CVs are stored persistently

- **Structured Extraction**: Automatically converts unstructured job descriptions and CVs into structured representations
- **Deterministic Scoring**: LLM provides ratings, but final score and decision are computed deterministically in code
- **Agent Loop**: Generates clarification questions when information is unclear and can re-evaluate
- **Evidence-Based**: Every requirement evaluation includes quoted evidence from the CV
- **Guardrails**: Ignores protected attributes and treats inputs as data only
- **Persistent Storage**: All data stored in PostgreSQL
- **Docker Support**: Fully containerized with docker-compose
- **Web UI**: Modern React frontend with beautiful, intuitive interface

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd mok-ai-agent-hr
```

2. Create `.env` file from example:
```bash
cp .env.example .env
```

3. Edit `.env` and set your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
```

4. Start the services:
```bash
docker compose up --build
```

The frontend will be available at `http://localhost:3000`
The API will be available at `http://localhost:8000`

### Using the Web UI

1. Open your browser and navigate to `http://localhost:3000`
2. **Create a Job Posting**: Click "Create Job" and paste a job description
3. **Upload a CV**: Click "Upload CV" and select a PDF, DOCX, or TXT file
4. **Run Screening**: Click "Run Screening", enter the candidate ID and position ID, then view results

### Verify Installation

```bash
# Test API
curl http://localhost:8000/

# Or just open the frontend in your browser
# http://localhost:3000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `DATABASE_URL` | Database connection string | `postgresql://postgres:postgres@localhost:5432/hr_screening` |
| `SCORING_THRESHOLD` | Score threshold for "pass" decision | `0.65` |
| `SCORING_HOLD_BAND` | Band width for "hold" decision | `0.10` |
| `LOG_LEVEL` | Logging level | `INFO` |

## API Endpoints

### 1. Create Job Posting

Convert raw job description text into a structured position.

```bash
curl -X POST "http://localhost:8000/positions" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_description": "We are looking for a Senior Python Developer with 5+ years of experience. Must have experience with FastAPI, PostgreSQL, and cloud platforms (AWS preferred). Nice to have: Docker, Kubernetes, machine learning experience."
  }'
```

Response:
```json
{
  "id": "abc123...",
  "raw_description": "...",
  "structured_data": {
    "title": "Senior Python Developer",
    "requirements": [
      {
        "text": "5+ years Python experience",
        "category": "must",
        "weight": 0.4
      },
      {
        "text": "FastAPI experience",
        "category": "must",
        "weight": 0.3
      },
      ...
    ],
    "summary": "..."
  },
  "is_open": true,
  "created_at": "2024-01-01T12:00:00"
}
```

### 2. Upload CV

Upload a candidate's CV (PDF, DOCX, or TXT).

```bash
curl -X POST "http://localhost:8000/candidates/upload" \
  -F "file=@candidate_cv.pdf"
```

Response:
```json
{
  "id": "def456...",
  "cv_file_path": "./uploads/candidate_cv.pdf",
  "cv_file_type": "pdf",
  "structured_profile": {
    "name": "John Doe",
    "email": "john@example.com",
    "experience": [...],
    "education": [...],
    "skills": ["Python", "FastAPI", ...],
    "summary": "..."
  },
  "created_at": "2024-01-01T12:00:00"
}
```

### 3. Run Screening

Evaluate a candidate against a position.

```bash
curl -X POST "http://localhost:8000/screenings?candidate_id=def456&position_id=abc123"
```

Response:
```json
{
  "id": "screening789",
  "candidate_id": "def456",
  "position_id": "abc123",
  "decision": "pass",
  "score": 0.75,
  "requirement_breakdown": [
    {
      "requirement_text": "5+ years Python experience",
      "category": "must",
      "weight": 0.4,
      "rating": 1.0,
      "evidence": ["\"5 years of Python development experience\""],
      "confidence": "high",
      "notes": "Strong match"
    },
    ...
  ],
  "strengths": [
    "5+ years Python experience (Fully met)",
    "FastAPI experience (Fully met)"
  ],
  "gaps": [
    "Kubernetes experience (Not met)"
  ],
  "clarification_questions": [],
  "suggested_interview_questions": [
    "Can you describe your experience with cloud platforms?",
    ...
  ],
  "candidate_email_draft": {
    "subject": "Application Update - Senior Python Developer",
    "body": "Dear John,\n\nThank you for your application..."
  },
  "audit_trail": {
    "threshold": 0.65,
    "hold_band": 0.10,
    "must_have_gating": true,
    "must_have_failed": false,
    "weighted_sum": 0.75,
    "score": 0.75,
    "decision": "pass",
    "evaluation_details": [...]
  },
  "scoring_policy": {
    "threshold": 0.65,
    "hold_band": 0.10,
    "must_have_gating": true
  },
  "version": 1,
  "created_at": "2024-01-01T12:00:00"
}
```

### 4. Agent Mode

Run screening with agent loop (can accept raw job description or position_id).

```bash
curl -X POST "http://localhost:8000/agent/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "position_id": "abc123",
    "candidate_id": "def456",
    "max_iterations": 3
  }'
```

Or with raw job description:
```bash
curl -X POST "http://localhost:8000/agent/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_job_description": "Looking for a Python developer...",
    "candidate_id": "def456",
    "max_iterations": 3
  }'
```

### 5. Match Against All Positions

Find top N matching positions for a candidate.

```bash
curl -X POST "http://localhost:8000/agent/match-positions?candidate_id=def456&top_n=5"
```

### 6. Get Stored Data

```bash
# Get position
curl "http://localhost:8000/positions/abc123"

# Get candidate
curl "http://localhost:8000/candidates/def456"

# Get screening
curl "http://localhost:8000/screenings/screening789"

# List screenings
curl "http://localhost:8000/screenings?candidate_id=def456"
curl "http://localhost:8000/screenings?position_id=abc123"
```

## Scoring System

### Decision Logic

1. **Must-Have Gating**: If any must-have requirement has rating < 1.0 → **REJECT**
2. **Score-Based Decision**:
   - Score >= threshold → **PASS**
   - Score >= (threshold - hold_band) → **HOLD**
   - Otherwise → **REJECT**

### Score Computation

```
score = Σ (requirement_rating × requirement_weight)
```

Weights are automatically normalized to sum to 1.0.

### Example

Given:
- Threshold: 0.65
- Hold band: 0.10

Evaluations:
- Must-have "Python 5+ years": rating=1.0, weight=0.4 → contribution=0.4
- Must-have "FastAPI": rating=1.0, weight=0.3 → contribution=0.3
- Nice-to-have "Kubernetes": rating=0.0, weight=0.3 → contribution=0.0

Score = 0.4 + 0.3 + 0.0 = 0.7

Decision: **PASS** (0.7 >= 0.65)

## Audit Trail

Every screening includes a detailed audit trail showing:
- Scoring policy used (threshold, hold_band, must_have_gating)
- Individual requirement contributions
- Must-have gating results
- Final score computation
- Decision rationale

This ensures reproducibility and transparency.

## Guardrails

The system implements several guardrails:

1. **Protected Attributes**: Ignores age, gender, nationality, ethnicity, religion, marital status, photos
2. **Untrusted Input**: Treats CV and job description as data only, does not follow any instructions within them
3. **Evidence Required**: Every requirement claim must include quoted evidence from the CV
4. **Unknown Handling**: Marks unclear information as unknown and generates clarification questions rather than guessing

## Agent Loop

When information is unclear or missing:

1. System generates clarification questions
2. Questions are stored in the screening record
3. In a full implementation, answers would be collected and candidate profile updated
4. Re-evaluation can be triggered with updated information
5. Version tracking maintains history of screening iterations

## Project Structure

```
mok-ai-agent-hr/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── cv_parser.py         # CV parsing (PDF/DOCX/TXT)
│   ├── llm_service.py       # LLM interactions
│   ├── scoring.py           # Deterministic scoring
│   └── agent_tools.py       # Agentic tools
├── tests/
│   ├── test_scoring.py      # Scoring logic tests
│   └── test_schemas.py      # Schema contract tests
├── data/                    # Database storage (created automatically)
├── uploads/                 # Uploaded CVs (created automatically)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Running Tests

```bash
# Inside container
docker compose exec api pytest

# Or locally (if dependencies installed)
pytest
```

## Development

### Local Development (without Docker)

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables (create `.env` file)

4. Run:
```bash
uvicorn app.main:app --reload
```

### Database

The system uses PostgreSQL. The default connection string is:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hr_screening
```

When using Docker Compose, PostgreSQL is automatically set up as a service. For local development, ensure PostgreSQL is running and update the connection string in `.env` if needed.

## Logging

Logs are output to stdout with the following levels:
- `INFO`: Normal operations (extraction, evaluation, scoring)
- `ERROR`: Errors (parsing failures, API failures)

Set `LOG_LEVEL` environment variable to control verbosity.

## Error Handling

- LLM API calls include retry logic (max 3 attempts with exponential backoff)
- CV parsing errors are logged and raised
- Database errors are handled gracefully
- API endpoints return appropriate HTTP status codes

## Limitations & Future Enhancements

Current MVP limitations:
- Clarification questions are generated but answers must be manually provided
- Simple position matching (could be enhanced with embeddings/vector search)
- Single LLM provider abstraction (OpenAI only, but structure supports others)

Potential enhancements:
- Automated clarification question answering via email/SMS
- Vector search for position matching
- Multi-provider LLM support (Gemini, Anthropic, etc.)
- Batch processing
- Export to ATS systems

## License

[Your License Here]

## Support

For issues or questions, please open an issue in the repository.
