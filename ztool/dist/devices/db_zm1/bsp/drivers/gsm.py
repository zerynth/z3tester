from quectel.bg96 import bg96 as drv
from wireless import gsm as gsmdrv

def init():
    try:
        drv.init(SERIAL2, D44, D33, D42, D43, D41) # slot 2 (ser, int, cs, rst, pwm, an)
    except Exception as e:
        print(e)
        drv.init(SERIAL2, D39, D33, D42, D16, D34) # slot 1 (ser, int, cs, rst, pwm, an)
    drv.startup()
    return drv

def interface():
    return gsmdrv