import platform

def is_windows() -> bool:
    try:
        return platform.system().lower().startswith('win')
    except Exception:
        return False
