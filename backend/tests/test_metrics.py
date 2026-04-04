from __future__ import annotations


def _create_metric_type(authed_client, name="Weight", unit="lbs"):
    resp = authed_client.post("/api/metric-types", json={"name": name, "unit": unit})
    assert resp.status_code == 201
    return resp.json()


class TestMetricTypes:
    def test_create_metric_type(self, authed_client):
        data = _create_metric_type(authed_client)
        assert data["name"] == "Weight"
        assert data["unit"] == "lbs"
        assert "id" in data

    def test_create_duplicate_metric_type(self, authed_client):
        _create_metric_type(authed_client, name="Weight")
        resp = authed_client.post("/api/metric-types", json={"name": "weight", "unit": "kg"})
        assert resp.status_code == 409

    def test_list_metric_types(self, authed_client):
        _create_metric_type(authed_client, name="Weight", unit="lbs")
        _create_metric_type(authed_client, name="Steps", unit="count")
        resp = authed_client.get("/api/metric-types")
        assert resp.status_code == 200
        types = resp.json()
        assert len(types) == 2
        names = [t["name"] for t in types]
        assert "Steps" in names
        assert "Weight" in names

    def test_update_metric_type(self, authed_client):
        mt = _create_metric_type(authed_client)
        resp = authed_client.put(f"/api/metric-types/{mt['id']}", json={"unit": "kg"})
        assert resp.status_code == 200
        assert resp.json()["unit"] == "kg"
        assert resp.json()["name"] == "Weight"

    def test_update_metric_type_duplicate_name(self, authed_client):
        _create_metric_type(authed_client, name="Weight")
        mt2 = _create_metric_type(authed_client, name="Steps", unit="count")
        resp = authed_client.put(f"/api/metric-types/{mt2['id']}", json={"name": "Weight"})
        assert resp.status_code == 409

    def test_delete_metric_type(self, authed_client):
        mt = _create_metric_type(authed_client)
        resp = authed_client.delete(f"/api/metric-types/{mt['id']}")
        assert resp.status_code == 204
        resp2 = authed_client.get("/api/metric-types")
        assert len(resp2.json()) == 0

    def test_delete_metric_type_not_found(self, authed_client):
        resp = authed_client.delete("/api/metric-types/nonexistent")
        assert resp.status_code == 404


class TestMetricEntries:
    def test_create_metric_entry(self, authed_client):
        mt = _create_metric_type(authed_client)
        resp = authed_client.post(
            "/api/metrics",
            json={
                "metric_type_id": mt["id"],
                "value": 185.5,
                "recorded_date": "2025-01-15",
                "notes": "Morning weigh-in",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["value"] == 185.5
        assert data["metric_type_id"] == mt["id"]
        assert data["notes"] == "Morning weigh-in"

    def test_create_metric_entry_invalid_type(self, authed_client):
        resp = authed_client.post(
            "/api/metrics",
            json={
                "metric_type_id": "nonexistent",
                "value": 100,
                "recorded_date": "2025-01-15",
            },
        )
        assert resp.status_code == 404

    def test_get_metric_entry(self, authed_client):
        mt = _create_metric_type(authed_client)
        create = authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 185, "recorded_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        resp = authed_client.get(f"/api/metrics/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["value"] == 185

    def test_get_metric_entry_not_found(self, authed_client):
        resp = authed_client.get("/api/metrics/nonexistent")
        assert resp.status_code == 404

    def test_list_metric_entries(self, authed_client):
        mt = _create_metric_type(authed_client)
        for i in range(3):
            authed_client.post(
                "/api/metrics",
                json={
                    "metric_type_id": mt["id"],
                    "value": 180 + i,
                    "recorded_date": f"2025-01-{15 + i:02d}",
                },
            )
        resp = authed_client.get("/api/metrics")
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_metric_entries_filter_by_type(self, authed_client):
        mt1 = _create_metric_type(authed_client, name="Weight", unit="lbs")
        mt2 = _create_metric_type(authed_client, name="Steps", unit="count")
        authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt1["id"], "value": 185, "recorded_date": "2025-01-15"},
        )
        authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt2["id"], "value": 10000, "recorded_date": "2025-01-15"},
        )
        resp = authed_client.get(f"/api/metrics?metric_type_id={mt1['id']}")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["value"] == 185

    def test_list_metric_entries_filter_by_date(self, authed_client):
        mt = _create_metric_type(authed_client)
        authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 180, "recorded_date": "2025-01-01"},
        )
        authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 185, "recorded_date": "2025-06-01"},
        )
        resp = authed_client.get("/api/metrics?date_from=2025-03-01")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["value"] == 185

    def test_list_metric_entries_pagination(self, authed_client):
        mt = _create_metric_type(authed_client)
        for i in range(5):
            authed_client.post(
                "/api/metrics",
                json={
                    "metric_type_id": mt["id"],
                    "value": 180 + i,
                    "recorded_date": f"2025-01-{10 + i:02d}",
                },
            )
        resp = authed_client.get("/api/metrics?page=1&per_page=2")
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_update_metric_entry(self, authed_client):
        mt = _create_metric_type(authed_client)
        create = authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 185, "recorded_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        resp = authed_client.put(f"/api/metrics/{entry_id}", json={"value": 183})
        assert resp.status_code == 200
        assert resp.json()["value"] == 183
        assert resp.json()["recorded_date"] == "2025-01-15"

    def test_update_metric_entry_not_found(self, authed_client):
        resp = authed_client.put("/api/metrics/nonexistent", json={"value": 100})
        assert resp.status_code == 404

    def test_delete_metric_entry(self, authed_client):
        mt = _create_metric_type(authed_client)
        create = authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 185, "recorded_date": "2025-01-15"},
        )
        entry_id = create.json()["id"]
        resp = authed_client.delete(f"/api/metrics/{entry_id}")
        assert resp.status_code == 204
        assert authed_client.get(f"/api/metrics/{entry_id}").status_code == 404

    def test_delete_metric_entry_not_found(self, authed_client):
        resp = authed_client.delete("/api/metrics/nonexistent")
        assert resp.status_code == 404


class TestMetricTrends:
    def test_trend_returns_correct_shape(self, authed_client):
        mt = _create_metric_type(authed_client)
        for i in range(5):
            authed_client.post(
                "/api/metrics",
                json={
                    "metric_type_id": mt["id"],
                    "value": 185 - i,
                    "recorded_date": f"2025-01-{10 + i:02d}",
                },
            )
        resp = authed_client.get(f"/api/metrics/trends/{mt['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric_type_id"] == mt["id"]
        assert data["metric_name"] == "Weight"
        assert data["unit"] == "lbs"
        assert len(data["data"]) == 5
        # ordered ascending by date
        dates = [p["recorded_date"] for p in data["data"]]
        assert dates == sorted(dates)

    def test_trend_with_date_filter(self, authed_client):
        mt = _create_metric_type(authed_client)
        authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 190, "recorded_date": "2025-01-01"},
        )
        authed_client.post(
            "/api/metrics",
            json={"metric_type_id": mt["id"], "value": 185, "recorded_date": "2025-06-01"},
        )
        resp = authed_client.get(f"/api/metrics/trends/{mt['id']}?date_from=2025-03-01")
        data = resp.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["value"] == 185

    def test_trend_empty(self, authed_client):
        mt = _create_metric_type(authed_client)
        resp = authed_client.get(f"/api/metrics/trends/{mt['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_trend_not_found(self, authed_client):
        resp = authed_client.get("/api/metrics/trends/nonexistent")
        assert resp.status_code == 404
