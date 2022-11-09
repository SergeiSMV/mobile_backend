import ast
import base64
import os

import websockets
from initialization import router
import json

from sockets.sim.sim_items import sim_all_items


@router.route('/delete_image')
async def delete_image(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'({client_data})')
                await ws.send(json.dumps(result))
            except websockets.ConnectionClosedOK:
                print(f'save_image websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'save_image websockets.ConnectionClosedError: отключился клиент {ws}')


async def f_delete_image(data):
    itemData = data['item_data']
    browser_link = itemData['images']
    link = browser_link.replace('https://backraz.ru', '/usr/local/bin')
    try:
        os.remove(link)
    except FileNotFoundError:
        pass
    await sim_all_items(broadcast=True)
    return 'done'
