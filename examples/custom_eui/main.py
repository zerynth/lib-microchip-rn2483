import streams
from microchip.rn2483 import rn2483

streams.serial()

print("init rn2483 module")
rn2483.init(SERIAL2, None, None, D4, join_lora=False)

# insert otaa credentials!!
appeui = ''
appkey = ''
deveui = ''

print("config rn2483 module")
rn2483.config(appeui, appkey, deveui)

print("join LoRaWAN network:")
i = 1
while True:
    try:
        print("attempt",i,"...")
        if rn2483.join():
            print("...succeded!")
            break
        else:
            print("...failed :(")
    except Exception as e:
        print(e)
    i += 1
    sleep(5000)

while True:
    try:
        print("sending ping, res:")
        print(rn2483.tx_uncnf("."))
    except rn2483Exception as e:
        print(e)
    sleep(5000) 
