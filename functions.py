import nsepython as nse
import logging
import json
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_ask_bid(asset, expiry_date, derivative_type='-', strike_price=0):
    fno_data = nse.nse_fno(asset.upper())
    contents = fno_data['stocks']
    derivative_type = derivative_type.lower()
    strike_price = int(strike_price)

    if strike_price not in fno_data['strikePrices']:
        print("Invalid Strike Price")
        return
    elif expiry_date not in fno_data['expiryDates']:
        print("Invalid Expiry Date")
        return

    if derivative_type == "futures":
        for i in contents:
            instrument_type = i['metadata']['instrumentType']
            if instrument_type == 'Index Futures':
                if i['metadata']['expiryDate'] == expiry_date:
                    ask = i["marketDeptOrderBook"]["ask"][0]["price"]
                    bid = i["marketDeptOrderBook"]["bid"][0]["price"]
                    return ask, bid
    else:
        for i in contents:
            instrument_type = i['metadata']['instrumentType']
            if instrument_type == 'Index Options' and i['metadata']['optionType'].lower() == derivative_type:
                if i['metadata']['expiryDate'] == expiry_date:
                    if i['metadata']['strikePrice'] == strike_price:
                        ask = i["marketDeptOrderBook"]["ask"][0]["price"]
                        bid = i["marketDeptOrderBook"]["bid"][0]["price"]
                        return ask, bid

def get_ltp(asset, expiry_date, derivative_type='-', strike_price=0):
    return nse.nse_quote_ltp(asset, expiry_date, derivative_type, strike_price)  

def get_opt_expiry_list(asset):
    exp_list = list(nse.expiry_list(asset)['Date'])
    return exp_list

def get_fut_expiry_list(asset):
    exp_list = []
    fno_data = nse.nse_fno(asset.upper())
    for i in fno_data['stocks']:
        if i['metadata']['instrumentType'] == 'Index Futures':
            exp_list.append(i['metadata']['expiryDate'])
    exp_list = list(dict.fromkeys(exp_list))
    return exp_list

def add_in_orders(text):
    with open('orders.txt', 'a') as f_obj:
        f_obj.write(text)
        f_obj.write('\n')

def update_position(content):
    with open('positions.json', 'w') as f_obj:
           json.dump(content, f_obj)

def buy(asset, qty, expiry_date, derivative_type='-', strike_price=0):
    print("came in buy")
    ask, bid = get_ask_bid(asset, expiry_date, derivative_type, strike_price)
    add_in_orders(f"Bought {qty} quantity of {asset} {expiry_date} {strike_price} {derivative_type} in Rs.{ask} on {time.asctime()}")
    with open('positions.json', 'r') as f_obj:
        content = json.load(f_obj)
    if f"{asset} {expiry_date} {strike_price} {derivative_type}" in content['sell'].keys():
        sold_qty = content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0]
        if qty < sold_qty:
            content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0] = sold_qty - qty
            update_position(content)
        elif qty > sold_qty:
            content['sell'].pop(f"{asset} {expiry_date} {strike_price} {derivative_type}")
            update_position(content)
            content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"] = ((qty - sold_qty), bid)
            update_position(content)
        else:
            content['sell'].pop(f"{asset} {expiry_date} {strike_price} {derivative_type}")
            update_position(content)

    elif f"{asset} {expiry_date} {strike_price} {derivative_type}" in content['buy'].keys():
        buy_qty = content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0]
        old_buy_price = content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][1]
        avg_buy_price = ((old_buy_price * buy_qty) + (bid * qty))/(buy_qty + qty)
        content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0] = buy_qty + qty
        content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][1] = avg_buy_price
        update_position(content)

    else:
        content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"] = (qty, ask)
        update_position(content)


def sell(asset, qty, expiry_date, derivative_type='-', strike_price=0):
    print("came in sell")
    ask, bid = get_ask_bid(asset, expiry_date, derivative_type, strike_price)
    add_in_orders(f"Sold {qty} quantity of {asset} {expiry_date} {strike_price} {derivative_type} in Rs.{bid} on {time.asctime()}")
    with open('positions.json', 'r') as f_obj:
        content = json.load(f_obj)
    if f"{asset} {expiry_date} {strike_price} {derivative_type}" in content['buy'].keys():
        buy_qty = content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0]
        if qty < buy_qty:
            content['buy'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0] = buy_qty - qty
            update_position(content)
        elif qty > buy_qty:
            content['buy'].pop(f"{asset} {expiry_date} {strike_price} {derivative_type}")
            update_position(content)
            content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"] = ((qty - buy_qty), bid)
            update_position(content)
        else:
            content['buy'].pop(f"{asset} {expiry_date} {strike_price} {derivative_type}")
            update_position(content)

    elif f"{asset} {expiry_date} {strike_price} {derivative_type}" in content['sell'].keys():
        sold_qty = content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0]
        old_sold_price = content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][1]
        avg_sold_price = ((old_sold_price * sold_qty) + (bid * qty))/(sold_qty + qty)
        content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][0] = sold_qty + qty
        content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"][1] = avg_sold_price
        update_position(content)

    else:
        content['sell'][f"{asset} {expiry_date} {strike_price} {derivative_type}"] = (qty, bid)
        update_position(content)
