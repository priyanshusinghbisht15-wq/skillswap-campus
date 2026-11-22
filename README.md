# SkillSwap Campus

> **Your skills are someone else's next breakthrough.**

A peer-to-peer skill exchange platform for college students — built for hackathons, scaled for campus.

---

## 🚀 Features

- **Authentication & Registration** — Secure student login, onboarding registration, and 1-click quick demo switcher
- **Video Study Room & Live Calls** — Built-in WebRTC video conferencing (Jitsi Meet) with live collaborative notes, whiteboard, timer, and teach-back takeaways
- **Intelligent Matchmaking** — Multi-factor match scores: 50% skill compatibility, 20% experience level, 20% shared free time, 10% partner ratings
- **Skill Swap Chains** — Directed graph cycle detection (DFS) discovers circular skill exchange loops (A→B→C→A)
- **Session Management** — Request, accept, join video calls, complete, and rate teaching/learning sessions
- **Session Notes & Teach-Back Verification** — Live shared notes during calls and verified learning badge confirmations
- **Learning Roadmaps** — Structured 4-stage paths (Web Dev, Data Science, UX/Design) with mentor discovery
- **Skill Heatmap** — Campus-wide supply vs. demand Chart.js visualization with demand-gap analysis
- **Achievements & XP** — Gamified progression system with 5 levels, badges, and campus leaderboard
- **Learning Reports** — Downloadable per-student text summary reports
- **Demo Mode** — 1-click switcher between 8 pre-seeded students with pre-configured sessions, badges, and ratings

---

## 🛠 Tech Stack

| Layer     | Technology                                  |
|-----------|---------------------------------------------|
| Backend   | Python Flask, Flask-SQLAlchemy, Werkzeug    |
| Database  | SQLite (Local persistent database)          |
| Video     | Jitsi Meet External API (WebRTC, Free, No API key) |
| Frontend  | HTML5, CSS3, Vanilla JavaScript             |
| Charts    | Chart.js (CDN)                              |
| Icons     | Lucide Icons (CDN)                          |

---

## 📦 Setup

```bash
# 1. Navigate to project directory
cd skillswap-campus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run unit test suite (30 unit tests)
python tests.py

# 4. Run the application
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## 🎮 Demo Credentials

All seeded accounts can be signed in with **1 click** from the login page or sidebar, or using:
- **Default password**: `password123`
- **Sample accounts**:
  - `asha@campus.edu` (Asha Patel — CS Year 3)
  - `ben@campus.edu` (Ben Carter — Design Year 2)
  - `chitra@campus.edu` (Chitra Nair — CS Year 2)
  - `dev@campus.edu` (Dev Sharma — CS Year 4)

---

## 🏗 Architecture

```
skillswap-campus/
├── app.py              # Flask app, routes, models, algorithms, seed data
├── requirements.txt    # Python dependencies
├── tests.py            # 30 Unit tests (algorithms, routes, auth, video call)
├── static/
│   ├── style.css       # Complete dark-theme design system & video call UI
│   └── main.js         # Frontend interactivity, Jitsi initialization & whiteboard
└── templates/
    ├── base.html       # Layout: sidebar + topbar + auth status
    ├── login.html      # Modern login page with 1-click demo accounts
    ├── register.html   # Student onboarding form with skills setup
    ├── call.html       # Video call screen with side-by-side workspace
    ├── dashboard.html  # Hero, statistics, matches, upcoming sessions
    ├── profile.html    # Profile view with availability grid
    ├── edit_profile.html
    ├── find_partners.html # Match score breakdowns & filter
    ├── chains.html     # Circular skill swap cycle diagram & explanation
    ├── sessions.html   # Scheduled sessions with direct call button
    ├── notes.html      # Shared notes & teach-back submissions
    ├── roadmaps.html   # 3 curated learning paths & mentor cards
    ├── heatmap.html    # Chart.js horizontal bar chart & skill gap list
    ├── achievements.html # Badges, levels, XP guide, leaderboard
    ├── report.html     # Learning report view & text download
    └── error.html
```

---

## 🧠 Algorithms

### Match Score (0–100)
```
Total = 0.50 × skill_compatibility
      + 0.20 × level_match
      + 0.20 × shared_availability
      + 0.10 × partner_rating
```

### Skill Swap Chain Detection
Uses **depth-first search (DFS)** on a directed skill-offer graph to find all simple cycles of length 3–5. Cycles are deduplicated by canonical form.

---

## 🧪 Tests

```bash
python tests.py
```

Tests cover: match score calculation, chain detection, overlap hours, badge awarding, and all major routes.

---

## 🌐 URL

**http://localhost:5000**

---

*Built with ❤️ for the college hackathon — SkillSwap Campus 2024*
