import logging.config

import yaml

with open("logging.yml", "r") as f:
    logging.config.dictConfig(yaml.safe_load(f))


def log(child: str = ""):
    if str:
        return logging.getLogger(f"base.{child}")
    return logging.getLogger("base")
