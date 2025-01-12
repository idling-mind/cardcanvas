def compare_dicts(obj1, obj2):
    """Compares two objects recursively, handling dicts and lists.
    returns True if the objects are equal, False otherwise.
    """
    if obj1 == obj2:
        return True
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        if obj1.keys() != obj2.keys():
            return False
        for key in obj1:
            if not compare_dicts(obj1[key], obj2[key]):
                return False
        return True
    if isinstance(obj1, list) and isinstance(obj2, list):
        if len(obj1) != len(obj2):
            return False
        for item1, item2 in zip(obj1, obj2):
            if not compare_dicts(item1, item2):
                return False
        return True
    return False
