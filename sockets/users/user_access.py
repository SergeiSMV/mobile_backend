import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

CLIENTS_ACCESS = {}


@router.route('/user_access')
async def user_access(ws, path):
    global CLIENTS_ACCESS
    user_id = 0
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                user_id = client_data['user_id']
                CLIENTS_ACCESS[user_id] = ws
                print(f'подключился клиент {ws}')
                func = client_data['func']
                result = await eval(func + f'({client_data})')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'websockets.ConnectionClosedOK: отключился клиент {ws}')
                await delClient(user_id)
                break
    except websockets.ConnectionClosedError:
        print(f'websockets.ConnectionClosedError: отключился клиент {ws}')
        await delClient(user_id)


async def sql_user_access(data):
    pageList = []
    user_id = data['user_id']
    sql = 'SELECT * FROM page_access WHERE user_id = %s AND access = 1'
    val = (user_id,)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()
    for pages in result:
        page = pages['page']
        mother_page = pages['mother_page']
        page_department = pages['page_department']
        page_description = pages['page_description']
        items_map = {
            'page': page,
            'mother_page': mother_page,
            'page_departments': page_department,
            'page_description': page_description
        }
        pageList.append(items_map)
    return pageList


async def sql_save_user_access(data):
    for update in data['data']:
        string_id = update['id']
        access_value = update['access']
        sql = 'UPDATE page_access SET access = %s WHERE id = %s'
        val = (access_value, string_id)
        connect.ping(reconnect=True)
        cursor.execute(sql, val)
        cursor.fetchall()
        connect.commit()
    # await CLIENTS_ACCESS[data['data']['user_id']].send(json.dumps( data['data']))
    print(CLIENTS_ACCESS)


async def delClient(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
