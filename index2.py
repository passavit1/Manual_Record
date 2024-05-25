import os
import pandas as pd
import requests
from datetime import datetime, timedelta

def fetch_data(symbol, start_time=None, end_time=None):
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1d",
        "limit": 1000
    }
    if start_time:
        params["startTime"] = int(start_time.timestamp() * 1000)
    if end_time:
        params["endTime"] = int(end_time.timestamp() * 1000)
        
    response = requests.get(base_url, params=params)
    data = response.json()
    if len(data) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume", 
        "close_time", "quote_asset_volume", "number_of_trades", 
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    return df[["open_time", "close"]]

def update_data(symbol):
    file_path = f"data/{symbol}.csv"
    if not os.path.exists(file_path):
        if not os.path.exists('data'):
            os.makedirs('data')
        start_time = datetime(2014, 1, 1)
        all_data = pd.DataFrame()
        while True:
            df = fetch_data(symbol, start_time=start_time)
            if df.empty:
                break
            all_data = pd.concat([all_data, df], ignore_index=True)
            start_time = df["open_time"].iloc[-1] + timedelta(milliseconds=1)
            if len(df) < 1000:
                break
        all_data.to_csv(file_path, index=False)
    else:
        existing_df = pd.read_csv(file_path)
        existing_df["open_time"] = pd.to_datetime(existing_df["open_time"])
        last_time = existing_df["open_time"].iloc[-1]
        all_data = existing_df.copy()
        while True:
            df = fetch_data(symbol, start_time=last_time + timedelta(milliseconds=1))
            if df.empty:
                break
            all_data = pd.concat([all_data, df], ignore_index=True)
            last_time = df["open_time"].iloc[-1]
            if len(df) < 1000:
                break
        all_data.to_csv(file_path, index=False)
    return pd.read_csv(file_path)

def calculate_ema(df, span):
    return df['close'].ewm(span=span, adjust=False).mean()

def add_ema(df):
    df['EMA12'] = calculate_ema(df, 12)
    df['EMA26'] = calculate_ema(df, 26)
    return df

def calculate_profit(entry_price, exit_price, quality=0.0001):
    percentage_change = ((float(exit_price) - float(entry_price)) / float(entry_price)) * 100
    percentage_loss = percentage_change / 100
    actual_loss = percentage_loss * float(quality)
    return actual_loss

def add_signals_and_profits(df, quality=0.0001):
    df['is_start_point'] = False
    df['is_end_point'] = False
    df['current_profit'] = 0.0
    in_position = False
    entry_price = 0.0
    total_profit = 0.0
    win_trades = 0
    total_trades = 0
    
    for i in range(26, len(df)):  # Start calculating after 26 days
        if df["EMA12"].iloc[i] > df["EMA26"].iloc[i] and not in_position:
            in_position = True
            entry_price = df["close"].iloc[i]
            df.at[i, 'is_start_point'] = True  # Mark start point
        elif df["EMA26"].iloc[i] > df["EMA12"].iloc[i] and in_position:
            in_position = False
            exit_price = df["close"].iloc[i]
            profit = calculate_profit(entry_price, exit_price, quality)
            df.at[i, 'is_end_point'] = True  # Mark end point
            df.at[i, 'current_profit'] = profit
            total_profit += profit
            total_trades += 1
            if profit > 0:
                win_trades += 1
            entry_price = 0.0
        else:
            if in_position:
                df.at[i, 'current_profit'] = calculate_profit(entry_price, df["close"].iloc[i], quality)
            else:
                df.at[i, 'current_profit'] = 0.0
    
    win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
    return df, total_profit, win_rate

def main():
    while True:
        symbol = input("Enter the symbol (or type 'exit' to quit): ").upper()
        if symbol.lower() == 'exit':
            break
        try:
            df = update_data(symbol)
            df = add_ema(df)
            df, total_profit, win_rate = add_signals_and_profits(df)
            df = df[["open_time", "close", "EMA12", "EMA26", "current_profit", "is_start_point", "is_end_point"]]
            df.to_csv(f"data/{symbol}_processed.csv", index=False, float_format='%.8f')
            print(f"Processed data saved to data/{symbol}_processed.csv")
            print(f"Total Profit: {total_profit:.8f}")
            print(f"Win Rate: {win_rate:.2f}%")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()