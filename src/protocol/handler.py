import json

KNOWN_TYPES = {"HEARTBEAT", "META", "FILE_CHUNK", "ACK", "REJECT", "ERROR", "SYNC_REQUEST", "SYNC_RESPONSE"}

def parse_message(raw_string):

    check = True

    try: message = json.loads(raw_string)

    except (json.JSONDecodeError, TypeError):
        return {"error" : "INVALID_JSON"}
    
    if not isinstance(message.get("type"), str):
        check = False

    if not isinstance(message.get("peer_id"), str) or not message.get("peer_id"):
        check = False

    if not isinstance(message.get("timestamp"), (int, float)):
        check = False

    if check == False:
        return {"error" : "MISSING_FIELDS"}

    if message["type"] not in KNOWN_TYPES:
        check = False

    if check == False:
        return {"error" : "UNKNOWN_TYPE"}

    return message