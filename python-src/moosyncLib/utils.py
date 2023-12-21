from dataclasses import asdict, is_dataclass
import json
import socket
import uuid

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


def generate_event_request(event_name, args):
    return {
        "type": "REQUEST",
        "data": {"id": str(uuid.uuid4()), "event": event_name, "args": args},
    }


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)
