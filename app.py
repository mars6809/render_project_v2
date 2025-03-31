from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_session import Session
import json
import subprocess
import openai
import os
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 設定 Session
app.secret_key = "your_secret_key_here"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 365  # 1 年
Session(app)

openai.api_key = "your_openai_api_key_here"  # 用你自己的 API 密鑰

# 用戶資料（初始管理員帳號）
users = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "user1", "password": "password1", "role": "user"},
]

# AI 策略與自選策略資料
def load_strategies():
    if not os.path.exists('strategies.json'):
        return {"user_defined": [], "ai_generated": [], "current_strategy": "未選擇"}
    with open('strategies.json', 'r') as f:
        return json.load(f)

# 登入頁面
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # 檢查是否為合法用戶
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = username
            session['role'] = user['role']
            session.permanent = True  # 設置 session 永久有效
            return redirect(url_for('index'))
        else:
            return "帳號或密碼錯誤，請重新嘗試。"
    return render_template("login.html")

# 主頁面（策略展示）
@app.route("/", methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    strategies = load_strategies()
    current_strategy = strategies.get('current_strategy', '未選擇')

    if request.method == 'POST':
        strategy_name = request.form.get("strategy_name")
        strategies['current_strategy'] = strategy_name
        with open('strategies.json', 'w') as f:
            json.dump(strategies, f, indent=4)
        return redirect('/')

    return render_template("index.html", strategies=strategies, current_strategy=current_strategy)

# 後台管理頁面（用戶管理）
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if 'user' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        new_role = request.form['new_role']
        new_user = {"username": new_username, "password": new_password, "role": new_role}
        users.append(new_user)  # 新用戶加入
        with open('strategies.json', 'w') as f:
            json.dump(users, f, indent=4)  # 更新用戶資料
        return redirect(url_for('admin'))

    return render_template("admin.html", users=users)

# AI 小助手路由
@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    user_input = request.form.get("question")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_input,
        max_tokens=100
    )
    answer = response.choices[0].text.strip()
    return jsonify({"answer": answer})

# 登出
@app.route("/logout")
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# 啟動網站後立刻執行回測
def run_backtest():
    subprocess.run(["python", "param_compare.py"])

# 排程器，每5分鐘自動執行一次回測
scheduler = BackgroundScheduler()
scheduler.add_job(run_backtest, "interval", minutes=5)
run_backtest()  # 立即執行一次回測
scheduler.start()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
