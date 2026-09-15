from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

import api.routes.data_contracts as contract_route
from api.main import app

client = TestClient(app)


def build_contract(
    *,
    contract_id: int = 10,
    catalog_id: int = 3,
    contract_version: int = 2,
    is_active: bool = True,
    enforcement_mode: str = "BLOCK",
) -> dict:
    timestamp = datetime(
        2026,
        9,
        15,
        1,
        0,
        0,
    )

    return {
        "contract_id": contract_id,
        "catalog_id": catalog_id,
        "contract_version": (
            contract_version
        ),
        "contract_name": (
            "customers-contract"
        ),
        "enforcement_mode": (
            enforcement_mode
        ),
        "is_active": is_active,
        "created_at": timestamp,
        "updated_at": timestamp,
        "columns": [
            {
                "contract_column_id": 50,
                "contract_id": contract_id,
                "column_name": (
                    "customer_id"
                ),
                "expected_type": (
                    "NUMERIC"
                ),
                "is_required": True,
                "is_nullable": False,
                "created_at": timestamp,
            }
        ],
    }


def test_create_data_contract_api(
    monkeypatch,
):
    captured: dict = {}

    def fake_create_data_contract(
        *,
        catalog_id,
        contract_name,
        columns,
        enforcement_mode,
        activate,
    ):
        captured.update(
            {
                "catalog_id": catalog_id,
                "contract_name": (
                    contract_name
                ),
                "columns": columns,
                "enforcement_mode": (
                    enforcement_mode
                ),
                "activate": activate,
            }
        )

        return build_contract()

    monkeypatch.setattr(
        contract_route,
        "create_data_contract",
        fake_create_data_contract,
    )

    response = client.post(
        "/api/data-contracts",
        json={
            "catalog_id": 3,
            "contract_name": (
                "customers-contract"
            ),
            "enforcement_mode": (
                "BLOCK"
            ),
            "activate": True,
            "columns": [
                {
                    "column_name": (
                        "customer_id"
                    ),
                    "expected_type": (
                        "NUMERIC"
                    ),
                    "is_required": True,
                    "is_nullable": False,
                }
            ],
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["contract_id"] == 10
    assert payload["catalog_id"] == 3
    assert payload["contract_version"] == 2
    assert payload["is_active"] is True

    assert captured[
        "enforcement_mode"
    ] == "BLOCK"

    assert captured["activate"] is True

    assert captured["columns"][0] == {
        "column_name": "customer_id",
        "expected_type": "NUMERIC",
        "is_required": True,
        "is_nullable": False,
    }


def test_get_data_contract_api(
    monkeypatch,
):
    monkeypatch.setattr(
        contract_route,
        "get_data_contract",
        lambda contract_id: (
            build_contract(
                contract_id=contract_id
            )
        ),
    )

    response = client.get(
        "/api/data-contracts/10"
    )

    assert response.status_code == 200
    assert (
        response.json()["contract_id"]
        == 10
    )


def test_get_data_contract_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        contract_route,
        "get_data_contract",
        lambda contract_id: None,
    )

    response = client.get(
        "/api/data-contracts/999"
    )

    assert response.status_code == 404


def test_get_contract_history_api(
    monkeypatch,
):
    monkeypatch.setattr(
        contract_route,
        "get_data_contract_history",
        lambda catalog_id: [
            build_contract(
                contract_id=12,
                catalog_id=catalog_id,
                contract_version=2,
                is_active=True,
            ),
            build_contract(
                contract_id=11,
                catalog_id=catalog_id,
                contract_version=1,
                is_active=False,
            ),
        ],
    )

    response = client.get(
        "/api/data-contracts/catalog/3"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["catalog_id"] == 3
    assert payload["count"] == 2

    assert (
        payload["items"][0][
            "contract_version"
        ]
        == 2
    )

    assert (
        payload["items"][1][
            "contract_version"
        ]
        == 1
    )


def test_get_active_contract_api(
    monkeypatch,
):
    monkeypatch.setattr(
        contract_route,
        "get_active_data_contract",
        lambda catalog_id: (
            build_contract(
                catalog_id=catalog_id
            )
        ),
    )

    response = client.get(
        "/api/data-contracts/catalog/3/active"
    )

    assert response.status_code == 200
    assert (
        response.json()["is_active"]
        is True
    )


def test_get_active_contract_returns_404(
    monkeypatch,
):
    monkeypatch.setattr(
        contract_route,
        "get_active_data_contract",
        lambda catalog_id: None,
    )

    response = client.get(
        "/api/data-contracts/catalog/3/active"
    )

    assert response.status_code == 404


def test_activate_data_contract_api(
    monkeypatch,
):
    def fake_activate_data_contract(
        contract_id: int,
    ):
        return build_contract(
            contract_id=contract_id,
            contract_version=4,
            is_active=True,
        )

    monkeypatch.setattr(
        contract_route,
        "activate_data_contract",
        fake_activate_data_contract,
    )

    response = client.post(
        "/api/data-contracts/10/activate"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["contract_id"] == 10
    assert payload["is_active"] is True


def test_activate_missing_contract_returns_404(
    monkeypatch,
):
    def fake_activate_data_contract(
        contract_id: int,
    ):
        raise ValueError(
            "Data contract not found: "
            f"{contract_id}"
        )

    monkeypatch.setattr(
        contract_route,
        "activate_data_contract",
        fake_activate_data_contract,
    )

    response = client.post(
        "/api/data-contracts/999/activate"
    )

    assert response.status_code == 404

    assert (
        "Data contract not found"
        in response.json()["detail"]
    )