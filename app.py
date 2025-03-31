from flask import Flask, render_template
import pandas as pd
import os
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import datetime

app = Flask(__name__)

# 執行回測的函式
def run_backtest():
    print("Running backtest:", datetime.datetime.now())
    subprocess.run(["python", "param_compare.py"])

# 排程器，每5分鐘自動執行一次回測
scheduler = BackgroundScheduler()
scheduler.add_job(func=run_backtest, trigger="interval", minutes=5)
scheduler.start()

@app.route("/")
def index():
    if not os.path.exists("param_compare_results.csv"):
        return "還沒有資料，系統正在更新，請稍後再試。"

    df = pd.read_csv("param_compare_results.csv")
    best_df = pd.read_csv("best_strategies.csv") if os.path.exists("best_strategies.csv") else pd.DataFrame()

    table_all = df.to_html(classes='table table-bordered table-sm', index=False)
    table_best = best_df.to_html(classes='table table-success table-sm', index=False) if not best_df.empty else "<p>尚未找到符合條件的最佳策略。</p>"

    return render_template("index.html", table_all=table_all, table_best=table_best)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
