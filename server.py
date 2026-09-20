"""
Virtual Gamepad - PC receiver (creates a virtual Xbox 360 controller).

Setup (Windows):
  1. Install ViGEmBus driver: https://github.com/nefarius/ViGEmBus/releases
  2. pip install vgamepad aiohttp
  3. python server.py
  4. Enter the printed IP in the phone app (same Wi-Fi / hotspot).
"""
import json, socket
from aiohttp import web, WSMsgType
import vgamepad as vg

PORT = 8080
B = vg.XUSB_BUTTON
MAP = {
    "a": B.XUSB_GAMEPAD_A, "b": B.XUSB_GAMEPAD_B,
    "x": B.XUSB_GAMEPAD_X, "y": B.XUSB_GAMEPAD_Y,
    "lb": B.XUSB_GAMEPAD_LEFT_SHOULDER, "rb": B.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "start": B.XUSB_GAMEPAD_START, "back": B.XUSB_GAMEPAD_BACK,
    "guide": B.XUSB_GAMEPAD_GUIDE,
    "l3": B.XUSB_GAMEPAD_LEFT_THUMB, "r3": B.XUSB_GAMEPAD_RIGHT_THUMB,
    "up": B.XUSB_GAMEPAD_DPAD_UP, "down": B.XUSB_GAMEPAD_DPAD_DOWN,
    "left": B.XUSB_GAMEPAD_DPAD_LEFT, "right": B.XUSB_GAMEPAD_DPAD_RIGHT,
}

pad = vg.VX360Gamepad()
held = set()

def clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, float(v)))

def apply(s):
    global held
    now = {k for k in s.get("b", []) if k in MAP}
    for k in now - held: pad.press_button(MAP[k])
    for k in held - now: pad.release_button(MAP[k])
    held = now
    pad.left_joystick_float(clamp(s.get("lx", 0)), clamp(-s.get("ly", 0)))
    pad.right_joystick_float(clamp(s.get("rx", 0)), clamp(-s.get("ry", 0)))
    pad.left_trigger_float(clamp(s.get("lt", 0), 0.0, 1.0))
    pad.right_trigger_float(clamp(s.get("rt", 0), 0.0, 1.0))
    pad.update()

def reset():
    global held
    held = set()
    pad.reset()
    pad.update()

async def ws_handler(req):
    ws = web.WebSocketResponse(heartbeat=10)
    await ws.prepare(req)
    print("Phone connected:", req.remote)
    try:
        async for m in ws:
            if m.type == WSMsgType.TEXT:
                try:
                    apply(json.loads(m.data))
                except Exception as e:
                    print("bad msg:", e)
    finally:
        reset()
        print("Phone disconnected")
    return ws

async def index(_):
    return web.Response(text="Virtual Gamepad server running")

def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

app = web.Application()
app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])

if __name__ == "__main__":
    print(f"\nEnter this in the phone app:  {lan_ip()}   port {PORT}\n")
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)
