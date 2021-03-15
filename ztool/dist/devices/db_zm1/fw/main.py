# fzb_slave_dhcp
# Created at 2019-08-30 09:02:45.435470
import streams
import mcu
import sfw
import eth 
from zerynth.fourzerobox import fourzerobox
from espressif.esp32net import esp32eth as eth_driver

sfw.watchdog(0, 2000000)
streams.serial()

fzbox = None

try:
    # Create FourZerobox Instance
    fzbox = fourzerobox.FourZeroBox(i2c_clk=100000)
    fzbox.clear_led()
except Exception as e:
    print(e)

print("ETH-KIT START")
    
    # ip_address = '192.168.71.17'
    # net_mask = '255.255.255.0'
    # net_gateway = '192.168.71.1'
    # primary_dns = '8.8.8.8'
    
    # eth_driver.set_link_info(ip_address, net_mask, net_gateway, primary_dns)
    # print("4ZB SET IP", rtc.get_utc(0))
    
for _ in range(5):
    try:
        sfw.kick()
    
        eth_driver.auto_init()
        print("ETH-KIT INITED")

        eth.link()
        print("ETH-KIT LINKED")
        fzbox.set_led('G')
        while True:
            sleep(5000)
    
    except Exception as e:
        print("ETH-KIT LINK", e)
        # print("4ZB RESET DONE D16")

fzbox.set_led('R')
while True:
    sleep(5000)