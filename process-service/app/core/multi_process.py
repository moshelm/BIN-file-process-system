import mmap
from concurrent.futures import ProcessPoolExecutor


def multi_process_file(fileno, file_name: str):
    mm = mmap.mmap(fileno, 0, access=mmap.ACCESS_READ)
