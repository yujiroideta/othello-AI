// 最小構成のオセロUIロジック

// オセロ盤とステータス表示エリアを取得
let boardEl = document.getElementById("board");
let statusEl = document.getElementById("status");

/**
 * サーバーから現在のゲーム状態を取得し、
 * 盤面を再描画する関数
 */
function fetchState() {
  fetch("/get_state")  // サーバーに現在の状態をリクエスト
    .then(res => res.json())  // JSON形式で受け取る
    .then(data => renderBoard(data));  // 盤面を更新
}

/**
 * ゲームの状態（盤面＋手番）を描画する関数
 */
function renderBoard(data) {
  boardEl.innerHTML = "";  // 盤面を一度クリア
  for (let row = 0; row < data.board.length; row++) {
    let tr = document.createElement("tr");
    for (let col = 0; col < data.board[row].length; col++) {
      let td = document.createElement("td");
      // クリックされたときに行と列が分かるようにデータ属性を付与
      td.dataset.row = row;
      td.dataset.col = col;
      // セルの内容に応じて石を表示（1: 黒 ●、2: 白 ○）
      let val = data.board[row][col];
      if (val === 1) td.textContent = "●";
      else if (val === 2) td.textContent = "○";
      // クリックイベントを設定（石を置く処理）
      td.onclick = handleClick;
      tr.appendChild(td);
    }
    boardEl.appendChild(tr);
  }
  // 現在の手番を表示（1: 黒, 2: 白）
  statusEl.textContent = data.current_player === 1 ? "黒の番です" : "白の番です";
}

/**
 * セルをクリックしたときに呼ばれる関数
 * サーバーに「このマスに石を置く」というリクエストを送る
 */
function handleClick(e) {
  let row = parseInt(e.target.dataset.row);
  let col = parseInt(e.target.dataset.col);
  fetch("/place_stone", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row, col })  // 行・列の情報を送信
  })
  .then(res => res.json())
  .then(res => {
    if (res.success) {
      // 成功したら盤面を再取得して更新
      fetchState();
    } else {
      // 置けない場所だったらアラートを表示
      alert("その場所には置けません！");
    }
  });
}

// ページ読み込み時に最初の状態を取得して表示
fetchState();