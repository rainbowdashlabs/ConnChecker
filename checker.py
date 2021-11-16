import logging
import time
from datetime import datetime
from typing import Union

import requests
import speedtest

import database

logger = logging.getLogger("base")


class Result:
    def __init__(self, success: bool, exception: IOError = None, response: requests.Response = None):
        self.success = success
        self.exception = exception
        self.response = response


class Checker:
    fails = 0
    disconnected: Union[datetime, None] = None
    last_speed_test: Union[datetime, None] = None

    def __init__(self, db: database.Database, url: str, threads: int = 4, timeout: int = 3):
        self.threads = threads
        self.url = url
        self.db = db
        self.timeout = timeout

    def start(self):
        while True:
            self.check_url()
            time.sleep(5)

    def check_url(self):
        result = self.check(self.url)
        if result.success:
            self.handle_success(result)
        else:
            if result.exception:
                logger.info("encountered error")
                logger.info(result.exception)
            self.handle_fail(result)

    def check(self, target: str, success_codes=None) -> Result:
        if success_codes is None:
            success_codes = [200]
        try:
            response = requests.get(target, timeout=3)
        except requests.RequestException as ex:
            return Result(False, exception=ex)
        return Result(response.status_code in success_codes, response=response)

    def handle_fail(self, result: Result):
        global fails, disconnected
        if disconnected is None:
            self.db.log_event(database.Events.DISCONNECT)
        fails += 1
        disconnected = disconnected or datetime.utcnow()
        logger.info(f"Fails: {fails}. Last success {disconnected} or {datetime.utcnow() - disconnected}")

    def handle_success(self, result: Result):
        global disconnected, last_speed_test
        self.db.log_ping(round(result.response.elapsed.microseconds / 1000, 2))
        if disconnected is None:
            self.schedule_speed_check()
            return
        self.db.log_event(database.Events.RECONNECT)
        duration = datetime.utcnow() - disconnected
        logger.info("Connection is back")
        logger.info(f"Connection was down for {duration}")
        disconnected = None
        self.check_speed()

    def schedule_speed_check(self):
        global last_speed_test
        if not last_speed_test:
            self.check_speed()
            return
        diff = datetime.utcnow() - last_speed_test
        hours = diff.seconds / 60.0 / 60.0
        if hours >= 1:
            self.check_speed()

    def check_speed(self):
        global last_speed_test
        logger.info("starting speed test")
        last_speed_test = datetime.utcnow()
        test = speedtest.Speedtest()
        test.get_servers([])
        test.get_best_server()
        test.download(threads=self.threads)
        test.upload(threads=self.threads)
        self.db.log_speed_test(int(test.results.upload), int(test.results.download), round(test.results.ping, 4))
        logger.info(f"============== Speedtest results ==============")
        logger.info(f"Download {round(test.results.download / 1000 / 1000)} MB/s.")
        logger.info(f"Upload {round(test.results.upload / 1000 / 1000)} MB/s.")
        logger.info(f"Latency {test.results.ping} ms")
        logger.info(f"===============================================")
