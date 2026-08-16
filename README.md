# Python Todoリストアプリ（課題2）

FlaskとGoogleスプレッドシートを使用したTodo管理Webアプリです。課題1の機能に、重要度、完了チェック、期限間近の強調・自動並び替えを追加しています。

## 1. Google側の準備

1. Google Cloudでプロジェクトを作成する。
2. Google Sheets APIとGoogle Drive APIを有効化する。
3. サービスアカウントを作成し、JSONキーを取得する。
4. 空のGoogleスプレッドシートを作成する。
5. スプレッドシートの共有設定で、サービスアカウントのメールアドレスに「編集者」を付与する。
6. URLの `/d/` と `/edit` の間にある文字列をスプレッドシートIDとして控える。

## 2. ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

環境変数を設定します。JSONは一行の文字列として設定してください。

```bash
export GOOGLE_SHEET_ID="スプレッドシートID"
export GOOGLE_SERVICE_ACCOUNT_JSON='JSONキーの内容'
export SECRET_KEY="任意の長いランダム文字列"
python app.py
```

ブラウザで `http://127.0.0.1:5000` を開きます。初回アクセス時に `todos` シートと見出し行が自動作成されます。

## 3. Renderで公開

1. このフォルダをGitHubリポジトリへpushする。
2. Renderで「New」→「Web Service」を選び、GitHubリポジトリを接続する。
3. Build Commandを `pip install -r requirements.txt`、Start Commandを `gunicorn app:app` にする。
4. Environmentで `GOOGLE_SHEET_ID`、`GOOGLE_SERVICE_ACCOUNT_JSON`、`SECRET_KEY` を設定する。
5. デプロイ完了後に発行されたURLで、登録・編集・一覧・削除を確認する。

## セキュリティ上の注意

- サービスアカウントのJSONキーをGitHubへ保存しないでください。
- JSONキーはRenderの環境変数にだけ登録してください。
- 誤って公開した場合は、Google Cloudで該当キーを直ちに無効化・削除してください。

## テスト

```bash
pip install pytest
pytest -q
```
