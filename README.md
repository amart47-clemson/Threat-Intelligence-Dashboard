# Threat Intelligence Dashboard

A full-stack threat intelligence dashboard that ingests IOCs from AlienVault OTX, enriches IP addresses with AbuseIPDB and GeoIP data, and visualizes threats on an interactive map with score history charts.

## Stack

- **Backend:** Python, Flask, PostgreSQL, APScheduler
- **Frontend:** React (Vite), Leaflet.js, Recharts
- **Deployment:** Render (`render.yaml` + `Procfile`)

## Project Structure

```
threat-intel-dashboard/
├── backend/          # Flask API, feeds, scheduler
├── frontend/         # React dashboard
├── .env.example      # Environment variable template
├── render.yaml       # Render deployment blueprint
└── Procfile          # Process definition for Render/Heroku
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- API keys: [AlienVault OTX](https://otx.alienvault.com/api), [AbuseIPDB](https://www.abuseipdb.com/)

## Quick Start

### 1. Database

```bash
createdb threatintel
cp .env.example .env
# Edit .env with your DATABASE_URL and API keys
```

### 2. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python init_db.py          # Create tables
python seed_data.py          # Optional: sample data for UI testing
python app.py                # Start Flask on :5001 (macOS may reserve :5000)
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                  # Start Vite on :5173
```

Open http://localhost:5173

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `OTX_API_KEY` | AlienVault OTX API key |
| `ABUSEIPDB_API_KEY` | AbuseIPDB API key |
| `FLASK_ENV` | `development` or `production` |
| `CORS_ORIGIN` | Frontend origin (e.g. `http://localhost:5173`) |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/iocs` | Paginated IOC list (filters: type, severity, country, search) |
| GET | `/api/iocs/:id` | Single IOC with score history |
| GET | `/api/lookup?q=` | Manual IOC lookup (cache or live) |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/export?format=csv` | CSV export |

## Scheduled Jobs

| Job | Interval | Description |
|-----|----------|-------------|
| OTX ingestion | 30 min | Pull subscribed pulses, upsert IOCs |
| AbuseIPDB enrichment | 60 min | Enrich IP IOCs missing abuse confidence |

## Scoring

```
threat_score = min(100, base_score + (abuse_confidence * 0.4) + (feed_count * 10))
```

| Pulses | Base Score |
|--------|------------|
| 0 | 10 |
| 1–3 | 30 |
| 4–9 | 50 |
| 10+ | 70 |

| Score | Severity |
|-------|----------|
| 0–30 | Low |
| 31–60 | Medium |
| 61–85 | High |
| 86–100 | Critical |

## Testing Feeds in Isolation

```bash
cd backend
source .venv/bin/activate
python test_otx.py    # Print OTX pulse/indicator summary to console
```

## Deploy to Render

1. Push repo to GitHub
2. Create a new Blueprint from `render.yaml`
3. Set `OTX_API_KEY`, `ABUSEIPDB_API_KEY`, and `CORS_ORIGIN` in the Render dashboard
4. The PostgreSQL database is provisioned automatically via the blueprint

## License

MIT
