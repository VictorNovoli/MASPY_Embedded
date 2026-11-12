BCM = "BCM"
OUT = "OUT"
HIGH = 1
LOW = 0
_state = {}

def setmode(mode): pass
def setup(pin, mode): _state.setdefault(pin, LOW)
def output(pin, value):
    _state[pin] = value
    print(f"[FAKE GPIO] pino {pin} -> {'HIGH' if value else 'LOW'}")
def input(pin): return _state.get(pin, LOW)
def cleanup(): pass