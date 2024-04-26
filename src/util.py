import time, os, uuid

def generate_data_path(suffix: str = "html", namespace: str = "default") -> str:
    os.makedirs("data", exist_ok=True)
    # 同时返回相对和绝对路径
    filename = f"{namespace}_{int(time.time())}_{uuid.uuid4().hex[:8]}.{suffix}"
    return os.path.join("data", filename), os.path.abspath(os.path.join("data", filename))