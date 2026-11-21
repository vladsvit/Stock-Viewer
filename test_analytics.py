from analytics import compare_returns


def test_compare_returns():
    prices = {
        "stock_a": {"2026-01-01": 100, "2026-01-02": 110},
        "stock_b": {"2026-01-01": 200, "2026-01-02": 190},
    }

    result = compare_returns(prices)

    assert result["stock_a_returns"] == [0.0, 10.0]
    assert result["stock_b_returns"] == [0.0, -5.0]