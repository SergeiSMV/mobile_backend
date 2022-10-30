import ast
import json
import websockets

from connection import cursor, connect
from initialization import router


@router.route('/user_info')
async def user_info(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            func = client_data['func']
            result = await eval(func + f'({client_data})')
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def sql_user_info(data):
    user_id = data['user_id']
    if user_id == 0:
        login = data['log']
        password = data['pass']
        sql1 = 'SELECT * FROM users WHERE login = %s AND pass = %s'
        val1 = (login, password)
        cursor.execute(sql1, val1)
        result = cursor.fetchall()
        connect.commit()
        return result[0]
    else:
        sql2 = 'SELECT * FROM users WHERE id = %s'
        val2 = (user_id, )
        cursor.execute(sql2, val2)
        result = cursor.fetchall()
        connect.commit()
        return result[0]

