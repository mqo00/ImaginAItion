# ImaginAItion

A multiplayer web game for studying how people prompt text-to-image models.
Players are shown a reference image, write a prompt to recreate it with an AI
image generator, and vote on each other's results across several themed rounds.

Built as a research platform: gameplay events (prompts, votes, generated images)
can be logged for later analysis.

## Stack

- **Backend:** FastAPI + Socket.IO (Python)
- **Frontend:** React + Vite + Tailwind CSS
- **Image generation:** OpenAI API — **each room provides its own API key at runtime**
  (no key is bundled with the project)

## Quick Start (Docker)

```bash
docker compose up --build
```

The app is served on a single port via an Nginx reverse proxy. For a
production-style build:

```bash
cp .env.example .env   # then edit values for your deployment
docker compose -f docker-compose.prod.yml up -d
```

## Local Development

| Task | Command |
| --- | --- |
| Frontend | `cd frontend && npm install && npm run dev` |
| Backend  | `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --host 0.0.0.0 --port 5001 --reload` |

You may need to do `conda deactivate` and rerun `uvicorn main:app --host 0.0.0.0 --port 5001 --reload` if you run into ModuleNotFoundError in backend. 

## Configuration

Environment variables (see `.env.example`):

- `BACKEND_URL` — public base URL of the deployment
- `VITE_API_URL` — frontend API base (leave empty to use Nginx relative paths)
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — credentials for the admin log-export
  dashboard. Set these to strong values before any public deployment.

By default each player supplies their own key in the UI; if you'd rather host the game with a single server-side key, you should adapt the system.  

## Admin / Data Export

An admin dashboard (`/admin`) allows exporting collected game logs for analysis.
Access is gated by the `ADMIN_USERNAME` / `ADMIN_PASSWORD` environment variables.

## 👥 Contributors

- **Megan Chai** — Designer ([LinkedIn](https://www.linkedin.com/in/megan-chai/))
- **Yike Tan (LikeGiver)** — Developer ([GitHub](https://github.com/LikeGiver))
- **Jihun Choi (cjh1212)** — Developer ([GitHub](https://github.com/cjh1212))
