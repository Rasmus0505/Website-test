# app.py
import os
import json
from flask import Flask, render_template, request, session, redirect, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from learning_system.session import LearningSession

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['TEMPLATES_AUTO_RELOAD'] = True

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_session():
    topic = request.form.get('topic')
    if not topic:
        return redirect('/')
    
    # 初始化学习会话
    learn_session = LearningSession(topic)
    
    # 如果无卡片则生成
    if not learn_session.cards:
        generated = generate_cards(topic)
        if not generated:
            return render_template('error.html', message="卡片生成失败")
        for card in generated:
            learn_session.add_card(card)
        learn_session.save_progress()
    
    # 保存到session
    session['topic'] = topic
    session['cards'] = learn_session.cards
    session['srs_data'] = learn_session.srs.card_data
    
    return redirect('/learning')

def generate_cards(topic):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": """你是一个严格遵循JSON格式的课程生成器，请按以下模板生成内容：
{
    "cards": [
        {
            "id": 唯一数字ID（必须为整数）,
            "title": "卡片标题",
            "knowledge": "知识点说明（100字内）",
            "questions": [
                {"q": "基础概念问题", "a": "参考答案"},
                {"q": "应用场景问题", "a": "参考答案"}
            ]
        }
    ]
}"""
            }, {
                "role": "user",
                "content": f"请为【{topic}】生成3-5张结构严格的学习卡片"
            }],
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=2000
        )
        
        response_data = json.loads(response.choices[0].message.content)
        return response_data.get('cards', [])
    
    except Exception as e:
        print(f"生成卡片失败: {str(e)}")
        return None

@app.route('/learning')
def learning_interface():
    if 'topic' not in session:
        return redirect('/')
    
    # 恢复学习会话
    learn_session = LearningSession(session['topic'])
    learn_session.cards = session['cards']
    learn_session.srs.card_data = session['srs_data']
    
    current_card = learn_session.get_next_card()
    if not current_card:
        return render_template('complete.html')
    
    return render_template(
        'learning.html',
        card=current_card,
        topic=session['topic']
    )

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    card_id = int(data['card_id'])
    scores = data['scores']
    
    # 更新学习进度
    learn_session = LearningSession(session['topic'])
    learn_session.cards = session['cards']
    learn_session.srs.card_data = session['srs_data']
    
    avg_score = sum(scores) / len(scores)
    learn_session.srs.update_card(card_id, avg_score)
    learn_session.save_progress()
    
    # 更新session数据
    session['srs_data'] = learn_session.srs.card_data
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)