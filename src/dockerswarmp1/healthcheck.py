import sys
import urllib.request

_STATUS_CODE = 200


def run() -> None:
  with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
    if response.status == _STATUS_CODE:
      sys.exit(0)
    else:
      sys.exit(1)
