# Usage

This tool monitors your internet connection and writes a log to a sqlite database.

# Setup
- Clone the repository.
- Run `pipenv install`

# Running
Use `python main.py`

# Configuring
You can configure some stuff via arguments
`python main.py arg1=val1 arg2=val2`

Possible arguments are:

| Name | description | default |
| ---- | ---- | ---- |
| url | The url which should get pinged | https://google.com |
| interval | The time between two checks in seconds | 5 |
| timeout | The time in seconds after a request is considered as failed when the website does not respond | 3 |
| speedcheck_threads | Amount of threads used by the speedcheck | cores / 2 |

