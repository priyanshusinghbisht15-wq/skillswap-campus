# ⚡ SkillSwap Campus
> *"Your skills are someone else's next breakthrough."*

SkillSwap Campus is a full-stack web application designed for campus hackathons that enables university students to exchange skills through peer-to-peer mentorship. Rather than relying on monetary transactions, students teach skills they already master in exchange for skills they want to learn.

---

## 🌟 Key Standout Features

### 1. 🔄 Skill Swap Chains (Signature Feature)
When direct 1-to-1 skill matches aren't available, SkillSwap Campus employs a **directed graph cycle detection algorithm** to identify multi-student circular knowledge exchanges of length 3 or greater.
- **Example:**
  - **Asha** teaches *Python* to **Ben**
  - **Ben** teaches *UI/UX Design* to **Chitra**
  - **Chitra** teaches *Data Structures & Algorithms* to **Asha**
- Renders an interactive circular SVG graph with curved arrows, participant avatars, and transferred skill badges.
- Automatically eliminates duplicate permutations using canonical minimum-rotation indexing.

### 2. 🎯 Smart Matchmaking & Transparent Match Score
Calculates peer compatibility dynamically based on 4 normalized components:
- **Two-way Skill Compatibility (50%):** Evaluates skills the user wants that the partner teaches, plus reciprocal teaching potential.
- **Experience Level Alignment (20%):** Compares mentor vs. learner proficiency tiers (Beginner, Intermediate, Advanced).
- **Shared Free Time Overlap (20%):** Computes exact overlapping weekly calendar intervals.
- **Partner Rating (10%):** Reflects authentic peer star reviews.

### 3. 🔥 Campus Skill Heatmap
- Horizontal comparative bar chart powered by **Chart.js** displaying campus-wide skill supply (students offering) vs. demand (students seeking).
- Ranked skill-gap list highlighting critical mentor deficits (e.g., severe shortages in Machine Learning and UI/UX Design).

### 4. 🕒 Free-Slot Finder
- Compares weekly schedules between two students.
- Identifies exact overlapping time windows and allows one-click session booking directly into that shared free window.

### 5. 🗺️ Goal-Based Learning Roadmaps
- Multi-stage learning paths (e.g. *Full-Stack Web Development*, *Machine Learning Practitioner*, *Modern UI/UX Product Design*).
- Displays campus mentors qualified to teach each milestone stage.

### 6. 💡 Teach-Back & Verification Loop
- Post-session active recall: Learners submit 2-3 key takeaways.
- Mentors review and verify takeaways to award the **Verified Scholar** badge and bonus XP.

### 7. 🏆 Gamification & Badges
- Progression system from Level 1 to Level 5 with XP rewards for sessions, teach-backs, and 5-star ratings.
- Real verifiable badges: *First Exchange*, *5-Star Mentor*, *Polyglot Learner*, *Streak Champion*, and *Verified Scholar*.

### 8. 📄 Official Learning Report
- Formatted transcript summarizing teaching hours given, learning hours received, ratings, and competencies.
- One-click print/PDF layout and downloadable JSON & Text exports.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.14 / Flask
- **Database & ORM:** SQLite with SQLAlchemy / Flask-SQLAlchemy
- **Frontend:** Semantic HTML5, Custom Modern CSS3 Design System, Vanilla JavaScript (ES6+)
- **Data Visualization:** Chart.js
- **Styling:** Electric violet & deep navy startup theme, responsive layouts for laptop & mobile.

---

## 🚀 Setup and Run Instructions

### 1. Prerequisites
Python 3.10+ installed on your machine.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Demo Data (Optional - automatic on first run)
```bash
python seed_data.py
```

### 4. Run the Application
```bash
python app.py
```

### 5. Access the Web Application
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Running Unit Tests

Unit tests are included for the matchmaking score calculation and cycle detection:
```bash
python -m unittest tests/test_algorithms.py
```

---

## 👥 Demo Profiles Included
The topbar includes a one-click student switcher allowing judges to immediately test features from any student's perspective:
1. **Asha Patel** (3rd Year, Computer Science) — Python Mentor, learning UI/UX.
2. **Ben Schneider** (2nd Year, Product Design) — UI/UX Mentor, learning Python & DSA.
3. **Chitra Raman** (3rd Year, Data Science) — DSA Mentor, learning Python & UI/UX.
4. **David Kim** (4th Year, Software Engineering) — React & Frontend Mentor.
5. **Elena Rostova** (Postgrad, Artificial Intelligence) — Machine Learning Mentor.
6. **Farhan Ali** (2nd Year, Cybersecurity) — Security Mentor.
7. **Grace Chen** (1st Year, Cognitive Science) — HTML/CSS Learner.
8. **Harsh Vardhan** (3rd Year, Quantitative Finance) — Tableau Mentor.
