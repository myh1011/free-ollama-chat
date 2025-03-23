# scan_llm.py
import requests
import concurrent.futures
import time

# config
TIMEOUT = 2
work_thread = 20


def fetch_ollama_models(ip_port):
    try:
        start_time = time.time()
        url = f"http://{ip_port}/api/tags"
        response = requests.get(url, timeout=TIMEOUT)
        latency = int((time.time() - start_time) * 1000)  # 计算延迟（毫秒）
        if response.status_code == 200:
            return (ip_port, {
                'models': [model['name'] for model in response.json().get('models', [])],
                'latency': latency
            })
        return (ip_port, {'models': [], 'latency': latency})
    except Exception as e:
        return (ip_port, {'models': [], 'latency': -1})


def scan_ips(ip_port_list):
    result = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=work_thread) as executor:
        futures = [executor.submit(fetch_ollama_models, ip) for ip in ip_port_list]
        for future in concurrent.futures.as_completed(futures):
            ip_port, data = future.result()
            if data['models']:
                result[ip_port] = data
    return result