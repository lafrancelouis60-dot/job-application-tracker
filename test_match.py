import unittest
from app import rank_jobs


class MatchTests(unittest.TestCase):
    def test_ranking(self):
        jobs = [
            {"job_id": 1, "job_title": "Analyst", "requirements": ["SQL", "Python", "Power BI"]},
            {"job_id": 2, "job_title": "Reporting", "requirements": ["SQL", "Power BI"]},
        ]
        results = rank_jobs(jobs, "sql, SQL, Power BI")
        self.assertEqual([job["percent"] for job in results], [100, 67])
        self.assertEqual(results[1]["missing"], ["python"])

    def test_no_match(self):
        jobs = [{"job_id": 1, "job_title": "Analyst", "requirements": ["SQL"]}]
        self.assertEqual(rank_jobs(jobs, "Excel")[0]["percent"], 0)

    def test_no_requirements(self):
        jobs = [{"job_id": 1, "job_title": "Intern", "requirements": []}]
        self.assertIsNone(rank_jobs(jobs, "SQL")[0]["percent"])


if __name__ == "__main__":
    unittest.main()