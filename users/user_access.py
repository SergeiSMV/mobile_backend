import json
from urllib.parse import unquote

from connection import cursor, connect
from initialization import router


@router.route('/getaccess/{id}')
async def get_access(ws, path):
    pageList = []
    user_id = unquote(path.params['id'])
    sql = 'SELECT * FROM page_access WHERE user_id = %s AND access = 1'
    val = (user_id, )
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()
    for pages in result:
        page = pages['page']
        # pages_map = {
        #     'page': page
        # }
        pageList.append(page)
    await ws.send(json.dumps(pageList))
