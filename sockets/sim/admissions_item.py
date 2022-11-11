import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

CLIENTS_ACCESS = {}


@router.route('/admission_items')
async def admission_items(ws, path):
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


async def sql_admission_items(broadcast=False):
    admissionsItemsList = []

    sql = 'SELECT * FROM admissions'
    connect.ping(reconnect=True)
    cursor.execute(sql, )
    result = cursor.fetchall()
    connect.commit()

    for items in result:
        itemId = items['id']
        bcode = items['bcode']
        category = items['category']
        name = items['name']
        color = items['color']
        producer = items['producer']
        unit = items['unit']

        quant = items['quant']
        fifo = items['fifo'].strftime('%d.%m.%Y')
        author = items['author']

        items_map = {
            'itemId': itemId, 'bcode': bcode,
            'category': category, 'name': name, 'color': color, 'producer': producer,
            'unit': unit, 'quant': quant, 'fifo': fifo, 'author': author
        }
        admissionsItemsList.append(items_map)
    if broadcast:
        for ws in CLIENTS_ACCESS:
            await CLIENTS_ACCESS[ws].send(json.dumps(admissionsItemsList))
    else:
        return admissionsItemsList


async def delClient(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
