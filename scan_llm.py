# scan_llm.py
import requests
import concurrent.futures

#config
TIMEOUT = 2
work_thread = 20


def fetch_ollama_models(ip_port):
    try:
        url = f"http://{ip_port}/api/tags"
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            return (ip_port, [model['name'] for model in response.json().get('models', [])])
        return (ip_port, [])
    except Exception as e:
        print(f"无法获取 {ip_port} 的模型：{str(e)}")
        return (ip_port, [])

def scan_ips(ip_port_list):
    result = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=work_thread) as executor:
        futures = [executor.submit(fetch_ollama_models, ip) for ip in ip_port_list]
        for future in concurrent.futures.as_completed(futures):
            ip_port, models = future.result()
            if models:
                result[ip_port] = models
    return result