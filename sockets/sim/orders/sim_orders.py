import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
import os

CLIENTS_ACCESS = {}


@router.route('/sim_orders')
async def sim_orders(ws, path):
    global CLIENTS_ACCESS
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_ACCESS[user_id] = ws
                print(f'подключился клиент {ws}')
                func = client_data['func']
                result = await eval(func + '()')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'websockets.ConnectionClosedOK: отключился клиент {ws}')
                await delClient(user_id)
                break
    except websockets.ConnectionClosedError:
        print(f'websockets.ConnectionClosedError: отключился клиент {ws}')
        await delClient(user_id)


async def sql_sim_orders(broadcast=False):
    allSimOrdersList = []

    sql = 'SELECT * FROM sim_orders WHERE actions = %s'
    val = ('заявка', )
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()

    for orders in result:
        order_id = orders['id']
        num = orders['num']
        actions = orders['actions']
        item_id = orders['item_id']
        item_place = orders['item_place']
        item_cell = orders['item_cell']
        date = orders['date'].strftime('%d.%m.%Y')
        time = orders['time']
        customer = orders['customer']
        category = orders['category']
        name = orders['name']
        color = orders['color']
        producer = orders['producer']
        order_quant = orders['order_quant']
        fact_quant = orders['fact_quant']
        status = orders['status']
        comment = orders['comment']
        err_cause = orders['err_cause']
        err_quant = orders['err_quant']
        err_color = orders['err_color']
        err_item = orders['err_item']
        unit = orders['unit']

        items_map = {
            'order_id': order_id, 'num': num, 'actions': actions, 'item_id': item_id, 'item_place': item_place,
            'item_cell': item_cell, 'date': date, 'time': time, 'customer': customer, 'category': category,
            'name': name, 'color': color, 'producer': producer, 'order_quant': order_quant, 'fact_quant': fact_quant,
            'status': status, 'comment': comment, 'err_cause': err_cause, 'err_quant': err_quant, 'err_color': err_color,
            'err_item': err_item, 'unit': unit
        }
        allSimOrdersList.append(items_map)
    if broadcast:
        for ws in CLIENTS_ACCESS:
            await CLIENTS_ACCESS[ws].send(json.dumps(allSimOrdersList))
    else:
        return allSimOrdersList


async def delClient(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
