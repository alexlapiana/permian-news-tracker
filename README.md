# Permian Basin News Tracker

Real-time intelligence feed for gas compression businesses. Automatically scrapes and scores oil & gas announcements from across the Permian Basin â tracking 40+ upstream and midstream operators across RSS feeds, Google News, and press releases.

## Features

- **Automated scraping** â Pulls from Rigzone, Hart Energy, OGJ, Reuters, Natural Gas Intelligence, Google News, and more
- **Smart relevance scoring** â Every article scored by company mentions, basin/region matches, and category keywords, with extra weight for compression-related content
- **React dashboard** â Dark-themed SPA with search, filtering by category and company, and sortable results
- **Background scheduling** â Scrapes automatically every 12 hours (configurable)
- **"Scan Now" button** â Trigger a fresh scrape from the dashboard anytime
- **Live status** â Watch scraping progress in real-time

## Quick Deploy

### Render (Recommended â Free Tier)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) â New â Web Service
3. Connect your GitHub repo
4. Render auto-detects the `render.yaml` â click Deploy

### Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) â New Project â Deploy from GitHub
3. Select your repo â Railway auto-detects `railway.json`

### Docker

```bash
docker build -t permian-tracker .
docker run -p 5000:5000 permian-tracker
```

### Local

```bash
pip install -r requirements.txt
python app.py
```

Opens automatically at `http://localhost:5000`

## Configuration

Edit `config.py` to customize:

- **COMPANIES** â Target upstream and midstream operators
- **BASINS / REGIONS** â Geographic focus areas
- **CATEGORIES** â Keyword categories and relevance weights
- **RSS_FEEDS** â News sources to scrape
- **SCORE_WEIGHTS** â How different match types are weighted

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5000` | Server port |
| `SCRAPE_INTERVAL_HOURS` | `12` | Hours between automatic scrapes |
| `SECRET_KEY` | (generated) | Flask secret key |

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard UI |
| `/api/articles` | GET | All scored articles (JSON) |
| `/api/stats` | GET | Summary statistics |
| `/api/config` | GET | Current tracker configuration |
| `/api/status` | GET | Scraper status (running/idle) |
| `/api/scrape` | POST | Trigger a new scrape |

## Project Structure

```
permian-news-tracker/
âââ app.py              # Main application (Flask + scraper + scheduler)
âââ config.py           # Companies, keywords, sources, scoring
âââ dashboard.html      # React SPA (single file, no build step)
âââ requirements.txt    # Python dependencies
âââ Procfile            # Heroku/Render process definition
âââ render.yaml         # Render deploy config
âââ railway.json        # Railway deploy config
âââ Dockerfile          # Container build
âââ start.bat           # Windows one-click launcher
âââ data/               # Scraped article storage (gitignored)
```
