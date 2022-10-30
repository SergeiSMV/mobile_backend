import ast
import json
import websockets
from connection import cursor, connect
from initialization import router


@router.route('/login')
async def login(ws, path):
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


async def sql_login(data):
    log = data['login']
    password = data['password']
    sql = 'SELECT count(*) FROM users WHERE login = %s AND pass = %s'
    val = (log, password)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()
    return result[0]['count(*)']
