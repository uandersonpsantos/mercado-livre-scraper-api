import hashlib
import json
from urllib.parse import quote, unquote

from curl_cffi import requests as curl_requests


BASE_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "accept-encoding": "gzip, deflate",
    "sec-ch-ua": '"Google Chrome";v="142", "Not.A/Brand";v="8", "Chromium";v="142"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "upgrade-insecure-requests": "1",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "priority": "u=0, i",
}

CLIENT_HINTS = {
    "device-memory": "32",
    "dpr": "1",
    "viewport-width": "1920",
    "rtt": "50",
    "downlink": "1.6",
    "ect": "4g",
    "sec-ch-ua-platform-version": '"10.0.0"',
    "sec-ch-ua-model": '""',
}

SESSION = curl_requests.Session(impersonate="chrome142")


def get_cookie(name):
    for cookie in SESSION.cookies.jar:
        if cookie.name == name:
            return cookie.value
    return None


def solve_bm_challenge(bmstate_raw):
    decoded = unquote(bmstate_raw)
    parts = decoded.split(';')
    seed = parts[0]
    difficulty = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    if difficulty == 0:
        return f"{seed};0"
    prefix = '0' * difficulty
    for nonce in range(10_000_000):
        h = hashlib.sha256(f"{seed}{nonce}".encode()).hexdigest()
        if h.startswith(prefix):
            return f"{seed};{nonce}"
    return f"{seed};0"


def init_session(first_url):
    h0 = dict(BASE_HEADERS)
    h0['sec-fetch-site'] = 'none'
    SESSION.get("https://www.mercadolivre.com.br/", headers=h0, timeout=30)

    h1 = dict(BASE_HEADERS)
    h1['sec-fetch-site'] = 'same-site'
    h1['referer'] = 'https://www.mercadolivre.com.br/'
    SESSION.get(first_url, headers=h1, timeout=30)

    bmstate = get_cookie('_bmstate')
    if bmstate:
        bmc_value = solve_bm_challenge(bmstate)
        SESSION.cookies.set('_bmc', quote(bmc_value, safe=''), domain='.mercadolivre.com.br', path='/')
    SESSION.cookies.set('_bm_skipml', 'true', domain='.mercadolivre.com.br', path='/')


def extract_state(html):
    script_start = html.find('<script id="__NORDIC_RENDERING_CTX__"')
    if script_start == -1:
        return None
    script_end = html.find('</script>', script_start)
    script_content = html[script_start:script_end]
    json_start = script_content.find('_n.ctx.r=') + len('_n.ctx.r=')
    raw_json = script_content[json_start:]
    decoder = json.JSONDecoder()
    data, _ = decoder.raw_decode(raw_json)
    return data['appProps']['pageProps']['initialState']


def parse_products(state):
    products = []
    for item in state.get('results', []):
        polycard = item.get('polycard', {})
        metadata = polycard.get('metadata', {})
        components = polycard.get('components', [])

        title = None
        price = None

        for comp in components:
            ctype = comp.get('type')
            if ctype == 'title':
                title = comp.get('title', {}).get('text')
            elif ctype == 'price':
                price_data = comp.get('price', {})
                current = price_data.get('current_price', {})
                price = current.get('value')

        raw_url = metadata.get('url', '')
        fragments = metadata.get('url_fragments', '')
        if raw_url:
            link = 'https://' + raw_url + fragments
        else:
            link = None

        if title and link and price is not None:
            products.append({
                'name': title,
                'link': link,
                'price': price,
            })
    return products


def get_next_page_url(state):
    pagination = state.get('pagination', {})
    next_page = pagination.get('next_page', {})
    if next_page.get('show') and next_page.get('url'):
        return next_page['url']
    return None


def fetch_page(url, referer):
    headers = dict(BASE_HEADERS)
    headers.update(CLIENT_HINTS)
    headers['sec-fetch-site'] = 'same-origin'
    headers['referer'] = referer
    resp = SESSION.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def search(product, max_results):
    slug = quote(product.replace(' ', '-').lower())
    first_url = f"https://lista.mercadolivre.com.br/{slug}"

    init_session(first_url)

    all_products = []
    visited = set()

    html = fetch_page(first_url, referer=first_url)
    state = extract_state(html)

    if not state:
        return all_products

    page_products = parse_products(state)
    all_products.extend(page_products)
    visited.add(first_url)

    current_referer = first_url
    next_url = get_next_page_url(state)

    while next_url and next_url not in visited:
        visited.add(next_url)
        html = fetch_page(next_url, referer=current_referer)
        state = extract_state(html)

        if not state:
            break

        page_products = parse_products(state)
        all_products.extend(page_products)

        current_referer = next_url
        next_url = get_next_page_url(state)

    all_products.sort(key=lambda x: x['price'])

    if max_results > 0:
        all_products = all_products[:max_results]

    return all_products


def main():
    product = input("Product: ").strip()
    max_results = int(input("Max results (0 for all): ").strip())

    results = search(product, max_results)

    print(f"\nFound {len(results)} products:\n")
    for idx, p in enumerate(results, 1):
        print(f"{idx}. {p['name']}")
        print(f"   Price: R$ {p['price']:,.2f}")
        print(f"   Link: {p['link']}")
        print()


if __name__ == '__main__':
    main()
