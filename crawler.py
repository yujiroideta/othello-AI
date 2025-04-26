# crawler.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# シンプルなクローラー関数（再帰なし）
def crawl(url, max_pages=5):
    visited = set()  # 訪問済みURLのセット
    pages = []  # クロールしたページ情報を格納するリスト
    queue = [url]  # クロール待ちのURLリスト（キュー）

    while queue and len(pages) < max_pages:
        current_url = queue.pop(0)
        if current_url in visited:
            continue

        try:
            response = requests.get(current_url, timeout=5)
            if response.status_code != 200:
                continue

            visited.add(current_url)
            soup = BeautifulSoup(response.text, "html.parser")

            # ページのテキストとタイトルを抽出
            text = soup.get_text(separator=' ', strip=True)
            title = soup.title.string if soup.title else current_url

            # ページ情報を保存
            pages.append({
                'url': current_url,
                'title': title,
                'content': text.lower()  # contentは小文字化して保存
            })

            # 同じドメイン内のリンクをキューに追加
            for link in soup.find_all('a', href=True):
                absolute = urljoin(current_url, link['href'])
                if urlparse(absolute).netloc == urlparse(url).netloc:
                    queue.append(absolute)

        except Exception as e:
            print(f"エラー: {e} ({current_url})")

    return pages
