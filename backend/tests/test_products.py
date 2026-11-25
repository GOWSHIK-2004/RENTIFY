from tests.factories import make_category, make_product

PRODUCT_PAYLOAD = {
    "name": "Canon EOS R50",
    "brand": "Canon",
    "model": "R50",
    "short_description": "Compact mirrorless camera",
    "description": "A lightweight camera for creators.",
    "daily_price": "749.00",
    "specifications": {"Sensor": "APS-C", "Video": "4K"},
}


def test_admin_routes_reject_anonymous_and_customers(client, customer_headers, category):
    payload = {**PRODUCT_PAYLOAD, "category_id": category.id}

    assert client.post("/api/v1/products", json=payload).status_code == 401
    assert client.post("/api/v1/products", json=payload, headers=customer_headers).status_code == 403
    assert client.post("/api/v1/categories", json={"name": "Drones"}, headers=customer_headers).status_code == 403
    assert client.get("/api/v1/admin/inventory", headers=customer_headers).status_code == 403


def test_admin_creates_product(client, admin_headers, category):
    response = client.post("/api/v1/products", json={**PRODUCT_PAYLOAD, "category_id": category.id}, headers=admin_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Canon EOS R50"
    assert body["daily_price"] == "749.00"
    assert body["category"]["slug"] == "cameras"
    assert body["specifications"]["Video"] == "4K"
    assert body["average_rating"] is None and body["review_count"] == 0


def test_create_product_validation(client, admin_headers, category):
    negative = {**PRODUCT_PAYLOAD, "category_id": category.id, "daily_price": "-5"}
    unknown_category = {**PRODUCT_PAYLOAD, "category_id": 9999}

    assert client.post("/api/v1/products", json=negative, headers=admin_headers).status_code == 422
    assert client.post("/api/v1/products", json=unknown_category, headers=admin_headers).status_code == 400


def test_get_product_and_404(client, product):
    assert client.get(f"/api/v1/products/{product.id}").json()["name"] == "Sony Alpha A6400"
    assert client.get("/api/v1/products/9999").status_code == 404


def test_search_by_name_or_brand_is_case_insensitive(client, db, category):
    make_product(db, category, name="Sony Alpha A6400", brand="Sony")
    make_product(db, category, name="GoPro HERO12", brand="GoPro")

    by_name = client.get("/api/v1/products", params={"q": "alpha"}).json()
    by_brand = client.get("/api/v1/products", params={"q": "GOPRO"}).json()

    assert [p["name"] for p in by_name["items"]] == ["Sony Alpha A6400"]
    assert [p["name"] for p in by_brand["items"]] == ["GoPro HERO12"]


def test_search_treats_wildcards_literally(client, db, category):
    make_product(db, category, name="Sony Alpha A6400")
    assert client.get("/api/v1/products", params={"q": "%"}).json()["total"] == 0


def test_filter_by_category_and_price_range(client, db):
    cameras = make_category(db, "Cameras")
    drones = make_category(db, "Drones")
    make_product(db, cameras, name="Cheap Cam", daily_price="300")
    make_product(db, cameras, name="Pricey Cam", daily_price="1500")
    make_product(db, drones, name="Mini Drone", daily_price="900")

    in_cameras = client.get("/api/v1/products", params={"category": "cameras"}).json()
    in_range = client.get("/api/v1/products", params={"min_price": 500, "max_price": 1000}).json()

    assert {p["name"] for p in in_cameras["items"]} == {"Cheap Cam", "Pricey Cam"}
    assert [p["name"] for p in in_range["items"]] == ["Mini Drone"]


def test_sorting_and_pagination(client, db, category):
    for index, price in enumerate(["500", "100", "300", "200", "400"]):
        make_product(db, category, name=f"Item {index}", daily_price=price)

    ascending = client.get("/api/v1/products", params={"sort": "price_asc", "page_size": 2}).json()
    descending = client.get("/api/v1/products", params={"sort": "price_desc"}).json()
    page_three = client.get("/api/v1/products", params={"sort": "price_asc", "page_size": 2, "page": 3}).json()
    newest = client.get("/api/v1/products", params={"sort": "newest"}).json()

    assert [p["daily_price"] for p in ascending["items"]] == ["100.00", "200.00"]
    assert (ascending["total"], ascending["pages"]) == (5, 3)
    assert descending["items"][0]["daily_price"] == "500.00"
    assert [p["daily_price"] for p in page_three["items"]] == ["500.00"]
    assert newest["items"][0]["name"] == "Item 4"
    assert client.get("/api/v1/products", params={"sort": "bogus"}).status_code == 422


def test_featured_products(client, db, category):
    make_product(db, category, name="Featured One", is_featured=True)
    make_product(db, category, name="Plain One")
    make_product(db, category, name="Hidden Featured", is_featured=True, is_active=False)

    names = [p["name"] for p in client.get("/api/v1/products/featured").json()]
    assert names == ["Featured One"]


def test_update_product_changes_price_and_fields(client, admin_headers, product):
    response = client.patch(
        f"/api/v1/products/{product.id}",
        json={"daily_price": "999.00", "is_featured": True},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["daily_price"] == "999.00"
    assert response.json()["is_featured"] is True
    assert response.json()["name"] == "Sony Alpha A6400"


def test_archived_product_is_hidden_from_customers_but_kept(client, admin_headers, product):
    assert client.delete(f"/api/v1/products/{product.id}", headers=admin_headers).status_code == 200

    assert client.get(f"/api/v1/products/{product.id}").status_code == 404
    assert client.get("/api/v1/products").json()["total"] == 0
    # Administrators can still see and manage it.
    assert client.get(f"/api/v1/products/{product.id}", headers=admin_headers).json()["is_active"] is False
    listing = client.get("/api/v1/products", params={"include_inactive": True}, headers=admin_headers).json()
    assert listing["total"] == 1


def test_include_inactive_is_admin_only(client, customer_headers):
    assert client.get("/api/v1/products", params={"include_inactive": True}).status_code == 403
    assert client.get("/api/v1/products", params={"include_inactive": True}, headers=customer_headers).status_code == 403


def test_archived_category_hides_its_products(client, db, admin_headers, category, product):
    response = client.delete(f"/api/v1/categories/{category.id}", headers=admin_headers)

    assert response.status_code == 200 and response.json()["is_active"] is False
    assert client.get("/api/v1/products").json()["total"] == 0
    assert client.get("/api/v1/categories").json() == []
    assert len(client.get("/api/v1/categories", params={"include_inactive": True}, headers=admin_headers).json()) == 1


def test_category_create_generates_slug_and_rejects_duplicates(client, admin_headers):
    created = client.post("/api/v1/categories", json={"name": "Audio Equipment"}, headers=admin_headers)
    duplicate = client.post("/api/v1/categories", json={"name": "Audio Equipment"}, headers=admin_headers)

    assert created.status_code == 201 and created.json()["slug"] == "audio-equipment"
    assert duplicate.status_code == 409
