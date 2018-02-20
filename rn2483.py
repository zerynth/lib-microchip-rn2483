#   Zerynth - libs - microchip-rn2483/rn2483.py
#
#   Zerynth driver for rn2483 lora module
#
#   
#
# @Author: andreabau
#
# @Date:   2017-05-17 09:08:48
# @Last Modified by:   andreabau
# @Last Modified time: 2017-07-14 08:43:22
"""
.. module:: rn2483

*************
RN2483 Module
*************

This Zerynth module currently supports over-the-air activation only to join a LoRaWAN network. Class A LoRaWAN devices, after correctly joining a network, are able to transmit a message up to 222 bytes and receive a response up to 230 bytes. during the subsequent downlink session. Sent messages can be confirmed (acknowledged) or unconfirmed; check your network policy to choose the proper transmit method (`datasheet <http://ww1.microchip.com/downloads/en/DeviceDoc/50002346A.pdf>`_)

.. note:: **rn2483Exception** is defined.

Usage example: ::

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


    """

import streams
import timers

new_exception(rn2483Exception, Exception)

_ser = None
_appeui = None
_appkey = None
_deveui  = None

ar = None

RESP_TIMEOUT = -1

# def _free_buff():
#     while _ser.available():
#         _ser.read(1)

def _send(cmd, discard_resp = False):
    _ser.write(cmd + '\r\n')
    if discard_resp:
        _read()

def _read(timeout = 2000):
    t = timers.timer()
    t.start()
    while not _ser.available():
        if t.get() > timeout:
            return RESP_TIMEOUT
    return _ser.readline().strip('\r\n')

def get_hweui(ser = None, rst = None):
    """
.. function:: get_hweui(ser = None, rst = None)

    Gets device EUI.
    If you need to get the EUI before joining a network, it is possible to specify:
        * *ser* serial port used for device-to-module communication (ex. SERIAL1)
        * *rst* module reset pin
    And call get_hweui() before init().

    """
    if ser is not None:
        init(ser, None, None, rst, short_startup = True)
    _send('sys get hweui')
    return _read()

def get_ch_status(channel):
    """
.. function:: get_ch_status(channel)

    Gets *channel* channel status: on if enabled, off otherwise.

    """
    _send('mac get ch status ' + str(channel))
    return _read()

def get_duty_cycle(channel, raw = False):
    """
.. function:: get_duty_cycle(channel, raw = False)

    Gets *channel* channel duty cycle: returned by default as a percentage.
    As a raw value passing *raw* as True.

    """
    _send('mac get ch dcycle ' + str(channel))
    res = int(_read())
    if raw:
        return res
    return 100.0/(res + 1)

# automatic reply state
def get_ar():
    """
.. function:: get_ar()

    Gets current automatic reply state ('on' or 'off').
    Automatic reply state is stored in *ar* global variable.

    """
    global ar
    _send('mac get ar')
    ar = _read()

def set_ar(state):
    """
.. function:: set_ar(state)

    Sets automatic reply to 'on' or 'off' state.
    Currently setting ar to 'on' does not have consequences on downlink session.

    """
    global ar
    _send('mac set ar ' + state, discard_resp = True)
    _send('mac get ar')
    ar = _read()
    if ar != state:
        raise rn2483Exception

def set_retransmissions(n):
    """
.. function:: set_retransmissions(n)

    Sets number of retransmissions to be used for an uplink confirmed packet,
    if no downlink acknoledgement is received from the server.

    """
    _send('mac set retx ' + str(n))
    if _read() != 'ok':
        raise rn2483Exception

def _get_startup_msg():
    while not _ser.available():
        pass
    while _ser.available():
        _read()

def init(ser, appeui, appkey, rst, short_startup = False):
    """
.. function:: init(ser, appeui, appkey, rst)

    Performs basic module configuration and try over-the-air activation.
    
        * *ser* is the serial port used for device-to-module communication (ex. SERIAL1)
        * *appeui*, *appkey* are needed for otaa
        * *rst* is the module reset pin

    """
    global _ser, _appeui, _appkey, _deveui

    if _ser is None:

        pinMode(rst, OUTPUT)
        digitalWrite(rst, HIGH)
        sleep(100)
        digitalWrite(rst, LOW)
        sleep(100)
        digitalWrite(rst, HIGH)

        _ser = streams.serial(ser, set_default = False, baud = 57600)
        _get_startup_msg()

        if short_startup:
            return

    _appeui  = appeui
    _appkey = appkey
    _deveui  = get_hweui()

    _send('mac reset 868', discard_resp = True)

    _send('mac set appeui ' + _appeui, discard_resp = True)

    _send('mac set appkey ' + _appkey, discard_resp = True)

    _send('mac set deveui ' + _deveui, discard_resp = True)

    _send('mac set pwridx 1', discard_resp = True)

    _send('mac set adr off', discard_resp = True)

    _send('mac set rx2 3 869525000', discard_resp = True)

    set_retransmissions(5)
    get_ar()
    set_ar('off')

    _send('mac save', discard_resp = True)

    joined = False

    for _ in range(3):
        _send('mac join otaa', discard_resp = True)
        res = _read(timeout = 30000)
        if res != RESP_TIMEOUT:
            if res.startswith('accepted'):
                joined = True
                break
            elif res.startswith('denied'):
                break
        sleep(1000)

    return joined

def _2str(s):
    r = str(s)
    if len(r) == 2:
        return r
    return '0'+r

def _base16encode(data):
    encoded = ''
    for xx in data:
        if type(data) == PSTRING:
            encoded += _2str(hex(ord(xx), prefix=''))
        elif type(data) == PBYTEARRAY:
            encoded += _2str(hex(xx, prefix =''))
    return encoded

def _base16tobytearray(data):
    b_len = len(data)//2
    b = bytearray(b_len)
    for i in range(b_len):
        b[i] = int(data[i*2:(i+1)*2], 16)
    return b

def tx_uncnf(data):
    """
.. function:: tx_uncnf(data)

    Transmits an unconfirmed message.
    *data* is a string or a bytearray.

    Returns True if no data is available during downlink session,
    a tuple (True, resp_data), where *resp_data* is a bytearray, otherwise.

    """
    return _tx('mac tx uncnf 1 ' + _base16encode(data))

def tx_cnf(data):
    """
.. function:: tx_cnf(data)

    Transmits a confirmed message.
    *data* is a string or a bytearray.

    Returns True if no data is available during downlink session,
    a tuple (True, resp_data), where *resp_data* is a bytearray, otherwise.

    """
    return _tx('mac tx cnf 1 ' + _base16encode(data))

def _tx(cmd):

    for _ in range(10):
        _send(cmd)
        res = _read()
        if res == 'ok':
            res = _read(timeout = 30000)

            if res == 'mac_tx_ok' or res == 'radio_tx_ok':
                return True
            if res.startswith('mac_rx'):
                # if ar == 'on':
                #     res_2 = _read(timeout = 30000)
                #     if res_2 != RESP_TIMEOUT:
                #         if res_2.startswith('mac_rx'):
                #             return (True, res.split(' ')[-1], res_2.split(' ')[-1])
                #     return (True, res.split(' ')[-1], None)
                return (True, _base16tobytearray(res.split(' ')[-1]))

            raise rn2483Exception

        if not res == 'busy':
            print(res)
            raise rn2483Exception
        sleep(1000)


def get_snr():
    """
.. function:: get_snr():
    
    Returns an integer between -128 and 127 representing the signal to noise ratio (SNR) for the last received packet.

    """
    t = _pause()
    if t == '0':
        raise rn2483Exception

    _send('radio get snr')
    snr = _read()  # signed decimal number from -128 to 127
    
    res = _resume()
    if not res == 'ok':
        print(res)
        raise rn2483Exception
    
    return int(snr)

def get_pwr():
    """
.. function:: get_pwr():
    
    Returns an integer between -3 and 15 representing the current power level settings used in operation.

    """
    t = _pause()
    if t == '0':
        raise rn2483Exception
    
    _send('radio get pwr')
    pwr = _read()  # signed decimal number from -3 to 15
    
    res = _resume()
    if not res == 'ok':
        print(res)
        raise rn2483Exception
    
    return int(pwr)

# pause LoRaWAN stack functionality to allow radio configuration
def _pause():
    _send('mac pause')
    res = _read()  # available time in ms
    return res

# resume LoRaWan stack functionality in order to continue normal functionality after being paused
def _resume():
    _send('mac resume')
    res = _read()   # ok
    return res
