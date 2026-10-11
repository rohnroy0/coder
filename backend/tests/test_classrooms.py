def helper_register_and_login(client, name, email, password, role):
    client.post("/api/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "role": role
    })
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_teacher_create_classroom(client):
    teacher_headers = helper_register_and_login(client, "Prof. Alan", "alan@example.com", "pass123", "TEACHER")
    
    payload = {
        "name": "Python Basics",
        "description": "Intro to Python Programming"
    }
    response = client.post("/api/classrooms", json=payload, headers=teacher_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Python Basics"
    assert "join_code" in data
    assert len(data["join_code"]) >= 5

def test_student_cannot_create_classroom(client):
    student_headers = helper_register_and_login(client, "Student Charlie", "charlie@example.com", "pass123", "STUDENT")
    
    payload = {
        "name": "Unauthorized Class",
        "description": "Should fail"
    }
    response = client.post("/api/classrooms", json=payload, headers=student_headers)
    assert response.status_code == 403

def test_student_join_classroom_and_view(client):
    teacher_headers = helper_register_and_login(client, "Teacher Dave", "dave@example.com", "pass123", "TEACHER")
    student_headers = helper_register_and_login(client, "Student Eve", "eve@example.com", "pass123", "STUDENT")

    # Teacher creates classroom
    create_res = client.post("/api/classrooms", json={"name": "Data Structures"}, headers=teacher_headers)
    classroom_data = create_res.json()
    join_code = classroom_data["join_code"]

    # Student joins classroom
    join_res = client.post("/api/classrooms/join", json={"join_code": join_code}, headers=student_headers)
    assert join_res.status_code == 200
    assert join_res.json()["id"] == classroom_data["id"]

    # Check joined classrooms list for student
    joined_res = client.get("/api/classrooms/joined", headers=student_headers)
    assert joined_res.status_code == 200
    joined_list = joined_res.json()
    assert len(joined_list) == 1
    assert joined_list[0]["join_code"] == join_code

def test_join_nonexistent_classroom_fails(client):
    student_headers = helper_register_and_login(client, "Student Frank", "frank@example.com", "pass123", "STUDENT")
    response = client.post("/api/classrooms/join", json={"join_code": "INVALID99"}, headers=student_headers)
    assert response.status_code == 404

def test_join_classroom_twice_fails(client):
    teacher_headers = helper_register_and_login(client, "Teacher Grace", "grace@example.com", "pass123", "TEACHER")
    student_headers = helper_register_and_login(client, "Student Hank", "hank@example.com", "pass123", "STUDENT")

    create_res = client.post("/api/classrooms", json={"name": "Algorithms"}, headers=teacher_headers)
    join_code = create_res.json()["join_code"]

    client.post("/api/classrooms/join", json={"join_code": join_code}, headers=student_headers)
    # Second attempt
    dup_res = client.post("/api/classrooms/join", json={"join_code": join_code}, headers=student_headers)
    assert dup_res.status_code == 400

def test_delete_classroom(client):
    teacher1_headers = helper_register_and_login(client, "Teacher Ivy", "ivy@example.com", "pass123", "TEACHER")
    teacher2_headers = helper_register_and_login(client, "Teacher Jack", "jack@example.com", "pass123", "TEACHER")

    create_res = client.post("/api/classrooms", json={"name": "Web Dev"}, headers=teacher1_headers)
    class_id = create_res.json()["id"]

    # Teacher 2 trying to delete Teacher 1's class should be forbidden
    forbidden_res = client.delete(f"/api/classrooms/{class_id}", headers=teacher2_headers)
    assert forbidden_res.status_code == 403

    # Teacher 1 deleting own class should succeed
    success_res = client.delete(f"/api/classrooms/{class_id}", headers=teacher1_headers)
    assert success_res.status_code == 200
