import ast
import base64
import os

import websockets
from initialization import router
import json

from sockets.sim.sim_items import sim_all_items


@router.route('/save_image')
async def save_image(ws, path):
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


async def f_save_image(data):
    itemData = data['item_data']
    category = itemData['category']
    name = itemData['name']
    producer = itemData['producer']
    color = itemData['color']
    files = []
    count = 1
    code = data['image']
    try:
        if os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
            for file in os.listdir(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}'):
                files.append(int(file.split('.')[0]))
            image_name = count + max(files)
            with open(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}/{image_name}.jpg', 'wb') as fh:
                fh.write(base64.b64decode(code))
            fh.close()
        else:
            image_name = count
            with open(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}/{image_name}.jpg', 'wb') as fh:
                fh.write(base64.b64decode(code))
            fh.close()
    except FileNotFoundError:
        os.makedirs(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}')
        image_name = count
        with open(f'/usr/local/bin/images/{category}/{name}/{producer}/{color}/{image_name}.jpg', 'wb') as fh:
            fh.write(base64.b64decode(code))
        fh.close()
    await sim_all_items(broadcast=True)
    return 'done'
