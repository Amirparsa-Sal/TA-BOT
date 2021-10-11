def get_file_name(file_address: str) -> str:
    last_slash = file_address.rfind('/')
    return file_address[last_slash+1:]