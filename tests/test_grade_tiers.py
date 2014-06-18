import os, sys
sys.path.insert(0, os.path.abspath(".."))
import unittest

from grades import GradeTiers

class GradeTiersTestCase(unittest.TestCase):
    def setUp(self):
        # Put these in backwards so we know that sort_before_run works
        self.grade_tiers = GradeTiers([(100, 'A'),
                                       (92, 'A-'),
                                       (89, 'B+'),
                                       (85, 'B'),
                                       (82, 'B-'),
                                       (79, 'C+'),
                                       (75, 'C'),
                                       (72, 'C-'),
                                       (69, 'D+'),
                                       (65, 'D'),
                                       (62, 'D-'),
                                       (59, 'F')
                                      ])

    def tearDown(self):
        self.grade_tiers = None

# TODO: Figure out how to test decorators
#    def test_sort_before_run(self):
#        class ExtendedGradeTiers(GradeTiers):
#            @GradeTiers.sort_before_run
#            def do_nothing(self):
#                pass
#        extended_grade_tiers = ExtendedGradeTiers(self.grade_tiers)
#        highest = float('-inf')
#        for percentile_grade in extended_grade_tiers.tiers:
#            print '%', percentile_grade
#            self.assertGreater(percentile_grade, highest, 'Percentile grade was not highest found')
#            highest = percentile_grade

    def test_letter(self):
        percentile_grade = 71
        expected_letter = 'C-'
        actual_letter = self.grade_tiers.letter(percentile_grade)
        self.assertEqual(expected_letter,
                         actual_letter,
                         'Percentile grade conversion from {0} to {1}, got {2}'
                         .format(percentile_grade,
                                 expected_letter,
                                 actual_letter))

if __name__ == '__main__':
    unittest.main()
