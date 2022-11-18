import ast
import json
import os

import websockets
from initialization import router
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@router.route('/send_barcode')
async def send_barcode(ws, path):
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
                print(f'send_barcode websockets.ConnectionClosedOK: отключился клиент {ws}')
                break
    except websockets.ConnectionClosedError:
        print(f'send_barcode websockets.ConnectionClosedError: отключился клиент {ws}')


async def sql_send_barcode(data):
    item_data = data['data']
    bcode = item_data['bcode']
    category = item_data['category']
    name = item_data['name']
    color = item_data['color']
    producer = item_data['producer']
    fifo = item_data['fifo']
    text = f'{category} {name} {color}\n({producer}) {fifo}'

    with open('/usr/local/bin/images/bcode.jpeg', 'wb') as fl:
        Code128(bcode, writer=ImageWriter()).write(fl)

    base_image = Image.open('/usr/local/bin/images/bcode.jpeg')
    base_size = base_image.size
    new_size = (base_size[0], base_size[1] + 30)
    image = Image.new('RGB', new_size, (255, 255, 255))
    image.paste(base_image, (0, 0))

    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", 10, encoding='UTF-8')
    draw.text((10, 260), text, font=font, fill=(0, 0, 0))
    image.save('/usr/local/bin/images/bcode.jpeg')

    sender = 's9051133401@yandex.ru'
    password = '905malina1133401'
    server = smtplib.SMTP('smtp.yandex.ru', 587)
    server.starttls()

    with open('/usr/local/bin/images/bcode.jpeg', 'rb') as f:
        img_data = f.read()
    msg = MIMEMultipart()
    msg['Subject'] = f'{category} {name} {color} ({fifo})'
    msg['From'] = sender
    text = MIMEText(
        f'штрих-код для {category} {name} {color}.\nПоставщик: {producer}\nДата поступления: {fifo}')
    msg.attach(text)
    image = MIMEImage(img_data)
    msg.attach(image)

    try:
        server.login(sender, password)
        server.sendmail(sender, 's9051133401@yandex.ru', msg.as_string())
        server.quit()
        os.remove('/usr/local/bin/images/bcode.jpeg')
    except Exception as _ex:
        pass

    return 'done'

