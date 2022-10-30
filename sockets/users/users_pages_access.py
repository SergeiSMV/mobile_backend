import ast
import json
import websockets
from connection import cursor, connect
from initialization import router


@router.route('/usersPages')
async def users_pages(ws, path):
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


async def sql_users_pages(data):
    user_id = data['user_id']
    sql = 'SELECT * FROM page_access WHERE user_id = %s'
    val = (user_id, )
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    pages = cursor.fetchall()
    connect.commit()
    return pages
