import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

from sockets.sim.items.sim_items import sim_all_items


@router.route('/change_item_status')
async def change_item_status(ws, path):
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


async def sql_change_item_status(data):
    item_id = data['item_id']
    all_comments = data['comment']
    status = data['status']
    comment = ''

    for c in all_comments:
        if c == '':
            continue
        else:
            comment = f'{c}]' + comment

    sql = 'UPDATE sim SET status = %s, comment = %s WHERE id = %s'
    val = (status, comment, item_id)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    await sim_all_items(broadcast=True)
    return 'done'

