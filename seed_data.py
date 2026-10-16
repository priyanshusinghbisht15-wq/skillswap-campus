import json
from datetime import datetime, timedelta
from models import db, Student, Skill, StudentSkill, Availability, Session, SessionNote, Rating, Badge, StudentBadge, TeachBack, Roadmap

def seed_database():
    """Seeds the SQLite database with rich, deterministic campus demo data."""
    # Clear existing data
    db.drop_all()
    db.create_all()

    # 1. Badges
    badges_data = [
        {
            'code': 'first_session',
            'name': 'First Exchange',
            'description': 'Completed your inaugural peer learning session on SkillSwap Campus.',
            'icon': 'zap',
            'xp_reward': 50
        },
        {
            'code': 'five_star_teacher',
            'name': '5-Star Mentor',
            'description': 'Awarded a perfect 5-star rating from a peer learner for outstanding mentorship.',
            'icon': 'award',
            'xp_reward': 100
        },
        {
            'code': 'polyglot_learner',
            'name': 'Polyglot Learner',
            'description': 'Broadened horizons by learning 3 or more distinct skills across campus.',
            'icon': 'book-open',
            'xp_reward': 150
        },
        {
            'code': 'mentor_streak',
            'name': 'Streak Champion',
            'description': 'Maintained peer teaching and learning activity across 3+ consecutive weeks.',
            'icon': 'flame',
            'xp_reward': 80
        },
        {
            'code': 'verified_learning',
            'name': 'Verified Scholar',
            'description': 'Submitted key session takeaways successfully verified by peer mentor.',
            'icon': 'check-circle-2',
            'xp_reward': 120
        }
    ]

    badges_map = {}
    for b_data in badges_data:
        b = Badge(**b_data)
        db.session.add(b)
        badges_map[b_data['code']] = b
    db.session.commit()

    # 2. Skills
    skills_data = [
        ('Python', 'Software & Web', 'Core Python programming, OOP, data structures, and script automation.'),
        ('UI/UX Design', 'Design & UX', 'User research, wireframing, heuristic evaluation, and visual interface design.'),
        ('Data Structures & Algorithms', 'Computer Science', 'Arrays, linked lists, trees, graphs, sorting, and dynamic programming.'),
        ('React.js', 'Software & Web', 'Component lifecycle, hooks, state management, and modern SPA architecture.'),
        ('Machine Learning', 'Data & AI', 'Supervised learning, classification, regression, model evaluation, and scikit-learn.'),
        ('SQL & Databases', 'Data & AI', 'Relational database schema design, indexing, joins, and query optimization.'),
        ('Figma & Prototyping', 'Design & UX', 'Auto-layout, interactive prototypes, design tokens, and developer handoff.'),
        ('Cloud Computing (AWS/GCP)', 'Systems & Cloud', 'Cloud architecture, Docker, serverless functions, and CI/CD pipelines.'),
        ('Cyber Security', 'Systems & Security', 'Network security, penetration testing fundamentals, and vulnerability scanning.'),
        ('HTML & Modern CSS', 'Software & Web', 'Semantic markup, Flexbox, CSS Grid, animations, and accessible design.'),
        ('Tableau & Data Viz', 'Business & Analytics', 'Executive dashboards, visual storytelling, and business metrics analytics.'),
        ('Flutter & Mobile', 'Software & Web', 'Cross-platform mobile application development for iOS and Android.')
    ]

    skills_map = {}
    for name, cat, desc in skills_data:
        s = Skill(name=name, category=cat, description=desc)
        db.session.add(s)
        skills_map[name] = s
    db.session.commit()

    # 3. Students
    students_data = [
        {
            'name': 'Asha Patel',
            'email': 'asha.patel@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
            'course': 'Computer Science & Engineering',
            'year': '3rd Year',
            'bio': 'Passionate Python developer building web backends and data pipelines. Looking to upgrade my UI/UX Design chops for upcoming hackathon projects!',
            'xp': 420,
            'streak_weeks': 4,
            'offers': [('Python', 'Advanced'), ('SQL & Databases', 'Intermediate')],
            'wants': [('UI/UX Design', 'Beginner'), ('Data Structures & Algorithms', 'Intermediate')],
            'avail': [('Monday', '14:00', '17:00'), ('Wednesday', '15:00', '18:00'), ('Friday', '10:00', '13:00')],
            'badge_codes': ['first_session', 'five_star_teacher', 'mentor_streak']
        },
        {
            'name': 'Ben Schneider',
            'email': 'ben.schneider@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&auto=format&fit=crop&q=80',
            'course': 'Digital Media & Product Design',
            'year': '2nd Year',
            'bio': 'Product designer and Figma enthusiast. Wanting to master Data Structures and Python scripting to build interactive generative design tools.',
            'xp': 310,
            'streak_weeks': 2,
            'offers': [('UI/UX Design', 'Advanced'), ('Figma & Prototyping', 'Advanced')],
            'wants': [('Data Structures & Algorithms', 'Beginner'), ('Python', 'Beginner')],
            'avail': [('Monday', '15:00', '18:00'), ('Thursday', '14:00', '17:00'), ('Saturday', '11:00', '14:00')],
            'badge_codes': ['first_session', 'five_star_teacher']
        },
        {
            'name': 'Chitra Raman',
            'email': 'chitra.raman@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80',
            'course': 'Data Science & Systems',
            'year': '3rd Year',
            'bio': 'Competitive programmer and DSA problem-solver. Eager to master modern Python automation and explore UI/UX fundamentals for data apps.',
            'xp': 580,
            'streak_weeks': 5,
            'offers': [('Data Structures & Algorithms', 'Advanced'), ('Cloud Computing (AWS/GCP)', 'Intermediate')],
            'wants': [('Python', 'Intermediate'), ('UI/UX Design', 'Beginner')],
            'avail': [('Monday', '14:00', '17:00'), ('Wednesday', '16:00', '19:00'), ('Sunday', '10:00', '13:00')],
            'badge_codes': ['first_session', 'five_star_teacher', 'polyglot_learner', 'mentor_streak']
        },
        {
            'name': 'David Kim',
            'email': 'david.kim@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
            'course': 'Software Engineering',
            'year': '4th Year',
            'bio': 'Frontend developer and open-source enthusiast. Building clean web apps with React. Looking for an AI mentor to learn Machine Learning.',
            'xp': 260,
            'streak_weeks': 3,
            'offers': [('React.js', 'Advanced'), ('HTML & Modern CSS', 'Advanced')],
            'wants': [('Machine Learning', 'Beginner'), ('Python', 'Intermediate')],
            'avail': [('Tuesday', '13:00', '16:00'), ('Thursday', '15:00', '18:00')],
            'badge_codes': ['first_session']
        },
        {
            'name': 'Elena Rostova',
            'email': 'elena.rostova@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
            'course': 'Artificial Intelligence & Robotics',
            'year': 'Postgraduate',
            'bio': 'AI researcher focusing on deep learning and predictive modeling. Seeking a frontend collaborator to build reactive web interfaces for research models.',
            'xp': 720,
            'streak_weeks': 6,
            'offers': [('Machine Learning', 'Advanced'), ('Python', 'Advanced')],
            'wants': [('React.js', 'Intermediate'), ('UI/UX Design', 'Beginner')],
            'avail': [('Tuesday', '14:00', '17:00'), ('Thursday', '15:00', '18:00'), ('Friday', '11:00', '14:00')],
            'badge_codes': ['first_session', 'five_star_teacher', 'mentor_streak', 'verified_learning']
        },
        {
            'name': 'Farhan Ali',
            'email': 'farhan.ali@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
            'course': 'Cybersecurity & Infrastructure',
            'year': '2nd Year',
            'bio': 'Security analyst and CTF competitor. Keen on applying Machine Learning models to anomaly detection and packet analysis.',
            'xp': 180,
            'streak_weeks': 2,
            'offers': [('Cyber Security', 'Advanced')],
            'wants': [('Machine Learning', 'Beginner'), ('Python', 'Intermediate')],
            'avail': [('Wednesday', '14:00', '17:00'), ('Friday', '13:00', '16:00')],
            'badge_codes': ['first_session']
        },
        {
            'name': 'Grace Chen',
            'email': 'grace.chen@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80',
            'course': 'Cognitive Science & Computing',
            'year': '1st Year',
            'bio': 'Freshman passionate about human-computer interaction. Love crafting responsive HTML/CSS designs and wanting to learn UI/UX prototyping.',
            'xp': 90,
            'streak_weeks': 1,
            'offers': [('HTML & Modern CSS', 'Intermediate')],
            'wants': [('UI/UX Design', 'Beginner'), ('Machine Learning', 'Beginner')],
            'avail': [('Tuesday', '10:00', '13:00'), ('Thursday', '10:00', '13:00')],
            'badge_codes': ['first_session']
        },
        {
            'name': 'Harsh Vardhan',
            'email': 'harsh.vardhan@campus.edu',
            'avatar_url': 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&auto=format&fit=crop&q=80',
            'course': 'Quantitative Economics & Analytics',
            'year': '3rd Year',
            'bio': 'Financial analyst building business intelligence dashboards. Eager to master Machine Learning and Python algorithms for predictive modeling.',
            'xp': 210,
            'streak_weeks': 2,
            'offers': [('Tableau & Data Viz', 'Advanced'), ('SQL & Databases', 'Intermediate')],
            'wants': [('Machine Learning', 'Beginner'), ('Python', 'Intermediate')],
            'avail': [('Monday', '16:00', '19:00'), ('Thursday', '13:00', '16:00')],
            'badge_codes': ['first_session']
        }
    ]

    students_map = {}
    for s_raw in students_data:
        student = Student(
            name=s_raw['name'],
            email=s_raw['email'],
            avatar_url=s_raw['avatar_url'],
            course=s_raw['course'],
            year=s_raw['year'],
            bio=s_raw['bio'],
            xp=s_raw['xp'],
            streak_weeks=s_raw['streak_weeks']
        )
        db.session.add(student)
        db.session.flush()
        students_map[s_raw['name']] = student

        # Add Skills
        for sk_name, prof in s_raw['offers']:
            if sk_name in skills_map:
                ss = StudentSkill(
                    student_id=student.id,
                    skill_id=skills_map[sk_name].id,
                    skill_type='offer',
                    proficiency=prof
                )
                db.session.add(ss)

        for sk_name, prof in s_raw['wants']:
            if sk_name in skills_map:
                ss = StudentSkill(
                    student_id=student.id,
                    skill_id=skills_map[sk_name].id,
                    skill_type='want',
                    proficiency=prof
                )
                db.session.add(ss)

        # Add Availability
        for day, st, et in s_raw['avail']:
            av = Availability(
                student_id=student.id,
                day_of_week=day,
                start_time=st,
                end_time=et
            )
            db.session.add(av)

        # Add Badges
        for b_code in s_raw['badge_codes']:
            if b_code in badges_map:
                sb = StudentBadge(
                    student_id=student.id,
                    badge_id=badges_map[b_code].id,
                    awarded_at=datetime.utcnow() - timedelta(days=10)
                )
                db.session.add(sb)

    db.session.commit()

    # 4. Realistic Completed and Upcoming Sessions
    # Completed session 1: Asha mentors Ben in Python
    s1 = Session(
        mentor_id=students_map['Asha Patel'].id,
        learner_id=students_map['Ben Schneider'].id,
        skill_id=skills_map['Python'].id,
        scheduled_date=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
        start_time='15:00',
        duration_minutes=60,
        session_format='Virtual',
        location_or_link='https://meet.skillswap.edu/asha-ben-py',
        status='completed',
        created_at=datetime.utcnow() - timedelta(days=7)
    )
    db.session.add(s1)
    db.session.flush()

    # Notes for s1
    n1 = SessionNote(
        session_id=s1.id,
        topics_covered='Covered Python syntax basics, list comprehensions, dictionary operations, and reading CSV files.',
        learning_outcomes='Ben successfully wrote a script to parse design tokens and extract color palettes automatically.',
        next_steps='Next step is integrating requests library to fetch design icons from a remote API.'
    )
    db.session.add(n1)

    # Rating for s1 from Ben to Asha
    r1 = Rating(
        session_id=s1.id,
        reviewer_id=students_map['Ben Schneider'].id,
        reviewee_id=students_map['Asha Patel'].id,
        stars=5,
        comment='Asha is a phenomenal mentor! Clear explanations, patient debugging, and practical real-world exercises.'
    )
    db.session.add(r1)

    # TeachBack for s1
    tb1 = TeachBack(
        session_id=s1.id,
        learner_id=students_map['Ben Schneider'].id,
        mentor_id=students_map['Asha Patel'].id,
        takeaways='1. List comprehensions provide an elegant, readable alternative to traditional loops for transforming data.\n2. Dictionary keys must be immutable types like strings or ints.\n3. Python with statement ensures file streams close safely without leaks.',
        teacher_confirmed=True,
        feedback='Terrific summary Ben! You applied the concepts accurately in the design automation script.',
        confirmed_at=datetime.utcnow() - timedelta(days=4)
    )
    db.session.add(tb1)

    # Award Verified Learning badge to Ben
    db.session.add(StudentBadge(
        student_id=students_map['Ben Schneider'].id,
        badge_id=badges_map['verified_learning'].id,
        awarded_at=datetime.utcnow() - timedelta(days=4)
    ))

    # Completed session 2: Ben mentors Asha in UI/UX Design
    s2 = Session(
        mentor_id=students_map['Ben Schneider'].id,
        learner_id=students_map['Asha Patel'].id,
        skill_id=skills_map['UI/UX Design'].id,
        scheduled_date=(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        start_time='16:00',
        duration_minutes=60,
        session_format='In-Person',
        location_or_link='Campus Library, Group Study Room B',
        status='completed',
        created_at=datetime.utcnow() - timedelta(days=6)
    )
    db.session.add(s2)
    db.session.flush()

    n2 = SessionNote(
        session_id=s2.id,
        topics_covered='Explored typography hierarchy, 8pt spacing grid system, and micro-interactions.',
        learning_outcomes='Asha redesigned her project dashboard with cohesive visual spacing and high accessible contrast.',
        next_steps='Build out interactive states in Figma before coding CSS.'
    )
    db.session.add(n2)

    r2 = Rating(
        session_id=s2.id,
        reviewer_id=students_map['Asha Patel'].id,
        reviewee_id=students_map['Ben Schneider'].id,
        stars=5,
        comment='Ben has an amazing eye for UI design! Learned so much about spacing, layout systems, and visual balance in just 1 hour.'
    )
    db.session.add(r2)

    # Completed session 3: Elena mentors David in Machine Learning
    s3 = Session(
        mentor_id=students_map['Elena Rostova'].id,
        learner_id=students_map['David Kim'].id,
        skill_id=skills_map['Machine Learning'].id,
        scheduled_date=(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
        start_time='15:00',
        duration_minutes=90,
        session_format='Virtual',
        location_or_link='https://meet.skillswap.edu/elena-david-ml',
        status='completed',
        created_at=datetime.utcnow() - timedelta(days=8)
    )
    db.session.add(s3)
    db.session.flush()

    r3 = Rating(
        session_id=s3.id,
        reviewer_id=students_map['David Kim'].id,
        reviewee_id=students_map['Elena Rostova'].id,
        stars=5,
        comment='Elena made complex ML concepts intuitive and fun. Walked through data splitting and random forest models.'
    )
    db.session.add(r3)

    # Upcoming Session 1: Chitra to mentor Asha in Data Structures & Algorithms
    s_upcoming1 = Session(
        mentor_id=students_map['Chitra Raman'].id,
        learner_id=students_map['Asha Patel'].id,
        skill_id=skills_map['Data Structures & Algorithms'].id,
        scheduled_date=(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
        start_time='16:00',
        duration_minutes=60,
        session_format='In-Person',
        location_or_link='Turing Hall 304',
        status='accepted',
        created_at=datetime.utcnow() - timedelta(days=1)
    )
    db.session.add(s_upcoming1)

    # Upcoming Session 2: David to mentor Elena in React.js
    s_upcoming2 = Session(
        mentor_id=students_map['David Kim'].id,
        learner_id=students_map['Elena Rostova'].id,
        skill_id=skills_map['React.js'].id,
        scheduled_date=(datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d'),
        start_time='15:30',
        duration_minutes=60,
        session_format='Virtual',
        location_or_link='https://meet.skillswap.edu/david-elena-react',
        status='accepted',
        created_at=datetime.utcnow()
    )
    db.session.add(s_upcoming2)

    # Pending Session: Harsh requesting ML session from Elena
    s_pending = Session(
        mentor_id=students_map['Elena Rostova'].id,
        learner_id=students_map['Harsh Vardhan'].id,
        skill_id=skills_map['Machine Learning'].id,
        scheduled_date=(datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d'),
        start_time='14:00',
        duration_minutes=60,
        session_format='Virtual',
        location_or_link='https://meet.skillswap.edu/elena-harsh-ml',
        status='pending',
        created_at=datetime.utcnow()
    )
    db.session.add(s_pending)

    # 5. Roadmaps
    roadmaps_data = [
        {
            'title': 'Full-Stack Web Development',
            'category': 'Software & Web',
            'description': 'Master the end-to-end craft of shipping scalable web applications from responsive frontend layouts to database-backed APIs.',
            'stages': [
                {
                    'stage': 1,
                    'skill_name': 'HTML & Modern CSS',
                    'title': 'Responsive Layouts & Semantic Web',
                    'description': 'Semantic markup, Flexbox, CSS Grid layouts, and responsive media queries.',
                    'recommended_hours': 15
                },
                {
                    'stage': 2,
                    'skill_name': 'React.js',
                    'title': 'Dynamic Frontend Component Systems',
                    'description': 'Functional components, hooks (useState, useEffect), state lifting, and API data fetching.',
                    'recommended_hours': 25
                },
                {
                    'stage': 3,
                    'skill_name': 'Python',
                    'title': 'Server-Side Backend & REST APIs',
                    'description': 'Flask application architecture, routing, request validation, authentication, and error handling.',
                    'recommended_hours': 25
                },
                {
                    'stage': 4,
                    'skill_name': 'SQL & Databases',
                    'title': 'Data Persistence & Relational Schemas',
                    'description': 'Entity-relationship modeling, migrations, indexing, and complex SQL joins.',
                    'recommended_hours': 20
                }
            ]
        },
        {
            'title': 'Machine Learning Practitioner',
            'category': 'Data & AI',
            'description': 'A rigorous path taking you from foundational data engineering into training and deploying predictive machine learning models.',
            'stages': [
                {
                    'stage': 1,
                    'skill_name': 'Python',
                    'title': 'Scientific Computing & Scripting',
                    'description': 'Vectorized operations, data transformation with pandas, and exploratory data analysis.',
                    'recommended_hours': 20
                },
                {
                    'stage': 2,
                    'skill_name': 'SQL & Databases',
                    'title': 'Analytical Queries & Data Extraction',
                    'description': 'Aggregations, window functions, and preparing cleaned feature datasets.',
                    'recommended_hours': 15
                },
                {
                    'stage': 3,
                    'skill_name': 'Machine Learning',
                    'title': 'Predictive Modeling & Evaluation',
                    'description': 'Feature engineering, cross-validation, hyperparameter tuning, and ensemble algorithms.',
                    'recommended_hours': 35
                },
                {
                    'stage': 4,
                    'skill_name': 'Cloud Computing (AWS/GCP)',
                    'title': 'Model Serving & Cloud Pipeline',
                    'description': 'Containerizing inference servers with Docker and deploying serverless endpoints.',
                    'recommended_hours': 20
                }
            ]
        },
        {
            'title': 'Modern UI/UX Product Design',
            'category': 'Design & UX',
            'description': 'Bridge user empathy with production-ready user interface systems that look stunning and solve real problems.',
            'stages': [
                {
                    'stage': 1,
                    'skill_name': 'UI/UX Design',
                    'title': 'User Research & Wireframing',
                    'description': 'Information architecture, user journey mapping, wireframing, and accessibility heuristics.',
                    'recommended_hours': 20
                },
                {
                    'stage': 2,
                    'skill_name': 'Figma & Prototyping',
                    'title': 'Design Systems & High-Fidelity Prototyping',
                    'description': 'Auto-layout, design tokens, interactive components, micro-interactions, and handoff.',
                    'recommended_hours': 25
                },
                {
                    'stage': 3,
                    'skill_name': 'HTML & Modern CSS',
                    'title': 'Design-to-Code Engineering Hand-off',
                    'description': 'Translating Figma designs pixel-perfectly into clean HTML5, CSS variables, and responsive grids.',
                    'recommended_hours': 20
                }
            ]
        }
    ]

    for r_data in roadmaps_data:
        r = Roadmap(
            title=r_data['title'],
            category=r_data['category'],
            description=r_data['description'],
            stages_json=json.dumps(r_data['stages'])
        )
        db.session.add(r)

    db.session.commit()
    print("Database successfully seeded with realistic campus demo data!")

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillswap.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        seed_database()
