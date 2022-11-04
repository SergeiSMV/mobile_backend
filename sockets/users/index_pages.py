import ast
import websockets
from connection import cursor, connect
from initialization import router


@router.route('/index_pages')
async def index_pages(ws, path):
    try:
        try:
            message = await ws.recv()
            client_data = ast.literal_eval(message)
            func = client_data['func']
            await eval(func + f'({client_data})')
        except websockets.ConnectionClosedOK:
            pass
    finally:
        pass


async def sql_index_pages(data):
    user_id = data['user_id']
    user_pages = []
    db_pages = []

    sql1 = 'SELECT * FROM pages'
    connect.ping(reconnect=True)
    cursor.execute(sql1,)
    pages_const = cursor.fetchall()
    connect.commit()

    sql2 = 'SELECT page FROM page_access WHERE user_id = %s'
    val2 = (user_id, )
    cursor.execute(sql2, val2)
    page_access = cursor.fetchall()
    connect.commit()
    for up in page_access:
        user_page = up['page']
        user_pages.append(user_page)
    for up in pages_const:
        db_page = up['page']
        db_pages.append(db_page)

    for p in pages_const:
        page = p['page']
        mother_page = p['mother_page']
        page_department = p['page_department']
        page_description = p['page_description']
        access = 0
        if page in user_pages:
            continue
        else:
            sql3 = 'INSERT INTO page_access (user_id, page, mother_page, page_department, page_description, access) VALUES (%s, %s, %s, %s, %s, %s)'
            val3 = (user_id, page, mother_page, page_department, page_description, access)
            connect.ping(reconnect=True)
            cursor.execute(sql3, val3)
            cursor.fetchall()
            connect.commit()
            continue

    for dl in page_access:
        page = dl['page']
        if page in db_pages:
            continue
        else:
            sql4 = 'DELETE FROM page_access WHERE page = %s AND user_id = %s'
            val4 = (page, user_id)
            connect.ping(reconnect=True)
            cursor.execute(sql4, val4)
            cursor.fetchall()
            connect.commit()
            continue
