import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
from datetime import datetime
from datetime import date

from sockets.sim.items.sim_items import sim_all_items
from sockets.sim.orders.get_items_by_num import sql_get_items_by_num
from sockets.sim.orders.sim_orders import sql_sim_orders
from sockets.sim.items.sim_uniq_items import sql_uniq_sim_items


@router.route('/sim_item_out')
async def sim_item_out(ws, path):
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


async def sql_sim_item_out(item_data):
    order_id = item_data['order_id']
    item_id = item_data['item_id']
    out_quant = item_data['out_quant']
    comment = item_data['comment']
    customer = item_data['customer']
    num = item_data['num']
    status_quant = int(item_data['status_quant'])
    order_fact = int(item_data['order_fact'])
    time = datetime.now().strftime('%H:%M')
    data = {'num': num}
    status = 2 if order_fact + int(out_quant) >= status_quant else 1

    sql = 'UPDATE sim_orders SET time = %s, customer = %s, fact_quant = %s, comment = %s, status = %s  WHERE num = %s AND item_id = %s'
    val = (time, customer, out_quant, comment, 2, num, item_id)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    sql = 'UPDATE sim_orders SET fact_quant = %s, status = %s  WHERE id = %s'
    val = (int(out_quant) + order_fact, status, order_id)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    await sql_get_items_by_num(data, broadcast=True)
    await sql_uniq_sim_items(broadcast=True)
    await sql_sim_orders(broadcast=True)
    await sim_all_items(broadcast=True)
    return 'done'
