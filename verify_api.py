import urllib.request
import json

def test_endpoint(name, url):
    req = urllib.request.urlopen(url)
    code = req.getcode()
    data = req.read().decode('utf-8')
    print(f"[{code}] {name}: {len(data)} characters")
    return json.loads(data)

# 1. HTML Home
html_req = urllib.request.urlopen('http://127.0.0.1:5000/')
print(f"[{html_req.getcode()}] Home HTML: {len(html_req.read())} bytes")

# 2. Students API
students = test_endpoint('Students API', 'http://127.0.0.1:5000/api/students')
print(f"   -> Total students: {students['count']}")

# 3. Matchmaking API
matches = test_endpoint('Matchmaking API (Asha)', 'http://127.0.0.1:5000/api/matchmaking/1')
top = matches['matches'][0]
print(f"   -> Top match for Asha: {top['partner']['name']} with score {top['match']['overall_score']}% ({top['match']['match_tier']})")
print(f"   -> 2-way swap? {top['match']['is_two_way_swap']}")
print(f"   -> Breakdown: Skill {top['match']['breakdown']['skill_compatibility']['score']}%, Exp {top['match']['breakdown']['experience_compatibility']['score']}%, Time {top['match']['breakdown']['shared_free_time']['score']}%, Rating {top['match']['breakdown']['partner_rating']['score']}%")

# 4. Swap Chains API
chains = test_endpoint('Swap Chains API', 'http://127.0.0.1:5000/api/swap-chains')
print(f"   -> Discovered swap chains: {chains['count']}")
if chains['count'] > 0:
    c = chains['chains'][0]
    print(f"   -> Chain 1: {c['summary']}")
    print(f"   -> Steps count: {len(c['steps'])}")
    print(f"   -> Reason: {c['explanation']}")

# 5. Heatmap API
heat = test_endpoint('Heatmap API', 'http://127.0.0.1:5000/api/heatmap')
print(f"   -> Total skills tracked: {heat['total_skills']}")
shortage = heat['high_shortage_skills'][0]
print(f"   -> Top shortage: {shortage['name']} (Offered: {shortage['offered_count']}, Wanted: {shortage['wanted_count']}, Gap: {shortage['gap']})")

# 6. Roadmaps API
roadmaps = test_endpoint('Roadmaps API', 'http://127.0.0.1:5000/api/roadmaps')
print(f"   -> Roadmaps: {len(roadmaps['roadmaps'])} learning pathways loaded")

# 7. Achievements API
ach = test_endpoint('Achievements API (Asha)', 'http://127.0.0.1:5000/api/students/1/achievements')
earned = [b for b in ach['badges'] if b['earned']]
print(f"   -> Asha Level: {ach['student']['level']} ({ach['student']['xp']} XP), Earned Badges: {len(earned)}")

# 8. Report API
rep = test_endpoint('Learning Report API (Asha)', 'http://127.0.0.1:5000/api/students/1/report')
print(f"   -> Asha Teaching: {rep['summary']['teaching_hours']}h, Learning: {rep['summary']['learning_hours']}h, Rating: {rep['summary']['average_rating']}")

print("\n>>> ALL API ENDPOINTS TESTED AND VALIDATED SUCCESSFULLY! <<<")
