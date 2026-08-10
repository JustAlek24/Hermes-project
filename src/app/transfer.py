from hashlib import sha256

def chunk_file(filepath, chunk_size=1048576):
    chunks = list()
    with open(filepath, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks, calculate_sha256(filepath)

def assemble_file(chunks, output_path, expected_sha256):
    with open(output_path, 'wb') as file:
        for chunk in chunks:
            file.write(chunk)
    return calculate_sha256(output_path) == expected_sha256

def calculate_sha256(filepath, chunk_size=1048576):
    h = sha256()
    with open(filepath, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()