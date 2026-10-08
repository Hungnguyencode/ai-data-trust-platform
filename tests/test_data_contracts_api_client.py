from __future__ import annotations

from typing import Any

import pytest
import requests

import app.services.data_contracts_api as data_contracts_api


class FakeResponse:
    def __init__(
        self,
        payload: Any,
    ):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self.payload


def test_load_contract_history_uses_data_contracts_api(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "catalog_id": 7,
                "count": 1,
                "items": [
                    {
                        "contract_id": 11,
                        "contract_version": 1,
                    }
                ],
            }
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "get",
        fake_get,
    )

    result = data_contracts_api.load_contract_history(
        7,
    )

    assert result == {
        "catalog_id": 7,
        "count": 1,
        "items": [
            {
                "contract_id": 11,
                "contract_version": 1,
            }
        ],
    }

    assert captured == {
        "url": (
            f"{data_contracts_api.DATA_CONTRACTS_URL}"
            "/catalog/7"
        ),
        "timeout": 10,
    }


def test_load_active_contract_returns_none_for_404(
    monkeypatch: pytest.MonkeyPatch,
):
    class NotFoundResponse(FakeResponse):
        status_code = 404

    def fake_get(
        url: str,
        *,
        timeout: int,
    ) -> NotFoundResponse:
        del url
        del timeout

        return NotFoundResponse(
            {},
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "get",
        fake_get,
    )

    assert (
        data_contracts_api.load_active_contract(
            7,
        )
        is None
    )


def test_load_active_contract_uses_active_contract_api(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    class ActiveResponse(FakeResponse):
        status_code = 200

    def fake_get(
        url: str,
        *,
        timeout: int,
    ) -> ActiveResponse:
        captured["url"] = url
        captured["timeout"] = timeout

        return ActiveResponse(
            {
                "contract_id": 11,
                "catalog_id": 7,
                "is_active": True,
            }
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "get",
        fake_get,
    )

    result = data_contracts_api.load_active_contract(
        7,
    )

    assert result == {
        "contract_id": 11,
        "catalog_id": 7,
        "is_active": True,
    }

    assert captured == {
        "url": (
            f"{data_contracts_api.DATA_CONTRACTS_URL}"
            "/catalog/7/active"
        ),
        "timeout": 10,
    }


def test_activate_contract_uses_activate_api(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "contract_id": 11,
                "is_active": True,
            }
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "post",
        fake_post,
    )

    result = data_contracts_api.activate_contract(
        11,
    )

    assert result == {
        "contract_id": 11,
        "is_active": True,
    }

    assert captured == {
        "url": (
            f"{data_contracts_api.DATA_CONTRACTS_URL}"
            "/11/activate"
        ),
        "timeout": 10,
    }


def test_create_contract_posts_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "contract_id": 12,
                **json,
            }
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "post",
        fake_post,
    )

    payload = {
        "catalog_id": 7,
        "contract_name": "customers",
        "enforcement_mode": "STRICT",
        "columns": [],
    }

    result = data_contracts_api.create_contract(
        payload,
    )

    assert result == {
        "contract_id": 12,
        **payload,
    }

    assert captured == {
        "url": data_contracts_api.DATA_CONTRACTS_URL,
        "json": payload,
        "timeout": 10,
    }


def test_data_contracts_api_wraps_history_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_get(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        del url
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        data_contracts_api.DataContractsApiError,
        match="Unable to load Data Contract History",
    ):
        data_contracts_api.load_contract_history(
            7,
        )


def test_load_active_contract_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_get(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        del url
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "get",
        fail_get,
    )

    with pytest.raises(
        data_contracts_api.DataContractsApiError,
        match="Unable to load Active Data Contract",
    ):
        data_contracts_api.load_active_contract(
            7,
        )


def test_activate_contract_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_post(
        url: str,
        *,
        timeout: int,
    ) -> FakeResponse:
        del url
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "post",
        fail_post,
    )

    with pytest.raises(
        data_contracts_api.DataContractsApiError,
        match="Unable to activate Data Contract",
    ):
        data_contracts_api.activate_contract(
            11,
        )


def test_create_contract_wraps_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_post(
        url: str,
        *,
        json: dict[str, Any],
        timeout: int,
    ) -> FakeResponse:
        del url
        del json
        del timeout

        raise requests.ConnectionError(
            "connection failed"
        )

    monkeypatch.setattr(
        data_contracts_api.requests,
        "post",
        fail_post,
    )

    with pytest.raises(
        data_contracts_api.DataContractsApiError,
        match="Unable to create Data Contract",
    ):
        data_contracts_api.create_contract(
            {
                "catalog_id": 7,
                "contract_name": "customers",
                "enforcement_mode": "STRICT",
                "columns": [],
            }
        )