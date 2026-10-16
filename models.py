from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    course = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak_weeks = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student_skills = db.relationship('StudentSkill', backref='student', lazy=True, cascade='all, delete-orphan')
    availabilities = db.relationship('Availability', backref='student', lazy=True, cascade='all, delete-orphan')
    badges = db.relationship('StudentBadge', backref='student', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_details=True):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'course': self.course,
            'year': self.year,
            'bio': self.bio,
            'xp': self.xp,
            'level': self.calculate_level(),
            'streak_weeks': self.streak_weeks,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_details:
            data['skills_offered'] = [
                ss.to_dict() for ss in self.student_skills if ss.skill_type == 'offer'
            ]
            data['skills_wanted'] = [
                ss.to_dict() for ss in self.student_skills if ss.skill_type == 'want'
            ]
            data['availability'] = [
                av.to_dict() for av in self.availabilities
            ]
            data['badges'] = [
                sb.badge.to_dict() for sb in self.badges if sb.badge
            ]
            
            # Calculate average rating as mentor
            mentor_ratings = Rating.query.filter_by(reviewee_id=self.id).all()
            if mentor_ratings:
                avg = sum(r.stars for r in mentor_ratings) / len(mentor_ratings)
                data['rating_avg'] = round(avg, 1)
                data['rating_count'] = len(mentor_ratings)
            else:
                data['rating_avg'] = None
                data['rating_count'] = 0

            # Teaching sessions count
            data['completed_teaching_sessions'] = Session.query.filter_by(mentor_id=self.id, status='completed').count()
            data['completed_learning_sessions'] = Session.query.filter_by(learner_id=self.id, status='completed').count()

        return data

    def calculate_level(self):
        # Level thresholds: 0-150: Lvl 1, 151-350: Lvl 2, 351-650: Lvl 3, 651-1000: Lvl 4, 1001+: Lvl 5
        if self.xp >= 1000:
            return 5
        elif self.xp >= 650:
            return 4
        elif self.xp >= 350:
            return 3
        elif self.xp >= 150:
            return 2
        return 1

    def add_xp(self, amount):
        self.xp += amount
        self.level = self.calculate_level()


class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description
        }


class StudentSkill(db.Model):
    __tablename__ = 'student_skills'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    skill_type = db.Column(db.String(10), nullable=False)  # 'offer' or 'want'
    proficiency = db.Column(db.String(20), nullable=False, default='Intermediate')  # 'Beginner', 'Intermediate', 'Advanced'

    skill = db.relationship('Skill', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'skill_id': self.skill_id,
            'skill_name': self.skill.name if self.skill else '',
            'category': self.skill.category if self.skill else '',
            'skill_type': self.skill_type,
            'proficiency': self.proficiency
        }


class Availability(db.Model):
    __tablename__ = 'availabilities'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.String(5), nullable=False)   # "14:00"
    end_time = db.Column(db.String(5), nullable=False)     # "16:00"

    def to_dict(self):
        return {
            'id': self.id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time,
            'end_time': self.end_time
        }


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    scheduled_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    start_time = db.Column(db.String(5), nullable=False)       # HH:MM
    duration_minutes = db.Column(db.Integer, default=60)
    session_format = db.Column(db.String(20), default='Virtual')  # 'Virtual', 'In-Person'
    location_or_link = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    mentor = db.relationship('Student', foreign_keys=[mentor_id], backref='mentored_sessions', lazy=True)
    learner = db.relationship('Student', foreign_keys=[learner_id], backref='learned_sessions', lazy=True)
    skill = db.relationship('Skill', lazy=True)
    note = db.relationship('SessionNote', backref='session', uselist=False, cascade='all, delete-orphan')
    teach_back = db.relationship('TeachBack', backref='session', uselist=False, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', backref='session', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'mentor_id': self.mentor_id,
            'mentor_name': self.mentor.name if self.mentor else 'Unknown',
            'mentor_avatar': self.mentor.avatar_url if self.mentor else None,
            'learner_id': self.learner_id,
            'learner_name': self.learner.name if self.learner else 'Unknown',
            'learner_avatar': self.learner.avatar_url if self.learner else None,
            'skill_id': self.skill_id,
            'skill_name': self.skill.name if self.skill else 'Unknown',
            'skill_category': self.skill.category if self.skill else 'General',
            'scheduled_date': self.scheduled_date,
            'start_time': self.start_time,
            'duration_minutes': self.duration_minutes,
            'session_format': self.session_format,
            'location_or_link': self.location_or_link,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_note': self.note is not None,
            'has_teach_back': self.teach_back is not None,
            'teach_back_confirmed': self.teach_back.teacher_confirmed if self.teach_back else False,
            'ratings_count': len(self.ratings) if self.ratings else 0
        }


class SessionNote(db.Model):
    __tablename__ = 'session_notes'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), unique=True, nullable=False)
    topics_covered = db.Column(db.Text, nullable=True)
    learning_outcomes = db.Column(db.Text, nullable=True)
    next_steps = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'topics_covered': self.topics_covered or '',
            'learning_outcomes': self.learning_outcomes or '',
            'next_steps': self.next_steps or '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Rating(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    stars = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('session_id', 'reviewer_id', name='uq_session_reviewer'),
    )

    reviewer = db.relationship('Student', foreign_keys=[reviewer_id])
    reviewee = db.relationship('Student', foreign_keys=[reviewee_id])

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer.name if self.reviewer else 'Anonymous',
            'reviewee_id': self.reviewee_id,
            'stars': self.stars,
            'comment': self.comment or '',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    xp_reward = db.Column(db.Integer, default=50)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'xp_reward': self.xp_reward
        }


class StudentBadge(db.Model):
    __tablename__ = 'student_badges'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    awarded_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'badge_id', name='uq_student_badge'),
    )

    badge = db.relationship('Badge')

    def to_dict(self):
        return {
            'id': self.id,
            'badge': self.badge.to_dict() if self.badge else None,
            'awarded_at': self.awarded_at.isoformat() if self.awarded_at else None
        }


class TeachBack(db.Model):
    __tablename__ = 'teach_backs'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), unique=True, nullable=False)
    learner_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    takeaways = db.Column(db.Text, nullable=False)
    teacher_confirmed = db.Column(db.Boolean, default=False)
    feedback = db.Column(db.Text, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    learner = db.relationship('Student', foreign_keys=[learner_id])
    mentor = db.relationship('Student', foreign_keys=[mentor_id])

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'learner_id': self.learner_id,
            'learner_name': self.learner.name if self.learner else '',
            'mentor_id': self.mentor_id,
            'mentor_name': self.mentor.name if self.mentor else '',
            'takeaways': self.takeaways,
            'teacher_confirmed': self.teacher_confirmed,
            'feedback': self.feedback or '',
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }


class Roadmap(db.Model):
    __tablename__ = 'roadmaps'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    stages_json = db.Column(db.Text, nullable=False)  # JSON string

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'stages': json.loads(self.stages_json) if self.stages_json else []
        }
