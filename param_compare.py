import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 假設資本數據保存在 equity_curve 中
def plot_equity_curve(equity_curve):
    plt.figure(figsize=(10, 6))
    plt.plot(equity_curve, label="Equity Curve", color="green")
    plt.title("Capital Growth Over Time")
    plt.xlabel("Time (Iterations)")
    plt.ylabel("Capital")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("equity_curve.png")  # 儲存圖片
    plt.close()

def plot_win_rate(win_rate_data):
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(win_rate_data)), win_rate_data, color="blue")
    plt.title("Win Rate Comparison")
    plt.xlabel("Strategy")
    plt.ylabel("Win Rate (%)")
    plt.tight_layout()
    plt.savefig("win_rate.png")  # 儲存圖片
    plt.close()

# 在回測結束後，這些圖表會被生成並保存在當前目錄

from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator

# === 參數組合清單 ===
param_list = [
    {"rsi_entry": 25, "rsi_exit": 50, "bb_std": 2,   "tp": 0.02,  "sl": -0.015},
    {"rsi_entry": 30, "rsi_exit": 50, "bb_std": 2,   "tp": 0.02,  "sl": -0.015},
    {"rsi_entry": 35, "rsi_exit": 50, "bb_std": 2,   "tp": 0.025, "sl": -0.015},
    {"rsi_entry": 30, "rsi_exit": 55, "bb_std": 2.5, "tp": 0.03,  "sl": -0.02},
    {"rsi_entry": 28, "rsi_exit": 50, "bb_std": 1.8, "tp": 0.015, "sl": -0.012},
]

# === 固定參數 ===
bb_window = 20
capital_ratio = 0.03
initial_capital = 100000
vol_multiplier = 1.5

# === 讀取資料 ===
df = pd.read_csv("btc_30min.csv", parse_dates=['timestamp'])
df.set_index('timestamp', inplace=True)

# === 回測主程式 ===
all_results = []

for params in param_list:
    df_copy = df.copy()
    bb = BollingerBands(close=df_copy['close'], window=bb_window, window_dev=params['bb_std'])
    df_copy['bb_upper'] = bb.bollinger_hband()
    df_copy['bb_middle'] = bb.bollinger_mavg()
    df_copy['bb_lower'] = bb.bollinger_lband()
    df_copy['rsi'] = RSIIndicator(close=df_copy['close'], window=14).rsi()
    df_copy['vol_ma'] = df_copy['volume'].rolling(window=20).mean()

    capital = initial_capital
    position = 0
    entry_price = 0
    equity_curve = []
    trades = []

    for i in range(bb_window, len(df_copy)):
        row = df_copy.iloc[i]

        if position == 0:
            if (
                row['close'] < row['bb_lower'] and
                row['rsi'] < params['rsi_entry'] and
                row['volume'] > vol_multiplier * row['vol_ma']
            ):
                position = capital * capital_ratio / row['close']
                entry_price = row['close']

        elif position > 0:
            gain = (row['close'] - entry_price) / entry_price
            if (
                row['rsi'] > params['rsi_exit'] or
                row['close'] > row['bb_middle'] or
                gain >= params['tp'] or
                gain <= params['sl']
            ):
                pnl = (row['close'] - entry_price) * position
                capital += pnl
                trades.append(gain * 100)
                position = 0
                entry_price = 0

        equity_curve.append(capital)

    trades = pd.Series(trades)
    total_trades = len(trades)
    win_rate = (trades > 0).sum() / total_trades * 100 if total_trades > 0 else 0
    avg_return = trades.mean() if total_trades > 0 else 0
    max_drawdown = np.min(equity_curve) - initial_capital
    final_capital = equity_curve[-1] if equity_curve else initial_capital

    result = {
        "RSI Entry": params['rsi_entry'],
        "RSI Exit": params['rsi_exit'],
        "BB Std": params['bb_std'],
        "Take Profit %": params['tp'] * 100,
        "Stop Loss %": params['sl'] * 100,
        "Total Trades": total_trades,
        "Win Rate (%)": round(win_rate, 2),
        "Avg Return (%)": round(avg_return, 2),
        "Max Drawdown": round(max_drawdown, 2),
        "Final Capital": round(final_capital, 2),
    }

    all_results.append(result)

# 儲存總表
results_df = pd.DataFrame(all_results)
results_df.to_csv("param_compare_results.csv", index=False)

# === 自動篩選最佳策略組合 ===
best = results_df[
    (results_df['Win Rate (%)'] >= 55) &
    (results_df['Avg Return (%)'] >= 0.3) &
    (results_df['Total Trades'] >= 10)
].sort_values(by="Final Capital", ascending=False).head(3)

best.to_csv("best_strategies.csv", index=False)

# === 圖表產出 ===
plt.figure(figsize=(12, 5))
plt.bar(results_df.index, results_df['Final Capital'], color='goldenrod')
plt.xticks(results_df.index, [f"RSI{r}" for r in results_df['RSI Entry']], rotation=45)
plt.ylabel("Final Capital")
plt.title("各參數組最終資本")
plt.tight_layout()
plt.savefig("final_capital_bar.png")
plt.close()

plt.figure(figsize=(12, 5))
plt.bar(results_df.index, results_df['Win Rate (%)'], color='skyblue')
plt.xticks(results_df.index, [f"RSI{r}" for r in results_df['RSI Entry']], rotation=45)
plt.ylabel("Win Rate (%)")
plt.title("各參數組勝率比較")
plt.tight_layout()
plt.savefig("win_rate_bar.png")
plt.close()

plt.figure(figsize=(12, 5))
plt.bar(results_df.index, results_df['Avg Return (%)'], color='lightgreen')
plt.xticks(results_df.index, [f"RSI{r}" for r in results_df['RSI Entry']], rotation=45)
plt.ylabel("Average Return (%)")
plt.title("各參數組平均報酬率比較")
plt.tight_layout()
plt.savefig("avg_return_bar.png")
plt.close()

print("✅ 回測完成，已自動篩選最佳策略並產出圖表。")
