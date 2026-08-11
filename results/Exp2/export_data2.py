import os
import csv
import time
import requests

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

def get_queries(range_str="5m"):
    try:
        if range_str.endswith("m"):
            duration_sec = int(range_str[:-1]) * 60
        elif range_str.endswith("s"):
            duration_sec = int(range_str[:-1])
        else:
            duration_sec = 300
    except ValueError:
        duration_sec = 300

    return {
        "TTFT_P50_Sec": f"histogram_quantile(0.50, sum(increase(vllm:time_to_first_token_seconds_bucket[{range_str}])) by (le))",
        "TTFT_P99_Sec": f"histogram_quantile(0.99, sum(increase(vllm:time_to_first_token_seconds_bucket[{range_str}])) by (le))",
        "GPU_Cache_Hit_Rate": f"sum(rate(vllm:prefix_cache_hits_total[{range_str}])) / sum(rate(vllm:prefix_cache_queries_total[{range_str}]))",
        "KV_Cache_Usage_Perc": f"avg_over_time(vllm:kv_cache_usage_perc[{range_str}]) * 100",
        "Throughput_Tokens_Per_Sec": f"sum(increase(vllm:generation_tokens_total[{range_str}])) / {duration_sec}",
        "Total_Completed_Requests": f"sum(increase(vllm:time_to_first_token_seconds_count[{range_str}]))"
    }

def fetch_metric_value(query):
    try:
        response = requests.get(PROMETHEUS_URL, params={'query': query}, timeout=5)
        res_json = response.json()
        if res_json.get('status') == 'success':
            result = res_json['data']['result']
            if result and len(result) > 0:
                val = float(result[0]['value'][1])
                if str(val) in ["nan", "inf", "-inf"]:
                    return 0.0
                return round(val, 4)
        return 0.0
    except Exception:
        return 0.0

if __name__ == "__main__":
    VALID_MODES = ["Prefix", "Non-prefix"]
    while True:
        mode = input(f"Enter benchmark mode {VALID_MODES}: ").strip()
        matched_mode = next((m for m in VALID_MODES if m.lower() == mode.lower()), None)
        if matched_mode:
            mode = matched_mode
            break
        print(f"Invalid mode. Choose from {VALID_MODES}")

    VALID_CONCURRENCIES = [10, 20, 30, 40, 50, 75]
    while True:
        concurrency = input(f"Enter concurrency {VALID_CONCURRENCIES}: ").strip()
        if concurrency.isdigit() and int(concurrency) in VALID_CONCURRENCIES:
            concurrency = int(concurrency)
            break
        print(f"Invalid concurrency. Choose from {VALID_CONCURRENCIES}")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    row_data = {
        "Timestamp": timestamp,
        "Mode": mode,
        "Concurrency": concurrency
    }

    print(f"\nFetching data from Prometheus ({mode} | Concurrency: {concurrency})...")

    queries = get_queries("5m")
    for column_name, query in queries.items():
        value = fetch_metric_value(query)
        row_data[column_name] = value
        print(f"  {column_name:<26} -> {value}")

    csv_file = "/workspace/results/vllm_matrix_benchmark.csv"
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    file_exists = os.path.exists(csv_file)
    headers = ["Timestamp", "Mode", "Concurrency"] + list(queries.keys())

    with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)

    print(f"\nSuccess. Data appended to: {csv_file}\n")