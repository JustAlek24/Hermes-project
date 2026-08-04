
ERRORS = {
    "FILE_NOT_FOUND",
    "TRANSFER_FAILED",
    "TIMEOUT",
    "INVALID_JSON",
    "INVALID_PEER",
}


def validate_message(parsed):

    data = parsed.get("data")

    if not isinstance(data, dict):
        return False, "data is not a dict"

    if parsed.get("type") == "META":
        if not isinstance(data.get("filename"), str):
            return False, "filename is not string"

        if not isinstance(data.get("file_size"), int):
            return False, "file_size is not int"

        if data.get("file_size") <= 0:
            return False, "file_size is incorrect"

        if not isinstance(data.get("chunks_count"), int):
            return False, "chunks_count is not int"

        if data.get("chunks_count") <= 0:
            return False, "chunks_count is incorrect"

        if not isinstance(data.get("sha256"), str):
            return False, "sha256 is not string"

        if len(data.get("sha256")) != 64:
            return False, "sha256 is incorrect"

    elif parsed.get("type") == "FILE_CHUNK":
        if not isinstance(data.get("chunk_id"), int):
            return False, "chunk_id is not int"

        if data.get("chunk_id") < 0:
            return False, "chunk_id is incorrect"

        if not isinstance(data.get("content"), str):
            return False, "content is not string"

    elif parsed.get("type") == "ACK":
        if not isinstance(data.get("ack_for"), str):
            return False, "ack_for is not string"

        if data.get("status") not in {"ok", "error"}:
            return False, "status is undefined"

        chunk_id = data.get("chunk_id")
        if chunk_id is not None and not isinstance(chunk_id, int):
            return False, "chunk_id is incorrect"

    elif parsed.get("type") == "REJECT":
        if not isinstance(data.get("reason"), str):
            return False, "reason is not string"

    elif parsed.get("type") == "ERROR":
        if data.get("code") not in ERRORS:
            return False, "code is undefined"

        if not isinstance(data.get("message"), str):
            return False, "message is not string"

    elif parsed.get("type") == "SYNC_REQUEST":
        if not isinstance(data.get("last_sync"), int):
            return False, "last_sync is not int"

    elif parsed.get("type") == "SYNC_RESPONSE":
        if not isinstance(data.get("peers"), list):
            return False, "peers is not list"

    return True, None
