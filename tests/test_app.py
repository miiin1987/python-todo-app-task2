from app import create_app


class FakeRepository:
    def __init__(self):
        self.todos = []

    def all(self): return self.todos
    def get(self, todo_id): return next((x for x in self.todos if x["id"] == todo_id), None)
    def create(self, title, content, due_date, priority):
        self.todos.append({"id": "1", "title": title, "content": content, "due_date": due_date, "priority": priority, "completed": False})
    def update(self, todo_id, title, content, due_date, priority):
        todo = self.get(todo_id)
        if not todo: return False
        todo.update(title=title, content=content, due_date=due_date, priority=priority)
        return True
    def toggle(self, todo_id):
        todo = self.get(todo_id)
        if not todo: return False
        todo["completed"] = not todo["completed"]
        return True
    def delete(self, todo_id):
        todo = self.get(todo_id)
        if not todo: return False
        self.todos.remove(todo)
        return True


def test_create_edit_delete_todo():
    repo = FakeRepository()
    client = create_app(repo).test_client()
    response = client.post("/todos/new", data={"title": "勉強", "content": "Python課題", "due_date": "2026-08-31", "priority": "high"})
    assert response.status_code == 302
    assert b"Python" in client.get("/").data
    response = client.post("/todos/1/edit", data={"title": "勉強完了", "content": "公開する", "due_date": "2026-09-01", "priority": "low"})
    assert response.status_code == 302
    assert "勉強完了" in client.get("/").data.decode()
    assert client.post("/todos/1/toggle").status_code == 302
    assert repo.todos[0]["completed"] is True
    assert client.post("/todos/1/delete").status_code == 302
    assert repo.todos == []
