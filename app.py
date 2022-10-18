import asyncio
import websockets
import logging
from users import *

from initialization import router

start_server = websockets.serve(router, "185.46.10.55", 1512)

if __name__ == '__main__':
    logging.basicConfig(filename='app_errors.log', level=logging.ERROR)
    logging.basicConfig(filename='app_critical.log', level=logging.CRITICAL)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
