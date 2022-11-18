import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
import os

CLIENTS_ACCESS = {}


@router.route('/uniq_sim_items')
async def uniq_sim_items(ws, path):
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


async def sql_uniq_sim_items(broadcast=False):
    uniqSimItemsList = []

    sql = 'SELECT category, name, color, producer, SUM(quant - reserve) AS quant, unit FROM sim WHERE status = %s' \
          'GROUP BY category, name, color, producer, unit'
    val = ('work', )
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()

    for items in result:
        category = items['category']
        name = items['name']
        color = items['color']
        producer = items['producer']
        quant = int(items['quant'])
        unit = items['unit']

        items_map = {
            'category': category,
            'name': name,
            'color': color,
            'producer': producer,
            'quant': quant,
            'unit': unit,
        }
        if quant <= 0:
            continue
        else:
            uniqSimItemsList.append(items_map)

    if broadcast:
        for ws in CLIENTS_ACCESS:
            await CLIENTS_ACCESS[ws].send(json.dumps(uniqSimItemsList))
    else:
        return uniqSimItemsList


async def delClient(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
