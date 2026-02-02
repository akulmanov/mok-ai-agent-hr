# HR Screening Agent - Frontend

Modern React frontend for the HR Screening Agent system.

## Features

- **Dashboard**: Overview of recent screenings
- **Job Posting Creation**: Create structured job postings from raw text
- **CV Upload**: Upload and parse candidate CVs
- **Screening**: Run agentic screening evaluations
- **Results View**: Detailed screening results with evidence, scores, and recommendations

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Docker

The frontend is containerized and included in the main `docker-compose.yml`. It uses:
- Multi-stage build (Node for build, Nginx for serving)
- Nginx reverse proxy for API calls
- SPA routing support

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: `/api` for production, `http://localhost:8000` for dev)
