import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

from sockets.sim.items.sim_items import sim_all_items


@router.route('/color_items')
async def color_items(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'()')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'color_items websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'color_items websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_color_items():
    colors = []

    sql = 'SELECT color FROM sim GROUP BY color'
    connect.ping(reconnect=True)
    cursor.execute(sql, )
    result = cursor.fetchall()
    connect.commit()

    colors.clear()
    for color in result:
        colors.append(color['color'])

    return colors

