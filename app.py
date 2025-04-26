# app.py
from flask import Flask, render_template, request
from crawler import crawl
import json
import os
import sqlite3

app = Flask(__name__)

# 一時的にインデックスを保存するリスト
index = []
# インデックスを保存するjsonファイル名
INDEX_FILE = 'index.json'

# トップページを表示
@app.route('/')
def index_page():
    return render_template('index.html')

# 検索処理
@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip().lower()  # 検索キーワードを取得
    results = []
    if keyword:
        conn = sqlite3.connect('search.db')
        c = conn.cursor()
        # contentカラムからキーワードを部分一致検索
        c.execute('''
            SELECT title, url FROM pages
            WHERE content LIKE ?
        ''', (f'%{keyword}%',))
        # 結果をリストに整形
        results = [{'title': row[0], 'url': row[1]} for row in c.fetchall()]
        conn.close()
    # 結果ページを表示
    return render_template('results.html', keyword=keyword, results=results)

# クロール開始処理
@app.route('/crawl', methods=['POST'])
def start_crawl():
    global index
    url = request.form.get('url')  # フォームから起点URLを取得
    if url:
        index = crawl(url, max_pages=10)  # 最大10ページまでクローリング
        save_to_db(index)  # クローリング結果をデータベースに保存
        save_index()  # クローリング結果をjsonに保存
        # デバッグ用ログ出力
        print(f"クロール完了: {len(index)} ページ保存済み")
        for i, page in enumerate(index):
            print(f"{i+1}. {page['title']} - {page['url']}")

    # トップページに戻る
    return render_template('index.html', crawled=True)

# データベースを初期化する関数
def init_db():
    conn = sqlite3.connect('search.db')
    c = conn.cursor()
    # pagesテーブルがなければ作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT UNIQUE,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

# クローリング結果をデータベースに保存する関数
def save_to_db(pages):
    conn = sqlite3.connect('search.db')
    c = conn.cursor()
    for page in pages:
        try:
            c.execute('''
                INSERT OR IGNORE INTO pages (title, url, content)
                VALUES (?, ?, ?)
            ''', (page['title'], page['url'], page['content']))
        except Exception as e:
            print(f"DB保存エラー: {e}")
    conn.commit()
    conn.close()

# クローリング結果をjsonファイルに保存する関数
def save_index():
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

# 起動時に保存済みindexを読み込む関数
def load_index():
    global index
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index = json.load(f)

# アプリ起動時にインデックスをロード
load_index()  

if __name__ == '__main__':
    init_db()  # アプリ移動時にデータベース初期化
    load_index() # インデックス読み込み
    app.run(debug=False)  # Flaskアプリの自動リロードをオフにして起動
