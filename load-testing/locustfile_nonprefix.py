from locust import task, between
from locust.contrib.fasthttp import FastHttpUser  # 切换到极速异步引擎
import random

# 真实常用单词
WORD_BANK = ["the", "project", "system", "data", "model", "test", "user", "server", "performance", "query"]

def make_long_prompt(min_words=450, max_words=500):
    words = random.randint(min_words, max_words)
    return " ".join(random.choices(WORD_BANK, k=words))

class AsyncBatchingUser(FastHttpUser):
    # 用户之间稍微错开一点时间，避免瞬时大浪涌
    wait_time = between(0.1, 0.5)

    @task
    def send_to_server(self):
        payload = {
            "model": "Qwen/Qwen2.5-7B",
            "messages": [{"role": "user", "content": make_long_prompt(450, 500)}],
            "max_tokens": 150,  # 稍微调小一点生成长度（比如150），让请求快速结束，方便我们看吞吐
            "temperature": 0.7,
            "stream": False     # 非流式，完整测出单次吞吐
        }
        
        # FastHttpUser 会自动拼接 `--host` 里的地址
        with self.client.post("/v1/chat/completions", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}, Error: {response.text}")