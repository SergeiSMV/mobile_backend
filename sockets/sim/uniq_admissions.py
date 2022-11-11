import ast
import json
import websockets
from connection import cursor, connect
from initialization import router


@router.route('/uniq_admissions')
async def uniq_admissions(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'()')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'sim_item_move websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'sim_item_move websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_uniq_admissions():
    uniqueAdmissions = []

    sql = 'SELECT category, name, color, producer, SUM(quant) AS quant, unit, fifo, author FROM admissions GROUP BY category, name, color, producer, unit, fifo, author'
    connect.ping(reconnect=True)
    cursor.execute(sql, )
    result = cursor.fetchall()
    connect.commit()

    for unique_items in result:
        category = unique_items['category']
        name = unique_items['name']
        color = unique_items['color']
        producer = unique_items['producer']
        quant = int(unique_items['quant'])
        unit = unique_items['unit']
        fifo = unique_items['fifo'].strftime('%d.%m.%Y')
        author = unique_items['author']
        items_map = {
            'category': category,
            'name': name,
            'color': color,
            'producer': producer,
            'quant': quant,
            'unit': unit,
            'fifo': fifo,
            'author': author
        }
        uniqueAdmissions.append(items_map)
    return uniqueAdmissions

