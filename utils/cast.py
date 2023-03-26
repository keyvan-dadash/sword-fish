
def cast_to_type(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

def can_be_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False