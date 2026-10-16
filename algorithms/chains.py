from collections import defaultdict

def canonical_cycle(cycle_nodes):
    """
    Returns the rotation of cycle_nodes starting with the minimum node ID.
    This guarantees that [1, 2, 3], [2, 3, 1], and [3, 1, 2] produce the exact same tuple.
    """
    min_idx = cycle_nodes.index(min(cycle_nodes))
    return tuple(cycle_nodes[min_idx:] + cycle_nodes[:min_idx])

def find_skill_swap_chains(students_list, min_length=3, max_length=5):
    """
    Finds circular multi-student skill exchanges of length >= 3 using directed graph cycle finding.
    students_list: list of student dictionaries with 'id', 'name', 'avatar_url', 'skills_offered', 'skills_wanted'.
    Returns a list of structured chain objects.
    """
    # 1. Build adjacency graph
    # Node = student_id
    # Edge A -> B exists if Student A offers a skill that Student B wants.
    students_by_id = {s['id']: s for s in students_list}
    
    # Pre-index skills
    # offers[student_id] = {skill_name.lower(): (skill_name, proficiency)}
    # wants[student_id] = {skill_name.lower(): (skill_name, proficiency)}
    offers = {}
    wants = {}
    for s in students_list:
        s_id = s['id']
        offers[s_id] = {
            sk['skill_name'].lower(): sk['skill_name'] 
            for sk in s.get('skills_offered', [])
        }
        wants[s_id] = {
            sk['skill_name'].lower(): sk['skill_name'] 
            for sk in s.get('skills_wanted', [])
        }

    # adj[u] = list of (v, skill_name_taught_by_u_to_v)
    adj = defaultdict(dict)
    for u_id in students_by_id:
        for v_id in students_by_id:
            if u_id == v_id:
                continue
            # Find what u offers that v wants
            common_skills = [
                offers[u_id][sk] 
                for sk in offers[u_id] 
                if sk in wants[v_id]
            ]
            if common_skills:
                # Store the primary matched skill
                adj[u_id][v_id] = common_skills[0]

    # 2. Find elementary directed cycles using DFS
    found_cycles = set()
    all_chains = []

    def dfs(start_node, current_node, path, visited):
        if len(path) > max_length:
            return

        for next_node, skill_taught in adj[current_node].items():
            if next_node == start_node:
                # Cycle closed! Check length >= min_length
                if len(path) >= min_length:
                    c_key = canonical_cycle(path)
                    if c_key not in found_cycles:
                        found_cycles.add(c_key)
                        chain_obj = format_chain(list(c_key), adj, students_by_id)
                        all_chains.append(chain_obj)
            elif next_node not in visited and len(path) < max_length:
                visited.add(next_node)
                path.append(next_node)
                dfs(start_node, next_node, path, visited)
                path.pop()
                visited.remove(next_node)

    all_student_ids = sorted(list(students_by_id.keys()))
    for s_id in all_student_ids:
        dfs(s_id, s_id, [s_id], {s_id})

    # Sort chains by length (shorter 3-person cycles first, easiest to coordinate)
    all_chains.sort(key=lambda c: len(c['steps']))
    return all_chains

def format_chain(cycle_ids, adj, students_by_id):
    """
    Constructs a rich UI-ready representation of the circular swap.
    cycle_ids: [A, B, C] where A -> B -> C -> A
    """
    n = len(cycle_ids)
    steps = []
    explanation_parts = []

    for i in range(n):
        curr_id = cycle_ids[i]
        next_id = cycle_ids[(i + 1) % n]
        prev_id = cycle_ids[(i - 1 + n) % n]

        curr_student = students_by_id[curr_id]
        next_student = students_by_id[next_id]
        prev_student = students_by_id[prev_id]

        teaches_skill = adj[curr_id][next_id]
        receives_skill = adj[prev_id][curr_id]

        steps.append({
            'student_id': curr_id,
            'name': curr_student['name'],
            'course': curr_student['course'],
            'avatar_url': curr_student.get('avatar_url'),
            'teaches_skill': teaches_skill,
            'teaches_to_id': next_id,
            'teaches_to_name': next_student['name'],
            'receives_skill': receives_skill,
            'receives_from_id': prev_id,
            'receives_from_name': prev_student['name']
        })

        explanation_parts.append(
            f"<strong>{curr_student['name']}</strong> teaches <em>{teaches_skill}</em> to <strong>{next_student['name']}</strong>"
        )

    explanation = "; ".join(explanation_parts) + ". Everyone receives a skill they want and gives back a skill they know!"

    return {
        'chain_id': f"chain_{'_'.join(str(i) for i in cycle_ids)}",
        'length': n,
        'student_ids': cycle_ids,
        'summary': f"{n}-Way Circular Skill Exchange ({', '.join(students_by_id[i]['name'] for i in cycle_ids)})",
        'explanation': explanation,
        'steps': steps
    }
