import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
import os

CLIENTS_ACCESS = {}


@router.route('/sim_items')
async def sim_items(ws, path):
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


async def sim_all_items(broadcast=False):
    allSimItemsList = []

    sql = 'SELECT * FROM sim'
    connect.ping(reconnect=True)
    cursor.execute(sql, )
    result = cursor.fetchall()
    connect.commit()

    for items in result:
        itemId = items['id']
        place = items['place']
        cell = items['cell']
        bcode = items['bcode']
        category = items['category']
        name = items['name']
        color = items['color']
        producer = items['producer']
        quantity = items['quant']
        reserve = items['reserve']
        unit = items['unit']
        fifo = items['fifo'].strftime('%d.%m.%Y')
        author = items['author']
        status = items['status']
        comment = items['comment'].split(']')

        imageLinks = []

        try:
            if os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
                for file in os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
                    imageLinks.append(f'https://backraz.ru/images/{category}/{name}/{producer}/{color}/{file}')
            else:
                pass
        except FileNotFoundError:
            pass

        items_map = {
            'itemId': itemId, 'place': place, 'cell': cell, 'bcode': bcode,
            'category': category, 'name': name, 'color': color, 'producer': producer,
            'quantity': quantity, 'reserve': reserve, 'unit': unit, 'fifo': fifo,
            'author': author, 'status': status, 'comment': comment,
            'images': imageLinks
        }
        allSimItemsList.append(items_map)
    if broadcast:
        for ws in CLIENTS_ACCESS:
            await CLIENTS_ACCESS[ws].send(json.dumps(allSimItemsList))
    else:
        return allSimItemsList


async def delClient(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
