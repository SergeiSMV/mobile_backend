import ast
import json
from urllib.parse import unquote
import websockets
from connection import cursor, connect
from initialization import router


@router.route('/login')
async def login(ws, path):
    try:
        try:
            message = await ws.recv()
            print(type(message))
            client_data = ast.literal_eval(message)
            # user_login = client_data['login']
            # password = client_data['password']
            func = client_data['func']
            result = await eval(func + f'({client_data})')
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass

    # decoder = unquote(path.params['data'])
    # dataList = decoder.split(',')
    # log = dataList[0]
    # password = dataList[1]
    # sql = 'SELECT count(*) FROM users WHERE login = %s AND pass = %s'
    # val = (log, password)
    # cursor.execute(sql, val)
    # result = cursor.fetchall()
    # connect.commit()
    # await ws.send(json.dumps(result[0]['count(*)']))


async def sql_login(data):
    log = data['login']
    password = data['password']
    sql = 'SELECT count(*) FROM users WHERE login = %s AND pass = %s'
    val = (log, password)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()
    return result[0]['count(*)']
