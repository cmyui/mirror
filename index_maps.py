from __future__ import annotations

import elasticsearch

elastic_client = elasticsearch.Elasticsearch(f"http://localhost:9200")


def process_hits(hits):
    print("updating", len(hits), "beatmapsets")
    operations = []
    for beatmapset in hits:
        if "beatmaps" in beatmapset["_source"]["data"]:
            continue

        beatmaps_resp = elastic_client.search(
            index="beatmaps",
            query={
                "bool": {
                    "must": [{"match": {"data.beatmapset_id": beatmapset["_id"]}}],
                },
            },
        )
        beatmaps = [b["_source"]["data"] for b in beatmaps_resp["hits"]["hits"]]

        new_beatmapset = beatmapset["_source"]
        new_beatmapset["data"]["beatmaps"] = beatmaps

        operations.append(
            {
                "index": {
                    "_index": "beatmapsets",
                    "_id": beatmapset["_id"],
                },
            },
        )
        operations.append(new_beatmapset)

    if operations:
        elastic_client.bulk(operations=operations)


all_maps = elastic_client.search(
    index="beatmapsets",
    scroll="2m",
    size=1000,
)

sid = all_maps["_scroll_id"]
scroll_size = len(all_maps["hits"]["hits"])

while scroll_size > 0:
    process_hits(all_maps["hits"]["hits"])

    all_maps = elastic_client.scroll(scroll_id=sid, scroll="2m")
    sid = all_maps["_scroll_id"]
    scroll_size = len(all_maps["hits"]["hits"])

elastic_client.clear_scroll(scroll_id=sid)
