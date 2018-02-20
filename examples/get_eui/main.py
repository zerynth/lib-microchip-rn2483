import streams
from microchip.rn2483 import rn2483

streams.serial()

# get deveui specifying serial connection used for device-to-module communication
# and module reset pin
print("DEVEUI: ", rn2483.get_hweui(SERIAL1, D16))
