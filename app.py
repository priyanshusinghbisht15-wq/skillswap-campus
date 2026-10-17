import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, send_from_directory
from models import db, Student, Skill, StudentSkill, Availability, Session, SessionNote, Rating, Badge, StudentBadge, TeachBack, Roadmap
from algorithms.matchmaking import calculate_match_score, calculate_time_overlap, time_to_minutes
from algorithms.chains import find_skill_swap_chains
from seed_data import seed_database

app = Flask(__name__)

# Support Vercel serverless environment (writable /tmp directory)
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None
if IS_VERCEL:
    db_file = '/tmp/skillswap.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillswap.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Ensure database tables and deterministic demo data exist on startup/cold-start
with app.app_context():
    db.create_all()
    if Student.query.count() == 0:
        try:
            seed_database()
        except Exception as err:
            print("Auto-seed error on startup:", err)


# Helper function to check and award badges
def check_and_award_badges(student_id):
    student = Student.query.get(student_id)
    if not student:
        return []

    newly_awarded = []
    current_badge_ids = {sb.badge_id for sb in student.badges}

    def award(code):
        badge = Badge.query.filter_by(code=code).first()
        if badge and badge.id not in current_badge_ids:
            sb = StudentBadge(student_id=student.id, badge_id=badge.id, awarded_at=datetime.now(timezone.utc))
            db.session.add(sb)
            current_badge_ids.add(badge.id)
            student.add_xp(badge.xp_reward)
            newly_awarded.append(badge.name)

    # 1. First Session badge
    completed_any = Session.query.filter(
        ((Session.mentor_id == student.id) | (Session.learner_id == student.id)) &
        (Session.status == 'completed')
    ).count()
    if completed_any >= 1:
        award('first_session')

    # 2. Five-Star Teacher badge
    has_five_star = Rating.query.filter_by(reviewee_id=student.id, stars=5).count()
    if has_five_star >= 1:
        award('five_star_teacher')

    # 3. Polyglot Learner badge (>= 3 distinct skills learned)
    learned_sessions = Session.query.filter_by(learner_id=student.id, status='completed').all()
    distinct_skills = {s.skill_id for s in learned_sessions}
    if len(distinct_skills) >= 3:
        award('polyglot_learner')

    # 4. Mentor Streak badge (streak_weeks >= 3)
    if student.streak_weeks >= 3:
        award('mentor_streak')

    db.session.commit()
    return newly_awarded


# --- Core Web Routes ---
@app.route('/')
def index():
    return render_template('index.html')


# --- API Routes ---

# 1. Students & Profiles
@app.route('/api/students', methods=['GET'])
def get_students():
    search = request.args.get('search', '').strip().lower()
    skill_filter = request.args.get('skill', '').strip().lower()
    course_filter = request.args.get('course', '').strip().lower()

    query = Student.query

    if course_filter:
        query = query.filter(Student.course.ilike(f'%{course_filter}%'))

    students = query.order_by(Student.name.asc()).all()
    result = []

    for s in students:
        s_dict = s.to_dict(include_details=True)
        # Filter in memory for rich skill search
        if search:
            name_match = search in s.name.lower() or search in s.course.lower() or (s.bio and search in s.bio.lower())
            skill_match = any(search in sk['skill_name'].lower() for sk in s_dict['skills_offered'] + s_dict['skills_wanted'])
            if not (name_match or skill_match):
                continue
        if skill_filter:
            skill_match = any(skill_filter in sk['skill_name'].lower() for sk in s_dict['skills_offered'] + s_dict['skills_wanted'])
            if not skill_match:
                continue

        result.append(s_dict)

    return jsonify({'students': result, 'count': len(result)})


@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict(include_details=True))


@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.json or {}

    if 'name' in data and data['name'].strip():
        student.name = data['name'].strip()
    if 'course' in data and data['course'].strip():
        student.course = data['course'].strip()
    if 'year' in data and data['year'].strip():
        student.year = data['year'].strip()
    if 'bio' in data:
        student.bio = data['bio'].strip()

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully', 'student': student.to_dict()})


@app.route('/api/students/<int:student_id>/skills', methods=['POST'])
def add_student_skill(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.json or {}

    skill_name = data.get('skill_name', '').strip()
    skill_type = data.get('skill_type', 'offer')  # 'offer' or 'want'
    proficiency = data.get('proficiency', 'Intermediate')

    if not skill_name:
        return jsonify({'error': 'Skill name is required'}), 400

    # Find or create skill
    skill = Skill.query.filter_by(name=skill_name).first()
    if not skill:
        skill = Skill(name=skill_name, category=data.get('category', 'General'), description='')
        db.session.add(skill)
        db.session.flush()

    # Check if already added
    existing = StudentSkill.query.filter_by(
        student_id=student.id, skill_id=skill.id, skill_type=skill_type
    ).first()
    if existing:
        existing.proficiency = proficiency
    else:
        ss = StudentSkill(
            student_id=student.id,
            skill_id=skill.id,
            skill_type=skill_type,
            proficiency=proficiency
        )
        db.session.add(ss)

    db.session.commit()
    return jsonify({'message': f'Skill {skill_name} added successfully', 'student': student.to_dict()})


@app.route('/api/students/<int:student_id>/skills/<int:student_skill_id>', methods=['DELETE'])
def remove_student_skill(student_id, student_skill_id):
    ss = StudentSkill.query.filter_by(id=student_skill_id, student_id=student_id).first_or_404()
    db.session.delete(ss)
    db.session.commit()
    return jsonify({'message': 'Skill removed successfully'})


@app.route('/api/students/<int:student_id>/availability', methods=['POST'])
def update_availability(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.json or {}
    slots = data.get('slots', [])

    # Replace existing
    Availability.query.filter_by(student_id=student.id).delete()

    for s in slots:
        day = s.get('day_of_week')
        start = s.get('start_time')
        end = s.get('end_time')
        if day and start and end:
            av = Availability(student_id=student.id, day_of_week=day, start_time=start, end_time=end)
            db.session.add(av)

    db.session.commit()
    return jsonify({'message': 'Availability updated successfully', 'availability': [av.to_dict() for av in student.availabilities]})


# 2. Smart Matchmaking
@app.route('/api/matchmaking/<int:student_id>', methods=['GET'])
def get_matches(student_id):
    current_student = Student.query.get_or_404(student_id)
    current_dict = current_student.to_dict(include_details=True)

    other_students = Student.query.filter(Student.id != student_id).all()
    matches = []

    for other in other_students:
        other_dict = other.to_dict(include_details=True)
        score_data = calculate_match_score(current_dict, other_dict)

        matches.append({
            'partner': {
                'id': other.id,
                'name': other.name,
                'course': other.course,
                'year': other.year,
                'avatar_url': other.avatar_url,
                'rating_avg': other_dict['rating_avg'],
                'rating_count': other_dict['rating_count'],
                'skills_offered': other_dict['skills_offered'],
                'skills_wanted': other_dict['skills_wanted'],
                'availability': other_dict['availability']
            },
            'match': score_data
        })

    # Sort descending by overall_score
    matches.sort(key=lambda x: x['match']['overall_score'], reverse=True)

    return jsonify({
        'current_student': {
            'id': current_student.id,
            'name': current_student.name
        },
        'matches': matches,
        'weights_explained': {
            'two_way_skill_compatibility': '50% - Evaluates skills you want that partner teaches, plus reciprocal teaching value.',
            'experience_level_compatibility': '20% - Measures mentor expertise relative to your learning goals.',
            'shared_free_time': '20% - Direct overlap between both student weekly calendars.',
            'partner_rating': '10% - Real peer reviews and teaching track record.'
        }
    })


# 3. Skill Swap Chains (3+ Circular Swaps)
@app.route('/api/swap-chains', methods=['GET'])
def get_swap_chains():
    all_students = Student.query.all()
    students_list = [s.to_dict(include_details=True) for s in all_students]

    chains = find_skill_swap_chains(students_list, min_length=3, max_length=5)

    return jsonify({
        'chains': chains,
        'count': len(chains),
        'explanation': 'A Skill Swap Chain is a multi-student circular exchange where student A teaches B, B teaches C, and C teaches A. Every student both teaches and learns without requiring direct 1-to-1 reciprocity.'
    })


# 4. Campus Skill Heatmap
@app.route('/api/heatmap', methods=['GET'])
def get_heatmap():
    skills = Skill.query.all()
    heatmap_data = []

    for sk in skills:
        offered = StudentSkill.query.filter_by(skill_id=sk.id, skill_type='offer').count()
        wanted = StudentSkill.query.filter_by(skill_id=sk.id, skill_type='want').count()
        gap = offered - wanted  # Negative means demand exceeds supply

        heatmap_data.append({
            'skill_id': sk.id,
            'name': sk.name,
            'category': sk.category,
            'offered_count': offered,
            'wanted_count': wanted,
            'gap': gap,
            'status': 'High Shortage' if gap < -2 else ('Shortage' if gap < 0 else ('Balanced' if gap == 0 else 'Surplus'))
        })

    # Sort by gap ascending (biggest shortage first)
    heatmap_data.sort(key=lambda x: x['gap'])

    return jsonify({
        'heatmap': heatmap_data,
        'total_skills': len(heatmap_data),
        'high_shortage_skills': [s for s in heatmap_data if s['gap'] < 0]
    })


# 5. Sessions Planner & Scheduling
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    student_id = request.args.get('student_id', type=int)
    status_filter = request.args.get('status')

    query = Session.query
    if student_id:
        query = query.filter((Session.mentor_id == student_id) | (Session.learner_id == student_id))
    if status_filter:
        query = query.filter(Session.status == status_filter)

    sessions = query.order_by(Session.scheduled_date.asc(), Session.start_time.asc()).all()
    return jsonify({'sessions': [s.to_dict() for s in sessions]})


@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json or {}
    mentor_id = data.get('mentor_id')
    learner_id = data.get('learner_id')
    skill_id = data.get('skill_id')
    scheduled_date = data.get('scheduled_date')
    start_time = data.get('start_time')
    duration_minutes = int(data.get('duration_minutes', 60))
    session_format = data.get('session_format', 'Virtual')
    location_or_link = data.get('location_or_link', '')

    if not all([mentor_id, learner_id, skill_id, scheduled_date, start_time]):
        return jsonify({'error': 'Missing required fields for session planning'}), 400

    if mentor_id == learner_id:
        return jsonify({'error': 'Cannot schedule a session with yourself'}), 400

    # Conflict check: Does mentor or learner have another accepted/pending session at this date & time?
    conflict = Session.query.filter(
        (Session.scheduled_date == scheduled_date) &
        (Session.start_time == start_time) &
        (Session.status.in_(['accepted', 'pending'])) &
        ((Session.mentor_id.in_([mentor_id, learner_id])) | (Session.learner_id.in_([mentor_id, learner_id])))
    ).first()

    if conflict:
        return jsonify({'error': 'Scheduling conflict: Either you or the partner already has a session booked at this time.'}), 409

    session = Session(
        mentor_id=mentor_id,
        learner_id=learner_id,
        skill_id=skill_id,
        scheduled_date=scheduled_date,
        start_time=start_time,
        duration_minutes=duration_minutes,
        session_format=session_format,
        location_or_link=location_or_link,
        status='pending'
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({'message': 'Session requested successfully', 'session': session.to_dict()}), 201


@app.route('/api/sessions/<int:session_id>/status', methods=['PUT'])
def update_session_status(session_id):
    session = Session.query.get_or_404(session_id)
    data = request.json or {}
    new_status = data.get('status')

    if new_status not in ['pending', 'accepted', 'completed', 'cancelled']:
        return jsonify({'error': 'Invalid status'}), 400

    session.status = new_status

    if new_status == 'completed':
        # Add XP to mentor and learner
        mentor = Student.query.get(session.mentor_id)
        learner = Student.query.get(session.learner_id)
        if mentor:
            mentor.add_xp(60)
        if learner:
            learner.add_xp(40)
        db.session.commit()
        # Check badges
        check_and_award_badges(session.mentor_id)
        check_and_award_badges(session.learner_id)

    db.session.commit()
    return jsonify({'message': f'Session status updated to {new_status}', 'session': session.to_dict()})


# 6. Shared Notes
@app.route('/api/sessions/<int:session_id>/notes', methods=['GET', 'POST'])
def session_notes(session_id):
    session = Session.query.get_or_404(session_id)

    if request.method == 'GET':
        note = SessionNote.query.filter_by(session_id=session.id).first()
        if not note:
            return jsonify({'note': None})
        return jsonify({'note': note.to_dict()})

    # POST (create or update)
    data = request.json or {}
    note = SessionNote.query.filter_by(session_id=session.id).first()
    if not note:
        note = SessionNote(session_id=session.id)
        db.session.add(note)

    note.topics_covered = data.get('topics_covered', '').strip()
    note.learning_outcomes = data.get('learning_outcomes', '').strip()
    note.next_steps = data.get('next_steps', '').strip()
    note.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    return jsonify({'message': 'Shared notes saved successfully', 'note': note.to_dict()})


# 7. Ratings
@app.route('/api/sessions/<int:session_id>/rate', methods=['POST'])
def rate_session(session_id):
    session = Session.query.get_or_404(session_id)
    data = request.json or {}

    reviewer_id = data.get('reviewer_id')
    stars = int(data.get('stars', 5))
    comment = data.get('comment', '').strip()

    if session.status != 'completed':
        return jsonify({'error': 'Ratings can only be submitted for completed sessions'}), 400

    if reviewer_id not in [session.mentor_id, session.learner_id]:
        return jsonify({'error': 'You were not a participant in this session'}), 403

    reviewee_id = session.learner_id if reviewer_id == session.mentor_id else session.mentor_id

    # Check duplicate
    existing = Rating.query.filter_by(session_id=session.id, reviewer_id=reviewer_id).first()
    if existing:
        return jsonify({'error': 'You have already submitted a rating for this session'}), 400

    rating = Rating(
        session_id=session.id,
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        stars=stars,
        comment=comment
    )
    db.session.add(rating)

    # If reviewee was rated 5 stars, award bonus XP
    reviewee = Student.query.get(reviewee_id)
    if reviewee and stars == 5:
        reviewee.add_xp(25)

    db.session.commit()
    check_and_award_badges(reviewee_id)

    return jsonify({'message': 'Rating submitted successfully', 'rating': rating.to_dict()})


# 8. Free-Slot Finder
@app.route('/api/free-slots', methods=['GET'])
def get_free_slots():
    student_a_id = request.args.get('student_a', type=int)
    student_b_id = request.args.get('student_b', type=int)

    if not student_a_id or not student_b_id:
        return jsonify({'error': 'Both student_a and student_b parameters are required'}), 400

    student_a = Student.query.get_or_404(student_a_id)
    student_b = Student.query.get_or_404(student_b_id)

    slots_a = [av.to_dict() for av in student_a.availabilities]
    slots_b = [av.to_dict() for av in student_b.availabilities]

    overlapping_slots, total_minutes = calculate_time_overlap(slots_a, slots_b)

    return jsonify({
        'student_a': {'id': student_a.id, 'name': student_a.name},
        'student_b': {'id': student_b.id, 'name': student_b.name},
        'overlapping_slots': overlapping_slots,
        'total_overlap_minutes': total_minutes,
        'has_overlap': total_minutes > 0
    })


# 9. Teach-Back Quiz / Key Takeaways
@app.route('/api/sessions/<int:session_id>/teach-back', methods=['GET', 'POST'])
def teach_back(session_id):
    session = Session.query.get_or_404(session_id)

    if request.method == 'GET':
        tb = TeachBack.query.filter_by(session_id=session.id).first()
        return jsonify({'teach_back': tb.to_dict() if tb else None})

    data = request.json or {}
    learner_id = data.get('learner_id')
    takeaways = data.get('takeaways', '').strip()

    if not takeaways:
        return jsonify({'error': 'Please provide 2-3 key takeaways'}), 400

    tb = TeachBack.query.filter_by(session_id=session.id).first()
    if not tb:
        tb = TeachBack(
            session_id=session.id,
            learner_id=session.learner_id,
            mentor_id=session.mentor_id,
            takeaways=takeaways,
            teacher_confirmed=False
        )
        db.session.add(tb)
    else:
        tb.takeaways = takeaways

    db.session.commit()
    return jsonify({'message': 'Key takeaways submitted for mentor confirmation', 'teach_back': tb.to_dict()})


@app.route('/api/sessions/<int:session_id>/teach-back/confirm', methods=['PUT'])
def confirm_teach_back(session_id):
    session = Session.query.get_or_404(session_id)
    tb = TeachBack.query.filter_by(session_id=session.id).first_or_404()

    data = request.json or {}
    feedback = data.get('feedback', '').strip()

    tb.teacher_confirmed = True
    tb.feedback = feedback
    tb.confirmed_at = datetime.now(timezone.utc)

    # Award learner Verified Learning badge & XP
    learner = Student.query.get(tb.learner_id)
    if learner:
        learner.add_xp(80)
        badge = Badge.query.filter_by(code='verified_learning').first()
        if badge:
            exists = StudentBadge.query.filter_by(student_id=learner.id, badge_id=badge.id).first()
            if not exists:
                db.session.add(StudentBadge(student_id=learner.id, badge_id=badge.id, awarded_at=datetime.now(timezone.utc)))
                learner.add_xp(badge.xp_reward)

    db.session.commit()
    return jsonify({'message': 'Takeaways confirmed and Verified Scholar badge awarded!', 'teach_back': tb.to_dict()})


# 10. Learning Roadmaps
@app.route('/api/roadmaps', methods=['GET'])
def get_roadmaps():
    roadmaps = Roadmap.query.all()
    result = []

    for r in roadmaps:
        r_dict = r.to_dict()
        # For each stage, find students on campus who offer this skill
        for stage in r_dict['stages']:
            skill_name = stage['skill_name']
            mentors = Student.query.join(StudentSkill).join(Skill).filter(
                Skill.name == skill_name,
                StudentSkill.skill_type == 'offer'
            ).all()

            stage['mentors'] = [{
                'id': m.id,
                'name': m.name,
                'avatar_url': m.avatar_url,
                'course': m.course
            } for m in mentors]

        result.append(r_dict)

    return jsonify({'roadmaps': result})


# 11. Achievements & Badges
@app.route('/api/badges', methods=['GET'])
def get_badges():
    badges = Badge.query.all()
    return jsonify({'badges': [b.to_dict() for b in badges]})


@app.route('/api/students/<int:student_id>/achievements', methods=['GET'])
def get_achievements(student_id):
    student = Student.query.get_or_404(student_id)
    all_badges = Badge.query.all()
    earned_badge_ids = {sb.badge_id: sb.awarded_at for sb in student.badges}

    badges_status = []
    for b in all_badges:
        earned = b.id in earned_badge_ids
        badges_status.append({
            'badge': b.to_dict(),
            'earned': earned,
            'awarded_at': earned_badge_ids[b.id].isoformat() if earned and earned_badge_ids[b.id] else None
        })

    level = student.calculate_level()
    thresholds = {1: (0, 150), 2: (150, 350), 3: (350, 650), 4: (650, 1000), 5: (1000, 2000)}
    min_xp, max_xp = thresholds.get(level, (1000, 2000))
    progress_pct = min(100, max(0, round(((student.xp - min_xp) / (max_xp - min_xp)) * 100))) if max_xp > min_xp else 100

    return jsonify({
        'student': {
            'id': student.id,
            'name': student.name,
            'xp': student.xp,
            'level': level,
            'streak_weeks': student.streak_weeks,
            'progress_pct': progress_pct,
            'next_level_xp': max_xp
        },
        'badges': badges_status
    })


# 12. Learning Report
@app.route('/api/students/<int:student_id>/report', methods=['GET'])
def get_learning_report(student_id):
    student = Student.query.get_or_404(student_id)
    s_dict = student.to_dict(include_details=True)

    # Gather completed mentored sessions
    mentored = Session.query.filter_by(mentor_id=student.id, status='completed').all()
    learned = Session.query.filter_by(learner_id=student.id, status='completed').all()

    # Calculate total teaching and learning hours
    teaching_minutes = sum(s.duration_minutes for s in mentored)
    learning_minutes = sum(s.duration_minutes for s in learned)

    # Received ratings
    ratings = Rating.query.filter_by(reviewee_id=student.id).all()

    return jsonify({
        'student': s_dict,
        'summary': {
            'teaching_hours': round(teaching_minutes / 60.0, 1),
            'learning_hours': round(learning_minutes / 60.0, 1),
            'total_completed_sessions': len(mentored) + len(learned),
            'mentored_sessions_count': len(mentored),
            'learned_sessions_count': len(learned),
            'average_rating': s_dict['rating_avg'],
            'total_ratings_received': len(ratings),
            'streak_weeks': student.streak_weeks,
            'xp': student.xp,
            'level': student.calculate_level()
        },
        'mentored_sessions': [s.to_dict() for s in mentored],
        'learned_sessions': [s.to_dict() for s in learned],
        'ratings': [r.to_dict() for r in ratings],
        'badges': s_dict['badges'],
        'skills_offered': s_dict['skills_offered'],
        'skills_wanted': s_dict['skills_wanted'],
        'generated_at': datetime.now(timezone.utc).strftime('%B %d, %Y - %H:%M UTC')
    })


# 13. Reset / Re-seed Demo Data API
@app.route('/api/demo/reset', methods=['POST'])
def reset_demo():
    seed_database()
    return jsonify({'message': 'Demo database successfully re-seeded with fresh sample data!'})


if __name__ == '__main__':
    # Initialize DB if not exists
    with app.app_context():
        db.create_all()
        if Student.query.count() == 0:
            seed_database()
    app.run(host='127.0.0.1', port=5000, debug=True)
