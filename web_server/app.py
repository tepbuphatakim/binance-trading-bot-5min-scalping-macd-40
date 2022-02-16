from flask import Flask, request, jsonify
from binance.client import Client
import config, json
from binance.enums import *

app = Flask(__name__)

client = Client(api_key=config.API_KEY, api_secret=config.API_SECRET, testnet=config.TEST_NET)

def get_wallet_balance(coin):
    try:
        multi_asset = client.futures_account_balance()
        for asset in multi_asset:
            if asset['asset'] == coin:
                return asset['balance']
        return 0
    except Exception as e:
        return str(e)

def open_order(symbol, side, qty, stop_loss, take_profit):
    try:
        cancel_all_open_order(symbol)

        client.futures_create_order(
            symbol=symbol,
            side=side,
            type=FUTURE_ORDER_TYPE_MARKET,
            quantity=qty
        )
        stopSide = ''
        if side == SIDE_BUY:
            stopSide = SIDE_SELL
        else:
            stopSide = SIDE_BUY

        client.futures_create_order(
            symbol=symbol,
            side=stopSide, 
            type=FUTURE_ORDER_TYPE_STOP_MARKET, 
            quantity=qty, 
            stopPrice=stop_loss, 
            timeInForce=TIME_IN_FORCE_GTC
        )
        client.futures_create_order(
            symbol=symbol, 
            side=stopSide, 
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, 
            quantity=qty, 
            stopPrice=take_profit, 
            timeInForce=TIME_IN_FORCE_GTC
        )

        return 'Order success'
    except Exception as e:
        return str(e)

def cancel_all_open_order(symbol):
    try:
        client.futures_cancel_all_open_orders(
            symbol=symbol
        )
        return 'All open order cancel'
    except Exception as e:
        return str(e)

@app.route('/', methods=['GET'])
def welcome():
    return 'Welcome binance 5 minute scalping MACD 40'

@app.route('/wallet-balance', methods=['GET'])
def wallet_balance():
    return str(get_wallet_balance(request.args.get("coin")))

@app.route('/binance-order', methods=['POST'])
def binance_order():
    data = json.loads(request.data)
    if data['passpharse'] != config.WEBHOOK_PASSPHRASE:
        return {
            "message": "Invalid passpharse"
        }

    side = data['order_action'].upper()
    stop_loss = 0
    take_profit = 0
    usdt_balance = get_wallet_balance('USDT')
    qty = 0
    
    if usdt_balance:
        qty = float(usdt_balance) / 2 / data['order_price'] * 20

        
    if data['order_action'] == 'buy':
        stop_loss = data['order_price'] - (data['order_price'] * 0.01)
        take_profit = data['order_price'] * 1.015
    else:
        stop_loss = data['order_price'] * 1.01
        take_profit = data['order_price'] - (data['order_price'] * 0.015)

    response = open_order(data['symbol'], side, round(qty, 3), round(stop_loss, 2), round(take_profit, 2))
    return jsonify(response)