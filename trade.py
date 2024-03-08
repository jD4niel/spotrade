import yaml
import pytz
import calendar, requests, time, os, sys
import glob
from datetime import datetime
from pandas import pandas as pd
import numpy as np
from binance.spot import Spot
from binance.error import ClientError as BinanceClientError


##################### COLOR SETTINGS #####################
COLOR_RED = '\u001b[31m'
COLOR_GREEN = '\u001b[32m'
COLOR_ORANGE = '\u001b[38;5;208m'
COLOR_RESET = '\u001b[0m'
COLOR_BG_BLUE = '\x1b[48;5;4m \x1b[38;5;16m'
COLOR_BLUE = '\x1b[38;5;39m'
COLOR_YELLOW = '\u001b[33m'
##################### TIMEZONE SETTINGS #####################
# Get the current time in UTC
utc_now = datetime.utcnow()
# Define the Mexico Central Time zone
mexico_timezone = pytz.timezone('America/Mexico_City')
##################### LOGGING SETTINGS #####################
import logging
logging.basicConfig(level=logging.INFO)

# ---------------- FUNCTIONS --------------------------
def read_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def send_message(message):
    try:
        secret = read_config('secret.yaml')
        chat_id = secret['telegram']['chat_id']
        token = secret['telegram']['token']
    except Exception as error:
        logging.info(f"{COLOR_RED}Error: {error} {COLOR_RESET}")
        sys.exit()

    url =  "https://api.telegram.org/bot" + token
    if message:
        send_message = f"/sendMessage?chat_id={chat_id}&text={message}"
        base_url = url + send_message
        return requests.get(base_url)

def colorize_text(text, color):
    return f"{color}{text}{COLOR_RESET}"

def format_variables(symbol, interval, mark_price, rsi, upper_band, middle_band, lower_band, macd_line, macd_signal, macd_histogram, rsi_up, rsi_down):
    # Format symbol
    formatted_symbol = f"{COLOR_BLUE}{symbol}{COLOR_RESET}"
    
    # Format mark_price
    formatted_mark_price = f"{COLOR_YELLOW}{mark_price:.2f}{COLOR_RESET}"
    
    # Format rsi
    if rsi <= rsi_down:
        formatted_rsi = f"{COLOR_RED}{rsi:.2f}{COLOR_RESET}"
    elif rsi >= rsi_up:
        formatted_rsi = f"{COLOR_GREEN}{rsi:.2f}{COLOR_RESET}"
    else:
        formatted_rsi = f"{COLOR_ORANGE}{rsi:.2f}{COLOR_RESET}"
    
    # Format macd_line, macd_signal, macd_histogram
    macd_line_last = macd_line[-1]
    macd_signal_last = macd_signal[-1]
    macd_histogram_last = macd_histogram[-1]
    
    formatted_macd_line = f"{COLOR_RED if macd_line_last < 0 else COLOR_GREEN}{macd_line_last:.2f}{COLOR_RESET}"
    formatted_macd_signal = f"{COLOR_RED if macd_signal_last < 0 else COLOR_GREEN}{macd_signal_last:.2f}{COLOR_RESET}"
    formatted_macd_histogram = f"{COLOR_RED if macd_histogram_last < 0 else COLOR_GREEN}{macd_histogram_last:.2f}{COLOR_RESET}"
    
    # Format upper_band, middle_band, lower_band
    if mark_price <= lower_band:
        formatted_upper_band = f"{COLOR_RED}{upper_band:.2f}{COLOR_RESET}"
        formatted_middle_band = f"{COLOR_RED}{middle_band:.2f}{COLOR_RESET}"
        formatted_lower_band = f"{COLOR_RED}{lower_band:.2f}{COLOR_RESET}"
    elif mark_price >= upper_band:
        formatted_upper_band = f"{COLOR_GREEN}{upper_band:.2f}{COLOR_RESET}"
        formatted_middle_band = f"{COLOR_GREEN}{middle_band:.2f}{COLOR_RESET}"
        formatted_lower_band = f"{COLOR_GREEN}{lower_band:.2f}{COLOR_RESET}"
    elif mark_price >= middle_band:
        formatted_upper_band = f"{upper_band:.2f}"
        formatted_middle_band = f"{COLOR_GREEN}{middle_band:.2f}{COLOR_RESET}"
        formatted_lower_band = f"{lower_band:.2f}"
    elif mark_price <= middle_band:
        formatted_upper_band = f"{upper_band:.2f}"
        formatted_middle_band = f"{COLOR_RED}{middle_band:.2f}{COLOR_RESET}"
        formatted_lower_band = f"{lower_band:.2f}"
    else:
        formatted_upper_band = f"{upper_band:.2f}"
        formatted_middle_band = f"{middle_band:.2f}"
        formatted_lower_band = f"{lower_band:.2f}"
    
    return (formatted_symbol, interval, formatted_mark_price, formatted_rsi, formatted_upper_band, formatted_middle_band, formatted_lower_band, formatted_macd_line, formatted_macd_signal, formatted_macd_histogram)


# --------------- BINANCE FUNCTIONS ------------------
def calculate_macd(data, ema_short_period=12, ema_long_period=26, dea_period=9):
    close_prices = np.array([float(entry[4]) for entry in data])
    
    def calculate_ema(data, period):
        ema = np.zeros_like(data)
        ema[0] = data[0]
        alpha = 2 / (period + 1)

        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]

        return ema
    
    # Calculate the short-term EMA
    ema_short = calculate_ema(close_prices, ema_short_period)
    # Calculate the long-term EMA
    ema_long = calculate_ema(close_prices, ema_long_period)
    # Calculate the MACD line (DIF)
    macd_line = ema_short - ema_long
    # Calculate the MACD signal line (DEA)
    macd_signal = calculate_ema(macd_line, dea_period)
    # Calculate the MACD histogram (DIFF)
    macd_histogram = macd_line - macd_signal
    return macd_line, macd_signal, macd_histogram


def get_bollinger_bands(data, period=10, std_dev_factor=2):
    # FOR DEFAULT PERIOD = 21, STD_DEV_FACTOR = 2
    closing_prices = [float(entry[4]) for entry in data]
    rolling_mean = np.mean(closing_prices[-period:])
    rolling_std = np.std(closing_prices[-period:])
    upper_band = rolling_mean + std_dev_factor * rolling_std
    middle_band = rolling_mean
    lower_band = rolling_mean - std_dev_factor * rolling_std
    return upper_band, middle_band, lower_band


def get_rsi(data,period=4,**args):   
    D = pd.DataFrame(data)
    D.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades',
                 'taker_base_vol', 'taker_quote_vol', 'is_best_match']
    df=D
    df['close'] = df['close'].astype(float)
    df2=df['close'].to_numpy()
    
    df2 = pd.DataFrame(df2, columns = ['close'])
    delta = df2.diff()
    
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    
    RS = _gain / _loss
    rsi=100 - (100 / (1 + RS))
    rsi=rsi['close'].iloc[-1]
    return float(rsi)


def get_data(symbol='BTCUSDT', timeinterval="4h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={timeinterval}&limit={limit}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        logging.debug(colorize_text("Data retrieved successfully.", COLOR_GREEN))
        return data
    else:
        logging.error(colorize_text(f"Error retrieving data. Status code: {response.status_code}", COLOR_RED))
        return None


def get_balance(client):
    balance = 0
    balance_obj = client.balance()
    spot_balance = list(filter(lambda x: x['walletName'] == 'Spot', balance))
    if spot_balance:
        balance = spot_balance[0].get('balance',0)

    return balance


def get_response_vals(response):
    fills = response.get("fills",{})
    if len(fills) > 1:
        send_message("Error: much fills in response")
    
    message = "\n"

    for key,value in fills[0].items():
        if isinstance(value, (int, float)):
            value = "{:.2f}".format(value)
        
        message += f"{key}: {value}\n"

    return message


def main():
    if not os.path.exists("config.yaml") or not os.path.exists("secret.yaml"):
        error_message = "Error: config.yaml or secret.yaml does not exist."
        logging.error(f"{COLOR_RED}{error_message}{COLOR_RESET}")
        send_message(error_message)

    print(f"""
{COLOR_ORANGE}--------------------------------------------------------------------------------{COLOR_RESET}

    {COLOR_BLUE} .d8888b. {COLOR_RESET}                   {COLOR_GREEN}88888888888{COLOR_RESET}                       888          
    {COLOR_BLUE}d88P  Y88b{COLOR_RESET}                   {COLOR_GREEN}    888    {COLOR_RESET}                       888          
    {COLOR_BLUE}Y88b.     {COLOR_RESET}                   {COLOR_GREEN}    888    {COLOR_RESET}                       888          
    {COLOR_BLUE} "Y888b.  {COLOR_RESET} 88888b.   .d88b.  {COLOR_GREEN}    888    {COLOR_RESET} 888d888  8888b.   .d88888  .d88b.  
    {COLOR_BLUE}    "Y88b.{COLOR_RESET} 888 "88b d88""88b {COLOR_GREEN}    888    {COLOR_RESET} 888P"       "88b d88" 888 d8P  Y8b 
    {COLOR_BLUE}      "888{COLOR_RESET} 888  888 888  888 {COLOR_GREEN}    888    {COLOR_RESET} 888     .d888888 888  888 88888888 
    {COLOR_BLUE}Y88b  d88P{COLOR_RESET} 888 d88P Y88..88P {COLOR_GREEN}    888    {COLOR_RESET} 888     888  888 Y88b 888 Y8b.     
    {COLOR_BLUE} "Y8888P" {COLOR_RESET} 88888P"   "Y88P"  {COLOR_GREEN}    888    {COLOR_RESET} 888     "Y888888  "Y88888  "Y8888  
    {COLOR_BLUE}          {COLOR_RESET} 888                                                              
    {COLOR_BLUE}          {COLOR_RESET} 888                                                              
    {COLOR_BLUE}          {COLOR_RESET} 888                                             

{COLOR_ORANGE}--------------------------------------------------------------------------------{COLOR_RESET}
    """)

    config_name = 'config.yaml'

    if len(sys.argv) > 1:
        config_name = sys.argv[1]

    print(f" Using config file: {COLOR_ORANGE}{config_name}{COLOR_RESET}\n")

    # Read variables from YAML file
    config = read_config(config_name.replace('.yaml','') + '.yaml')
    binance_spot = read_config('secret.yaml')
    access = binance_spot['binance_spot_access']

    api_key = access['api_key']
    secret_key = access['secret_key']
    client = Spot()
    # API key/secret are required for user data endpoints
    client = Spot(api_key=api_key, api_secret=secret_key)

    # Access trade parameters
    trade_params = config['trade']
    symbol = trade_params['symbol'].upper()
    interval = trade_params['interval']
    qty = trade_params['qty']
    close_trade = trade_params['close_trade']

    # Access RSI parameters
    rsi_params = config['rsi']
    rsi_up = rsi_params['rsi_up']
    rsi_down = rsi_params['rsi_down']
    rsi_period = rsi_params['rsi_period']
    rsi_divergence = rsi_params['rsi_divergence']

    # Access Bollinger Band parameters
    bollinger_params = config['bollinger']
    profit_boll_middle = bollinger_params['profit_boll_middle']
    double_boll_validation = bollinger_params['double_boll_validation']
    boll_period = bollinger_params['boll_period']
    boll_dev_factor = bollinger_params['boll_dev_factor']

    # Access MACD parameters
    macd_params = config['macd']
    macd_divergence = macd_params['macd_divergence']
    full_macd = macd_params['full_macd']
    enable_macd = macd_params['enable_macd']

    # LIST YAML FILEs
    yaml_files = glob.glob("*.yaml")
    # Filter out secret.yaml
    yaml_files = [file for file in yaml_files if file != "secret.yaml"]

    output = (
        f"   symbol ················· {COLOR_ORANGE}{symbol}{COLOR_RESET}\n"
        f"   interval ··············· {COLOR_ORANGE}{interval}{COLOR_RESET}\n"
        f"   qty ···················· {COLOR_ORANGE}{qty}{COLOR_RESET}\n"
        f"   close_trade ············ {COLOR_ORANGE}{close_trade}{COLOR_RESET}\n"
        f"   rsi_up ················· {COLOR_ORANGE}{rsi_up}{COLOR_RESET}\n"
        f"   rsi_down ··············· {COLOR_ORANGE}{rsi_down}{COLOR_RESET}\n"
        f"   rsi_period ············· {COLOR_ORANGE}{rsi_period}{COLOR_RESET}\n"
        f"   rsi_divergence ········· {COLOR_ORANGE}{rsi_divergence}{COLOR_RESET}\n"
        f"   profit_boll_middle ····· {COLOR_ORANGE}{profit_boll_middle}{COLOR_RESET}\n"
        f"   double_boll_validation · {COLOR_ORANGE}{double_boll_validation}{COLOR_RESET}\n"
        f"   boll_period ············ {COLOR_ORANGE}{boll_period}{COLOR_RESET}\n"
        f"   boll_dev_factor ········ {COLOR_ORANGE}{boll_dev_factor}{COLOR_RESET}\n\n"
        f"{COLOR_ORANGE}--------------------------------------------------------------------------------{COLOR_RESET}\n"
        f"{COLOR_GREEN} Available .yaml config files: {COLOR_RESET}{(f'{COLOR_YELLOW}, {COLOR_RESET}'.join(yaml_files))}\n"
        f"\n{COLOR_ORANGE}Usage: {COLOR_RESET}python script.py {COLOR_YELLOW}config_name{COLOR_RESET}\n\n"
    )


    # Print concatenated string
    print(output)

    user_input = input("Click enter to continue or 'c' for cancel: ")
    if user_input.lower() == 'c':
        sys.exit()
    
    order_type = False

    if 'USDT' not in symbol:
        logging.error(colorize_text(f"Error config values. Incorrect pair try ex. BTCUSDT: {symbol}", COLOR_RED))

    while True:
        try:
            data = get_data(symbol=symbol, timeinterval=interval)
            # GET VALUES
            rsi = get_rsi(data, period=rsi_period)
            upper_band, middle_band, lower_band = get_bollinger_bands(data, period=boll_period, std_dev_factor=boll_dev_factor)
            # DIF, DEA and MACD
            macd_line, macd_signal, macd_histogram = calculate_macd(data)
            # ARGS
            mark_price = float(requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}").json().get('price',0))
        except Exception as error:
            logging.error(f"{COLOR_RED} ERROR get data: {COLOR_RESET}{COLOR_ORANGE}{error}{COLOR_RESET}")
            continue

        now = datetime.now(mexico_timezone).strftime(f"{COLOR_ORANGE}%d-%m-%Y{COLOR_RESET} {COLOR_BLUE}%H:%M:%S{COLOR_RESET}")
        ### BOOLEAN FOR DETERMINE IF TRADE OR DONT

        symbol_ft, interval_ft, mark_price_ft, rsi_ft, upper_band_ft, middle_band_ft, lower_band_ft, macd_line_ft, macd_signal_ft, macd_histogram_ft = format_variables(symbol, interval, mark_price, rsi, upper_band, middle_band, lower_band, macd_line, macd_signal, macd_histogram, rsi_up, rsi_down)

        # VALIDATE RSI, BOLL AND MACD
        if rsi <= rsi_down and mark_price <= lower_band and macd_line[-1] < 0 and macd_signal[-1] < 0 and macd_histogram[-1] < 0:
            if not order_type:
                order_type = "BUY" # LONG


        logging.info(f"{now} - {order_type} {symbol_ft} {interval_ft} | {mark_price_ft} | RSI:{rsi_ft} | BOLL ({upper_band_ft}|{middle_band_ft}|{lower_band_ft}) | MACD: l:{macd_line_ft} s:{macd_signal_ft} h:{macd_histogram_ft}")
        #----------------------------------------- CREATE ORDER -------------------------------------------------------


        params = {
            'symbol': symbol,
            'side': order_type,
            'type': 'MARKET',
            'quantity': qty,
        }

        try:
            t_now = datetime.now(mexico_timezone).strftime(f"%d-%m-%Y %H:%M")
            message = f"{order_type} {symbol} - {interval}  🚀 \n{t_now}\n\nRSI: {rsi:.2f}\nupper: {upper_band:.2f}\nmiddle: {middle_band:.2f}\nlower: {lower_band:.2f}"
            if  order_type == 'BUY':
                # balance = get_balance(client)
                avg_price = float(client.avg_price(symbol)['price'])
                logging.info(f"     BUY - avg_price: {COLOR_ORANGE}{avg_price}{COLOR_RESET} - mark_price: {COLOR_GREEN}{mark_price}{COLOR_RESET}")
                if mark_price < avg_price:
                    response = client.new_order(**params)
                    print(response)
                    response_data = get_response_vals(response)
                    send_message(message + response_data)
                    order_type = 'SELL'

            elif order_type == 'SELL':
                logging.info(f"     SELL - middle: {COLOR_ORANGE}{middle_band:.2f}{COLOR_RESET} - mark_price: {COLOR_RED}{mark_price}{COLOR_RESET}")
                if mark_price > middle_band:
                    response = client.new_order(**params)
                    print(response)
                    response_data = get_response_vals(response)
                    send_message(message + response_data)
                    order_type = False

        except BinanceClientError as error:
            send_message(f"Error {symbol}-{interval} new_order: {error.error_message}")
            logging.error(f"{COLOR_RED} ERROR new_order {COLOR_RESET}{COLOR_ORANGE}{error.header}{COLOR_RESET}")
            sys.exit()

        except Exception as error:
            send_message(f"Error new_order: {error}")
            logging.error(f"{COLOR_RED} ERROR new_order {COLOR_RESET}{COLOR_ORANGE}{error}{COLOR_RESET}")
            sys.exit()


if __name__ == "__main__":
    main()

