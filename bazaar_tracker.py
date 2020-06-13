import requests
import tkinter as tk #Make interface with BUTTON(S)
import shutil, os
from time import strftime
import time
import json

from products import products 
from minions_info import minions_info
from items_info import items_info
from items_info import minion_fuels


API_KEY = ''
MINION_AMOUNT = 1
DAYS_AFK = 1

def get_item_info(item_id):
    # Will get all of the info (from the item name, 'buying_price','selling_price','weekly_sell_volume')
    # from the Hypixel API, requires the addition of an API-Key,
    # which is gained by doing '/api new' in game, on the server.
    # **Need to check if API key is valid ('Success?')
    global api_key

    while True: #to make sure that the item is gotten
        f = requests.get(
        'https://api.hypixel.net/skyblock/bazaar/product?key=' + API_KEY + '&productId=' + item_id).json()
            
        print(item_id)
        try:
            item_name = item_id #Name of item
            selling_price = f['product_info']['sell_summary'][0]['pricePerUnit'] #to find profit
            buying_price = f['product_info']['buy_summary'][0]['pricePerUnit'] #to find cost for upgrading minions
            weekly_sell_volume = f['product_info']['quick_status']['sellVolume'] #amount sold in last week

            print('SUCCESS!')
            break
        except:
            print('ERROR!')
            time.sleep(1)
            
    return {'selling_price':selling_price,
            'buying_price':buying_price,
            'weekly_sell_volume':weekly_sell_volume}

def get_items_info():
    global items_info
    global minion_fuels
    global minion_info

    counter = 0
    time_before = time.time()
    for i in products:
        items_info[i] = get_item_info(i) #Ensures that items are always propers' made
        counter += 1
        print(str(counter) + '/' + str(len(products)))

    time_after = time.time()

    time_for_operation = round(time_after - time_before, 2)
    print('Fetching operation took %.2f seconds' % time_for_operation)    
        
    # Things not listed in bazaar, just hardcoding them in, lmao.
    # Might be best to just default within the 'items_info.py' file
    items_info['ENCHANTED_WOOL'] = {'selling_price':320,'buying_price':0,'weekly_sell_volume':1000000}
    items_info['SILVER_FANG'] = {'selling_price':25*items_info['ENCHANTED_GHAST_TEAR']['selling_price'],\
                                 'buying_price':25*items_info['ENCHANTED_GHAST_TEAR']['buying_price'],\
                                 'weekly_sell_volume':items_info['ENCHANTED_GHAST_TEAR']['weekly_sell_volume']/25}
    items_info['COAL_BLOCK'] = {'selling_price':9*items_info['COAL']['selling_price'],\
                                 'buying_price':9*items_info['COAL']['buying_price'],\
                                 'weekly_sell_volume':items_info['COAL']['weekly_sell_volume']/25}

    for fuel in minion_fuels:
        items_per_day = fuel['items_per_day']
        fuel_name     = fuel['fuel']        
        fuel_price    = items_info[fuel_name]['buying_price']

        fuel['fuel_cost'] = fuel_price * items_per_day

    minion_fuels = sorted(minion_fuels, key = lambda i: i['fuel_cost'], reverse = True)    

    
    # To cache values of items_info
    c = open('items_info.py', 'w')
    c.write('items_info = ' + str(items_info) + '\n\n')
    c.write('minion_fuels = ' + str(minion_fuels))
    c.close()

def find_profit(minion):
    # Returns actual values calculated from the info gathered in get_item_info in dict format
    # {'minion':minion, 'profit':profit, 'fuel':fuel, 'item_information':minion_items}
    global items_info
    global minion_fuels
    global MINION_AMOUNT

    minion_info = minions_info[minion]
    efficiency_upgrade = minion_info['efficiency_upgrade']
    upgrade_slot = minion_info['upgrade_slot']
    
    profit = 0
    minion_items = []
    #separately makes a list for every item that the minion produces
    
    for minion_item_produced in minion_info['items_produced']: #adds profit for every item
        item = minion_item_produced[0]
        items_per_day = round(minion_item_produced[1] * efficiency_upgrade * MINION_AMOUNT, 3) #add DAYS_AFK as Coefficient
        weekly_sell_volume = items_info[item]['weekly_sell_volume']

        percentage_of_market = round(((items_per_day / weekly_sell_volume \
                                       * 7 * efficiency_upgrade) * 100), 3) #Divide by DAYS_AFK
                                       #be wary if >5% or so, might be hard to sell
        
        minion_items.append([item, percentage_of_market, items_per_day]) #, percentage_of_market

        profit += items_info[item]['selling_price'] * items_per_day    

    fuel = None
    # Checks every fuel type, adds as fuel, and adjusts profits if applicable
    for minion_fuel in minion_fuels:


        speed_upgrade = minion_fuel['speed_upgrade']

        new_profit = profit / upgrade_slot * speed_upgrade - minion_fuel['fuel_cost']
        if new_profit > profit:
            fuel = minion_fuel['fuel']
            profit = new_profit

            for item in minion_items:
                item[1] = round(speed_upgrade * item[1] / upgrade_slot, 3)
                item[2] = round(speed_upgrade * item[2] / upgrade_slot, 3)                

    profit = round(profit, 3)
    
    return {'minion':minion, 'profit':profit, 'fuel':fuel, 'item_information':minion_items}

def write_values(parsed_minion_info):
    #
    out_line = parsed_minion_info['minion'] + ' Minion:\n'

    out_line += 'Profit:' + str(parsed_minion_info['profit']) + '\n'

    out_line += 'Fuel:' + str(parsed_minion_info['fuel']) + '\n'
    
    out_line += 'Items Produced:\n'
    for i in parsed_minion_info['item_information']:
        out_line += '   ' + i[0] + ':\n'
        print('Calculating... ' + i[0])
        out_line += '       Market Share:' + str(i[1]) + '%\n'
        out_line += '       Items Per Day:' + str(i[2]) + '\n'

    out_line += '-' * 30 + '\n'

    return out_line        

def calc_and_sort_data():
    global minion_fuels
    
    parsed_minion_profits = []
    for minion in minions_info:
        minion_info = minions_info[minion]
        
        parsed_minion_profits.append(find_profit(minion))

    parsed_minion_profits = sorted(parsed_minion_profits, key = lambda i: i['profit'], reverse = True)

    current_time_readable = strftime('%y-%m-%d %H%M%S')
    current_time_unix = int(time.time())
    
    file_name = current_time_readable + '.txt'
    json_file_name = str(current_time_unix) + '.json'
    print(file_name)
    
    # Parsed & readable
    d = open(file_name, 'w')
    for i in parsed_minion_profits:
        d.write(write_values(i))
    d.close()    
    shutil.move(file_name, 'Bazaar Prices')

    # With no parsing, to allow for easy graphing of, generally just for more future use
    e = open(json_file_name, 'w')
    e.write('{\n')

    counter = 0
    for i in parsed_minion_profits:
        out_line  = '"' + i['minion'] + '":'
        del i['minion'] 
        i_json = json.dumps(i)

        out_line += str(i_json)
        
        counter += 1
        if counter != len(parsed_minion_profits):
            out_line += ',\n'
        e.write(out_line)
    e.write('\n}')
    e.close()    
    shutil.move(json_file_name, 'Bazaar Prices json')
    
    print('\nDONE')

def get_and_parse():
    
    get_items_info()
    calc_and_sort_data()

def constantly_calculate():
    while True:
        get_and_parse()
        time.sleep(501)

def close_gui():
    window.destroy()


# Creates tk window to do various functions   
window = tk.Tk()
greeting = tk.Label(text = 'Minion Profit Calculator')

# Fetch and recalculate values
get_items_info_button = tk.Button(window,
                                  fg = 'blue',
                                  text='Click to get values',
                                  command=get_and_parse)
get_items_info_button.pack(side=tk.LEFT)

# Mostly for testing / debugging
recaculate_button = tk.Button(window, 
                              fg = 'green',
                              text='Click to recalculate profits',
                              command=calc_and_sort_data)
recaculate_button.pack(side=tk.LEFT)

# To continuously loop the get_and_parse function
constant_calculating_button = tk.Button(window,
                                        fg = 'purple',
                                        text='Click to get values every 10 minutes',
                                        command=constantly_calculate)
constant_calculating_button.pack(side=tk.LEFT)

exit_program_button = tk.Button(window, text="Exit", fg="red",command=close_gui)
exit_program_button.pack(side=tk.LEFT)

window.mainloop()
