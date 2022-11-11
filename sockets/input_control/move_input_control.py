import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
from datetime import datetime

from sockets.sim.admissions_item import sql_admission_items
from sockets.sim.sim_items import sim_all_items


@router.route('/move_input_control')
async def move_input_control(ws, path):
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


async def sql_move_input_control(data):
    item_data = data['item']

    item_id = item_data['itemId']

    place = item_data['place']
    cell = item_data['cell']
    bcode = item_data['bcode']
    category = item_data['category']
    name = item_data['name']
    color = item_data['color']
    producer = item_data['producer']
    quant = item_data['quant']
    unit = item_data['unit']
    fifo = item_data['fifo']
    dateReplace = fifo.replace('.', '/')
    dateCorrect = datetime.strptime(dateReplace, '%d/%m/%Y')
    author = item_data['author']

    sql = 'INSERT INTO sim (place, cell, bcode, category, name, color, producer, quant, unit, fifo, author, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    val = (place, cell, bcode, category, name, color, producer, quant, unit, dateCorrect.date(), author, 'work')
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    sql2 = 'DELETE FROM admissions WHERE id = %s'
    val2 = (item_id, )
    connect.ping(reconnect=True)
    cursor.execute(sql2, val2)
    cursor.fetchall()
    connect.commit()

    await sim_all_items(broadcast=True)
    await sql_admission_items(broadcast=True)
    return 'done'

