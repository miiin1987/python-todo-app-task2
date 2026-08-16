import json
import os
from datetime import date, datetime, timedelta

import gspread
from flask import Flask, flash, redirect, render_template, request, url_for
from google.oauth2.service_account import Credentials


HEADERS = [
    "id", "title", "content", "due_date", "created_at", "updated_at",
    "priority", "completed",
]
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class GoogleSheetsTodoRepository:
    def __init__(self):
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        credentials_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not sheet_id or not credentials_json:
            raise RuntimeError(
                "GOOGLE_SHEET_ID と GOOGLE_SERVICE_ACCOUNT_JSON を設定してください。"
            )

        info = json.loads(credentials_json)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_key(sheet_id)
        try:
            self.sheet = spreadsheet.worksheet("todos")
        except gspread.WorksheetNotFound:
            self.sheet = spreadsheet.add_worksheet(title="todos", rows=1000, cols=6)
        current_headers = self.sheet.row_values(1)
        if not current_headers:
            self.sheet.append_row(HEADERS)
        elif current_headers != HEADERS:
            # 課題1で作成済みのシートに新しい列だけを安全に追加する。
            self.sheet.update("A1:H1", [HEADERS])

    def all(self):
        records = self.sheet.get_all_records()
        today = date.today()
        for item in records:
            item["priority"] = item.get("priority") or "medium"
            item["completed"] = str(item.get("completed", "")).lower() == "true"
            try:
                due = date.fromisoformat(str(item["due_date"]))
                if due < today:
                    item["due_status"] = "overdue"
                elif due <= today + timedelta(days=3):
                    item["due_status"] = "soon"
                else:
                    item["due_status"] = "normal"
            except ValueError:
                item["due_status"] = "normal"

        def sort_key(item):
            due_date = str(item["due_date"])
            urgent = item["due_status"] in {"overdue", "soon"}
            if item["completed"]:
                return (2, 0, due_date)
            if urgent:
                return (0, 0, due_date)
            return (1, PRIORITY_ORDER.get(item["priority"], 1), due_date)

        return sorted(
            records,
            key=sort_key,
        )

    def get(self, todo_id):
        for todo in self.all():
            if str(todo["id"]) == str(todo_id):
                return todo
        return None

    def create(self, title, content, due_date, priority):
        now = datetime.now().isoformat(timespec="seconds")
        todo_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.sheet.append_row(
            [todo_id, title, content, due_date, now, now, priority, "false"]
        )

    def update(self, todo_id, title, content, due_date, priority):
        cell = self.sheet.find(str(todo_id), in_column=1)
        if not cell:
            return False
        created_at = self.sheet.cell(cell.row, 5).value
        completed = self.sheet.cell(cell.row, 8).value or "false"
        now = datetime.now().isoformat(timespec="seconds")
        self.sheet.update(
            f"A{cell.row}:H{cell.row}",
            [[str(todo_id), title, content, due_date, created_at, now, priority, completed]],
        )
        return True

    def toggle(self, todo_id):
        cell = self.sheet.find(str(todo_id), in_column=1)
        if not cell:
            return False
        current = self.sheet.cell(cell.row, 8).value.lower() == "true"
        self.sheet.update_cell(cell.row, 8, str(not current).lower())
        return True

    def delete(self, todo_id):
        cell = self.sheet.find(str(todo_id), in_column=1)
        if not cell:
            return False
        self.sheet.delete_rows(cell.row)
        return True


def create_app(repository=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "local-development-key")
    repo = repository

    def get_repo():
        nonlocal repo
        if repo is None:
            repo = GoogleSheetsTodoRepository()
        return repo

    @app.get("/")
    def index():
        return render_template("index.html", todos=get_repo().all())

    @app.route("/todos/new", methods=["GET", "POST"])
    def new_todo():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            due_date = request.form.get("due_date", "").strip()
            priority = request.form.get("priority", "medium")
            if not title or not content or not due_date:
                flash("タイトル・内容・期日はすべて必須です。", "error")
                return render_template("form.html", todo=request.form, mode="登録"), 400
            get_repo().create(title, content, due_date, priority)
            flash("Todoを登録しました。", "success")
            return redirect(url_for("index"))
        return render_template("form.html", todo=None, mode="登録")

    @app.route("/todos/<todo_id>/edit", methods=["GET", "POST"])
    def edit_todo(todo_id):
        todo = get_repo().get(todo_id)
        if todo is None:
            return "Todoが見つかりません。", 404
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            due_date = request.form.get("due_date", "").strip()
            priority = request.form.get("priority", "medium")
            if not title or not content or not due_date:
                flash("タイトル・内容・期日はすべて必須です。", "error")
                return render_template("form.html", todo=request.form, mode="編集"), 400
            get_repo().update(todo_id, title, content, due_date, priority)
            flash("Todoを更新しました。", "success")
            return redirect(url_for("index"))
        return render_template("form.html", todo=todo, mode="編集")

    @app.post("/todos/<todo_id>/toggle")
    def toggle_todo(todo_id):
        if not get_repo().toggle(todo_id):
            return "Todoが見つかりません。", 404
        return redirect(request.referrer or url_for("index"))

    @app.post("/todos/<todo_id>/delete")
    def delete_todo(todo_id):
        if not get_repo().delete(todo_id):
            return "Todoが見つかりません。", 404
        flash("Todoを削除しました。", "success")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
