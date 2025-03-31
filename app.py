from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

@app.route("/")
def index():
    if not os.path.exists("param_compare_results.csv"):
        return "還沒有資料，請稍後再試。"

    df = pd.read_csv("param_compare_results.csv")
    best_df = pd.read_csv("best_strategies.csv") if os.path.exists("best_strategies.csv") else pd.DataFrame()

    table_all = df.to_html(classes='table table-bordered table-sm', index=False)
    table_best = best_df.to_html(classes='table table-success table-sm', index=False) if not best_df.empty else "<p>尚未找到符合條件的最佳策略。</p>"

    return render_template("index.html", table_all=table_all, table_best=table_best)

if __name__ == "__main__":
    app.run(debug=True)
