import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

from sockets.sim.items.sim_items import sim_all_items
from sockets.sim.orders.get_items_by_num import sql_get_items_by_num
from sockets.sim.orders.sim_orders import sql_sim_orders
from sockets.sim.items.sim_uniq_items import sql_uniq_sim_items


@router.route('/quant_err_handler')
async def quant_err_handler(ws, path):
    try:
        while True:
            try:
                message = await ws.recv()
                client_data = ast.literal_eval(message)
                func = client_data['func']
                result = await eval(func + f'({client_data})')
                await ws.send(json.dumps(result))
                await ws.wait_closed()
            except websockets.ConnectionClosedOK:
                print(f'sim_item_move websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'sim_item_move websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_quant_err_handler(data):
    item_data = data['item_data']
    order_id = item_data['order_id']
    num = item_data['num']
    item_id = item_data['item_id']
    err_cause = item_data['err_cause']
    fact_quant = item_data['fact_quant']
    order_id = item_data['order_id']
    order_fact = item_data['order_fact']
    order_quant = item_data['order_quant']

    if err_cause == 'clear':
        # снимаем ошибку с позиции в заявке
        clear = 'UPDATE sim_orders SET fact_quant = %s, status = %s, err_cause = %s, err_quant = %s  WHERE num = %s AND item_id = %s'
        clear_val = (order_quant, 2, '', 0, num, item_id)
        connect.ping(reconnect=True)
        cursor.execute(clear, clear_val)
        cursor.fetchall()
        connect.commit()

        # получаем список всех статусов по заявке
        get_status_list = 'SELECT status FROM sim_orders WHERE num = %s AND actions = %s'
        get_value = (num, 'выдача')
        connect.ping(reconnect=True)
        cursor.execute(get_status_list, get_value)
        result = cursor.fetchall()
        connect.commit()
        status_list = []
        for st in result:
            status_list.append(st['status'])
        status = min(status_list)

        # ставим минимальный статус в ордере
        update_status = 'UPDATE sim_orders SET status = %s WHERE id = %s'
        update_value = (status, order_id)
        connect.ping(reconnect=True)
        cursor.execute(update_status, update_value)
        cursor.fetchall()
        connect.commit()

    elif err_cause == 'more':
        # меняем фактически выданное количество и err_cause в позиции
        change_color = 'UPDATE sim_orders SET fact_quant = %s, err_cause = %s WHERE item_id = %s'
        change_value = (fact_quant, 'more', item_id)
        connect.ping(reconnect=True)
        cursor.execute(change_color, change_value)
        cursor.fetchall()
        connect.commit()

    elif err_cause == 'return':
        change_color = 'UPDATE sim_orders SET fact_quant = %s, err_cause = %s WHERE item_id = %s'
        change_value = (fact_quant, 'return', item_id)
        connect.ping(reconnect=True)
        cursor.execute(change_color, change_value)
        cursor.fetchall()
        connect.commit()

    data = {'num': num}

    await sql_get_items_by_num(data, broadcast=True)
    await sql_uniq_sim_items(broadcast=True)
    await sql_sim_orders(broadcast=True)
    await sim_all_items(broadcast=True)
    return 'done'
