import sys
import socket
import json
import asyncio

__dirname = sys.argv[1]
pipePath = sys.argv[2]

print(pipePath, flush=True)

# https://stackoverflow.com/questions/38235997/how-to-implement-recvmsg-with-asyncio
def _sock_recvmsg(loop, fut, registered, sock, bufsize, ancbufsize):
    self = loop
    fd = sock.fileno()
    if registered: self.remove_reader(fd)
    if fut.cancelled(): return
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
    if sock.gettimeout() != 0: raise ValueError('the socket must be non-blocking')
    fut = asyncio.futures.Future(loop=self)
    self._sock_recvmsg(fut, False, sock, bufsize, ancbufsize)
    return fut


asyncio.unix_events._UnixSelectorEventLoop._sock_recvmsg = _sock_recvmsg
asyncio.unix_events._UnixSelectorEventLoop.sock_recvmsg = sock_recvmsg

class ExtensionEventHandler():
    def __init__(self) -> None:
        self.callbacks = {}
        
    def add_listener(self, event_name, callback):
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
    
    async def emit_event(self, event_name, args):
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                callback(*args)
                
event_handler = ExtensionEventHandler()

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect(pipePath)
client.setblocking(0)

loop = asyncio.get_event_loop()

async def read_pipe():
    half_read_data = b""
    while True:
        data_tmp = await loop.sock_recvmsg(client, 1024)
        if not (data_tmp[0].endswith(b"\x0c")):
            half_read_data += data_tmp[0]
            continue
        elif len(half_read_data) != 0:
            half_read_data += data_tmp[0]
        else:
            half_read_data = data_tmp[0]
            
        parsed = json.loads(half_read_data.strip())
        half_read_data = b""
        if parsed["type"] == "EVENT":
            data = parsed["data"]
            if isinstance(data, str):
                data = json.loads(data)
            
            loop.create_task(event_handler.emit_event(data["event"], data["args"]))

def start():
    loop.create_task(read_pipe())        
    loop.run_forever()


