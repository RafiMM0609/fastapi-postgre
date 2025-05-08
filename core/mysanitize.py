import re

def mask_five_chars(text: str) -> str:
    """
    Replace the last 5 characters of the string with '*****'.
    If the string has fewer than 5 characters, replace all with '*'.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    if len(text) <= 5:
        return '*' * len(text)
    return text[:-5] + '*****'

def sanitize_sql_identifier(identifier: str, max_length: int = 80) -> str:
    """
    Sanitize a string to be safely used as a SQL identifier (e.g., column alias).
    Only allows alphanumeric characters, underscores, and spaces.
    Truncates to max_length.
    Raises ValueError if the identifier contains invalid characters.
    """
    if not isinstance(identifier, str):
        raise ValueError("Identifier must be a string")
    # identifier = remove_leading_numbers(identifier)
    if len(identifier) > max_length:
        identifier = identifier[:max_length]
    # Only allow alphanumeric, underscore, and space
    # if not re.fullmatch(r"[A-Za-z0-9_ ]*", identifier):
    #     raise ValueError("Invalid characters in SQL identifier")
    identifier = re.sub(r"[^A-Za-z0-9_ ]", "0", identifier)
    return identifier

def sanitize_sql_identifier_ex_space(identifier: str, max_length: int = 30) -> str:
    """
    Sanitize a string to be safely used as a SQL identifier (e.g., column alias).
    Only allows alphanumeric characters, underscores, and spaces.
    Truncates to max_length.
    Raises ValueError if the identifier contains invalid characters.
    """
    if not isinstance(identifier, str):
        raise ValueError("Identifier must be a string")
    # identifier = remove_leading_numbers(identifier)
    if len(identifier) > max_length:
        identifier = identifier[:max_length]
    identifier = re.sub(r"[^A-Za-z0-9_ ]", "0", identifier)
    identifier = identifier.replace(" ", "")  # Remove all spaces
    return identifier

def remove_leading_numbers(text: str) -> str:
    """
    Remove numbers at the beginning of the string, but allow numbers elsewhere.
    Example: '123abc456' -> 'abc456'
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    return re.sub(r'^\d+', '', text)

def sanitize_alphanumeric(text: str, max_length: int = 80) -> str:
    """
    Sanitize a string to only allow alphanumeric characters.
    Non-alphanumeric characters are replaced with '0'.
    Truncates to max_length.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    sanitized = re.sub(r'[^A-Za-z0-9]', '0', text)
    return sanitized[:max_length]

def sanitize_alpha_space_number_end(text: str, max_length: int = 30) -> str | bool:
    """
    Sanitize a string to only allow letters (upper/lower), numbers, and spaces.
    If the string contains invalid characters, return False.
    Truncates to max_length.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    if not re.fullmatch(r"[A-Za-z0-9 ]+", text):
        return False
    return text[:max_length]

def sanitize_alphanumeric_dot(text: str, max_length: int = 80) -> str | bool:
    """
    Sanitize a string to only allow alphanumeric characters, hyphen, and dot.
    If the string contains any other character, return False.
    Truncates to max_length.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    if not re.fullmatch(r"[A-Za-z0-9.-]*", text):
        return False
    return text[:max_length]

#check leng data
def validator_data_length(text: str, min_length: int):
    try:
        if len(text) > min_length:
            return False
        return text
    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error validator length data")

def validator_data_min_length(text: str, min_length: int):
    try:
        if len(text) < min_length:
            return False
        return text
    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error validator length data")
