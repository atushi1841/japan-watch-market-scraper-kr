# 일본 중고 시계 마켓 — 크로스샵 비교（Jackroad+Kitamura）

**일본 최대 중고 명품 시계 전문점 잭로드와 키타무라(시계 재고 395+점)의 중고 시계 가격을 크로스샵 비교. 같은 모델의 매장 간 가격 차이를 확인할 수 있습니다.**

> 🇯🇵 English/日本語版: [Japan Market](https://apify.com/fruitful_quintessence)

## Input

| Field | Type | Default | Description |
|---|---|---|---|
| `searchKeyword` | string | `ROLEX` | 검색 키워드 |
| `maxItems` | integer | 100 | 최대 수집 개수 |
| `maxPages` | integer | 2 | 소스별 최대 페이지 수 |
| `sources` | string | `jackroad,kitamura` | 데이터 소스（쉼표 구분） |
| `proxyConfiguration` | object | — | Apify proxy |

## Output Sample

```json
{
  "productId": "6341419",
  "title": "ロレックス エアキング",
  "price": 848000,
  "brand": "ロレックス",
  "condition": "ヴィンテージ",
  "stockStatus": "在庫あり",
  "productUrl": "https://www.jackroad.co.jp/shop/g/g6341419/",
  "shop": "Jackroad",
  "source": "jackroad",
  "category": "中古時計",
  "scrapedAt": "2026-08-10T09:54:53Z"
}
```

## Use Cases

- 직구/되팔기: 저가 상품 발견 → 마진 확보
- 시세 조사: 특정 모델의 시장 가격 추이 추적
- 재고 모니터링: 매장 재고 변화 감시

## Pricing

이벤트당 과금 — $0.00005/실행 + **$0.002/건**

## Data Source

공개 상품 정보(명칭, 가격, 브랜드, 재고 상태)만 수집합니다.
