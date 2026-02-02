# Quick Start Guide

## 1. Create Environment File

Create a `.env` file in the project root:

```bash
# Copy this content to .env file
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
DATABASE_URL=sqlite:///./data/hr_screening.db
SCORING_THRESHOLD=0.65
SCORING_HOLD_BAND=0.10
LOG_LEVEL=INFO
```

## 2. Start with Docker

```bash
docker compose up --build
```

## 3. Use the Web UI

Open your browser and navigate to `http://localhost:3000`

The web interface provides:
- **Dashboard**: View recent screenings
- **Create Job Posting**: Paste job descriptions to create structured positions
- **Upload CV**: Upload candidate CVs (PDF, DOCX, TXT)
- **Run Screening**: Evaluate candidates against positions
- **View Results**: See detailed screening results with scores, evidence, and recommendations

## 4. Or Use the API Directly

```bash
# Check if API is running
curl http://localhost:8000/

# Create a job posting
curl -X POST "http://localhost:8000/positions" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_description": "Looking for a Python developer with 3+ years experience. Must know FastAPI and SQL."
  }'

# Save the position_id from the response, then upload a CV
curl -X POST "http://localhost:8000/candidates/upload" \
  -F "file=@path/to/candidate_cv.pdf"

# Save the candidate_id, then run screening
curl -X POST "http://localhost:8000/screenings?candidate_id=YOUR_CANDIDATE_ID&position_id=YOUR_POSITION_ID"
```

See README.md for full API documentation.
