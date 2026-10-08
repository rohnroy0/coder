def test_register_user_success(client):
    payload = {
        "name": "Teacher Jane",
        "email": "jane.teacher@example.com",
        "password": "password123",
        "role": "TEACHER"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Teacher Jane"
    assert data["email"] == "jane.teacher@example.com"
    assert data["role"] == "TEACHER"
    assert "id" in data

def test_register_duplicate_email_fails(client):
    payload = {
        "name": "Student Bob",
        "email": "bob@example.com",
        "password": "password123",
        "role": "STUDENT"
    }
    client.post("/api/auth/register", json=payload)
    
    # Duplicate attempt
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"

def test_login_success(client):
    payload = {
        "name": "Student Alice",
        "email": "alice@example.com",
        "password": "secretpassword",
        "role": "STUDENT"
    }
    client.post("/api/auth/register", json=payload)

    login_payload = {
        "email": "alice@example.com",
        "password": "secretpassword"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 401

def test_get_current_user_me(client):
    # Register & Login
    client.post("/api/auth/register", json={
        "name": "Prof Smith",
        "email": "smith@example.com",
        "password": "password123",
        "role": "TEACHER"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "smith@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "smith@example.com"
    assert data["role"] == "TEACHER"
