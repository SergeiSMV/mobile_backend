import ast
import json
import websockets
from connection import cursor, connect
from initialization import router
from datetime import datetime
from datetime import date

from sockets.sim.items.sim_items import sim_all_items
from sockets.sim.orders.sim_orders import sql_sim_orders
from sockets.sim.items.sim_uniq_items import sql_uniq_sim_items


@router.route('/sim_add_order')
async def sim_add_order(ws, path):
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


async def sql_sim_add_order(data):
    order_data = data['data']
    num = datetime.now().strftime('%Y%m%d%H%M%S')
    date_order = date.today().strftime('%Y-%m-%d')
    time_order = datetime.now().strftime('%H:%M')
    for i in order_data:
        category = i['category']
        name = i['name']
        color = i['color']
        producer = i['producer']
        customer = i['customer']
        order_quant = i['order_quant']
        unit = i['unit']
        comment = i['comment']

        # добавляем данные в базу заявок
        sql1 = 'INSERT INTO sim_orders (num, date, time, customer, category, name, color, producer, order_quant, comment, unit) ' \
               'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        val1 = (num, date_order, time_order, customer, category, name, color, producer, order_quant, comment, unit)
        connect.ping(reconnect=True)
        cursor.execute(sql1, val1)
        cursor.fetchall()
        connect.commit()

        # запрос в основной базе СиМ коплектующих по параметрам, сортируя по ФИФО
        sql2 = 'SELECT * FROM sim WHERE category = %s AND name = %s AND color = %s AND producer = %s ORDER by fifo'
        val2 = (category, name, color, producer)
        connect.ping(reconnect=True)
        cursor.execute(sql2, val2)
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
                sql3 = 'INSERT INTO sim_orders (num, actions, item_id, item_place, item_cell, date, category, name, color, producer, order_quant, unit) ' \
                       'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                val3 = (num, 'выдача', itemId, itemPlace, itemCell, fifo, category, name, color, producer, order_quant, unit)
                connect.ping(reconnect=True)
                cursor.execute(sql3, val3)
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
                    updtReserve = 'UPDATE sim SET reserve = reserve + %s WHERE id = %s'
                    updtReserveValue = (quantityMax, itemId)
                    connect.ping(reconnect=True)
                    cursor.execute(updtReserve, updtReserveValue)
                    connect.commit()

                    # добавляем в заявку информацию о комплектующих к выдаче
                    sql4 = 'INSERT INTO sim_orders (num, actions, item_id, item_place, item_cell, date, category, name, color, producer, order_quant, unit) ' \
                           'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
                    val4 = (num, 'выдача', itemId, itemPlace, itemCell, fifo, category, name, color, producer, quantityMax, unit)
                    connect.ping(reconnect=True)
                    cursor.execute(sql4, val4)
                    cursor.fetchall()
                    connect.commit()
                    order_quant = checkQuantity * -1
                continue

    await sql_uniq_sim_items(broadcast=True)
    await sql_sim_orders(broadcast=True)
    await sim_all_items(broadcast=True)
    return 'done'
