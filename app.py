from flask import Flask, jsonify, render_template, request
import sqlite3
import yfinance as yf
import os

app = Flask(__name__)
# On Render, store the DB on the persistent disk mounted at /data
DB = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "portfolio.db"))


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                ticker TEXT PRIMARY KEY,
                shares REAL NOT NULL
            )
        """)
        conn.commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/portfolio", methods=["GET"])
def get_portfolio():
    with get_db() as conn:
        rows = conn.execute("SELECT ticker, shares FROM holdings").fetchall()

    if not rows:
        return jsonify({"holdings": [], "total_value": 0, "total_day_change": 0})

    holdings = []
    total_value = 0
    total_day_change = 0

    tickers = [row["ticker"] for row in rows]
    shares_map = {row["ticker"]: row["shares"] for row in rows}

    # Fetch all at once for efficiency
    data = yf.download(tickers, period="2d", auto_adjust=True, progress=False)

    for ticker in tickers:
        shares = shares_map[ticker]
        try:
            if len(tickers) == 1:
                close_series = data["Close"]
            else:
                close_series = data["Close"][ticker]

            close_series = close_series.dropna()
            if len(close_series) < 1:
                raise ValueError("No data")

            current_price = float(close_series.iloc[-1])
            prev_price = float(close_series.iloc[-2]) if len(close_series) >= 2 else current_price

            value = current_price * shares
            day_change = (current_price - prev_price) * shares
            pct_change = ((current_price - prev_price) / prev_price * 100) if prev_price else 0

            total_value += value
            total_day_change += day_change

            holdings.append({
                "ticker": ticker,
                "shares": shares,
                "current_price": round(current_price, 2),
                "prev_price": round(prev_price, 2),
                "value": round(value, 2),
                "day_change": round(day_change, 2),
                "pct_change": round(pct_change, 2),
            })
        except Exception as e:
            holdings.append({
                "ticker": ticker,
                "shares": shares,
                "current_price": None,
                "prev_price": None,
                "value": None,
                "day_change": None,
                "pct_change": None,
                "error": str(e),
            })

    return jsonify({
        "holdings": holdings,
        "total_value": round(total_value, 2),
        "total_day_change": round(total_day_change, 2),
        "total_day_pct": round((total_day_change / (total_value - total_day_change) * 100) if (total_value - total_day_change) else 0, 2),
    })


@app.route("/api/holdings", methods=["POST"])
def add_holding():
    data = request.get_json()
    ticker = data.get("ticker", "").upper().strip()
    shares = data.get("shares")

    if not ticker or shares is None:
        return jsonify({"error": "ticker and shares are required"}), 400

    try:
        shares = float(shares)
        if shares <= 0:
            return jsonify({"error": "shares must be positive"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "shares must be a number"}), 400

    # Validate ticker exists
    try:
        info = yf.Ticker(ticker).fast_info
        if not hasattr(info, 'last_price') or info.last_price is None:
            return jsonify({"error": f"Could not find ticker '{ticker}'"}), 400
    except Exception:
        return jsonify({"error": f"Could not validate ticker '{ticker}'"}), 400

    with get_db() as conn:
        conn.execute(
            "INSERT INTO holdings (ticker, shares) VALUES (?, ?) ON CONFLICT(ticker) DO UPDATE SET shares=?",
            (ticker, shares, shares)
        )
        conn.commit()

    return jsonify({"success": True, "ticker": ticker, "shares": shares})


@app.route("/api/holdings/<ticker>", methods=["DELETE"])
def remove_holding(ticker):
    ticker = ticker.upper()
    with get_db() as conn:
        conn.execute("DELETE FROM holdings WHERE ticker=?", (ticker,))
        conn.commit()
    return jsonify({"success": True})


if __name__ == "__main__":
    init_db()
    # host="0.0.0.0" makes it accessible from your phone on the same WiFi
    app.run(host="0.0.0.0", port=5000, debug=False)
