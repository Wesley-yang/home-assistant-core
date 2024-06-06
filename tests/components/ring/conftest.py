"""Configuration for Ring tests."""

import re
from unittest.mock import AsyncMock, Mock, patch

import pytest
import requests_mock
from typing_extensions import Generator

from homeassistant.components.ring import DOMAIN
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.components.light.conftest import mock_light_profiles  # noqa: F401


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.ring.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_ring_auth():
    """Mock ring_doorbell.Auth."""
    with patch(
        "homeassistant.components.ring.config_flow.Auth", autospec=True
    ) as mock_ring_auth:
        mock_ring_auth.return_value.fetch_token.return_value = {
            "access_token": "mock-token"
        }
        yield mock_ring_auth.return_value


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock ConfigEntry."""
    return MockConfigEntry(
        title="Ring",
        domain=DOMAIN,
        data={
            CONF_USERNAME: "foo@bar.com",
            "token": {"access_token": "mock-token"},
        },
        unique_id="foo@bar.com",
    )


@pytest.fixture
async def mock_added_config_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_ring_auth: Mock,
) -> MockConfigEntry:
    """Mock ConfigEntry that's been added to HA."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert DOMAIN in hass.config_entries.async_domains()
    return mock_config_entry


@pytest.fixture(name="requests_mock")
def requests_mock_fixture():
    """Fixture to provide a requests mocker."""
    with requests_mock.mock() as mock:
        # Note all devices have an id of 987652, but a different device_id.
        # the device_id is used as our unique_id, but the id is what is sent
        # to the APIs, which is why every mock uses that id.

        # Mocks the response for authenticating
        mock.post(
            "https://oauth.ring.com/oauth/token",
            text=load_fixture("oauth.json", "ring"),
        )
        # Mocks the response for getting the login session
        mock.post(
            "https://api.ring.com/clients_api/session",
            text=load_fixture("session.json", "ring"),
        )
        # Mocks the response for getting all the devices
        mock.get(
            "https://api.ring.com/clients_api/ring_devices",
            text=load_fixture("devices.json", "ring"),
        )
        mock.get(
            "https://api.ring.com/clients_api/dings/active",
            text=load_fixture("ding_active.json", "ring"),
        )
        # Mocks the response for getting the history of a device
        mock.get(
            re.compile(
                r"https:\/\/api\.ring\.com\/clients_api\/doorbots\/\d+\/history"
            ),
            text=load_fixture("doorbot_history.json", "ring"),
        )
        # Mocks the response for getting the health of a device
        mock.get(
            re.compile(r"https:\/\/api\.ring\.com\/clients_api\/doorbots\/\d+\/health"),
            text=load_fixture("doorboot_health_attrs.json", "ring"),
        )
        # Mocks the response for getting a chimes health
        mock.get(
            re.compile(r"https:\/\/api\.ring\.com\/clients_api\/chimes\/\d+\/health"),
            text=load_fixture("chime_health_attrs.json", "ring"),
        )
        mock.get(
            re.compile(
                r"https:\/\/api\.ring\.com\/clients_api\/dings\/\d+\/share/play"
            ),
            status_code=200,
            json={"url": "http://127.0.0.1/foo"},
        )
        mock.get(
            "https://api.ring.com/groups/v1/locations/mock-location-id/groups",
            text=load_fixture("groups.json", "ring"),
        )
        # Mocks the response for getting the history of the intercom
        mock.get(
            "https://api.ring.com/clients_api/doorbots/185036587/history",
            text=load_fixture("intercom_history.json", "ring"),
        )
        # Mocks the response for setting properties in settings (i.e. motion_detection)
        mock.patch(
            re.compile(
                r"https:\/\/api\.ring\.com\/devices\/v1\/devices\/\d+\/settings"
            ),
            text="ok",
        )
        # Mocks the open door command for intercom devices
        mock.put(
            "https://api.ring.com/commands/v1/devices/185036587/device_rpc",
            status_code=200,
            text="{}",
        )
        # Mocks the response for getting the history of the intercom
        mock.get(
            "https://api.ring.com/clients_api/doorbots/185036587/history",
            text=load_fixture("intercom_history.json", "ring"),
        )
        yield mock
