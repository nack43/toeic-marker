import unittest
import app


class TestCaculateAnswerRatio(unittest.TestCase):

	def test_correct(self):
		actual = 


SELECT ua.problem_id, p.part_id, ua.user_answer, p.correct_answer FROM user_answer ua INNER JOIN exam_date ed ON ua.exam_date_id = ed.exam_date_id INNER JOIN problem p ON p.problem_id = ua.problem_id AND p.exam_id = ed.exam_id WHERE ua.exam_date_id=1

