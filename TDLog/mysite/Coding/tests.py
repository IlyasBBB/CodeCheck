import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Domain, InitialTest, Membre, Problem, Submission
from .views import create_default_questions, execute_code

SQUARE_CASES = json.dumps([{"input": "5", "expected": "25"}, {"input": "3", "expected": "9"}])


def new_member(username="alice", **extra):
    user = User.objects.create_user(username=username, password="mot-de-passe-test-123")
    return Membre.objects.create(user=user, nom="Test", prenom=username, telephone="", email=f"{username}@ex.test",
                                 **extra)


class LevelTests(TestCase):
    def test_level_thresholds(self):
        membre = new_member()
        for points, level in ((0, 0), (99, 0), (100, 1), (399, 1), (400, 2), (700, 3)):
            membre.points = points
            membre.update_level()
            self.assertEqual(membre.level, level, points)

    def test_update_level_reports_change(self):
        membre = new_member(points=100)
        self.assertEqual(membre.update_level(), (True, 0, 1))
        self.assertEqual(membre.update_level(), (False, 1, 1))


class ExecuteCodeTests(TestCase):
    def test_correct_solution_passes(self):
        result = execute_code("def solution(n):\n    return n * n", SQUARE_CASES)
        self.assertTrue(result["passed"], result["output"])

    def test_wrong_solution_fails(self):
        result = execute_code("def solution(n):\n    return n + n", SQUARE_CASES)
        self.assertFalse(result["passed"])
        self.assertIn("Expected=9, Got=6", result["output"])

    def test_syntax_error_is_reported(self):
        result = execute_code("def solution(n) return n", SQUARE_CASES)
        self.assertFalse(result["passed"])
        self.assertIn("SyntaxError", result["output"])

    def test_infinite_loop_times_out(self):
        result = execute_code("def solution(n):\n    while True:\n        pass", json.dumps([{"input": "1",
                                                                                          "expected": "1"}]))
        self.assertFalse(result["passed"])
        self.assertIn("timed out", result["output"])

    def test_user_code_cannot_read_server_environment(self):
        code = "import os\ndef solution(n):\n    return os.environ.get('DJANGO_SECRET_KEY', 'absent')"
        result = execute_code(code, json.dumps([{"input": "0", "expected": "absent"}]))
        self.assertTrue(result["passed"], result["output"])


class SubmissionTests(TestCase):
    def setUp(self):
        self.membre = new_member(has_completed_initial_test=True, level=1)
        domain = Domain.objects.create(name="Basics", description="-", icon="fas fa-code")
        self.problem = Problem.objects.create(title="Square", description="-", difficulty="easy", domain=domain,
                                              test_cases=SQUARE_CASES, points=10, penalty_points=5)
        self.client.force_login(self.membre.user)
        self.url = reverse("coding:submit_solution", args=[self.problem.id])

    def submit(self, code, **extra):
        return self.client.post(self.url, json.dumps({"code": code, **extra}), content_type="application/json").json()

    def test_points_awarded_once_per_problem(self):
        good = "def solution(n):\n    return n * n"
        self.assertEqual(self.submit(good)["points"], 10)
        self.assertEqual(self.submit(good)["points"], 0)
        self.membre.refresh_from_db()
        self.assertEqual(self.membre.points, 10)
        self.assertEqual(Submission.objects.filter(status="S").count(), 2)

    def test_time_penalty(self):
        self.assertEqual(self.submit("def solution(n):\n    return n * n", time_exceeded=True)["points"], 5)

    def test_failed_submission_is_recorded(self):
        self.assertFalse(self.submit("def solution(n):\n    return 0")["passed"])
        self.assertEqual(Submission.objects.get().status, "F")

    def test_give_up_costs_twenty_points(self):
        self.membre.points = 30
        self.membre.save()
        rep = self.client.post(reverse("coding:give_up_problem", args=[self.problem.id])).json()
        self.assertEqual(rep["new_total_points"], 10)


class InitialTestTests(TestCase):
    def setUp(self):
        create_default_questions()
        self.membre = new_member()
        self.client.force_login(self.membre.user)
        self.first = InitialTest.objects.order_by("id").first()

    def test_score_ignores_points_sent_by_the_browser(self):
        forged = [{"id": q.id, "points": q.points} for q in InitialTest.objects.all()]
        rep = self.client.post(reverse("coding:complete_initial_test"), json.dumps({"solved_questions": forged}),
                               content_type="application/json").json()
        self.assertEqual((rep["points"], rep["level"]), (0, "Débutant"))

    def test_score_counts_questions_passed_on_the_server(self):
        self.client.post(reverse("coding:submit_initial_test"),
                         json.dumps({"question_id": self.first.id, "code": "def solution(n):\n    return n * n"}),
                         content_type="application/json")
        rep = self.client.post(reverse("coding:complete_initial_test"), "{}", content_type="application/json").json()
        self.assertEqual(rep["points"], self.first.points)
        self.membre.refresh_from_db()
        self.assertTrue(self.membre.has_completed_initial_test)

    def test_initial_test_cannot_be_taken_twice(self):
        self.membre.has_completed_initial_test = True
        self.membre.save()
        self.assertRedirects(self.client.get(reverse("coding:initial_test")), reverse("coding:problems"))


class AccessTests(TestCase):
    def test_pages_require_login(self):
        for name in ("coding:profile", "coding:problems", "coding:initial_test"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)

    def test_account_without_member_profile_does_not_crash(self):
        admin = User.objects.create_superuser("admin", "a@ex.test", "mot-de-passe-test-123")
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("coding:home")).status_code, 200)

    def test_register_creates_member_and_starts_initial_test(self):
        rep = self.client.post(reverse("coding:register"), {
            "username": "bob", "password1": "un-mot-de-passe-long", "password2": "un-mot-de-passe-long",
            "email": "bob@ex.test", "nom": "Test", "prenom": "Bob"})
        self.assertRedirects(rep, reverse("coding:initial_test"), fetch_redirect_response=False)
        self.assertTrue(Membre.objects.filter(user__username="bob").exists())
