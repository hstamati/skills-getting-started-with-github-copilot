import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data(monkeypatch):
    data = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 2,
            "participants": ["enrolled@example.com"],
        },
        "Art Club": {
            "description": "Explore drawing, painting, and other visual arts",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 1,
            "participants": ["full@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", data)
    return data


@pytest.fixture
def client(activity_data):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_all_activity_data(client, activity_data):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activity_data


def test_signup_adds_participant(client, activity_data):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@example.com for Chess Club"
    }
    assert "new@example.com" in activity_data["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client, activity_data):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert len(activity_data) == 2


def test_signup_rejects_duplicate_participant(client, activity_data):
    participants = activity_data["Chess Club"]["participants"].copy()

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "enrolled@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activity_data["Chess Club"]["participants"] == participants


def test_signup_rejects_full_activity(client, activity_data):
    participants = activity_data["Art Club"]["participants"].copy()

    response = client.post(
        "/activities/Art Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert activity_data["Art Club"]["participants"] == participants


def test_signup_requires_email(client):
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_unregister_removes_participant(client, activity_data):
    response = client.delete(
        "/activities/Chess Club/participants/enrolled@example.com"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered enrolled@example.com from Chess Club"
    }
    assert "enrolled@example.com" not in activity_data["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants/enrolled@example.com"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_nonparticipant(client, activity_data):
    participants = activity_data["Chess Club"]["participants"].copy()

    response = client.delete(
        "/activities/Chess Club/participants/absent@example.com"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activity_data["Chess Club"]["participants"] == participants