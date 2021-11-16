import concurrent.futures as futures
import logging.config

import yaml

import checker
from database import Database

with open("logging.yml", "r") as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger("base")

# settings
url = "https://google.com"
timeout = 3
threads = 4

db = Database("data.db")
db.setup()

if __name__ == '__main__':
    executor = futures.Executor()
    while True:
        check = checker.Checker(db, url, timeout=timeout, threads=threads)
        result = executor.submit(check.start)
        e = result.exception(timeout=None)
        logger.info(e, exc_info=True)
        logger.info("Restarting")
