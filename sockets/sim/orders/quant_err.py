import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

from sockets.sim.items.sim_items import sim_all_items
from sockets.sim.orders.get_items_by_num import sql_get_items_by_num
from sockets.sim.orders.sim_orders import sql_sim_orders
from sockets.sim.items.sim_uniq_items import sql_uniq_sim_items


@router.route('/quant_err')
async def quant_err(ws, path):
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


async def sql_quant_err(data):
    item_data = data['item_data']
    order_id = item_data['order_id']
    num = item_data['num']
    item_id = item_data['item_id']
    data = {'num': num}
    err_quant = item_data['err_quant']
    status = item_data['status']

    sql = 'UPDATE sim_orders SET status = %s, err_quant = %s WHERE num = %s AND item_id = %s'
    val = (status, err_quant, num, item_id)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    sql = 'UPDATE sim_orders SET status = %s  WHERE id = %s'
    val = (status, order_id)
    connect.ping(reconnect=True)
    cursor.execute(sql, val)
    cursor.fetchall()
    connect.commit()

    await sql_get_items_by_num(data, broadcast=True)
    await sql_uniq_sim_items(broadcast=True)
    await sql_sim_orders(broadcast=True)
    await sim_all_items(broadcast=True)
    return 'done'
