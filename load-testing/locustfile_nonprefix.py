from locust import task, between
from locust.contrib.fasthttp import FastHttpUser 
import random
WORD_BANK = ["the", "project", "system", "data", "model", "test", "user", "server", "performance", "query"]
def make_long_prompt(min_words=450, max_words=500):
    words = random.randint(min_words, max_words)
    return " ".join(random.choices(WORD_BANK, k=words))

class AsyncBatchingUser(FastHttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def send_to_server(self):
        payload = {
            "model": "Qwen/Qwen2.5-7B",
            "messages": [{"role": "user", "content": make_long_prompt(450, 500)}],
            "max_tokens": 150,  
            "temperature": 0.7,
            "stream": False    
        }

        with self.client.post("/v1/chat/completions", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}, Error: {response.text}")
