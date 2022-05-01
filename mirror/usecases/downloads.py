import mirror.sessions
import random
import mirror.services


async def download_beatmap_set(beatmap_set_id: int, osz2_path: str) -> bool:
    """Download a beatmap set .osz file from osu!'s servers."""
    # TODO: ratelimit on a per account basis
    session = random.choice(mirror.sessions.sessions)

    response = await mirror.services.http_client.get(
        f"https://osu.ppy.sh/d/{beatmap_set_id}",
        cookies={
            "osu_session": session.osu_session_token,
            "XSRF-TOKEN": session.xsrf_token,
        },
        follow_redirects=True,
    )
    response_body = await response.aread()

    # TODO: handle 404?

    if response.status_code != 200:
        print(f"download failed with {response.status_code}")
        print(response_body.decode())

        return False

    print("downloaded beatmap set", beatmap_set_id)

    with open(osz2_path, "wb") as f:
        f.write(response_body)

    return True
