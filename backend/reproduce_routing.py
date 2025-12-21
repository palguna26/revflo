from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_audit_route():
    # Attempt to hit the route.
    # It should return 401 (Unauthorized) or 404 (Specific detail) or 404 (Generic)
    # If generic 404 {"detail": "Not Found"}, routing is broken.
    # If 401 or custom 404, routing works.
    response = client.get("/api/repos/testowner/testrepo/audit")
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")

if __name__ == "__main__":
    test_audit_route()
