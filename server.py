from flask import Flask, request, Response, render_template
import requests
import json
import logging
import re
import pandas as pd
import scan_llm
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Aaa236875'
app.logger.setLevel(logging.DEBUG)
df = pd.read_csv('data.csv')
# 初始IP列表
data_array = df.to_numpy()
ip_list = data_array[:, 0]
ip_models = {}

def update_ip_models():
    global ip_models
    app.logger.info("开始定时扫描IP可用性...")
    new_models = scan_llm.scan_ips(ip_list)
    ip_models = new_models  # 直接替换整个字典，避免并发问题
    app.logger.info(f"IP扫描完成，当前可用IP及模型: {ip_models}")

# 初始化时立即扫描一次
update_ip_models()

# 配置定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(update_ip_models, 'interval', minutes=30)
scheduler.start()


@app.route('/')
def index():
    return render_template('index.html', ip_models=ip_models)
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/api/models')
def get_models():
    ip = request.args.get('ip')
    app.logger.debug(f"Request models for IP: {ip}")
    return {'models': ip_models.get(ip, [])}

@app.route('/api/chat', methods=['GET'])
@app.route('/api/chat', methods=['GET'])
def chat_stream():
    ip_port = request.args.get('ip')
    model = request.args.get('model')
    user_message = request.args.get('q', '')

    if not ip_port or not model:
        return Response(
            "event: error\ndata: {'error': '缺少必要参数'}\n\n",
            mimetype='text/event-stream'
        )

    app.logger.debug(f"Chat request - IP: {ip_port}, Model: {model}, Query: {user_message}")

    def event_stream():
        try:
            with requests.post(
                f'http://{ip_port}/api/generate',
                json={
                    'model': model,
                    'prompt': user_message,
                    'stream': True
                },
                stream=True,
                timeout=30
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = chunk.get('response', '')
                    if '<think>' in token:
                        import re
                        parts = re.split(r'(<think>.*?</think>)', token)
                        for part in parts:
                            if part.startswith('<think>') and part.endswith('</think>'):
                                think_content = part[len('<think>'):-len('</think>')]
                                yield f"event: think\ndata: {json.dumps({'content': think_content})}\n\n"
                            elif part:
                                yield f"data: {json.dumps({'text': part})}\n\n"
                    else:
                        yield f"data: {json.dumps({'text': token})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            app.logger.error(f"Stream error: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': '服务连接失败'})}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, port=5000,host="0.0.0.0")
