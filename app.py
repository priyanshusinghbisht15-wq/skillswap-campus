# =============================================================================
# SkillSwap Campus — app.py
# =============================================================================

import os
import json
from datetime import datetime, date, timedelta
from collections import defaultdict
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_file
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import io

# ─── App & DB config ───────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
application = app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'skillswap-secret-2024-campus')

if os.environ.get('VERCEL'):
    db_path = os.path.join('/tmp', 'skillswap.db')
else:
    db_path = os.path.join(BASE_DIR, 'skillswap.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── MODELS ────────────────────────────────────────────────────────────────

class Student(db.Model):
    __tablename__ = 'students'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    avatar_color  = db.Column(db.String(20), default='#7c3aed')
    course        = db.Column(db.String(100))
    year          = db.Column(db.Integer)
    bio           = db.Column(db.Text)
    xp            = db.Column(db.Integer, default=0)
    level         = db.Column(db.Integer, default=1)
    streak_weeks  = db.Column(db.Integer, default=0)

    skills        = db.relationship('StudentSkill', backref='student', lazy=True, cascade='all,delete-orphan')
    availabilities= db.relationship('Availability',  backref='student', lazy=True, cascade='all,delete-orphan')
    badges        = db.relationship('Badge',         backref='student', lazy=True, cascade='all,delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def initials(self):
        parts = self.name.split()
        return ''.join(p[0] for p in parts[:2]).upper()

    def xp_to_next_level(self):
        thresholds = [0, 200, 500, 1000, 2000, 999999]
        current = thresholds[self.level - 1]
        next_t  = thresholds[self.level]
        return next_t - self.xp, next_t - current

    def level_progress_pct(self):
        thresholds = [0, 200, 500, 1000, 2000, 999999]
        current = thresholds[self.level - 1]
        next_t  = thresholds[self.level]
        return round((self.xp - current) / (next_t - current) * 100, 1)


class Skill(db.Model):
    __tablename__ = 'skills'
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))


class StudentSkill(db.Model):
    __tablename__ = 'student_skills'
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id    = db.Column(db.Integer, db.ForeignKey('skills.id'),   nullable=False)
    skill_type  = db.Column(db.String(10), nullable=False)   # 'offer' | 'want'
    proficiency = db.Column(db.String(20), default='Beginner')  # Beginner/Intermediate/Advanced

    skill       = db.relationship('Skill')


class Availability(db.Model):
    __tablename__ = 'availabilities'
    id          = db.Column(db.Integer, primary_key=True)
    student_id  = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)   # 0=Mon … 6=Sun
    start_hour  = db.Column(db.Integer, nullable=False)
    end_hour    = db.Column(db.Integer, nullable=False)


class Session(db.Model):
    __tablename__ = 'sessions'
    id               = db.Column(db.Integer, primary_key=True)
    teacher_id       = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    learner_id       = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id         = db.Column(db.Integer, db.ForeignKey('skills.id'),   nullable=False)
    date             = db.Column(db.String(20))
    start_time       = db.Column(db.String(10))
    duration_minutes = db.Column(db.Integer, default=60)
    format           = db.Column(db.String(20), default='Online')   # Online | In-Person
    status           = db.Column(db.String(20), default='pending')  # pending/accepted/completed/cancelled
    notes            = db.Column(db.Text, default='')
    room_id          = db.Column(db.String(100), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    teacher  = db.relationship('Student', foreign_keys=[teacher_id])
    learner  = db.relationship('Student', foreign_keys=[learner_id])
    skill    = db.relationship('Skill')
    ratings  = db.relationship('Rating',   backref='session', lazy=True, cascade='all,delete-orphan')
    takeaways= db.relationship('Takeaway', backref='session', lazy=True, cascade='all,delete-orphan')

    def get_room_id(self):
        if not self.room_id:
            import hashlib
            raw = f"SkillSwap-Campus-Session-{self.id}"
            return "SkillSwap-" + hashlib.md5(raw.encode()).hexdigest()[:10]
        return self.room_id


class Rating(db.Model):
    __tablename__ = 'ratings'
    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    rater_id   = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    ratee_id   = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    stars      = db.Column(db.Integer, nullable=False)
    comment    = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    rater = db.relationship('Student', foreign_keys=[rater_id])
    ratee = db.relationship('Student', foreign_keys=[ratee_id])


class Badge(db.Model):
    __tablename__ = 'badges'
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)
    earned_at  = db.Column(db.DateTime, default=datetime.utcnow)


class Takeaway(db.Model):
    __tablename__ = 'takeaways'
    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    confirmed  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    learner = db.relationship('Student', foreign_keys=[learner_id])


# ─── BADGE DEFINITIONS ─────────────────────────────────────────────────────
BADGE_INFO = {
    'first_session':     {'label': 'First Session',      'icon': '🎯', 'description': 'Complete your first session', 'xp': 100},
    'five_star_teacher': {'label': 'Five-Star Teacher',  'icon': '⭐', 'description': 'Maintain 4.8+ avg rating with 2+ ratings', 'xp': 150},
    'polyglot_learner':  {'label': 'Polyglot Learner',   'icon': '🌐', 'description': 'Learn 3+ distinct skills', 'xp': 200},
    'mentor_streak':     {'label': 'Mentor Streak',      'icon': '🔥', 'description': 'Complete 3+ teaching sessions', 'xp': 150},
    'verified_learning': {'label': 'Verified Learning',  'icon': '✅', 'description': 'Have 3 takeaways confirmed by teachers', 'xp': 100},
}

# ─── HELPERS ───────────────────────────────────────────────────────────────

def get_current_student():
    if session.get('logged_out'):
        return None
    student_id = session.get('student_id')
    if student_id:
        student = db.session.get(Student, student_id)
        if student:
            return student
    # Fallback to first student for seamless testing and initial demo
    student = Student.query.first()
    if student and not session.get('logged_out'):
        session['student_id'] = student.id
        return student
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current = get_current_student()
        if not current:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def calculate_overlap_hours(student_a, student_b):
    total_overlap = 0
    for av_a in student_a.availabilities:
        for av_b in student_b.availabilities:
            if av_a.day_of_week == av_b.day_of_week:
                overlap_start = max(av_a.start_hour, av_b.start_hour)
                overlap_end   = min(av_a.end_hour,   av_b.end_hour)
                if overlap_end > overlap_start:
                    total_overlap += overlap_end - overlap_start
    return total_overlap


def calculate_match_score(student_a, student_b):
    PROF_LEVEL = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}

    a_offers = {ss.skill_id: ss.proficiency for ss in student_a.skills if ss.skill_type == 'offer'}
    a_wants  = {ss.skill_id for ss in student_a.skills if ss.skill_type == 'want'}
    b_offers = {ss.skill_id: ss.proficiency for ss in student_b.skills if ss.skill_type == 'offer'}
    b_wants  = {ss.skill_id for ss in student_b.skills if ss.skill_type == 'want'}

    # 1. Two-way skill compatibility (50%)
    a_can_teach_b = a_offers.keys() & b_wants
    b_can_teach_a = b_offers.keys() & a_wants
    total_possible = max(len(a_offers) + len(b_offers), 1)
    raw_skill = (len(a_can_teach_b) + len(b_can_teach_a)) / total_possible
    skill_score = min(raw_skill * 100, 100)

    # 2. Level compatibility (20%)
    level_scores = []
    for sk_id in a_can_teach_b:
        teacher_level = PROF_LEVEL.get(a_offers[sk_id], 1)
        diff = teacher_level - 1  # teacher vs beginner learner
        level_scores.append(min(diff / 2 * 100, 100))
    for sk_id in b_can_teach_a:
        teacher_level = PROF_LEVEL.get(b_offers[sk_id], 1)
        diff = teacher_level - 1
        level_scores.append(min(diff / 2 * 100, 100))
    level_score = sum(level_scores) / len(level_scores) if level_scores else 50

    # 3. Shared availability (20%)
    overlap_hours  = calculate_overlap_hours(student_a, student_b)
    avail_score    = min(overlap_hours, 10) / 10 * 100

    # 4. Partner rating (10%)
    ratings = Rating.query.filter_by(ratee_id=student_b.id).all()
    if ratings:
        avg_rating = sum(r.stars for r in ratings) / len(ratings)
        rating_score = (avg_rating / 5) * 100
    else:
        rating_score = 60.0

    total = 0.50 * skill_score + 0.20 * level_score + 0.20 * avail_score + 0.10 * rating_score

    reasons = []
    if a_can_teach_b:
        skill_names = [Skill.query.get(sid).name for sid in a_can_teach_b]
        reasons.append(f"You can teach: {', '.join(skill_names)}")
    if b_can_teach_a:
        skill_names = [Skill.query.get(sid).name for sid in b_can_teach_a]
        reasons.append(f"They can teach you: {', '.join(skill_names)}")
    if overlap_hours > 0:
        reasons.append(f"{overlap_hours}h shared availability per week")
    if ratings:
        reasons.append(f"Avg rating: {avg_rating:.1f}/5 ({len(ratings)} reviews)")

    return {
        'total':        round(total, 1),
        'skill':        round(skill_score, 1),
        'level':        round(level_score, 1),
        'availability': round(avail_score, 1),
        'rating':       round(rating_score, 1),
        'reasons':      reasons,
        'a_teaches_b':  [Skill.query.get(sid).name for sid in a_can_teach_b],
        'b_teaches_a':  [Skill.query.get(sid).name for sid in b_can_teach_a],
    }


def find_skill_swap_chains(max_length=5):
    """Find all simple cycles of length 3..max_length in the skill-offer graph."""
    students = Student.query.all()

    # Build adjacency: student_id → [(target_id, skill_name)]
    adjacency = defaultdict(list)
    for s in students:
        s_offers = {ss.skill_id: ss.skill.name for ss in s.skills if ss.skill_type == 'offer'}
        for t in students:
            if t.id == s.id:
                continue
            t_wants = {ss.skill_id for ss in t.skills if ss.skill_type == 'want'}
            matching = s_offers.keys() & t_wants
            for sk_id in matching:
                adjacency[s.id].append((t.id, s_offers[sk_id]))

    student_map = {s.id: s for s in students}
    chains = []
    seen_chains = set()

    def dfs(path, path_skills, start_id):
        current = path[-1]
        if len(path) >= 3:
            # Check if we can close the cycle back to start
            for (nxt, skill) in adjacency.get(current, []):
                if nxt == start_id:
                    # Found a cycle — build steps: each node teaches the next
                    canonical = tuple(sorted(path))
                    if canonical not in seen_chains:
                        seen_chains.add(canonical)
                        # path = [A, B, C], path_skills = [skill_A_teaches, skill_B_teaches]
                        # closing: C teaches `skill` back to A
                        full_path   = path + [start_id]
                        full_skills = path_skills + [skill]
                        chain_steps = []
                        for i in range(len(path)):
                            chain_steps.append({
                                'from_student': student_map[full_path[i]],
                                'to_student':   student_map[full_path[i + 1]],
                                'skill':        full_skills[i],
                            })
                        chains.append({
                            'length': len(path),
                            'steps':  chain_steps,
                        })
        if len(path) < max_length:
            for (nxt, skill) in adjacency.get(current, []):
                if nxt not in path and nxt != start_id:
                    dfs(path + [nxt], path_skills + [skill], start_id)

    for s in students:
        for (nxt, skill) in adjacency.get(s.id, []):
            if nxt != s.id:
                dfs([s.id, nxt], [skill], s.id)

    # Sort by chain length
    chains.sort(key=lambda c: c['length'])
    return chains


def award_badge_if_not_exists(student_id, badge_type):
    existing = Badge.query.filter_by(student_id=student_id, badge_type=badge_type).first()
    if not existing:
        badge = Badge(student_id=student_id, badge_type=badge_type)
        db.session.add(badge)
        xp_gain = BADGE_INFO.get(badge_type, {}).get('xp', 50)
        update_xp(student_id, xp_gain)
        db.session.commit()
        return True
    return False


def update_xp(student_id, points):
    student = Student.query.get(student_id)
    if student:
        student.xp += points
        # Update level
        thresholds = [0, 200, 500, 1000, 2000]
        for i, t in enumerate(thresholds):
            if student.xp >= t:
                student.level = i + 1
        db.session.commit()


def check_and_award_badges(student_id):
    # First Session
    completed = Session.query.filter(
        db.or_(Session.teacher_id == student_id, Session.learner_id == student_id),
        Session.status == 'completed'
    ).count()
    if completed >= 1:
        award_badge_if_not_exists(student_id, 'first_session')

    # Mentor Streak — 3+ teaching sessions completed
    taught = Session.query.filter_by(teacher_id=student_id, status='completed').count()
    if taught >= 3:
        award_badge_if_not_exists(student_id, 'mentor_streak')

    # Five-Star Teacher
    ratings = Rating.query.filter_by(ratee_id=student_id).all()
    if ratings:
        avg = sum(r.stars for r in ratings) / len(ratings)
        if avg >= 4.8 and len(ratings) >= 2:
            award_badge_if_not_exists(student_id, 'five_star_teacher')

    # Polyglot Learner — 3+ distinct skills learned
    learned = Session.query.filter_by(learner_id=student_id, status='completed')\
        .with_entities(Session.skill_id).distinct().count()
    if learned >= 3:
        award_badge_if_not_exists(student_id, 'polyglot_learner')

    # Verified Learning — 3+ confirmed takeaways
    confirmed = Takeaway.query.filter_by(learner_id=student_id, confirmed=True).count()
    if confirmed >= 3:
        award_badge_if_not_exists(student_id, 'verified_learning')


# ─── SEED DATA ─────────────────────────────────────────────────────────────

def seed_database():
    if Student.query.first():
        return  # Already seeded

    # Skills
    skills_data = [
        ('Python',             'Programming'),
        ('Data Structures',    'Programming'),
        ('UI Design',          'Design'),
        ('Figma',              'Design'),
        ('Java',               'Programming'),
        ('Machine Learning',   'Data Science'),
        ('Public Speaking',    'Communication'),
        ('Writing',            'Communication'),
        ('Photography',        'Creative'),
        ('Illustrator',        'Design'),
        ('Web Dev',            'Programming'),
        ('Flask',              'Programming'),
        ('Excel',              'Productivity'),
        ('Business Analytics', 'Business'),
        ('Pandas',             'Data Science'),
        ('Deep Learning',      'Data Science'),
    ]
    skill_map = {}
    for name, cat in skills_data:
        sk = Skill(name=name, category=cat)
        db.session.add(sk)
        db.session.flush()
        skill_map[name] = sk.id

    # Students
    students_data = [
        # name, email, password, avatar_color, course, year, bio, xp, level, streak
        ('Asha Patel',   'asha@campus.edu',   'password123', '#7c3aed', 'Computer Science',  3, 'Passionate CS student who loves algorithms and open-source. Looking to bridge the gap between code and design.',           350, 2, 4),
        ('Ben Carter',   'ben@campus.edu',    'password123', '#3b82f6', 'Design',             2, 'Creative UI/UX designer with a love for clean interfaces. Eager to learn programming to prototype faster.',              220, 2, 2),
        ('Chitra Nair',  'chitra@campus.edu', 'password123', '#06b6d4', 'Computer Science',  2, 'Sophomore CS student building strong fundamentals. Passionate about the intersection of art and technology.',             180, 1, 1),
        ('Dev Sharma',   'dev@campus.edu',    'password123', '#10b981', 'Computer Science',  4, 'Final year ML researcher. Presenting my thesis on neural architecture search. Public speaking is my next frontier.',      600, 3, 6),
        ('Elan Torres',  'elan@campus.edu',   'password123', '#f59e0b', 'Communications',    3, 'Debate champion and tech enthusiast. Bridging the gap between technical concepts and compelling narratives.',             290, 2, 3),
        ('Farah Khan',   'farah@campus.edu',  'password123', '#ef4444', 'Design',             1, 'First-year design student with a passion for visual storytelling. Photography is my first language.',                   90,  1, 1),
        ('Gita Rao',     'gita@campus.edu',   'password123', '#8b5cf6', 'Computer Science',  3, 'Full-stack developer building campus tools. Looking to level up in ML and collaborate on cross-disciplinary projects.',  450, 3, 5),
        ('Hiro Tanaka',  'hiro@campus.edu',   'password123', '#ec4899', 'Business',           2, 'Business student leveraging data analytics. Bridging business strategy with technical implementation.',                  160, 1, 2),
    ]
    student_objs = []
    for name, email, pwd, color, course, year, bio, xp, lvl, streak in students_data:
        s = Student(name=name, email=email, avatar_color=color, course=course, year=year, bio=bio, xp=xp, level=lvl, streak_weeks=streak)
        s.set_password(pwd)
        db.session.add(s)
        db.session.flush()
        student_objs.append(s)

    # Aliases for readability
    asha, ben, chitra, dev, elan, farah, gita, hiro = student_objs

    # StudentSkills
    skill_entries = [
        # Asha — offers Python(Adv), Data Structures(Adv) | wants UI Design, Data Structures(refresh)
        (asha.id,   'Python',             'offer', 'Advanced'),
        (asha.id,   'Data Structures',    'offer', 'Advanced'),
        (asha.id,   'UI Design',          'want',  'Beginner'),
        (asha.id,   'Photography',        'want',  'Beginner'),
        (asha.id,   'Data Structures',    'want',  'Intermediate'),  # refresh — enables chain C→A

        # Ben — offers UI Design(Adv), Figma(Int) | wants Python, Data Structures
        (ben.id,    'UI Design',          'offer', 'Advanced'),
        (ben.id,    'Figma',              'offer', 'Intermediate'),
        (ben.id,    'Python',             'want',  'Beginner'),
        (ben.id,    'Data Structures',    'want',  'Beginner'),

        # Chitra — offers Data Structures(Int), Java(Int) | wants Python, UI Design
        (chitra.id, 'Data Structures',    'offer', 'Intermediate'),
        (chitra.id, 'Java',               'offer', 'Intermediate'),
        (chitra.id, 'Python',             'want',  'Beginner'),
        (chitra.id, 'UI Design',          'want',  'Beginner'),

        # Dev — offers ML(Adv), Python(Int) | wants UI Design, Public Speaking, Business Analytics
        (dev.id,    'Machine Learning',   'offer', 'Advanced'),
        (dev.id,    'Python',             'offer', 'Intermediate'),
        (dev.id,    'UI Design',          'want',  'Beginner'),
        (dev.id,    'Public Speaking',    'want',  'Beginner'),
        (dev.id,    'Business Analytics', 'want',  'Beginner'),

        # Elan — offers Public Speaking(Adv), Writing(Adv) | wants Python, Machine Learning
        (elan.id,   'Public Speaking',    'offer', 'Advanced'),
        (elan.id,   'Writing',            'offer', 'Advanced'),
        (elan.id,   'Python',             'want',  'Beginner'),
        (elan.id,   'Machine Learning',   'want',  'Beginner'),

        # Farah — offers Photography(Int), Illustrator(Beg) | wants Python, Figma
        (farah.id,  'Photography',        'offer', 'Intermediate'),
        (farah.id,  'Illustrator',        'offer', 'Beginner'),
        (farah.id,  'Python',             'want',  'Beginner'),
        (farah.id,  'Figma',              'want',  'Beginner'),

        # Gita — offers Web Dev(Adv), Flask(Int) | wants Machine Learning, UI Design, Public Speaking
        (gita.id,   'Web Dev',            'offer', 'Advanced'),
        (gita.id,   'Flask',              'offer', 'Intermediate'),
        (gita.id,   'Machine Learning',   'want',  'Beginner'),
        (gita.id,   'UI Design',          'want',  'Beginner'),
        (gita.id,   'Public Speaking',    'want',  'Beginner'),

        # Hiro — offers Excel(Adv), Business Analytics(Int) | wants Python, Web Dev
        (hiro.id,   'Excel',              'offer', 'Advanced'),
        (hiro.id,   'Business Analytics', 'offer', 'Intermediate'),
        (hiro.id,   'Python',             'want',  'Beginner'),
        (hiro.id,   'Web Dev',            'want',  'Beginner'),
    ]
    for sid, sname, stype, prof in skill_entries:
        db.session.add(StudentSkill(student_id=sid, skill_id=skill_map[sname], skill_type=stype, proficiency=prof))

    # Availabilities (day 0=Mon, hours 24h)
    avail_data = [
        # Asha: Mon,Wed,Fri 14-18
        (asha.id,   0, 14, 18),
        (asha.id,   2, 14, 18),
        (asha.id,   4, 10, 14),
        # Ben: Mon,Tue 10-14, Thu 14-18
        (ben.id,    0, 10, 14),
        (ben.id,    1, 10, 14),
        (ben.id,    3, 14, 18),
        # Chitra: Wed,Thu 10-14
        (chitra.id, 2, 10, 14),
        (chitra.id, 3, 10, 14),
        # Dev: Mon-Fri 18-21
        (dev.id,    0, 18, 21),
        (dev.id,    1, 18, 21),
        (dev.id,    2, 18, 21),
        (dev.id,    3, 18, 21),
        (dev.id,    4, 18, 21),
        # Elan: Tue,Thu 14-17
        (elan.id,   1, 14, 17),
        (elan.id,   3, 14, 17),
        # Farah: Sat,Sun 10-16
        (farah.id,  5, 10, 16),
        (farah.id,  6, 10, 16),
        # Gita: Mon,Wed 10-13, Fri 14-18
        (gita.id,   0, 10, 13),
        (gita.id,   2, 10, 13),
        (gita.id,   4, 14, 18),
        # Hiro: Mon,Tue,Thu 12-16
        (hiro.id,   0, 12, 16),
        (hiro.id,   1, 12, 16),
        (hiro.id,   3, 12, 16),
    ]
    for sid, day, sh, eh in avail_data:
        db.session.add(Availability(student_id=sid, day_of_week=day, start_hour=sh, end_hour=eh))

    db.session.flush()

    # Sessions
    sessions_data = [
        # teacher_id, learner_id, skill_name, date, time, dur, fmt, status
        (asha.id,  ben.id,   'Python',           '2024-10-01', '14:00', 90,  'Online',    'completed'),
        (ben.id,   chitra.id,'UI Design',         '2024-10-05', '10:00', 60,  'In-Person', 'completed'),
        (dev.id,   elan.id,  'Machine Learning',  '2024-10-20', '18:00', 120, 'Online',    'accepted'),
        (gita.id,  hiro.id,  'Web Dev',           '2024-10-22', '10:00', 60,  'Online',    'pending'),
        (asha.id,  chitra.id,'Python',            '2024-09-15', '14:00', 60,  'Online',    'completed'),
        (elan.id,  dev.id,   'Public Speaking',   '2024-10-10', '18:00', 90,  'In-Person', 'completed'),
        (gita.id,  ben.id,   'Web Dev',           '2024-10-25', '10:00', 60,  'Online',    'pending'),
        (dev.id,   gita.id,  'Machine Learning',  '2024-10-28', '19:00', 90,  'Online',    'accepted'),
    ]
    sess_objs = []
    for tid, lid, sname, dt, tm, dur, fmt, status in sessions_data:
        s = Session(
            teacher_id=tid, learner_id=lid, skill_id=skill_map[sname],
            date=dt, start_time=tm, duration_minutes=dur, format=fmt, status=status,
            notes='Session notes will appear here after completion.'
        )
        db.session.add(s)
        db.session.flush()
        sess_objs.append(s)

    # Ratings for completed sessions
    ratings_data = [
        (sess_objs[0].id, ben.id,    asha.id,   5, 'Asha explained Python concepts brilliantly! Best teacher ever.'),
        (sess_objs[0].id, asha.id,   ben.id,    4, 'Ben was engaged and asked great questions.'),
        (sess_objs[1].id, chitra.id, ben.id,    4, 'Ben made UI Design approachable and fun.'),
        (sess_objs[1].id, ben.id,    chitra.id, 5, 'Chitra picked up concepts quickly and was very enthusiastic.'),
        (sess_objs[4].id, chitra.id, asha.id,   5, 'Fantastic session on Python basics. Highly recommend!'),
        (sess_objs[5].id, dev.id,    elan.id,   5, 'Elan transformed my public speaking. Incredible session.'),
        (sess_objs[5].id, elan.id,   dev.id,    4, 'Dev is clearly an expert who learns fast.'),
    ]
    for sid, rid, raid, stars, comment in ratings_data:
        db.session.add(Rating(session_id=sid, rater_id=rid, ratee_id=raid, stars=stars, comment=comment))

    # Takeaways
    takeaways_data = [
        (sess_objs[0].id, ben.id,   'Learned list comprehensions, decorators, and how to write Pythonic code. Next step: build a small Flask project.', True),
        (sess_objs[1].id, chitra.id,'Understood the 8-point grid system and component hierarchy. Going to redesign my project UI using Figma.', True),
        (sess_objs[4].id, chitra.id,'Grasped loops, functions, and OOP basics. Planning to solve 5 LeetCode problems this week.', True),
    ]
    for sid, lid, content, confirmed in takeaways_data:
        db.session.add(Takeaway(session_id=sid, learner_id=lid, content=content, confirmed=confirmed))

    # Badges (seed some for demo)
    badges_seed = [
        (asha.id,  'first_session'),
        (asha.id,  'mentor_streak'),
        (asha.id,  'five_star_teacher'),
        (ben.id,   'first_session'),
        (chitra.id,'first_session'),
        (dev.id,   'first_session'),
        (dev.id,   'mentor_streak'),
        (elan.id,  'first_session'),
        (elan.id,  'five_star_teacher'),
        (gita.id,  'mentor_streak'),
    ]
    for sid, btype in badges_seed:
        db.session.add(Badge(student_id=sid, badge_type=btype))

    db.session.commit()


# ─── BEFORE REQUEST ────────────────────────────────────────────────────────

_seeded = False

@app.before_request
def ensure_seeded():
    global _seeded
    if not _seeded:
        with app.app_context():
            db.create_all()
            seed_database()
        _seeded = True


# ─── CONTEXT PROCESSOR ─────────────────────────────────────────────────────

@app.context_processor
def inject_globals():
    current_student = get_current_student()
    all_students    = Student.query.order_by(Student.name).all()
    is_logged_in    = current_student is not None and not session.get('logged_out')
    return dict(current_student=current_student, all_students=all_students, BADGE_INFO=BADGE_INFO, is_logged_in=is_logged_in)


# ─── AUTH ROUTES ───────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        student = Student.query.filter(db.func.lower(Student.email) == email).first()

        if student and student.check_password(password):
            session.pop('logged_out', None)
            session['student_id'] = student.id
            flash(f'Welcome back, {student.name}!', 'success')
            next_url = request.args.get('next') or request.form.get('next') or url_for('dashboard')
            return redirect(next_url)
        else:
            flash('Invalid email or password. You can use Quick Demo Sign-In or check credentials below.', 'error')

    all_demo_students = Student.query.order_by(Student.id).all()
    return render_template('login.html', demo_students=all_demo_students, next=request.args.get('next', ''))


@app.route('/register', methods=['GET', 'POST'])
def register():
    all_skills = Skill.query.order_by(Skill.name).all()
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        course   = request.form.get('course', 'Computer Science').strip()
        year     = int(request.form.get('year', 1))
        bio      = request.form.get('bio', '').strip()
        offer_skill_id = request.form.get('offer_skill_id')
        offer_prof     = request.form.get('offer_proficiency', 'Intermediate')
        want_skill_id  = request.form.get('want_skill_id')

        if not name or not email or not password:
            flash('Please fill in your name, email, and password.', 'error')
            return render_template('register.html', all_skills=all_skills)

        if password != confirm:
            flash('Passwords do not match. Please verify.', 'error')
            return render_template('register.html', all_skills=all_skills)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html', all_skills=all_skills)

        existing = Student.query.filter(db.func.lower(Student.email) == email).first()
        if existing:
            flash('An account with this email already exists. Please sign in.', 'error')
            return redirect(url_for('login'))

        colors = ['#7c3aed', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6']
        import random
        color = random.choice(colors)

        new_student = Student(
            name=name, email=email, course=course, year=year,
            bio=bio or f'Student studying {course}. Excited to learn and swap skills on campus!',
            avatar_color=color, xp=50, level=1, streak_weeks=1
        )
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.flush()

        if offer_skill_id and offer_skill_id.isdigit():
            db.session.add(StudentSkill(
                student_id=new_student.id, skill_id=int(offer_skill_id),
                skill_type='offer', proficiency=offer_prof
            ))

        if want_skill_id and want_skill_id.isdigit():
            db.session.add(StudentSkill(
                student_id=new_student.id, skill_id=int(want_skill_id),
                skill_type='want', proficiency='Beginner'
            ))

        # Default sample availability (Mon, Wed 14:00-18:00)
        db.session.add(Availability(student_id=new_student.id, day_of_week=0, start_hour=14, end_hour=18))
        db.session.add(Availability(student_id=new_student.id, day_of_week=2, start_hour=14, end_hour=18))

        db.session.commit()

        session.pop('logged_out', None)
        session['student_id'] = new_student.id
        flash(f'Account created successfully! Welcome to SkillSwap Campus, {new_student.name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html', all_skills=all_skills)


@app.route('/quick-login/<int:student_id>')
def quick_login(student_id):
    student = Student.query.get_or_404(student_id)
    session.pop('logged_out', None)
    session['student_id'] = student.id
    flash(f'Signed in as {student.name} ({student.course})', 'success')
    next_url = request.args.get('next') or url_for('dashboard')
    return redirect(next_url)


@app.route('/logout')
def logout():
    session.clear()
    session['logged_out'] = True
    flash('You have been signed out. Demo mode: click any student to sign back in.', 'info')
    return redirect(url_for('login'))


# ─── CORE ROUTES ───────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    current = get_current_student()
    if not current:
        return redirect(url_for('login'))

    # Top 3 partner matches
    all_students = Student.query.filter(Student.id != current.id).all()
    matches = []
    for s in all_students:
        score = calculate_match_score(current, s)
        if score['total'] > 0:
            matches.append((s, score))
    matches.sort(key=lambda x: x[1]['total'], reverse=True)
    top_matches = matches[:3]

    # Upcoming sessions
    upcoming = Session.query.filter(
        db.or_(Session.teacher_id == current.id, Session.learner_id == current.id),
        Session.status.in_(['pending', 'accepted'])
    ).order_by(Session.date).limit(5).all()

    # Stats
    completed_count = Session.query.filter(
        db.or_(Session.teacher_id == current.id, Session.learner_id == current.id),
        Session.status == 'completed'
    ).count()

    skills_learning = len([ss for ss in current.skills if ss.skill_type == 'want'])
    teaching_hours  = Session.query.filter_by(teacher_id=current.id, status='completed')\
        .with_entities(db.func.sum(Session.duration_minutes)).scalar() or 0
    teaching_hours  = round(teaching_hours / 60, 1)

    # Recent activity feed (last 5 sessions)
    recent = Session.query.filter(
        db.or_(Session.teacher_id == current.id, Session.learner_id == current.id)
    ).order_by(Session.created_at.desc()).limit(5).all()

    # Skill gap chart data
    skill_offers = defaultdict(int)
    skill_wants  = defaultdict(int)
    for s in Student.query.all():
        for ss in s.skills:
            if ss.skill_type == 'offer':
                skill_offers[ss.skill.name] += 1
            else:
                skill_wants[ss.skill.name] += 1
    all_skill_names = sorted(set(list(skill_offers.keys()) + list(skill_wants.keys())))
    chart_labels  = all_skill_names[:8]
    chart_offers  = [skill_offers.get(n, 0) for n in chart_labels]
    chart_wants   = [skill_wants.get(n, 0)  for n in chart_labels]

    return render_template('dashboard.html',
        current_student=current,
        top_matches=top_matches,
        upcoming=upcoming,
        completed_count=completed_count,
        skills_learning=skills_learning,
        teaching_hours=teaching_hours,
        recent=recent,
        chart_labels=json.dumps(chart_labels),
        chart_offers=json.dumps(chart_offers),
        chart_wants=json.dumps(chart_wants),
    )


@app.route('/switch/<int:student_id>')
def switch_student(student_id):
    s = Student.query.get_or_404(student_id)
    session.pop('logged_out', None)
    session['student_id'] = s.id
    flash(f'Switched to {s.name}', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/profile/<int:student_id>')
def profile(student_id):
    student = Student.query.get_or_404(student_id)
    current = get_current_student()

    sessions_taught = Session.query.filter_by(teacher_id=student.id, status='completed').count()
    sessions_learned= Session.query.filter_by(learner_id=student.id, status='completed').count()
    ratings_received= Rating.query.filter_by(ratee_id=student.id).all()
    avg_rating = sum(r.stars for r in ratings_received) / len(ratings_received) if ratings_received else 0

    offers = [ss for ss in student.skills if ss.skill_type == 'offer']
    wants  = [ss for ss in student.skills if ss.skill_type == 'want']

    # Group availabilities by day
    DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    avail_by_day = defaultdict(list)
    for av in student.availabilities:
        avail_by_day[av.day_of_week].append(av)

    match_score = None
    if current and current.id != student.id:
        match_score = calculate_match_score(current, student)

    return render_template('profile.html',
        student=student,
        offers=offers,
        wants=wants,
        sessions_taught=sessions_taught,
        sessions_learned=sessions_learned,
        avg_rating=round(avg_rating, 1),
        rating_count=len(ratings_received),
        avail_by_day=avail_by_day,
        DAY_NAMES=DAY_NAMES,
        match_score=match_score,
    )


@app.route('/profile/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_profile(student_id):
    student = Student.query.get_or_404(student_id)
    current = get_current_student()
    if current.id != student.id:
        flash('You can only edit your own profile.', 'error')
        return redirect(url_for('profile', student_id=student.id))

    all_skills = Skill.query.order_by(Skill.name).all()

    if request.method == 'POST':
        student.name   = request.form.get('name', student.name).strip()
        student.bio    = request.form.get('bio', '').strip()
        student.course = request.form.get('course', student.course).strip()
        student.year   = int(request.form.get('year', student.year))

        # Update skills
        StudentSkill.query.filter_by(student_id=student.id).delete()
        for sk in all_skills:
            for stype in ['offer', 'want']:
                key  = f'skill_{stype}_{sk.id}'
                prof = request.form.get(f'prof_{stype}_{sk.id}', 'Beginner')
                if request.form.get(key):
                    db.session.add(StudentSkill(student_id=student.id, skill_id=sk.id, skill_type=stype, proficiency=prof))

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', student_id=student.id))

    return render_template('edit_profile.html', student=student, all_skills=all_skills)


@app.route('/find-partners', methods=['GET', 'POST'])
def find_partners():
    current = get_current_student()
    all_students = Student.query.filter(Student.id != current.id).all()

    skill_filter = request.values.get('skill_filter', '')
    avail_filter = request.values.get('avail_filter', '')

    matches = []
    for s in all_students:
        score = calculate_match_score(current, s)
        if skill_filter:
            offered_names = [ss.skill.name for ss in s.skills if ss.skill_type == 'offer']
            if skill_filter not in offered_names:
                continue
        matches.append({'student': s, 'score': score})

    matches.sort(key=lambda x: x['score']['total'], reverse=True)

    all_skills = Skill.query.order_by(Skill.name).all()
    return render_template('find_partners.html',
        matches=matches,
        skill_filter=skill_filter,
        all_skills=all_skills,
    )


@app.route('/chains')
def chains():
    found_chains = find_skill_swap_chains(max_length=5)
    return render_template('chains.html', chains=found_chains)


@app.route('/sessions')
def sessions_list():
    current = get_current_student()
    tab = request.args.get('tab', 'upcoming')

    base = Session.query.filter(
        db.or_(Session.teacher_id == current.id, Session.learner_id == current.id)
    )

    if tab == 'upcoming':
        sessions = base.filter(Session.status.in_(['pending', 'accepted'])).order_by(Session.date).all()
    elif tab == 'past':
        sessions = base.filter(Session.status.in_(['completed', 'cancelled'])).order_by(Session.date.desc()).all()
    else:
        sessions = base.order_by(Session.date.desc()).all()

    all_students = Student.query.filter(Student.id != current.id).all()
    all_skills   = Skill.query.order_by(Skill.name).all()

    # Check which sessions current student has already rated
    rated_session_ids = {r.session_id for r in Rating.query.filter_by(rater_id=current.id).all()}

    return render_template('sessions.html',
        sessions=sessions,
        tab=tab,
        all_students=all_students,
        all_skills=all_skills,
        rated_session_ids=rated_session_ids,
    )


@app.route('/sessions/create', methods=['POST'])
def create_session():
    current = get_current_student()
    partner_id = int(request.form.get('partner_id'))
    skill_id   = int(request.form.get('skill_id'))
    date_str   = request.form.get('date', '')
    time_str   = request.form.get('start_time', '')
    duration   = int(request.form.get('duration', 60))
    fmt        = request.form.get('format', 'Online')
    role       = request.form.get('role', 'learner')  # am I the teacher or learner?

    if not partner_id or not skill_id:
        flash('Please select a partner and skill.', 'error')
        return redirect(url_for('sessions_list'))

    if role == 'teacher':
        teacher_id, learner_id = current.id, partner_id
    else:
        teacher_id, learner_id = partner_id, current.id

    s = Session(
        teacher_id=teacher_id, learner_id=learner_id, skill_id=skill_id,
        date=date_str, start_time=time_str, duration_minutes=duration, format=fmt,
        status='pending'
    )
    db.session.add(s)
    db.session.commit()
    flash('Session request sent!', 'success')
    return redirect(url_for('sessions_list'))


@app.route('/sessions/<int:session_id>/accept', methods=['POST'])
def accept_session(session_id):
    s = Session.query.get_or_404(session_id)
    s.status = 'accepted'
    db.session.commit()
    flash('Session accepted!', 'success')
    return redirect(url_for('sessions_list'))


@app.route('/sessions/<int:session_id>/complete', methods=['POST'])
def complete_session(session_id):
    s = Session.query.get_or_404(session_id)
    s.status = 'completed'
    db.session.commit()
    update_xp(s.teacher_id, 100)
    update_xp(s.learner_id, 75)
    check_and_award_badges(s.teacher_id)
    check_and_award_badges(s.learner_id)
    flash('Session marked as completed! XP awarded.', 'success')
    return redirect(url_for('sessions_list'))


@app.route('/sessions/<int:session_id>/cancel', methods=['POST'])
def cancel_session(session_id):
    s = Session.query.get_or_404(session_id)
    s.status = 'cancelled'
    db.session.commit()
    flash('Session cancelled.', 'info')
    return redirect(url_for('sessions_list'))


@app.route('/sessions/<int:session_id>/notes', methods=['GET', 'POST'])
def session_notes(session_id):
    s = Session.query.get_or_404(session_id)
    current = get_current_student()

    if request.method == 'POST':
        s.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Notes saved!', 'success')
        return redirect(url_for('session_notes', session_id=session_id))

    existing_takeaway = Takeaway.query.filter_by(session_id=session_id, learner_id=current.id).first()
    return render_template('notes.html', session=s, existing_takeaway=existing_takeaway)


@app.route('/sessions/<int:session_id>/rate', methods=['POST'])
def rate_session(session_id):
    current = get_current_student()
    s = Session.query.get_or_404(session_id)

    # Check already rated
    existing = Rating.query.filter_by(session_id=session_id, rater_id=current.id).first()
    if existing:
        flash('You have already rated this session.', 'info')
        return redirect(url_for('sessions_list'))

    stars   = int(request.form.get('stars', 3))
    comment = request.form.get('comment', '').strip()

    # Who is being rated? If current is the learner, rate the teacher, vice versa
    if current.id == s.learner_id:
        ratee_id = s.teacher_id
    else:
        ratee_id = s.learner_id

    rating = Rating(session_id=session_id, rater_id=current.id, ratee_id=ratee_id, stars=stars, comment=comment)
    db.session.add(rating)
    if stars == 5:
        update_xp(ratee_id, 50)
    db.session.commit()
    check_and_award_badges(ratee_id)
    flash('Rating submitted! Thank you.', 'success')
    return redirect(url_for('sessions_list'))


@app.route('/sessions/<int:session_id>/takeaway', methods=['POST'])
def submit_takeaway(session_id):
    current = get_current_student()
    s = Session.query.get_or_404(session_id)
    content = request.form.get('content', '').strip()
    if not content:
        flash('Please enter your takeaway.', 'error')
        return redirect(url_for('session_notes', session_id=session_id))

    existing = Takeaway.query.filter_by(session_id=session_id, learner_id=current.id).first()
    if existing:
        existing.content = content
    else:
        db.session.add(Takeaway(session_id=session_id, learner_id=current.id, content=content))
    db.session.commit()
    update_xp(current.id, 25)
    check_and_award_badges(current.id)
    flash('Takeaway submitted! +25 XP', 'success')
    return redirect(url_for('session_notes', session_id=session_id))


@app.route('/takeaway/<int:takeaway_id>/confirm', methods=['POST'])
def confirm_takeaway(takeaway_id):
    t = Takeaway.query.get_or_404(takeaway_id)
    t.confirmed = True
    db.session.commit()
    check_and_award_badges(t.learner_id)
    flash('Takeaway confirmed!', 'success')
    return redirect(url_for('session_notes', session_id=t.session_id))


@app.route('/roadmaps')
def roadmaps():
    current = get_current_student()
    learned_skill_ids = {
        s.skill_id for s in Session.query.filter_by(learner_id=current.id, status='completed').all()
    }
    offered_skill_ids = {ss.skill_id for ss in current.skills if ss.skill_type == 'offer'}
    known_ids = learned_skill_ids | offered_skill_ids

    def skill_obj(name):
        return Skill.query.filter_by(name=name).first()

    def mentors_for(skill_name):
        sk = skill_obj(skill_name)
        if not sk:
            return []
        return [ss.student for ss in StudentSkill.query.filter_by(skill_id=sk.id, skill_type='offer').all()
                if ss.student_id != current.id]

    roadmaps_data = [
        {
            'title': 'Web Development',
            'icon': '🌐',
            'description': 'Go from zero to full-stack web developer',
            'color': 'var(--accent-blue)',
            'stages': [
                {'skill': 'HTML/CSS', 'label': 'HTML & CSS', 'desc': 'Structure and style web pages'},
                {'skill': 'Web Dev',  'label': 'JavaScript & Web Dev', 'desc': 'Make pages interactive'},
                {'skill': 'Flask',    'label': 'Backend with Flask', 'desc': 'Build server-side apps'},
                {'skill': 'Python',   'label': 'Python Fundamentals', 'desc': 'Core programming skills'},
            ],
        },
        {
            'title': 'Data Science',
            'icon': '📊',
            'description': 'Master data analysis and machine learning',
            'color': 'var(--accent-green)',
            'stages': [
                {'skill': 'Python',           'label': 'Python Basics',     'desc': 'Foundation language'},
                {'skill': 'Data Structures',  'label': 'Data Structures',   'desc': 'Efficient data management'},
                {'skill': 'Machine Learning', 'label': 'Machine Learning',  'desc': 'Predictive modeling'},
                {'skill': 'Deep Learning',    'label': 'Deep Learning',     'desc': 'Neural networks & AI'},
            ],
        },
        {
            'title': 'UX / Design',
            'icon': '🎨',
            'description': 'Create beautiful, user-centered digital experiences',
            'color': 'var(--accent-purple)',
            'stages': [
                {'skill': 'Figma',       'label': 'Figma Prototyping', 'desc': 'Design & prototype UIs'},
                {'skill': 'UI Design',   'label': 'UI Design Principles', 'desc': 'Visual design fundamentals'},
                {'skill': 'Illustrator', 'label': 'Adobe Illustrator',  'desc': 'Vector graphics & branding'},
                {'skill': 'Photography', 'label': 'Photography',         'desc': 'Visual storytelling'},
            ],
        },
    ]

    for rm in roadmaps_data:
        completed = 0
        for stage in rm['stages']:
            sk = skill_obj(stage['skill'])
            stage['known']   = sk and sk.id in known_ids
            stage['mentors'] = mentors_for(stage['skill'])
            if stage['known']:
                completed += 1
        rm['progress'] = round(completed / len(rm['stages']) * 100)

    return render_template('roadmaps.html', roadmaps=roadmaps_data)


@app.route('/heatmap')
def heatmap():
    return render_template('heatmap.html', all_students=Student.query.all())


@app.route('/api/heatmap-data')
def heatmap_data():
    skill_offers = defaultdict(int)
    skill_wants  = defaultdict(int)
    skill_cats   = {}
    for s in Student.query.all():
        for ss in s.skills:
            skill_cats[ss.skill.name] = ss.skill.category
            if ss.skill_type == 'offer':
                skill_offers[ss.skill.name] += 1
            else:
                skill_wants[ss.skill.name] += 1

    all_names = sorted(set(list(skill_offers.keys()) + list(skill_wants.keys())))
    data = []
    for name in all_names:
        o = skill_offers.get(name, 0)
        w = skill_wants.get(name, 0)
        gap = w - o
        data.append({'skill': name, 'category': skill_cats.get(name, 'Other'),
                     'offered': o, 'wanted': w, 'gap': gap})

    data.sort(key=lambda x: x['gap'], reverse=True)
    return jsonify(data)


@app.route('/achievements')
def achievements():
    current = get_current_student()
    earned_badges = {b.badge_type for b in current.badges}

    leaderboard = Student.query.order_by(Student.xp.desc()).limit(5).all()

    return render_template('achievements.html',
        earned_badges=earned_badges,
        leaderboard=leaderboard,
    )


@app.route('/report/<int:student_id>')
def report(student_id):
    student = Student.query.get_or_404(student_id)
    sessions_taught  = Session.query.filter_by(teacher_id=student.id, status='completed').all()
    sessions_learned = Session.query.filter_by(learner_id=student.id, status='completed').all()
    ratings_received = Rating.query.filter_by(ratee_id=student.id).all()
    avg_rating = sum(r.stars for r in ratings_received) / len(ratings_received) if ratings_received else 0
    takeaways  = Takeaway.query.filter_by(learner_id=student.id).all()

    return render_template('report.html',
        student=student,
        sessions_taught=sessions_taught,
        sessions_learned=sessions_learned,
        ratings_received=ratings_received,
        avg_rating=round(avg_rating, 1),
        takeaways=takeaways,
    )


@app.route('/report/<int:student_id>/download')
def download_report(student_id):
    student = Student.query.get_or_404(student_id)
    sessions_taught  = Session.query.filter_by(teacher_id=student.id, status='completed').all()
    sessions_learned = Session.query.filter_by(learner_id=student.id, status='completed').all()
    ratings_received = Rating.query.filter_by(ratee_id=student.id).all()
    avg_rating = sum(r.stars for r in ratings_received) / len(ratings_received) if ratings_received else 0
    takeaways  = Takeaway.query.filter_by(learner_id=student.id, confirmed=True).all()

    lines = [
        '=' * 60,
        f'SKILLSWAP CAMPUS — LEARNING REPORT',
        '=' * 60,
        f'Student: {student.name}',
        f'Course:  {student.course}, Year {student.year}',
        f'Level:   {student.level} | XP: {student.xp}',
        f'Streak:  {student.streak_weeks} weeks',
        '',
        '─' * 60,
        'PROFILE SUMMARY',
        '─' * 60,
        student.bio or 'No bio provided.',
        '',
        '─' * 60,
        'SKILLS OFFERED',
        '─' * 60,
    ]
    for ss in student.skills:
        if ss.skill_type == 'offer':
            lines.append(f'  • {ss.skill.name} ({ss.proficiency})')
    lines += ['', '─' * 60, 'SKILLS WANTED', '─' * 60]
    for ss in student.skills:
        if ss.skill_type == 'want':
            lines.append(f'  • {ss.skill.name}')
    lines += ['', '─' * 60, f'TEACHING ({len(sessions_taught)} sessions)', '─' * 60]
    for s in sessions_taught:
        lines.append(f'  • {s.skill.name} → {s.learner.name} on {s.date} ({s.duration_minutes} min)')
    lines += ['', '─' * 60, f'LEARNING ({len(sessions_learned)} sessions)', '─' * 60]
    for s in sessions_learned:
        lines.append(f'  • {s.skill.name} ← {s.teacher.name} on {s.date} ({s.duration_minutes} min)')
    lines += ['', '─' * 60, f'RATINGS RECEIVED (avg {avg_rating:.1f}/5)', '─' * 60]
    for r in ratings_received:
        lines.append(f'  • {r.stars}★ from {r.rater.name}: "{r.comment}"')
    lines += ['', '─' * 60, 'CONFIRMED TAKEAWAYS', '─' * 60]
    for t in takeaways:
        lines.append(f'  • {t.content}')
    lines += ['', '─' * 60, 'BADGES', '─' * 60]
    for b in student.badges:
        info = BADGE_INFO.get(b.badge_type, {})
        lines.append(f'  • {info.get("icon","🏅")} {info.get("label", b.badge_type)}')
    lines += ['', '=' * 60, f'Generated by SkillSwap Campus | {datetime.utcnow().strftime("%Y-%m-%d")}', '=' * 60]

    content = '\n'.join(lines)
    buf = io.BytesIO(content.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name=f'report_{student.name.replace(" ","_")}.txt',
                     mimetype='text/plain')


# ─── VIDEO CALL ROUTES ─────────────────────────────────────────────────────

@app.route('/sessions/<int:session_id>/call')
def session_call(session_id):
    current = get_current_student()
    if not current:
        return redirect(url_for('login', next=request.url))
    s = Session.query.get_or_404(session_id)
    partner = s.learner if current.id == s.teacher_id else s.teacher
    is_teacher = (current.id == s.teacher_id)
    room_id = s.get_room_id()
    existing_takeaway = Takeaway.query.filter_by(session_id=session_id, learner_id=current.id).first()
    return render_template('call.html',
        session_obj=s,
        partner=partner,
        is_teacher=is_teacher,
        room_id=room_id,
        is_instant=False,
        existing_takeaway=existing_takeaway
    )


@app.route('/call')
def instant_call():
    current = get_current_student()
    if not current:
        return redirect(url_for('login', next=request.url))
    room_id = request.args.get('room')
    if not room_id:
        import hashlib, time
        room_id = f"SkillSwap-Study-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
    return render_template('call.html',
        session_obj=None,
        partner=None,
        is_teacher=False,
        room_id=room_id,
        is_instant=True,
        existing_takeaway=None
    )


# ─── API ENDPOINTS ─────────────────────────────────────────────────────────

@app.route('/api/partner-skills/<int:partner_id>')
def partner_skills(partner_id):
    partner = Student.query.get_or_404(partner_id)
    skills = [{'id': ss.skill_id, 'name': ss.skill.name, 'proficiency': ss.proficiency}
              for ss in partner.skills if ss.skill_type == 'offer']
    return jsonify(skills)


@app.route('/api/availability/<int:a_id>/<int:b_id>')
def availability_overlap(a_id, b_id):
    a = Student.query.get_or_404(a_id)
    b = Student.query.get_or_404(b_id)
    DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    slots = []
    for av_a in a.availabilities:
        for av_b in b.availabilities:
            if av_a.day_of_week == av_b.day_of_week:
                overlap_start = max(av_a.start_hour, av_b.start_hour)
                overlap_end   = min(av_a.end_hour,   av_b.end_hour)
                if overlap_end > overlap_start:
                    slots.append({
                        'day':   DAY_NAMES[av_a.day_of_week],
                        'start': f'{overlap_start:02d}:00',
                        'end':   f'{overlap_end:02d}:00',
                    })
    return jsonify({'slots': slots, 'total_hours': calculate_overlap_hours(a, b)})


# ─── ERROR HANDLERS ────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Page not found'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='Internal server error'), 500


# ─── ENTRY POINT ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True, port=5000)
