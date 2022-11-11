import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

from sockets.sim.sim_items import sim_all_items


@router.route('/sim_item_move')
async def sim_item_move(ws, path):
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


async def sql_sim_item_move(data):
    item_id = data['item_id']
    place = data['place']
    cell = data['cell']

    sql = 'UPDATE sim SET place = %s, cell = %s  WHERE id = %s'
    val = (place, cell, item_id)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    await sim_all_items(broadcast=True)
    return 'done'

