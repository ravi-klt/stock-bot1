import os

import pytest

from broker.ibkr_client import (
    IBKRClient,
    build_us_stock_contract,
)

from config import load_config

from data.market_data import (
    MarketDataService,
)


def test_build_us_stock_contract():

    contract = (
        build_us_stock_contract(
            " msft "
        )
    )

    assert contract.symbol == "MSFT"

    assert contract.secType == "STK"

    assert contract.exchange == "SMART"

    assert contract.currency == "USD"


def test_empty_ticker_is_rejected():

    with pytest.raises(
        ValueError
    ):
        build_us_stock_contract(
            "   "
        )


@pytest.mark.skipif(
    os.getenv(
        "RUN_IBKR_INTEGRATION"
    ) != "1",
    reason=(
        "Real IBKR integration test "
        "is disabled."
    ),
)
def test_real_ibkr_read_only_basics():

    config = load_config()

    if config.ibkr_port is None:
        pytest.fail(
            "IBKR_PORT is required "
            "for integration testing."
        )

    if config.ibkr_client_id is None:
        pytest.fail(
            "IBKR_CLIENT_ID is required "
            "for integration testing."
        )

    client = IBKRClient(
        host=config.ibkr_host,
        port=config.ibkr_port,
        client_id=(
            config.ibkr_client_id
        ),
    )

    try:
        client.connect()

        assert client.is_connected

        contract = (
            client.resolve_us_stock(
                "MSFT"
            )
        )

        assert (
            contract.symbol
            == "MSFT"
        )

        assert (
            contract.secType
            == "STK"
        )

        assert (
            contract.currency
            == "USD"
        )

        assert contract.conId > 0

        positions = (
            client.read_positions()
        )

        assert isinstance(
            positions,
            list,
        )

        market_data = (
            MarketDataService(
                client
            )
        )

        bars = (
            market_data
            .get_sample_daily_bars(
                ticker="MSFT",
                duration="1 M",
            )
        )

        assert len(bars) > 0

        for bar in bars[-5:]:

            assert bar.open > 0
            assert bar.high > 0
            assert bar.low > 0
            assert bar.close > 0

            assert (
                bar.high
                >= bar.open
            )

            assert (
                bar.high
                >= bar.close
            )

            assert (
                bar.low
                <= bar.open
            )

            assert (
                bar.low
                <= bar.close
            )

            assert bar.volume >= 0

    finally:
        client.disconnect()