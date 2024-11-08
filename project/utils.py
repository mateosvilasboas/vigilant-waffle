def format_error(status_code: int, error: str):
    data = {
        "status_code": status_code,
        "error": error
    }
    return data