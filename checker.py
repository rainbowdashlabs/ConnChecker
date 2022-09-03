import asyncio
from datetime import datetime
from typing import Union

import speedtest
from aiohttp import ClientSession, ClientTimeout, ClientResponse

import database
from logger import log

logger = log("checker")


class Result:
    def __init__(self, success: bool, exception: Exception = None, response: ClientResponse = None,
                 duration:float= None):
        self.success = success
        self.exception = exception
        self.response = response
        self.duration = duration


async def check(target: str, success_codes=None) -> Result:
    if success_codes is None:
        success_codes = [200]
    async with ClientSession(timeout=ClientTimeout(total=3)) as session:
        try:
            start = asyncio.get_event_loop().time()
            async with session.get(target) as req:
                return Result(req.status in success_codes, response=req, duration=asyncio.get_event_loop().time() - start)
        except Exception as e:
            return Result(False, exception=e)


class Checker:
    fails = 0
    disconnected: Union[datetime, None] = None
    last_speed_test: Union[datetime, None] = None

    def get_url(self) -> str:
        self.curr_url += 1
        return self.urls[self.curr_url % len(self.urls)]

    def __init__(self, db: database.Database, urls: list[str], threads: int = 4, timeout: float = 3, interval: int = 5):
        self.threads = threads
        self.urls = urls
        self.db = db
        self.timeout = timeout
        self.interval = interval
        self.curr_url = 0

    def start(self):
        asyncio.run(self.loop())

    async def loop(self):
        while True:
            try:
                await self.check_url()
            except Exception as e:
                print(e)
            await asyncio.sleep(self.interval)

    async def check_url(self):
        result = await check(self.get_url())
        if result.success:
            self.handle_success(result)
        else:
            if result.exception:
                logger.info("encountered error")
                logger.info(result.exception)
            self.handle_fail(result)

    def handle_fail(self, result: Result):
        if self.disconnected is None:
            self.db.log_event(database.Events.DISCONNECT)
        self.fails += 1
        self.disconnected = self.disconnected or datetime.utcnow()
        logger.info(f"Fails: {self.fails}. Last success {self.disconnected} or {datetime.utcnow() - self.disconnected}")

    def handle_success(self, result: Result):
        self.db.log_ping(round(result.duration, 2))
        if self.disconnected is None:
            self.schedule_speed_check()
            return
        self.db.log_event(database.Events.RECONNECT)
        logger.info("Connection is back")
        logger.info(f"Connection was down for {datetime.utcnow() - self.disconnected}")
        self.disconnected = None
        self.check_speed()

    def schedule_speed_check(self):
        if not self.last_speed_test:
            self.check_speed()
            return
        diff = datetime.utcnow() - self.last_speed_test
        hours = diff.seconds / 60.0 / 60.0
        if hours >= 1:
            self.check_speed()

    def check_speed(self):
        logger.info("starting speed test")
        self.last_speed_test = datetime.utcnow()
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
