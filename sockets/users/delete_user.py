import ast
import websockets
from connection import cursor, connect
from initialization import router
import json


@router.route('/delete_user')
async def delete_user(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'({client_data})')
                await ws.send(json.dumps(result))
            except websockets.ConnectionClosedOK:
                print(f'add_user websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'add_user websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_delete_user(data):
    user_id = data['user_id']

    sql = 'DELETE FROM users WHERE id = %s'
    val = (user_id,)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    sql2 = 'DELETE FROM page_access WHERE user_id = %s'
    val2 = (user_id,)
    connect.ping(reconnect=True)
    cursor.execute(sql2, val2)
    cursor.fetchall()
    connect.commit()

    return 'done'
