import os
import sys
import time
import signal
import requests
import redis

sys.stdout.reconfigure(line_buffering=True)
running = True

def handle_signal(signum, frame):
    global running
    print(f"[Signal] Received signal {signum}. Initiating graceful shutdown...")
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

r = redis.Redis(
    host="redis-0.redis-headless.default.svc.cluster.local",
    port=6379,
    password="lixinhang11",
    decode_responses=True,
    socket_timeout=5
)

CONSUMER_NAME = os.getenv("HOSTNAME", "vllm_worker_node_1")
GROUP_NAME    = "vllm_inference_group"
STREAM_NAME   = "vllm_task_stream"
VLLM_URL      = "http://vllm-gateway-service.default.svc.cluster.local:8000/v1/chat/completions"
VLLM_HEALTH   = "http://vllm-gateway-service.default.svc.cluster.local:8000/health"
MODEL_NAME    = "Qwen/Qwen2.5-7B-Instruct-AWQ"


def wait_for_vllm(interval=5):
    print(f"[Init] Waiting for vLLM to be ready at {VLLM_HEALTH} ...")
    while True:
        try:
            resp = requests.get(VLLM_HEALTH, timeout=3)
            if resp.status_code == 200:
                print("[Init] vLLM is ready.")
                return
        except requests.exceptions.RequestException:
            pass
        print(f"[Init] vLLM not ready, retrying in {interval}s...")
        time.sleep(interval)


def claim_abandoned_tasks():
    print(f"[Init] Claiming abandoned tasks (idle > 60s)...")
    claimed = 0
    while True:
        try:
            result = r.xautoclaim(
                STREAM_NAME, GROUP_NAME, CONSUMER_NAME,
                min_idle_time=60000,
                start_id="0-0",
                count=10
            )
            messages = result[1]
            if not messages:
                break
            for message_id, message_data in messages:
                print(f"[Reclaim] Claimed abandoned task {message_id}")
                claimed += 1
        except Exception as e:
            print(f"[Reclaim] xautoclaim failed: {e}")
            break
    print(f"[Init] Claimed {claimed} abandoned tasks.")


def process_message(message_id, message_data):
    request_id  = message_data.get("id")
    user_prompt = message_data.get("prompt")
    print(f"[Task] id={request_id} | prompt={user_prompt!r}")

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": 150,
        "temperature": 0.7
    }

    try:
        start_time = time.time()
        response   = requests.post(VLLM_URL, json=payload, timeout=60)

        if response.status_code == 200:
            result    = response.json()
            ai_reply  = result["choices"][0]["message"]["content"]
            cost_time = time.time() - start_time
            print(f"[OK] {cost_time:.2f}s | reply={ai_reply!r}")
            r.xack(STREAM_NAME, GROUP_NAME, message_id)
            return True
        else:
            print(f"[Error] vLLM returned status {response.status_code}: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("[Error] vLLM request timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[Error] Failed to reach vLLM endpoint: {e}")
        return False


def main():
    wait_for_vllm()
    claim_abandoned_tasks()
    print(f"[Worker] [{CONSUMER_NAME}] started. Listening on [{STREAM_NAME}]...")
    while running:
        try:
            assigned_tasks = r.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={STREAM_NAME: ">"},
                count=1,
                block=2000
            )
            if not assigned_tasks:
                continue
            for stream_name, message_list in assigned_tasks:
                for message_id, message_data in message_list:
                    process_message(message_id, message_data)
        except redis.exceptions.ConnectionError as e:
            print(f"[Error] Redis connection lost: {e}, retrying in 3s...")
            time.sleep(3)
        except Exception as e:
            print(f"[Error] Unexpected error: {e}")
            time.sleep(1)
    print("[Worker] Shut down gracefully.")

if __name__ == "__main__":
    main()
