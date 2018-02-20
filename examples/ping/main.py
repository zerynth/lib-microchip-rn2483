import streams
from microchip.rn2483 import rn2483

streams.serial()

rst = D16
# insert otaa credentials!!
appeui = "" 
appkey = ""
print("joining...")

if not rn2483.init(SERIAL1, appeui, appkey, rst):
    print("denied :(")
    raise Exception

print("sending first message, res:")
print(rn2483.tx_uncnf('TTN'))

while True:
    print("ping, res:")
    print(rn2483.tx_uncnf("."))
    sleep(5000)