import concurrent.futures as futures
import multiprocessing
import sys

import checker
import logger
from database import Database

# settings
options = {}

for arg in sys.argv[1:]:
    args = arg.split("=")
    if len(args) != 2:
        continue
    options[args[0]] = args[1]

logger = logger.log()

url = options.get("url", "https://google.com")
timeout = float(options.get("timeout", 3))
threads = int(options.get("speedcheck_threads", multiprocessing.cpu_count() / 2))
interval = int(options.get("interval", 5))

logger.info(f"Url: {url} | Timeout: {timeout} | Speedtest Threads: {threads}")

db = Database("data.db")
db.setup()

if __name__ == '__main__':
    executor = futures.ThreadPoolExecutor(4)
    logger.info("Starting checker")
    while True:
        check = checker.Checker(db, url, timeout=timeout, threads=threads)
        result = executor.submit(check.start)
        e = result.exception(timeout=None)
        logger.info(e, exc_info=True)
        logger.info("Restarting")
