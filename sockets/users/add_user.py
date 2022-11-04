import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
from sockets.users.index_pages import sql_index_pages


@router.route('/add_user')
async def add_user(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'({client_data})')
                print(result)
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'add_user websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'add_user websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_add_user(data):
    name = data['name']
    surname = data['surname']
    patronymic = data['patronymic']
    position = data['position']
    department = data['department']
    login = data['login']
    password = data['pass']
    status = data['status']

    sql = 'INSERT INTO users (' \
          'name, surname, patronymic, position, department, login, pass, status) ' \
          'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    val = (name, surname, patronymic, position, department, login, password, status)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    sql2 = 'SELECT MAX(id) FROM users'
    connect.ping(reconnect=True)
    cursor.execute(sql2, )
    result = cursor.fetchall()
    connect.commit()
    index_data = {'user_id': result[0]['MAX(id)']}

    await sql_index_pages(index_data)
    return 'done'

