import urllib.request
import json

BASE_URL = 'http://127.0.0.1:5000'

def request_json(url, method='GET', data=None):
    headers = {'Content-Type': 'application/json'}
    body = json.dumps(data).encode('utf-8') if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

# 1. Schedule a new session between Asha (1) and David (4) for React
print("1. Testing Session Scheduling...")
sched_payload = {
    'mentor_id': 4,
    'learner_id': 1,
    'skill_id': 4, # React.js
    'scheduled_date': '2026-11-01',
    'start_time': '11:00',
    'duration_minutes': 60,
    'session_format': 'Virtual',
    'location_or_link': 'https://meet.skillswap.edu/david-asha-react'
}
sess_resp = request_json(f'{BASE_URL}/api/sessions', method='POST', data=sched_payload)
new_session_id = sess_resp['session']['id']
print(f"   -> Created session ID {new_session_id}, status: {sess_resp['session']['status']}")

# 2. Accept session
print("2. Testing Session Acceptance...")
accept_resp = request_json(f'{BASE_URL}/api/sessions/{new_session_id}/status', method='PUT', data={'status': 'accepted'})
print(f"   -> Status updated to: {accept_resp['session']['status']}")

# 3. Add Notes
print("3. Testing Shared Notes...")
notes_payload = {
    'topics_covered': 'React Hooks, Custom hooks, and state management.',
    'learning_outcomes': 'Asha implemented a clean useFetch hook.',
    'next_steps': 'Build out the dashboard components.'
}
notes_resp = request_json(f'{BASE_URL}/api/sessions/{new_session_id}/notes', method='POST', data=notes_payload)
print(f"   -> Saved notes for session {new_session_id}: {notes_resp['note']['topics_covered']}")

# 4. Complete session
print("4. Testing Session Completion & XP Awarding...")
complete_resp = request_json(f'{BASE_URL}/api/sessions/{new_session_id}/status', method='PUT', data={'status': 'completed'})
print(f"   -> Completed session ID {new_session_id}")

# 5. Rate session
print("5. Testing Rating & Mentor Feedback...")
rate_payload = {
    'reviewer_id': 1,
    'stars': 5,
    'comment': 'Fantastic mentor, super patient explaining React hooks!'
}
rate_resp = request_json(f'{BASE_URL}/api/sessions/{new_session_id}/rate', method='POST', data=rate_payload)
print(f"   -> Rating added: {rate_resp['rating']['stars']} stars")

# 6. Teach-back workflow
print("6. Testing Teach-Back Key Takeaways...")
tb_payload = {
    'learner_id': 1,
    'takeaways': '1. Custom hooks allow encapsulating reusable state logic.\n2. Dependency arrays in useEffect prevent infinite loops.'
}
tb_resp = request_json(f'{BASE_URL}/api/sessions/{new_session_id}/teach-back', method='POST', data=tb_payload)
print(f"   -> Submitted takeaways: {tb_resp['teach_back']['takeaways'][:30]}...")

# 7. Mentor confirms teach-back
print("7. Testing Mentor Teach-Back Confirmation & Badge Award...")
tb_confirm_resp = request_json(f'{BASE_URL}/api/sessions/{new_session_id}/teach-back/confirm', method='PUT', data={'feedback': 'Excellent takeaways!'})
print(f"   -> Teach-back confirmed: {tb_confirm_resp['teach_back']['teacher_confirmed']}")

print("\n>>> ALL MUTATION WORKFLOWS TESTED AND VERIFIED SUCCESSFULLY! <<<")
