import ast
import datetime
import json
import websockets
from connection import cursor, connect
from initialization import router
from sockets.sim.add_items.admissions_item import sql_admission_items


@router.route('/sim_add_item')
async def sim_add_item(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'({client_data})')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'sim_item_move websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'sim_item_move websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_add_item(data):
    bcode = data['bcode']
    category = data['category']
    name = data['name']
    color = data['color']
    producer = data['producer']
    quant = data['quant']
    unit = data['unit']
    fifo = datetime.datetime.now().date()
    author = data['author']

    addItem = 'INSERT INTO admissions (bcode, category, name, color, producer, quant, unit, fifo, author) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    addItemVal = (bcode, category, name, color, producer, quant, unit, fifo, author)
    connect.ping(reconnect=True)
    cursor.execute(addItem, addItemVal)
    cursor.fetchall()
    connect.commit()

    # addItem = 'INSERT INTO sim (bcode, category, name, color, producer, quant, unit, fifo, author, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    # addItemVal = (bcode, category, name, color, producer, quant, unit, fifo, author, 'wait')
    # connect.ping(reconnect=True)
    # cursor.execute(addItem, addItemVal)
    # cursor.fetchall()
    # connect.commit()
    #
    # await sim_all_items(broadcast=True)
    await sql_admission_items(broadcast=True)
    return 'done'

