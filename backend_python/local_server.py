import socket
from fastapi import FastAPI, Request
from handler import lambda_handler
from zeroconf import ServiceInfo, Zeroconf

# Extragere IP Local
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('10.255.255.255', 1))
    LOCAL_IP = s.getsockname()[0]
except Exception:
    LOCAL_IP = '127.0.0.1'
finally:
    s.close()

app = FastAPI()
zeroconf_instance = None

@app.on_event("startup")
def startup_event():
    global zeroconf_instance
    try:
        zeroconf_instance = Zeroconf()
        info = ServiceInfo(
            "_http._tcp.local.",
            "AI_Dispatcher._http._tcp.local.",
            addresses=[socket.inet_aton(LOCAL_IP)],
            port=8000,
            properties={"path": "/"},
            server="ai-dispatcher.local.",
        )
        zeroconf_instance.register_service(info)
        print(f"\n📡 [MDNS] Broadcast activat!")
        print(f"👉 Device-urile locale te pot gasi acum la: http://ai-dispatcher.local:8000")
        print(f"👉 (IP Fizic: {LOCAL_IP}:8000)\n")
    except Exception as e:
        print(f"Eroare la inregistrarea mDNS: {e}")

@app.on_event("shutdown")
def shutdown_event():
    global zeroconf_instance
    if zeroconf_instance:
        zeroconf_instance.close()

@app.post("/{path:path}")
async def handle_all(path: str, request: Request):
    body = await request.body()
    event = {
        "rawPath": "/" + path,
        "requestContext": {"http": {"method": "POST"}},
        "body": body.decode("utf-8")
    }
    context = {}
    return lambda_handler(event, context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
