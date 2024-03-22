"""This is a file for using proxy from KuaiDaili.

And dealing requests.get() invaild in windows sometimes.
"""

import json
import os
import random
import ssl
import time
from pathlib import Path
from typing import Any

import requests
import urllib3
from requests.adapters import HTTPAdapter

from spider import logger


class CustomHttpAdapter(HTTPAdapter):
    # Type annotation is not accurate
    """Transport adapter" that allows us to use custom ssl_context."""

    # ref: https://stackoverflow.com/a/73519818/16493978

    def __init__(self, ssl_context: Any = None, **kwargs: Any) -> None:  # noqa: ANN401
        """Init the ssl_context param."""
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,  # noqa: FBT001, FBT002
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Create a urllib3.PoolManager for each proxy."""
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
            **kwargs,
        )


def get_legacy_session() -> requests.Session:
    """Get legacy session."""
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    return session


class Proxy:
    """Class for get Kdl proxy."""

    def __init__(self, *, local: bool) -> None:
        """Init Proxy."""
        self.local = local

        if not self.local:
            self.secret_path = Path(__file__).resolve().parent.parent / ".secret"
            if not self.secret_path.exists():
                Path.touch(self.secret_path)

            # if not set, raise KeyError
            self.secret_id: str = os.environ["KUAI_SECRET_ID"]
            self.secret_key: str = os.environ["KUAI_SECRET_KEY"]

            self.proxies: list[str] = []
            self.proxy = ""

    def _get_secret_token(self) -> tuple[str, str, str]:
        r = requests.post(
            url="https://auth.kdlapi.com/api/get_secret_token",
            data={"secret_id": self.secret_id, "secret_key": self.secret_key},
            timeout=10,
        )
        if r.status_code != 200:  # noqa: PLR2004
            raise KdlException(r.status_code, r.content.decode("utf8"))
        res = json.loads(r.content.decode("utf8"))
        code, msg = res["code"], res["msg"]
        if code != 0:
            raise KdlException(code, msg)
        secret_token = res["data"]["secret_token"]
        expire = str(res["data"]["expire"])
        _time = f"{time.time():.6f}"
        return secret_token, expire, _time

    def _write_secret_token(
        self, secret_token: str, expire: str, _time: str, secret_id: str
    ) -> None:
        try:
            with Path.open(self.secret_path, "w", encoding="utf-8") as f:
                f.write(secret_token + "|" + expire + "|" + _time + "|" + secret_id)
        except OSError as e:
            logger.error(f"An error occurred while writing to the file: {e}")

    def _read_secret_token(self) -> str:
        with Path.open(self.secret_path, encoding="utf-8") as f:
            token_info = f.read()
            if token_info == "":
                secret_token, expire, _time = self._get_secret_token()
                self._write_secret_token(secret_token, expire, _time, self.secret_id)
                return secret_token
        secret_token, expire, _time, last_secret_id = token_info.split("|")
        if (
            float(_time) + float(expire) - 3 * 60 < time.time()
            or last_secret_id != self.secret_id
        ):  # 还有3分钟过期或SecretId变化时更新
            secret_token, expire, _time = self._get_secret_token()
            self._write_secret_token(secret_token, expire, _time, self.secret_id)
        return secret_token

    def _get_proxies(self) -> None:
        """Get a list of proxy ip."""
        api = "https://dps.kdlapi.com/api/getdps"
        response = requests.get(
            api,
            params={
                "secret_id": self.secret_id,
                "signature": self._read_secret_token(),
                "num": str(1),
            },
            timeout=10,
        )
        if response.status_code != 200:  # noqa: PLR2004
            raise KdlException(response.status_code, response.content.decode("utf8"))
        self.proxies = [f"http://{ip}" for ip in response.text.split("\n")]
        logger.info(f"Get proxies: {self.proxies}")

    def get_cur_ip(self) -> None:
        """Get current ip."""
        url = "https://dev.kdlapi.com/api/getmyip"
        response = requests.get(
            url,
            params={
                "secret_id": self.secret_id,
                "signature": self._read_secret_token(),
            },
            timeout=10,
        )
        logger.info(f"Current ip: {response.text}")

    def get(self) -> str:
        """Get a proxy ip."""
        if self.local and PLAT_CODE == 1:
            proxy = random.choice(PROXY_GROUP)
            logger.info(f"Using proxy {proxy}")
            return proxy

        if self.local and PLAT_CODE == 0:
            logger.info("Not using proxy")
            return ""

        if not self.proxies:
            self._get_proxies()
        self.proxy = self.proxies.pop()
        logger.info(f"Using proxy {self.proxy}")
        return self.proxy


class KdlException(Exception):  # noqa: N818
    """KdlException."""

    def __init__(self, code: int | None = None, message: str | None = None) -> None:
        """Init KdlException."""
        self.code = code
        self.message = message
        self._hint_message = f"[KdlException] code: {self.code} message: {self.message}"

    @property
    def hint_message(self) -> str:
        """Get hint message."""
        return self._hint_message

    @hint_message.setter
    def hint_message(self, value: str) -> None:
        """Set hint message."""
        self._hint_message = value

    def __str__(self) -> str:
        """Return hint message."""
        return self.hint_message


# if in wsl/windows - code is 0, should use `get_legacy_session()`
# else use `requests.get()` - code is 1
# Why need `requests.get()` is not clear, and sometimes it not needed.
PLAT_CODE = 0
PROXY_GROUP = [  # proxy port of local
    "http://localhost:30001",
    "http://localhost:30002",
    "http://localhost:30003",
    "http://localhost:30004",
    "http://localhost:30005",
    "http://localhost:30006",
    "http://localhost:30007",
    "http://localhost:30008",
    "http://localhost:30009",
]

if __name__ == "__main__":
    p = Proxy(local=False)
    p.get_cur_ip()
