<div align="center">

<img src="../assets/logo.svg" alt="Rewind Bulk Creator" width="150" />

# Rewind Bulk Creator（リウィンド バルク クリエイター）

**Rewind.ai のアカウントを一括作成し、自動でメール認証を行い、それぞれに API キーを発行します — コマンドひとつで。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![ライセンス: MIT](https://img.shields.io/badge/%E3%83%A9%E3%82%A4%E3%82%BB%E3%83%B3%E3%82%B9-MIT-3DA639?style=flat-square)](../LICENSE)
[![プラットフォーム](https://img.shields.io/badge/%E3%83%97%E3%83%A9%E3%83%83%E3%83%88%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A0-Rewind.ai-6366F1?style=flat-square)](https://rewind.ai/)
[![受信箱](https://img.shields.io/badge/%E5%8F%97%E4%BF%A1%E7%AE%B1-mail.tm-06B6D4?style=flat-square)](https://mail.tm/)
[![ステータス](https://img.shields.io/badge/%E3%82%B9%E3%83%86%E3%83%BC%E3%82%BF%E3%82%B9-%E6%9C%89%E5%8A%B9-22C55E?style=flat-square)]()

[English](../README.md) · [Español](README.es.md) · [Português](README.pt.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [中文](README.zh.md)

</div>

---

## 概要

Rewind Bulk Creator は、Rewind.ai の登録フロー全体を自動化する軽量な Python
CLI です。[mail.tm](https://mail.tm/) で使い捨ての受信箱を作成し、それぞれに
Rewind.ai アカウントを登録し、認証メールを待ち、認証リンクを開き、最後に
ランダムな名前の API キーを作成します。各アカウントとキーは JSON、CSV、および
`email:key` のテキストとして保存されます。

HTTP エンドポイントを直接利用するため、ブラウザやヘッドレスドライバー、
Selenium は不要です。

## 機能

- コマンドひとつで任意の数のアカウントを作成。
- mail.tm による使い捨て受信箱 — 設定は不要。
- 認証メールの自動処理（受信箱からトークンを抽出）。
- ランダムで読みやすい API キー名（`key-cobalt-falcon-4f2a`）。
- ランダムな強力パスワード、または `--password` で固定。
- レート制限を適切に処理（待機して再試行するモード付き）。
- JSON / CSV / `email:key` テキストで出力。
- ネットワーク通信なしのドライラン（`--dry-run`）。

## クイックスタート

```bash
git clone https://github.com/<あなたのユーザー名>/rewind-bulk-creator.git
cd rewind-bulk-creator
pip install -r requirements.txt

# 認証済みアカウントを5個作成し、それぞれにAPIキーを発行
python rewind_bulk.py --count 5
```

結果は `accounts/` に出力されます：

```
accounts/
├── accounts.json
├── accounts.csv
└── keys.txt
```

## 使い方

```bash
# mail.tm のランダム受信箱で10アカウント
python rewind_bulk.py -n 10

# 固定パスワードで3アカウント
python rewind_bulk.py -n 3 --password "MyFixedPassw0rd!"

# キー名の接頭辞をカスタマイズ
python rewind_bulk.py -n 5 --label-prefix worker

# ネットワーク通信なしで計画のみ
python rewind_bulk.py -n 3 --dry-run

# Rewind.ai がIPを制限したら自動で待機して継続
python rewind_bulk.py -n 20 --wait-on-rate-limit
```

## 仕組み

1. mail.tm で**受信箱を作成**。
2. `POST /v1/auth/signup` で**登録**。
3. **認証メールを待ち**、リンクから `token` を抽出。
4. `POST /v1/auth/verify-email` で**認証**。
5. `POST /v1/api-keys` で**API キーを作成**。

## 動作要件

- Python 3.10 以上
- `requests`
- `api.mail.tm` と `api.rewind.ai` へのネットワークアクセス

## 注意事項と制限

- Rewind.ai は IP ごとに登録数を制限します（例：1時間に10件）。本ツールは
  制限を検出し、フラグに応じて停止または待機します。
- メール配信は mail.tm に依存します。遅い場合は `--verify-timeout` を増やして
  ください。
- 各自の責任で、利用するプラットフォームの利用規約を守って使用してください。

## ライセンス

[MIT ライセンス](../LICENSE) の下で公開されています。
