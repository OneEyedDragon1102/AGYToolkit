import pytest
from fastapi.testclient import TestClient

from {{PACKAGE_NAME}}.main import create_app
from {{PACKAGE_NAME}}.services.item_service import item_service


@pytest.fixture
def client():
    item_service.clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    item_service.clear()
