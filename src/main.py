import asyncio
import datetime
import json
import sys
import unicodedata

import httpx

try:
    from apify import Actor
except Exception:
    Actor = None


def _norm_key(text):
    """Normalize text using NFC and casefold."""
    return unicodedata.normalize('NFC', text).casefold()


async def run(actor_input, actor=None):
    stats_mode = actor_input.get("statsMode", False)
    stats_keyword = actor_input.get("statsKeyword", "")
    collected_items = []
    search_keyword = actor_input.get("searchKeyword") or ""
    max_items = int(actor_input.get("maxItems", 100))
    max_pages = int(actor_input.get("maxPages", 2))
    sources = [s.strip() for s in actor_input.get("sources", "jackroad,kitamura").split(",") if s.strip()]

    proxy_url = None
    if actor is not None:
        proxy_config = await actor.create_proxy_configuration(actor_proxy_input=actor_input.get("proxyConfiguration"))
        if proxy_config:
            proxy_url = await proxy_config.new_url()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    # キタムラAPIはApifyプロキシ(海外DC IP)を403ブロックするため、プロキシなしのクライアントが必要
    async with httpx.AsyncClient(proxy=proxy_url, headers=headers, timeout=30.0, follow_redirects=True) as client, \
               httpx.AsyncClient(proxy=None, headers=headers, timeout=30.0, follow_redirects=True) as client_direct:
        collected = 0
        for src in sources:
            if collected >= max_items:
                break
            remaining = max_items - collected
            items = []
            if src == "jackroad":
                if not search_keyword:
                    continue  # ジャックロードはキーワード必須
                from sources.jackroad import fetch_jackroad
                items = await fetch_jackroad(client, keyword=search_keyword, max_pages=max_pages, max_items=remaining)
            elif src == "kitamura":
                from sources.kitamura import fetch_kitamura
                # キタムラは時計カテゴリに絞る（キーワードがあればキーワード検索）
                items = await fetch_kitamura(client_direct, keyword=search_keyword, max_pages=max_pages,
                                             max_items=remaining, category_filter="中古時計")

            for item in items:
                if stats_mode:
                    collected_items.append(item)
                else:
                    if actor is not None:
                        await actor.push_data(item)
                    else:
                        print(json.dumps(item, ensure_ascii=False))
                collected += 1
                if collected >= max_items:
                    break

        if stats_mode:
            keyword = stats_keyword or search_keyword
            filtered = collected_items
            if keyword:
                kw = _norm_key(keyword)
                filtered = [it for it in collected_items if kw in _norm_key(it.get("title", ""))]
            prices = []
            for it in filtered:
                try:
                    prices.append(int(it["price"]))
                except (KeyError, ValueError, TypeError):
                    continue
            count = len(prices)
            price_min = min(prices) if prices else None
            price_max = max(prices) if prices else None
            if prices:
                price_sum = sum(prices)
                price_avg = price_sum // count
                sorted_prices = sorted(prices)
                mid = count // 2
                if count % 2 == 0:
                    price_median = (sorted_prices[mid-1] + sorted_prices[mid]) // 2
                else:
                    price_median = sorted_prices[mid]
            else:
                price_avg = None
                price_median = None
            sample_items = [
                {
                    "title": it.get("title", ""),
                    "price": it.get("price"),
                    "detailUrl": it.get("detailUrl", it.get("url", "")),
                    "shop": it.get("shop", it.get("source", "")),
                }
                for it in filtered[:3]
            ]
            stats_result = {
                "statsType": "japan-watch-price-kr",
                "keyword": keyword,
                "count": count,
                "priceMin": price_min,
                "priceMax": price_max,
                "priceAvg": price_avg,
                "priceMedian": price_median,
                "sampleItems": sample_items,
                "collectedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if actor is not None:
                await actor.push_data(stats_result)
            else:
                print(json.dumps(stats_result, ensure_ascii=False))
            return


async def main():
    if Actor is not None:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            await run(actor_input, actor=Actor)
    else:
        raw = sys.stdin.read() or ""
        try:
            actor_input = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            actor_input = {}
        await run(actor_input, actor=None)


if __name__ == "__main__":
    asyncio.run(main())
