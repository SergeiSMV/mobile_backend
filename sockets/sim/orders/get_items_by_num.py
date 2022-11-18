import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

CLIENTS_ACCESS = {}


@router.route('/get_items_by_num')
async def get_items_by_num(ws, path):
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


async def sql_get_items_by_num(data, broadcast=False):
    num = data['num']
    items_by_num = []

    sql = 'SELECT * FROM sim_orders WHERE num = %s AND actions = %s'
    val = (num, 'выдача')
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    result = cursor.fetchall()
    connect.commit()

    for item in result:
        item_id = item['item_id']
        item_place = item['item_place']
        item_cell = item['item_cell']
        fifo = item['date'].strftime('%d.%m.%Y')
        time = item['time']
        customer = item['customer']
        category = item['category']
        name = item['name']
        color = item['color']
        producer = item['producer']
        order_quant = item['order_quant']
        fact_quant = item['fact_quant']
        status = item['status']
        comment = item['comment']
        err_cause = item['err_cause']
        err_quant = item['err_quant']
        err_color = item['err_color']
        err_item = item['err_item']
        unit = item['unit']

        sql2 = 'SELECT quant FROM sim WHERE id = %s'
        val2 = (item_id, )
        connect.ping(reconnect=True)
        cursor.execute(sql2, val2)
        quant_result = cursor.fetchone()
        connect.commit()

        base_quant = quant_result['quant']

        sql3 = 'SELECT id, order_quant, fact_quant FROM sim_orders WHERE num = %s AND actions = %s AND category = %s AND name = %s AND color = %s'
        val3 = (num, 'заявка', category, name, color)
        connect.ping(reconnect=True)
        cursor.execute(sql3, val3)
        order_info = cursor.fetchone()
        connect.commit()

        order_id = order_info['id']
        order_fact = order_info['fact_quant']
        status_quant = order_info['order_quant']

        # order_fact = order_fact_result['fact_quant']

        items_map = {
            'order_id': order_id, 'num': num, 'item_id': item_id, 'item_place': item_place, 'fifo': fifo,
            'item_cell': item_cell, 'category': category, 'name': name, 'color': color, 'producer': producer, 'order_fact': order_fact,
            'base_quant': base_quant, 'order_quant': order_quant, 'fact_quant': fact_quant, 'status': status, 'comment': comment,
            'err_cause': err_cause, 'err_quant': err_quant, 'err_color': err_color, 'err_item': err_item, 'unit': unit,
            'status_quant': status_quant, 'customer': customer, 'time': time
        }
        items_by_num.append(items_map)

    if broadcast:
        for ws in CLIENTS_ACCESS:
            await CLIENTS_ACCESS[ws].send(json.dumps(items_by_num))
    else:
        return items_by_num


async def delClient(user_id):
    try:
        del CLIENTS_ACCESS[user_id]
    except KeyError:
        pass
