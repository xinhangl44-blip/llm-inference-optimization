from locust import HttpUser, task, between
import random, string

def make_long_prompt(min_words=450, max_words=500):
    words = random.randint(min_words, max_words)
    return " ".join(random.choices(string.ascii_lowercase, k=words))

class BatchingUser(HttpUser):
    wait_time = between(0.2, 0.4)

    @task
    def send_to_server(self):
        payload = {
            "model": "Qwen/Qwen3-8B-FP8",
            "messages": [{"role": "user", "content": make_long_prompt(450, 500)}],
            "max_tokens": 400,
            "temperature": 0.7
        }
        self.client.post("/v1/chat/completions", json=payload, name="Result")