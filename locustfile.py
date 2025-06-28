# locustfile.py

from locust import HttpUser, task, between
import json, random

class StudentUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        username = f"teststudent{random.randint(1,1000)}"
        password = "testpassword"
        resp = self.client.post("/accounts/login/", {
            "username": username,
            "password": password
        }, allow_redirects=True)
        assert resp.status_code in [200, 302]
        self.client.cookies.set("course_id", "1")

    @task
    def submit_quiz(self):
        answers = {str(i): random.choice(["Option1","Option2","Option3","Option4"]) for i in range(1,11)}
        resp = self.client.post(
            "/student/calculate_marks",
            data=json.dumps(answers),
            headers={"Content-Type": "application/json"}
        )
        if resp.status_code != 200:
            print("❌", resp.status_code, resp.text)
