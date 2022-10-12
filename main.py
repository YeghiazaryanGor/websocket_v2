import websockets
import asyncio
import datetime
from pyngrok import ngrok


def day_number():
    """
        This function calculates the difference between current date
        and 2000/01/01 to find the amount of days passed
    """
    today = datetime.datetime.today()
    y = today.year
    d = today.day
    m = today.month
    days_diff = 367 * y - (7 * (y + ((m + 9) / 12))) / 4 + (275 * m) / 9 + d - 730530
    return days_diff


async def handler(websocket, path):
    print("Client connected")
    try:
        while True:
            await websocket.send('b')
            await asyncio.sleep(10)
    except websockets.exceptions.ConnectionClosed:
        print("Client just disconnected")


if __name__ == "__main__":
    http_tunnel = ngrok.connect(8080, bind_tls=True)
    print("testing url is: ", http_tunnel.public_url)
    PORT = 8080
    start_server = websockets.serve(handler, "localhost", PORT)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
