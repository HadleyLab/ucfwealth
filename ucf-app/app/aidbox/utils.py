def get_error_payload(message, *, code):
    return {"error": code, "error_description": message}