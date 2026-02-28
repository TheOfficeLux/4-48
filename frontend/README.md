# Learning Buddy — Frontend

Child-friendly Next.js app for the Adaptive Learning RAG API.

## Run

1. **API running**  
   Backend at `http://localhost:8000` (or set `NEXT_PUBLIC_API_URL` in `.env.local`).

2. **Install and dev**
   ```bash
   npm install
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000).

## What’s included

- **Auth:** Sign in, Create account (JWT stored in `localStorage`).
- **Dashboard:** List learners, add a learner (name + date of birth).
- **Child profile:** Summary and links to **Start learning** and **See progress**.
- **Learn:** Start session → chat-style Q&A (Ask → response from RAG). Optional “Good” / “Need help” reactions (sent as signals). End session when done.
- **Progress:** Overview (sessions, interactions), Mastery by topic, Timeline (last 30 days), Caregiver report, Review queue (due topics).

## Child-friendly design

- Large buttons and inputs (min 44px height where it matters).
- Soft colours (sky blue, mint, peach).
- Nunito font, rounded corners, simple layout.
- Clear labels and short copy.

## Env

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | API base URL (default `http://localhost:8000`) |

Copy `.env.local.example` to `.env.local` and change if needed.
