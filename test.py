import psutil
import os

def print_memory():
    process = psutil.Process(os.getpid())
    print(
        "MEMORY:",
        process.memory_info().rss / 1024 / 1024,
        "MB"
    )