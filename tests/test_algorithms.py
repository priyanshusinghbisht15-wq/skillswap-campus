import unittest
from algorithms.matchmaking import calculate_match_score, calculate_time_overlap, time_to_minutes
from algorithms.chains import find_skill_swap_chains, canonical_cycle

class TestMatchmaking(unittest.TestCase):
    def setUp(self):
        self.user_asha = {
            'id': 1,
            'name': 'Asha Patel',
            'skills_offered': [
                {'skill_name': 'Python', 'proficiency': 'Advanced'},
                {'skill_name': 'SQL & Databases', 'proficiency': 'Intermediate'}
            ],
            'skills_wanted': [
                {'skill_name': 'UI/UX Design', 'proficiency': 'Beginner'},
                {'skill_name': 'Data Structures & Algorithms', 'proficiency': 'Intermediate'}
            ],
            'availability': [
                {'day_of_week': 'Monday', 'start_time': '14:00', 'end_time': '17:00'},
                {'day_of_week': 'Wednesday', 'start_time': '15:00', 'end_time': '18:00'}
            ],
            'rating_avg': 5.0,
            'rating_count': 3
        }

        self.partner_ben = {
            'id': 2,
            'name': 'Ben Schneider',
            'skills_offered': [
                {'skill_name': 'UI/UX Design', 'proficiency': 'Advanced'},
                {'skill_name': 'Figma & Prototyping', 'proficiency': 'Advanced'}
            ],
            'skills_wanted': [
                {'skill_name': 'Python', 'proficiency': 'Beginner'}
            ],
            'availability': [
                {'day_of_week': 'Monday', 'start_time': '15:00', 'end_time': '18:00'},
                {'day_of_week': 'Thursday', 'start_time': '14:00', 'end_time': '17:00'}
            ],
            'rating_avg': 4.9,
            'rating_count': 2
        }

        self.incompatible_partner = {
            'id': 99,
            'name': 'No Match',
            'skills_offered': [{'skill_name': 'Pottery', 'proficiency': 'Beginner'}],
            'skills_wanted': [{'skill_name': 'Astronomy', 'proficiency': 'Beginner'}],
            'availability': [{'day_of_week': 'Sunday', 'start_time': '08:00', 'end_time': '09:00'}],
            'rating_avg': None,
            'rating_count': 0
        }

    def test_two_way_skill_swap_detection(self):
        result = calculate_match_score(self.user_asha, self.partner_ben)
        self.assertTrue(result['is_two_way_swap'])
        self.assertIn('UI/UX Design', result['user_can_learn'])
        self.assertIn('Python', result['partner_can_learn'])
        self.assertGreaterEqual(result['overall_score'], 75)

    def test_shared_free_time_overlap(self):
        overlap_slots, total_minutes = calculate_time_overlap(
            self.user_asha['availability'],
            self.partner_ben['availability']
        )
        self.assertEqual(len(overlap_slots), 1)
        self.assertEqual(overlap_slots[0]['day_of_week'], 'Monday')
        self.assertEqual(overlap_slots[0]['start_time'], '15:00')
        self.assertEqual(overlap_slots[0]['end_time'], '17:00')
        self.assertEqual(total_minutes, 120)

    def test_incompatible_partner(self):
        result = calculate_match_score(self.user_asha, self.incompatible_partner)
        self.assertFalse(result['is_two_way_swap'])
        self.assertEqual(len(result['user_can_learn']), 0)
        self.assertEqual(len(result['partner_can_learn']), 0)
        self.assertLess(result['overall_score'], 40)


class TestSkillSwapChains(unittest.TestCase):
    def test_canonical_cycle_rotation(self):
        c1 = canonical_cycle([1, 2, 3])
        c2 = canonical_cycle([2, 3, 1])
        c3 = canonical_cycle([3, 1, 2])
        self.assertEqual(c1, c2)
        self.assertEqual(c2, c3)
        self.assertEqual(c1, (1, 2, 3))

    def test_three_person_circular_cycle_detection(self):
        # Asha -> Ben -> Chitra -> Asha
        demo_students = [
            {
                'id': 1,
                'name': 'Asha',
                'course': 'CS',
                'skills_offered': [{'skill_name': 'Python'}],
                'skills_wanted': [{'skill_name': 'Data Structures'}]
            },
            {
                'id': 2,
                'name': 'Ben',
                'course': 'Design',
                'skills_offered': [{'skill_name': 'UI Design'}],
                'skills_wanted': [{'skill_name': 'Python'}]
            },
            {
                'id': 3,
                'name': 'Chitra',
                'course': 'Data Science',
                'skills_offered': [{'skill_name': 'Data Structures'}],
                'skills_wanted': [{'skill_name': 'UI Design'}]
            }
        ]

        chains = find_skill_swap_chains(demo_students, min_length=3, max_length=5)
        self.assertEqual(len(chains), 1)
        chain = chains[0]
        self.assertEqual(chain['length'], 3)
        self.assertEqual(set(chain['student_ids']), {1, 2, 3})
        
        # Verify steps and circular teaching
        steps = chain['steps']
        self.assertEqual(len(steps), 3)
        for s in steps:
            self.assertTrue(bool(s['teaches_skill']))
            self.assertTrue(bool(s['receives_skill']))

    def test_empty_when_no_cycle(self):
        no_cycle_students = [
            {
                'id': 1,
                'name': 'A',
                'course': 'CS',
                'skills_offered': [{'skill_name': 'Python'}],
                'skills_wanted': [{'skill_name': 'Rust'}]
            },
            {
                'id': 2,
                'name': 'B',
                'course': 'CS',
                'skills_offered': [{'skill_name': 'Java'}],
                'skills_wanted': [{'skill_name': 'Go'}]
            }
        ]
        chains = find_skill_swap_chains(no_cycle_students, min_length=3)
        self.assertEqual(len(chains), 0)


if __name__ == '__main__':
    unittest.main()
