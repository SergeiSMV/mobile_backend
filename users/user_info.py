import json
from urllib.parse import unquote

from connection import cursor, connect
from initialization import router


@router.route('/userinfo/{data}')
async def user_info(ws, path):
    decoder = unquote(path.params['data'])
    dataList = decoder.split(',')
    log = dataList[0]
    password = dataList[1]
    sql = 'SELECT * FROM users WHERE login = %s AND pass = %s'
    val = (log, password)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()
    await ws.send(json.dumps(result[0]))
