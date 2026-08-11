from locust import HttpUser, task, between
import random
import string

def make_long_prompt(min_words, max_words):
    words = random.randint(min_words, max_words)
    return " ".join(random.choices(string.ascii_lowercase, k=words))

class NonPrefixUser(HttpUser):
    wait_time = between(0.2, 0.4)

    @task
    def send_to_server(self):
        random_long_prefix = make_long_prompt(300, 340)
        dynamic_suffix = make_long_prompt(50, 60)
        full_content = random_long_prefix + " " + dynamic_suffix
        payload = {
            "model": "Qwen/Qwen3-8B-FP8",
            "messages": [{"role": "user", "content": full_content}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        self.client.post("/v1/chat/completions", json=payload, name="Result_NonPrefix")