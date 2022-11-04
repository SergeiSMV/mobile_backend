import ast
import json
import websockets
from connection import cursor, connect
from initialization import router


@router.route('/all_users')
async def all_users(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            func = client_data['func']
            result = await eval(func + f'()')
            await ws.send(json.dumps(result))
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def sql_all_users():
    usersList = []
    sql = 'SELECT * FROM users'
    connect.ping(reconnect=True)
    cursor.execute(sql, )
    users = cursor.fetchall()
    connect.commit()
    for user in users:
        user_id = user['id']
        surname = user['surname']
        name = user['name']
        patronymic = user['patronymic']
        position = user['position']
        department = user['department']
        phone = user['phone']
        status = user['status']
        login = user['login']
        password = user['pass']
        users_map = {
            'user_id': user_id,
            'surname': surname,
            'name': name,
            'patronymic': patronymic,
            'position': position,
            'department': department,
            'phone': phone,
            'status': status,
            'login': login,
            'pass': password
        }
        usersList.append(users_map)
    return usersList

