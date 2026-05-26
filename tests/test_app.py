import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

import src.app as app_module

# Snapshot the initial activities so tests can reset global state
INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Reset the in-memory activities before each test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(INITIAL_ACTIVITIES))
    yield


def client():
    return TestClient(app_module.app)


def test_get_activities():
    with client() as c:
        r = c.get("/activities")
        assert r.status_code == 200
        data = r.json()
        assert "Chess Club" in data
        assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_and_duplicate_and_delete_flow():
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    encoded_activity = urllib.parse.quote(activity, safe='')

    with client() as c:
        # Sign up
        r = c.post(f"/activities/{encoded_activity}/signup", params={"email": email})
        assert r.status_code == 200
        assert "Signed up" in r.json().get("message", "")

        # Ensure participant appears
        r2 = c.get("/activities")
        assert email in r2.json()[activity]["participants"]

        # Duplicate signup should fail
        r3 = c.post(f"/activities/{encoded_activity}/signup", params={"email": email})
        assert r3.status_code == 400

        # Delete participant
        r4 = c.delete(f"/activities/{encoded_activity}/signup", params={"email": email})
        assert r4.status_code == 200
        assert "Unregistered" in r4.json().get("message", "")

        # Confirm removal
        r5 = c.get("/activities")
        assert email not in r5.json()[activity]["participants"]
