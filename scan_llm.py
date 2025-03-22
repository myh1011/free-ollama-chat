import requests
import time
TIMEOUT = 0.3

def fetch_ollama_models(ip_port):
    try:
        url = f"http://{ip_port}/api/tags"
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            return [model['name'] for model in response.json().get('models', [])]
        return []
    except Exception as e:
        print(f"无法获取 {ip_port} 的模型：{str(e)}")
        return []

def scan_ips(ip_port_list):
    result = {}
    for ip_port in ip_port_list:
        print(f"正在扫描 {ip_port}...")
        models = fetch_ollama_models(ip_port)
        if models:
            result[ip_port] = models
        time.sleep(0.5)
    return result