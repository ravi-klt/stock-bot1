import json

import pytest

from config import (
    ConfigurationError,
    load_watchlist,
)


def test_valid_watchlist_loads(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": [
                    "MSFT",
                    "FTNT",
                ]
            }
        ),
        encoding="utf-8",
    )

    result = load_watchlist(
        watchlist_file
    )

    assert result == [
        "MSFT",
        "FTNT",
    ]


def test_watchlist_normalizes_tickers(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": [
                    " msft ",
                    "ftnt",
                    "MSFT",
                ]
            }
        ),
        encoding="utf-8",
    )

    result = load_watchlist(
        watchlist_file
    )

    assert result == [
        "MSFT",
        "FTNT",
    ]


def test_dynamic_watchlist_reload(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": [
                    "MSFT"
                ]
            }
        ),
        encoding="utf-8",
    )

    first_result = load_watchlist(
        watchlist_file
    )

    assert first_result == [
        "MSFT"
    ]

    # Simulate user editing watchlist.json
    # while the application is running.
    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": [
                    "MSFT",
                    "AMD",
                ]
            }
        ),
        encoding="utf-8",
    )

    second_result = load_watchlist(
        watchlist_file
    )

    assert second_result == [
        "MSFT",
        "AMD",
    ]


def test_invalid_json_fails(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError
    ):

        load_watchlist(
            watchlist_file
        )


def test_tickers_must_be_list(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": "MSFT"
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError
    ):

        load_watchlist(
            watchlist_file
        )


def test_ticker_must_be_string(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": [
                    "MSFT",
                    123,
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError
    ):

        load_watchlist(
            watchlist_file
        )


def test_empty_ticker_fails(
    tmp_path,
):

    watchlist_file = (
        tmp_path / "watchlist.json"
    )

    watchlist_file.write_text(
        json.dumps(
            {
                "tickers": [
                    "MSFT",
                    "   ",
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError
    ):

        load_watchlist(
            watchlist_file
        )