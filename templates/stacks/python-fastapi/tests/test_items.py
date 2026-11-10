def test_create_item_success(client):
    payload = {"name": "Test Gadget", "price": 49.95}
    response = client.post("/api/v1/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Gadget"
    assert data["price"] == 49.95
    assert "id" in data
    assert "created_at" in data


def test_create_item_validation_error(client):
    payload = {"name": "", "price": -10.0}
    response = client.post("/api/v1/items", json=payload)
    assert response.status_code == 422


def test_get_item_not_found(client):
    response = client.get("/api/v1/items/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
