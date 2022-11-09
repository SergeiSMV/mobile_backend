import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
import os


@router.route('/sim_locates')
async def sim_locates(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                print(f'sim_locates подключился клиент {ws}')
                func = client_data['func']
                result = await eval(func + '()')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'sim_locates websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'sim_locates websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_sim_locates():
    nameList = []
    cellsList = []
    data = {}

    sql = 'SELECT name FROM storage_locate GROUP BY name'
    connect.ping(reconnect=True)
    cursor.execute(sql, )
    names = cursor.fetchall()
    connect.commit()

    for n in names:
        name = n['name']
        nameList.append(name)
    data['locate'] = nameList

    for c in nameList:
        sql2 = 'SELECT cell FROM storage_locate WHERE name = %s'
        val2 = (c,)
        cursor.execute(sql2, val2)
        result = cursor.fetchall()
        connect.commit()
        data[f'{c}'] = []
        for cell in result:
            data[f'{c}'].append(cell['cell'])

    return data
