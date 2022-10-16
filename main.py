import websockets
import asyncio
import datetime
from pyngrok import ngrok
from math import floor, pi, sin, cos, atan2


def calculate_day_difference():
    """
        This function calculates the difference between current date
        and 2000/01/01 to find the amount of days passed
    """
    today = datetime.datetime.today()
    y = today.year
    d = today.day
    m = today.month
    days_diff = 367 * y - (
            ((7 * (y + ((m + 9) / 12))) / 4) + ((275 * m) / 9) + d - 730530)
    return days_diff


def minimize_degrees(degree):
    return degree - floor(degree / 360) * 360


def calculate_orbital_elements(days_diff) -> dict:
    """
        The orbital elements of the Moon are:
        1. Longitude Ascension Node (degrees)
        2. Inclination (degrees)
        3. Argument of Perigee (degrees)
        4. Mean Distance
        5. Eccentricity
        6. Mean anomaly (degrees)
    """
    LongAscensionNode = 125.1228 - 0.0529538083 * days_diff
    Inclination = 5.1454
    PerigeeArg = 318.0634 + 0.1643573223 * days_diff
    MeanDist = 60.2666
    Eccentricity = 0.054900
    MeanAnomaly = 115.3654 + 13.0649929509 * days_diff
    return {
        "LANode": minimize_degrees(LongAscensionNode),
        "Incl": minimize_degrees(Inclination),
        "PerArg": minimize_degrees(PerigeeArg),
        "MeanDist": MeanDist,
        "Ecc": Eccentricity,
        "MeanAnomaly": minimize_degrees(MeanAnomaly)
    }


def calculate_eccentric_anomaly(meanAn, ecc):
    E0 = meanAn + ((180 / pi) * ecc * sin(meanAn) * (1 + (ecc * cos(meanAn))))
    E1 = E0 - ((E0 - (((180 / pi) * ecc * sin(E0)) - meanAn)) / (
            1 - (ecc * cos(E0))))
    while E1 - E0 <= 0.005:
        E0 = E1
        E1 = (E0 - (E0 - (((180 / pi) * ecc * sin(E0)) - meanAn))) / (
                1 - (ecc * cos(E0)))
    return E1


def compute_rectangular_coordinates(eccAnomaly, ecc, meanDist):
    """
        This function computes the rectangular coordinates only in the
        plane of the lunar orbit!!
    """
    x = meanDist * (cos(eccAnomaly) - ecc)
    y = meanDist * ((1 - (ecc * ecc)) ** 0.5) * sin(eccAnomaly)
    return x, y


def calculate_distance_trunAnomaly(x, y):
    """
        This function calculates distance and true anomaly by converting
        x,y coordinates.
    """
    dist = ((x * x) + (y * y)) ** 0.5
    trueAn = atan2(y, x)
    return dist, trueAn


def calculate_ecliptic_coordinates(dist, trueAn, perArg, LANode, incl):
    xeclip = dist * ((cos(LANode) * cos(trueAn + perArg)) - (sin(LANode) * sin(
        trueAn + perArg) * cos(incl)))
    yeclip = dist * ((sin(LANode) * cos(trueAn + perArg)) + (cos(LANode) * sin(
        trueAn + perArg) * cos(incl)))
    zeclip = dist * sin(trueAn + perArg) * sin(incl)
    return xeclip, yeclip, zeclip


def convert_to_raDec(xeclip, yeclip, zeclip):
    ra = atan2(yeclip, xeclip)
    dec = atan2(zeclip, ((xeclip * xeclip) + (yeclip * yeclip)) ** 0.5)
    return ra, dec


async def handler(websocket, path):
    print("Client connected")
    try:
        while True:
            days_diff = calculate_day_difference()
            orb_elems = calculate_orbital_elements(days_diff)
            ecc_anomaly = calculate_eccentric_anomaly(
                orb_elems["MeanAnomaly"],
                orb_elems["Ecc"]
            )
            rect_coord = compute_rectangular_coordinates(
                ecc_anomaly,
                orb_elems["Ecc"],
                orb_elems["MeanDist"]
            )
            dist_trueAn = calculate_distance_trunAnomaly(
                rect_coord[0],
                rect_coord[1]
            )
            eclip_coord = calculate_ecliptic_coordinates(
                dist_trueAn[0],
                dist_trueAn[1],
                orb_elems["PerArg"],
                orb_elems["LANode"],
                orb_elems["Incl"]
            )
            raDec = convert_to_raDec(
                eclip_coord[0],
                eclip_coord[1],
                eclip_coord[2]
            )
            message = str(raDec[0]) + ", " + str(raDec[1])
            await websocket.send(message)
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
