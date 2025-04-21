# Webオセロゲームの試作 AI対戦
# 勝敗判定＆パス・ゲーム終了メッセージの追加

import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 定数定義
BOARD_SIZE = 8
EMPTY, BLACK, WHITE = 0, 1, 2

# ゲームの初期状態
game_state = {
    "board": [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)],
    "current_player": BLACK,  # 黒からスタート
    "ai_enabled": True  # TrueでAI（白）と対戦可能
}

# 初期配置を設定
def setup_board():
    mid = BOARD_SIZE // 2
    game_state["board"][mid - 1][mid - 1] = WHITE
    game_state["board"][mid][mid] = WHITE
    game_state["board"][mid - 1][mid] = BLACK
    game_state["board"][mid][mid - 1] = BLACK

setup_board()

# ゲーム状態を初期化する関数
def reset_game_state():
    game_state["board"] = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    game_state["current_player"] = BLACK
    game_state["game_over"] = False
    setup_board()  # 初期4石配置

# メイン画面(HTML)を返す
@app.route("/")
def index():
    return render_template("index.html")

# 現在のゲーム状態をJSON形式で返す
@app.route("/get_state")
def get_state():
    return jsonify(game_state)

# 石を挟める位置を返す（石が置けるかどうかの判断にも使用）
def get_flippable_stones(row, col, player):
    opponent = BLACK if player == WHITE else WHITE
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1), (1, 0), (1, 1)]
    to_flip = []
    for dr, dc in directions:
        r, c = row + dr, col + dc
        flip_temp = []
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and game_state["board"][r][c] == opponent:
            flip_temp.append((r, c))
            r += dr
            c += dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and game_state["board"][r][c] == player and flip_temp:
            to_flip.extend(flip_temp)
    return to_flip

# 指定プレイヤーが合法手を持つかどうかをチェック
def has_valid_moves(player):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game_state["board"][row][col] == EMPTY:
                if get_flippable_stones(row, col, player):
                    return True
    return False

# プレイヤーが石を置いた時の処理
@app.route("/place_stone", methods=["POST"])
def place_stone():
    data = request.json
    row, col = data["row"], data["col"]
    player = game_state["current_player"]

    # すでに石がある場所には置けない
    if game_state["board"][row][col] != EMPTY:
        return jsonify({"success": False})

    # 石をひっくり返せない（合法手でない）場合は無効
    flipped = get_flippable_stones(row, col, player)
    if not flipped:
        return jsonify({"success": False})
    
    # 石を配置し、盤面と手番を更新
    apply_move(row, col, flipped, player)

    # ターン後の判定
    messages = []

    # 次のプレイヤーに合法手がない場合はパスする
    next_player = game_state["current_player"]
    if not has_valid_moves(next_player):
        # 両者に合法手がなければゲーム終了（ここでは警告だけ）
        if not has_valid_moves(player):
            print("両プレイヤーとも合法手なし → ゲーム終了")
        else:
            # パスして元に戻す
            game_state["current_player"] = player
            messages.append(f"{'白' if next_player == WHITE else '黒'} はパスします")

        return jsonify({
            "success": True,
            "board": game_state["board"],
            "current_player": game_state["current_player"],
            "messages": messages,
            "game_over": game_state.get("game_over", False)
        })
    
    # ← ここが「通常の流れ」での return
    return jsonify({
        "success": True,
        "board": game_state["board"],
        "current_player": game_state["current_player"],
        "messages": messages,
        "game_over": game_state.get("game_over", False)
    })


@app.route("/ai_move", methods=["POST"])
def ai_move_route():
    messages = []

    if game_state["ai_enabled"] and game_state["current_player"] == WHITE:
        ai_move(messages)

    return jsonify({
        "board": game_state["board"],
        "current_player": game_state["current_player"],
        "messages": messages,
        "game_over": game_state.get("game_over", False)
    })

# 石を置いたあと盤面と手番を更新する
def apply_move(row, col, flipped, player):
    game_state["board"][row][col] = player
    for r, c in flipped:
        game_state["board"][r][c] = player
    game_state["current_player"] = BLACK if player == WHITE else WHITE

# 簡易AI（合法手からランダムに1つ選んで置く）
def ai_move(messages):
    moves = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if game_state["board"][row][col] == EMPTY:
                flipped = get_flippable_stones(row, col, WHITE)
                if flipped:
                    moves.append((row, col, flipped))
    if moves:
        row, col, flipped = random.choice(moves)
        apply_move(row, col, flipped, WHITE)

        # 次のプレイヤー（黒）に合法手がなければパス
        if not has_valid_moves(BLACK):
            if not has_valid_moves(WHITE):
                messages.append("ゲーム終了！")
                messages.append(judge_winner())
                game_state["game_over"] = True
            else:
                messages.append("黒はパスします")
                game_state["current_player"] = WHITE

# 勝者を判定する
def judge_winner():
    black_count = sum(row.count(BLACK) for row in game_state["board"])
    white_count = sum(row.count(WHITE) for row in game_state["board"])
    if black_count > white_count:
        return f"黒の勝ち！（黒: {black_count} 対 白: {white_count}）"
    elif white_count > black_count:
        return f"白の勝ち！（白: {white_count} 対 黒: {black_count}）"
    else:
        return f"引き分け！（黒: {black_count} 対 白: {white_count}）"
    
# リセットボタン
@app.route("/reset_game", methods=["POST"])
def reset_game():
    reset_game_state()
    return jsonify({
        "board": game_state["board"],
        "current_player": game_state["current_player"],
        "messages": [],
        "game_over": False
    })

# ゲーム終了ボタン
@app.route("/end_game", methods=["POST"])
def end_game():
    game_state["game_over"] = True
    return jsonify({
        "board": game_state["board"],
        "current_player": game_state["current_player"],
        "messages": ["ゲーム終了"],
        "game_over": True
    })

# 終了ページ
@app.route("/goodbye")
def goodbye():
    return "<h1>ご利用ありがとうございました！</h1><p>また遊んでね :)</p>"

# Flaskアプリの起動
if __name__ == "__main__":
    app.run(debug=True)