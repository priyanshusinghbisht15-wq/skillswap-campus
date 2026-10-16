def time_to_minutes(time_str):
    """Converts 'HH:MM' string to minutes from midnight."""
    try:
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0

def minutes_to_time(minutes):
    """Converts minutes from midnight to 'HH:MM' string."""
    h = (minutes // 60) % 24
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def calculate_time_overlap(slots_a, slots_b):
    """
    Computes shared free time intervals and total overlapping minutes.
    slots_a, slots_b: list of dicts with 'day_of_week', 'start_time', 'end_time'
    """
    overlapping_slots = []
    total_minutes = 0

    for a in slots_a:
        day_a = a.get('day_of_week')
        start_a = time_to_minutes(a.get('start_time', '00:00'))
        end_a = time_to_minutes(a.get('end_time', '00:00'))

        for b in slots_b:
            if b.get('day_of_week') == day_a:
                start_b = time_to_minutes(b.get('start_time', '00:00'))
                end_b = time_to_minutes(b.get('end_time', '00:00'))

                overlap_start = max(start_a, start_b)
                overlap_end = min(end_a, end_b)

                if overlap_end > overlap_start:
                    duration = overlap_end - overlap_start
                    total_minutes += duration
                    overlapping_slots.append({
                        'day_of_week': day_a,
                        'start_time': minutes_to_time(overlap_start),
                        'end_time': minutes_to_time(overlap_end),
                        'duration_minutes': duration
                    })

    return overlapping_slots, total_minutes

def calculate_match_score(user_data, partner_data):
    """
    Calculates a transparent compatibility score between user and partner.
    Weights:
      - Two-way skill compatibility: 50%
      - Experience level compatibility: 20%
      - Shared free time: 20%
      - Partner rating: 10%

    All sub-scores normalized between 0 and 100.
    """
    # 1. Skill Compatibility (50%)
    # Skills user wants that partner offers
    user_wants = {s['skill_name'].lower(): s for s in user_data.get('skills_wanted', [])}
    partner_offers = {s['skill_name'].lower(): s for s in partner_data.get('skills_offered', [])}

    # Skills partner wants that user offers (mutual swap)
    partner_wants = {s['skill_name'].lower(): s for s in partner_data.get('skills_wanted', [])}
    user_offers = {s['skill_name'].lower(): s for s in user_data.get('skills_offered', [])}

    user_can_learn = [s_name for s_name in user_wants if s_name in partner_offers]
    partner_can_learn = [s_name for s_name in partner_wants if s_name in user_offers]

    skill_score = 0
    skill_reason = ""
    is_two_way_swap = False

    if not user_can_learn and not partner_can_learn:
        skill_score = 0
        skill_reason = "No matching teaching or learning skills found."
    elif user_can_learn and partner_can_learn:
        # Full two-way reciprocal swap!
        is_two_way_swap = True
        base = 80
        bonus = min(20, (len(user_can_learn) - 1) * 10 + (len(partner_can_learn) - 1) * 10)
        skill_score = min(100, base + bonus)
        user_learn_str = ", ".join([partner_offers[k]['skill_name'] for k in user_can_learn])
        partner_learn_str = ", ".join([user_offers[k]['skill_name'] for k in partner_can_learn])
        skill_reason = f"Mutual Skill Swap! You can learn {user_learn_str} and teach {partner_learn_str}."
    elif user_can_learn:
        # One-way: Partner can mentor User
        base = 65
        bonus = min(25, (len(user_can_learn) - 1) * 15)
        skill_score = min(90, base + bonus)
        user_learn_str = ", ".join([partner_offers[k]['skill_name'] for k in user_can_learn])
        skill_reason = f"Partner offers {user_learn_str} which you want to learn."
    else:
        # One-way: User can mentor Partner
        base = 40
        bonus = min(20, (len(partner_can_learn) - 1) * 10)
        skill_score = min(60, base + bonus)
        partner_learn_str = ", ".join([user_offers[k]['skill_name'] for k in partner_can_learn])
        skill_reason = f"You can mentor partner in {partner_learn_str}."

    # 2. Experience Level Compatibility (20%)
    level_weights = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
    exp_scores = []
    exp_reason = ""

    for s_name in user_can_learn:
        p_lvl = level_weights.get(partner_offers[s_name].get('proficiency', '').lower(), 2)
        u_lvl = level_weights.get(user_wants[s_name].get('proficiency', '').lower(), 2)
        
        if p_lvl > u_lvl:
            exp_scores.append(100) # Mentor is more advanced than learner
        elif p_lvl == u_lvl:
            exp_scores.append(85 if p_lvl >= 2 else 70)
        else:
            exp_scores.append(50) # Learner is same or higher

    if exp_scores:
        exp_score = sum(exp_scores) / len(exp_scores)
        if exp_score >= 90:
            exp_reason = "Excellent level fit: Mentor holds advanced proficiency in your target skill."
        elif exp_score >= 70:
            exp_reason = "Good level alignment: Strong practical match for collaborative learning."
        else:
            exp_reason = "Moderate level alignment: Both students can share peer practice."
    elif partner_can_learn:
        exp_score = 75
        exp_reason = "Peer experience level compatible for knowledge transfer."
    else:
        exp_score = 50
        exp_reason = "Standard baseline proficiency compatibility."

    # 3. Shared Free Time (20%)
    user_avail = user_data.get('availability', [])
    partner_avail = partner_data.get('availability', [])

    time_score = 50
    time_reason = ""
    overlap_slots, total_overlap_minutes = calculate_time_overlap(user_avail, partner_avail)

    if not user_avail or not partner_avail:
        time_score = 50
        time_reason = "Availability data pending for one or both students (neutral score applied)."
    else:
        if total_overlap_minutes >= 120:
            time_score = 100
            time_reason = f"Optimal schedule match: {total_overlap_minutes} mins of shared free time weekly."
        elif total_overlap_minutes > 0:
            time_score = round((total_overlap_minutes / 120.0) * 100)
            time_reason = f"Compatible schedule: {total_overlap_minutes} mins overlapping time available."
        else:
            time_score = 15
            time_reason = "No direct weekly schedule overlap found; flexible scheduling needed."

    # 4. Partner Rating (10%)
    rating_avg = partner_data.get('rating_avg')
    rating_count = partner_data.get('rating_count', 0)

    if rating_avg is not None and rating_count > 0:
        # Scale 1-5 to 0-100
        rating_score = round((rating_avg / 5.0) * 100)
        rating_reason = f"Proven mentor reputation: {rating_avg:.1f} / 5.0 stars ({rating_count} review{'s' if rating_count != 1 else ''})."
    else:
        # Fair starting neutral score without inventing data
        rating_score = 75
        rating_reason = "New campus mentor with trusted baseline starting score (75%)."

    # Composite Match Score Calculation
    final_score = (
        0.50 * skill_score +
        0.20 * exp_score +
        0.20 * time_score +
        0.10 * rating_score
    )
    final_score = max(0, min(100, round(final_score)))

    # Match summary headline
    if final_score >= 80:
        match_tier = "Excellent Match"
    elif final_score >= 60:
        match_tier = "Strong Match"
    elif final_score >= 40:
        match_tier = "Moderate Match"
    else:
        match_tier = "Low Match"

    return {
        'overall_score': final_score,
        'match_tier': match_tier,
        'is_two_way_swap': is_two_way_swap,
        'user_can_learn': [partner_offers[k]['skill_name'] for k in user_can_learn],
        'partner_can_learn': [user_offers[k]['skill_name'] for k in partner_can_learn],
        'breakdown': {
            'skill_compatibility': {
                'score': round(skill_score),
                'weight': '50%',
                'reason': skill_reason
            },
            'experience_compatibility': {
                'score': round(exp_score),
                'weight': '20%',
                'reason': exp_reason
            },
            'shared_free_time': {
                'score': round(time_score),
                'weight': '20%',
                'reason': time_reason,
                'overlap_minutes': total_overlap_minutes,
                'overlap_slots': overlap_slots
            },
            'partner_rating': {
                'score': round(rating_score),
                'weight': '10%',
                'reason': rating_reason
            }
        }
    }
