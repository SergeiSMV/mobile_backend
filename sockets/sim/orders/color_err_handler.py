import ast
import json
import websockets
from connection import cursor, connect
from initialization import router

from sockets.sim.items.sim_items import sim_all_items
from sockets.sim.orders.get_items_by_num import sql_get_items_by_num
from sockets.sim.orders.sim_orders import sql_sim_orders
from sockets.sim.items.sim_uniq_items import sql_uniq_sim_items


@router.route('/color_err_handler')
async def color_err_handler(ws, path):
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


async def sql_color_err_handler(data):
    item_data = data['item_data']
    order_id = item_data['order_id']
    num = item_data['num']
    item_id = item_data['item_id']
    data = {'num': num}
    err_color = item_data['err_color']
    status = item_data['status']
    err_cause = item_data['err_cause']

    category = item_data['category']
    name = item_data['name']
    color = item_data['color']
    producer = item_data['producer']
    order_quant = item_data['order_quant']
    unit = item_data['unit']

    if err_cause == 'clear':
        # снимаем ошибку с позиции в заявке
        clear = 'UPDATE sim_orders SET status = %s, err_cause = %s, err_color = %s  WHERE num = %s AND item_id = %s'
        clear_val = (2, '', '', num, item_id)
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
    elif err_cause == 'change_color':
        # меняем цвет на складе
        change_color = 'UPDATE sim SET color = %s WHERE id = %s'
        change_value = (err_color, item_id)
        connect.ping(reconnect=True)
        cursor.execute(change_color, change_value)
        cursor.fetchall()
        connect.commit()

        # меняем err_cause у позиции в заявке для возврата в ячейку
        update_cause = 'UPDATE sim_orders SET err_cause = %s WHERE item_id = %s'
        cause_value = ('return', item_id)
        connect.ping(reconnect=True)
        cursor.execute(update_cause, cause_value)
        cursor.fetchall()
        connect.commit()

        # запрос в основной базе СиМ коплектующих по параметрам, сортируя по ФИФО
        new_item = 'SELECT * FROM sim WHERE category = %s AND name = %s AND color = %s AND producer = %s ORDER by fifo'
        new_item_value = (category, name, color, producer)
        connect.ping(reconnect=True)
        cursor.execute(new_item, new_item_value)
        itemsList = cursor.fetchall()
        connect.commit()

        for items in itemsList:
            baseQuantity = int(items['quant'])
            baseReserve = int(items['reserve'])
            checkQuantity = (baseQuantity - baseReserve) - int(order_quant)
            itemId = items['id']
            itemPlace = items['place']
            itemCell = items['cell']
            fifo = items['fifo']

            # если в ближайшей, согласно fifo, ячейке количество комлектующих больше, чем запрошено, то формируем резерв и прерываем цикл
            if checkQuantity >= 0:
                # обновляем (добавляем) резерв в основную базу СиМ
                updtReserve = 'UPDATE sim SET reserve = reserve + %s WHERE id = %s'
                updtReserveValue = (order_quant, itemId)
                connect.ping(reconnect=True)
                cursor.execute(updtReserve, updtReserveValue)
                connect.commit()

                # добавляем в заявку информацию о комплектующих к выдаче
                add_new_item = 'INSERT INTO sim_orders (num, actions, item_id, item_place, item_cell, date, category, name, color, producer, order_quant, unit) ' \
                               'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                add_value = (num, 'выдача', itemId, itemPlace, itemCell, fifo, category, name, color, producer, order_quant, unit)
                connect.ping(reconnect=True)
                cursor.execute(add_new_item, add_value)
                cursor.fetchall()
                connect.commit()
                break

            # если в ближайшей, согласно fifo, ячейке количество комлектующих меньше, чем запрошено, то формируем резерв и продолжаем цикл по ячейкам согласно ФИФО
            if checkQuantity < 0:
                # вычитаем резерв из количество комплектующих в ячейке, для корректного sql запроса и исключения reserve > quantity
                quantityMax = baseQuantity - baseReserve
                # ставим в резерв максимально доступное количество комплектующих в текущей ячейке
                if quantityMax == 0:
                    continue
                else:
                    # обновляем (добавляем) резерв в основную базу СиМ
                    updtReserve1 = 'UPDATE sim SET reserve = reserve + %s WHERE id = %s'
                    updtReserveValue1 = (quantityMax, itemId)
                    connect.ping(reconnect=True)
                    cursor.execute(updtReserve1, updtReserveValue1)
                    connect.commit()

                    # добавляем в заявку информацию о комплектующих к выдаче
                    add_new_item1 = 'INSERT INTO sim_orders (num, actions, item_id, item_place, item_cell, date, category, name, color, producer, order_quant, unit) ' \
                                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                    add_value1 = (num, 'выдача', itemId, itemPlace, itemCell, fifo, category, name, color, producer, quantityMax, unit)
                    connect.ping(reconnect=True)
                    cursor.execute(add_new_item1, add_value1)
                    cursor.fetchall()
                    connect.commit()
                    order_quant = checkQuantity * -1
                continue

    elif err_cause == 'return':
        del_item = 'DELETE FROM sim_orders WHERE item_id = %s'
        del_value = (item_id, )
        connect.ping(reconnect=True)
        cursor.execute(del_item, del_value)
        connect.commit()

    await sql_get_items_by_num(data, broadcast=True)
    await sql_uniq_sim_items(broadcast=True)
    await sql_sim_orders(broadcast=True)
    await sim_all_items(broadcast=True)
    return 'done'
