from __future__ import annotations

import asyncio
from typing import Optional
from typing import TypedDict
from typing import Union

import mirror.config
import mirror.services
import mirror.sessions
from mirror.models.sessions import OsuWebSession

LOGIN_BODY_BASE = {
    # assigned at login time,
    # picked from a list of accounts
    # "username": "",
    # "password": "",
    "autologin": "on",
    "redirect": "index.php",
    "sid": "",
    "login": "Login",
}

LOGIN_HEADERS = {
    # "Host": old.ppy.sh
    # "Connection": keep-alive
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    # TODO: send this?
    # "sec-ch-ua": ' Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "Upgrade-Insecure-Requests": "1",
    "Origin": "https://old.ppy.sh",
    # "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://old.ppy.sh/forum/ucp.php?mode=login",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Referrer": "https://old.ppy.sh/",
}


class OsuAccount(TypedDict):
    username: str
    password: str


# TODO: rewrite with osu!api v2 & lazer
# https://osu.ppy.sh/docs/index.html#authentication
# https://osu.ppy.sh/home/account/edit#new-oauth-application


async def osu_login(osu_account: OsuAccount) -> Optional[OsuWebSession]:
    # TODO: check if this sends python user agent?
    response = await mirror.services.http_client.post(
        "https://old.ppy.sh/forum/ucp.php",
        params={"mode": "login"},
        headers=LOGIN_HEADERS,
        data=LOGIN_BODY_BASE | osu_account,
        follow_redirects=True,
    )

    if response.status_code != 200:
        # TODO: should we try to login again any time soon?
        print(f"login failed with {response.status_code}")

        return None

    print("logged in as", osu_account["username"])

    return OsuWebSession(
        username=osu_account["username"],
        password=osu_account["password"],
        osu_session_token=response.cookies["osu_session"],
        xsrf_token=response.cookies["XSRF-TOKEN"],
    )


async def osu_login_after_delay(
    osu_account: OsuAccount,
    delay: Union[float, int],
) -> Optional[OsuWebSession]:
    await asyncio.sleep(delay)

    return await osu_login(osu_account)
