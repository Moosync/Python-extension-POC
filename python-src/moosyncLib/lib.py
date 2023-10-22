import sys
import socket
import json
import asyncio
import uuid

__dirname = sys.argv[1]
pipePath = sys.argv[2]

print(pipePath, flush=True)

# https://stackoverflow.com/questions/38235997/how-to-implement-recvmsg-with-asyncio
def _sock_recvmsg(loop, fut, registered, sock, bufsize, ancbufsize):
    self = loop
    fd = sock.fileno()
    if registered: 
        self.remove_reader(fd)
    if fut.cancelled(): 
        return
    try: 
        data = sock.recvmsg(bufsize, ancbufsize)
    except (BlockingIOError, InterruptedError): 
        self.add_reader(fd, self._sock_recvmsg, fut, True, sock, bufsize, ancbufsize)
    except Exception as exc: 
        fut.set_exception(exc)
    else: 
        fut.set_result(data)

def sock_recvmsg(loop, sock, bufsize, ancbufsize=0):
    self = loop
    if sock.gettimeout() != 0: 
        raise ValueError('the socket must be non-blocking')
    fut = asyncio.futures.Future(loop=self)
    self._sock_recvmsg(fut, False, sock, bufsize, ancbufsize)
    return fut

asyncio.unix_events._UnixSelectorEventLoop._sock_recvmsg = _sock_recvmsg
asyncio.unix_events._UnixSelectorEventLoop.sock_recvmsg = sock_recvmsg

loop = asyncio.get_event_loop()

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect(pipePath)
client.setblocking(0)

def generate_huge_data():
    data = {}
    for i in range(65535):
        data[i] = str(uuid.uuid4())
    return data

class ExtensionEventHandler():
    def __init__(self) -> None:
        self.callbacks = {}
        
    def generate_event_request(self, event_name, args):
        return {
            "type": "REQUEST",
            "data": {
                "id": str(uuid.uuid4()),
                "event": event_name,
                "args": args
            }
        }
        
    async def add_listener(self, event_name, callback):
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
        
        data = self.generate_event_request("registerListener", [event_name])
        await loop.sock_sendall(client, json.dumps(data).encode() + b'\x0c')
        
    def generate_event_reply(self, request, data):
        return {
            "type": "REPLY",
            "data": {
                "id": request["id"],
                "event": request["event"],
                "args": data
            }
        }
    
    async def emit_event(self, request):
        event_name = request["event"]
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                callback_res = callback(*request["args"])
                if callback_res is not None:
                    data = self.generate_event_reply(request, [callback_res])
                    await loop.sock_sendall(client, json.dumps(data).encode() + b'\x0c')
                
event_handler = ExtensionEventHandler()

async def read_pipe():
    half_read_data = b""
    while True:
        data_tmp = await loop.sock_recvmsg(client, 1024)
        
        split = data_tmp[0].split(b'\x0c')
        for i in range(len(split) - 1):
            split[i] = split[i] + b'\x0c'
        
        for s in split:
            if len(s) == 0:
                continue

            if not (s.endswith(b"\x0c")):
                half_read_data += s
                continue
            elif len(half_read_data) != 0:
                half_read_data += s
            else:
                half_read_data = s
                
            parsed = json.loads(half_read_data.strip())
                        
            half_read_data = b""
            if parsed["type"] == "EVENT":
                data = parsed["data"]
                if isinstance(data, str):
                    data = json.loads(data)
                    
                loop.create_task(event_handler.emit_event(data))

async def start():
    await read_pipe()        


