# MercadoLivre Scraper

> ⚠️ **Aviso Legal / Disclaimer** — veja ao final do documento.

---

## Português

### O que é

Script Python que busca produtos no [MercadoLivre Brasil](https://www.mercadolivre.com.br), varre todas as páginas de resultados e retorna a lista ordenada do menor para o maior preço.

### Requisitos

- Python 3.10+
- [`curl_cffi`](https://github.com/yifeikong/curl_cffi)

```bash
pip install curl_cffi
```

### Como usar

```bash
python scraper.py
```

O script pedirá duas informações:

```
Product: iphone 14
Max results (0 for all): 10
```

- **Product** — nome do produto a buscar.
- **Max results** — quantidade máxima de resultados a retornar. Use `0` para retornar todos.

### Saída

Os produtos são exibidos em ordem crescente de preço:

```
Found 10 products:

1. Apple iPhone 14 (128 GB) - Roxo - Excelente (Recondicionado)
   Price: R$ 2,310.00
   Link: https://www.mercadolivre.com.br/...
...
```

### Como funciona

1. **Inicialização da sessão** — acessa a página inicial do MercadoLivre para estabelecer cookies de sessão (`_mldataSessionId`, `_d2id`).
2. **Micro-landing / desafio do bot** — a primeira requisição à página de busca retorna uma página intermediária que executa um desafio de prova de trabalho (SHA-256 Proof-of-Work). O script resolve o desafio em Python e define os cookies `_bmc` e `_bm_skipml`.
3. **Busca real** — com os cookies corretos e os cabeçalhos Client Hints (`device-memory`, `dpr`, `viewport-width`, etc.), o script requisita a página de resultados e obtém o HTML completo.
4. **Extração de dados** — os dados dos produtos estão embutidos no HTML dentro de um bloco JSON (`__NORDIC_RENDERING_CTX__`), no campo `initialState.results`. Cada produto contém título, preço atual e URL.
5. **Paginação** — o script segue o campo `pagination.next_page.url` até não haver mais páginas (offsetes de 48 em 48: `_Desde_49_`, `_Desde_97_`, etc.).
6. **Ordenação e corte** — após coletar todos os produtos de todas as páginas, ordena por preço crescente e aplica o limite `max_results`.

---

## English

### What it is

A Python script that searches for products on [MercadoLivre Brasil](https://www.mercadolivre.com.br), crawls all result pages, and returns the list sorted from lowest to highest price.

### Requirements

- Python 3.10+
- [`curl_cffi`](https://github.com/yifeikong/curl_cffi)

```bash
pip install curl_cffi
```

### How to use

```bash
python scraper.py
```

The script will prompt for two inputs:

```
Product: iphone 14
Max results (0 for all): 10
```

- **Product** — name of the product to search for.
- **Max results** — maximum number of results to return. Use `0` to return all.

### Output

Products are displayed in ascending price order:

```
Found 10 products:

1. Apple iPhone 14 (128 GB) - Purple - Excellent (Refurbished)
   Price: R$ 2,310.00
   Link: https://www.mercadolivre.com.br/...
...
```

### How it works

1. **Session initialization** — visits the MercadoLivre homepage to establish session cookies (`_mldataSessionId`, `_d2id`).
2. **Micro-landing / bot challenge** — the first request to the search URL returns an intermediate page that runs a SHA-256 Proof-of-Work challenge in JavaScript. The script solves the challenge in Python and sets the `_bmc` and `_bm_skipml` cookies.
3. **Real search request** — with the correct cookies and Client Hints headers (`device-memory`, `dpr`, `viewport-width`, etc.), the script fetches the full search results HTML.
4. **Data extraction** — product data is embedded in the HTML inside a JSON blob (`__NORDIC_RENDERING_CTX__`), under `initialState.results`. Each entry contains the title, current price, and URL.
5. **Pagination** — the script follows `pagination.next_page.url` until no more pages exist (offsets of 48: `_Desde_49_`, `_Desde_97_`, and so on).
6. **Sorting and trimming** — after collecting all products from all pages, sorts by ascending price and applies the `max_results` limit.

---

## ⚠️ Aviso Legal / Disclaimer

**PT:** Este projeto foi desenvolvido exclusivamente para fins educacionais e de estudo. O autor não se responsabiliza por qualquer uso indevido, violação dos Termos de Serviço do MercadoLivre ou danos causados pelo uso deste software. Use por sua própria conta e risco.

**EN:** This project was developed solely for educational and study purposes. The author takes no responsibility for any misuse, violation of MercadoLivre's Terms of Service, or damages caused by the use of this software. Use at your own risk.
