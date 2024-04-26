import time, os, uuid

def generate_data_path(suffix: str = "html", namespace: str = "default") -> str:
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"), exist_ok=True)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"{namespace}_{int(time.time())}_{uuid.uuid4().hex[:8]}.{suffix}")