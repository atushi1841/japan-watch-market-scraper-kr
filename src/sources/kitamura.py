import asyncio
import random
import re
import datetime
import httpx

API_URL = "https://shop.kitamura.jp/ec/api/cache/s/v1/used_sell_search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Referer": "https://shop.kitamura.jp/ec/ct/used/list",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
}


def parse_price(price):
    """キタムラのpriceは '1,588,000円' 形式のことがある"""
    if isinstance(price, (int, float)):
        return int(price)
    if isinstance(price, str):
        digits = re.sub(r"\D", "", price)
        try:
            return int(digits) if digits else None
        except ValueError:
            return None
    return None


async def fetch_kitamura(client, keyword="", max_pages=2, max_items=100, category_filter=None):
    results = []
    offset = 1
    size = min(80, max_items)
    page = 0
    while page < max_pages and len(results) < max_items:
        params = {
            "sort": "default",
            "size": size,
            "offset": offset,
            "func": "srch",
            "ref_id": "used_sell_search",
            "extra_fields": "sales_status,is_maintenance,sale_start_at,sale_end_at",
            "site": "ns",
            "is_logged_in": "0",
            "aggs": "default",
        }
        if keyword:
            params["query"] = keyword

        resp = await client.get(API_URL, params=params, headers=HEADERS)
        if resp.status_code != 200:
            print(f"[kitamura] HTTP {resp.status_code}: {resp.text[:200]}")
            break
        if not resp.text.strip():
            print("[kitamura] 空レスポンス")
            break
        try:
            data = resp.json()
        except Exception as e:
            print(f"[kitamura] JSONパース失敗: {resp.text[:300]}")
            raise
        hits = (data.get("search") or {}).get("hits") or []
        if not hits:
            break

        for hit in hits:
            cats = hit.get("category") or []
            cat_str = ":".join(cats) if isinstance(cats, list) else str(cats)
            # 時計カテゴリのみ（category_filter指定時）
            if category_filter and category_filter not in cat_str:
                continue
            item = {
                "productId": hit.get("id"),
                "title": hit.get("title", ""),
                "price": parse_price(hit.get("price")),
                "brand": hit.get("maker", "") or hit.get("brand", ""),
                "shop": hit.get("shop", ""),
                "category": cat_str,
                "imageUrl": hit.get("image_link", ""),
                "productUrl": f"https://shop.kitamura.jp/ec/prd/{hit.get('id')}",
                "condition": hit.get("rank", ""),
                "source": "kitamura",
                "scrapedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            results.append(item)
            if len(results) >= max_items:
                break

        offset += size
        page += 1
        if len(hits) < size:
            break
        await asyncio.sleep(random.uniform(1, 2))

    return results[:max_items]
