import sqlite3


class Connection:
    def __init__(self, con: sqlite3.Connection):
        self.con = con
        self.cur = None

    def __enter__(self) -> sqlite3.Cursor:
        return self.cursor()

    def cursor(self) -> sqlite3.Cursor:
        self.cur = self.cur or self.con.cursor()
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.commit()
        self.con.close()
        pass


class Event:
    def __init__(self, name: str):
        self.name = name


class Events:
    RECONNECT = Event("reconnect")
    DISCONNECT = Event("disconnect")


class Database:
    def __init__(self, path: str, timeout: int = 30):
        self.path = path
        self.con = sqlite3.connect(path, timeout=timeout)

    def connection(self, timeout: int = 30) -> Connection:
        con = sqlite3.connect(self.path, timeout=timeout)
        return Connection(con)

    def setup(self):
        with self.connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS ping(
                pinged timestamp default current_timestamp,
                ping numeric)
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS speedtest(
                test_time timestamp default current_timestamp,
                bytes_up integer,
                bytes_down integer, 
                ping numeric)""")
            con.execute("""
                CREATE TABLE IF NOT EXISTS events(
                event_time timestamp default current_timestamp,
                event_type varchar)
            """)

    def log_ping(self, ping: float):
        with self.connection() as con:
            con.execute("INSERT INTO ping(ping) VALUES (?)", (ping,))

    def log_event(self, event: Event):
        with self.connection() as con:
            con.execute("INSERT INTO events(event_type) VALUES (?)", (event.name,))

    def log_speed_test(self, bytes_up: int, bytes_down: int, ping: float):
        with self.connection() as con:
            con.execute("INSERT INTO speedtest(bytes_up, bytes_down, ping) VALUES (?,?,?)",
                        (bytes_up, bytes_down, ping))
