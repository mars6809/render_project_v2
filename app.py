from flask import Flask, render_template, request, redirect
import pandas as pd
import json, os
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess

app = Flask(__name__)

# 回測函式
def run_backtest():
    subprocess.run(["python", "param_compare.py"])

# 排程器，每5分鐘執行一次
scheduler = BackgroundScheduler()
scheduler.add_job(run_backtest, "interval", minutes=5)
run_backtest()
scheduler.start()

# 首頁（策略管理）
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.form.get("strategy_name")
        with open('strategies.json', 'r+') as f:
            strategies = json.load(f)
            strategies['current_strategy'] = data
            f.seek(0)
            json.dump(strategies, f, indent=4)
        return redirect('/')

    if not os.path.exists("param_compare_results.csv"):
        return "系統更新中，請稍後再試。"

    with open('strategies.json') as f:
        strategies = json.load(f)

    current_strategy = strategies.get('current_strategy', '未選擇')

    df = pd.read_csv("param_compare_results.csv")
    best_df = pd.read_csv("best_strategies.csv") if os.path.exists("best_strategies.csv") else pd.DataFrame()

    table_all = df.to_html(classes='table table-bordered', index=False)
    table_best = best_df.to_html(classes='table table-success', index=False) if not best_df.empty else "<p>尚未找到最佳策略。</p>"

    return render_template("index.html",
                           table_all=table_all,
                           table_best=table_best,
                           strategies=strategies,
                           current_strategy=current_strategy)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
