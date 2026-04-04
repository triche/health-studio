from __future__ import annotations


class TestCreateJournal:
    def test_create_journal_entry(self, client):
        response = client.post(
            "/api/journals",
            json={"title": "My First Entry", "content": "Hello world", "entry_date": "2025-01-15"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My First Entry"
        assert data["content"] == "Hello world"
        assert data["entry_date"] == "2025-01-15"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_journal_entry_empty_content(self, client):
        response = client.post(
            "/api/journals",
            json={"title": "Empty Entry", "entry_date": "2025-01-15"},
        )
        assert response.status_code == 201
        assert response.json()["content"] == ""

    def test_create_journal_entry_missing_title(self, client):
        response = client.post(
            "/api/journals",
            json={"content": "No title", "entry_date": "2025-01-15"},
        )
        assert response.status_code == 422

    def test_create_journal_entry_empty_title(self, client):
        response = client.post(
            "/api/journals",
            json={"title": "", "content": "stuff", "entry_date": "2025-01-15"},
        )
        assert response.status_code == 422


class TestGetJournal:
    def test_get_journal_entry(self, client):
        create = client.post(
            "/api/journals",
            json={"title": "Test", "content": "Body", "entry_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        response = client.get(f"/api/journals/{entry_id}")
        assert response.status_code == 200
        assert response.json()["id"] == entry_id
        assert response.json()["title"] == "Test"

    def test_get_journal_entry_not_found(self, client):
        response = client.get("/api/journals/nonexistent-id")
        assert response.status_code == 404


class TestListJournals:
    def test_list_journals_empty(self, client):
        response = client.get("/api/journals")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20

    def test_list_journals_returns_entries(self, client):
        for i in range(3):
            client.post(
                "/api/journals",
                json={"title": f"Entry {i}", "content": "", "entry_date": f"2025-01-{15 + i:02d}"},
            )
        response = client.get("/api/journals")
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_journals_pagination(self, client):
        for i in range(5):
            client.post(
                "/api/journals",
                json={"title": f"Entry {i}", "content": "", "entry_date": f"2025-01-{10 + i:02d}"},
            )
        response = client.get("/api/journals?page=1&per_page=2")
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2

        response2 = client.get("/api/journals?page=3&per_page=2")
        data2 = response2.json()
        assert len(data2["items"]) == 1

    def test_list_journals_ordered_by_date_desc(self, client):
        client.post(
            "/api/journals",
            json={"title": "Old", "content": "", "entry_date": "2025-01-01"},
        )
        client.post(
            "/api/journals",
            json={"title": "New", "content": "", "entry_date": "2025-01-20"},
        )
        client.post(
            "/api/journals",
            json={"title": "Mid", "content": "", "entry_date": "2025-01-10"},
        )
        response = client.get("/api/journals")
        items = response.json()["items"]
        dates = [item["entry_date"] for item in items]
        assert dates == sorted(dates, reverse=True)

    def test_list_journals_date_filtering(self, client):
        client.post(
            "/api/journals",
            json={"title": "Jan", "content": "", "entry_date": "2025-01-15"},
        )
        client.post(
            "/api/journals",
            json={"title": "Feb", "content": "", "entry_date": "2025-02-15"},
        )
        client.post(
            "/api/journals",
            json={"title": "Mar", "content": "", "entry_date": "2025-03-15"},
        )

        response = client.get("/api/journals?date_from=2025-02-01&date_to=2025-02-28")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Feb"

    def test_list_journals_date_from_only(self, client):
        client.post(
            "/api/journals",
            json={"title": "Old", "content": "", "entry_date": "2025-01-01"},
        )
        client.post(
            "/api/journals",
            json={"title": "New", "content": "", "entry_date": "2025-06-01"},
        )
        response = client.get("/api/journals?date_from=2025-03-01")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "New"


class TestUpdateJournal:
    def test_update_journal_entry(self, client):
        create = client.post(
            "/api/journals",
            json={"title": "Original", "content": "old", "entry_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        response = client.put(
            f"/api/journals/{entry_id}",
            json={"title": "Updated", "content": "new content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["content"] == "new content"
        assert data["entry_date"] == "2025-01-15"  # unchanged

    def test_update_journal_partial(self, client):
        create = client.post(
            "/api/journals",
            json={"title": "Original", "content": "keep this", "entry_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        response = client.put(
            f"/api/journals/{entry_id}",
            json={"title": "New Title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["content"] == "keep this"

    def test_update_journal_not_found(self, client):
        response = client.put(
            "/api/journals/nonexistent-id",
            json={"title": "Nope"},
        )
        assert response.status_code == 404


class TestDeleteJournal:
    def test_delete_journal_entry(self, client):
        create = client.post(
            "/api/journals",
            json={"title": "To Delete", "content": "", "entry_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        response = client.delete(f"/api/journals/{entry_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/journals/{entry_id}")
        assert get_response.status_code == 404

    def test_delete_journal_not_found(self, client):
        response = client.delete("/api/journals/nonexistent-id")
        assert response.status_code == 404
