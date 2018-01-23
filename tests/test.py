import hodl
import pytest
from tests.utils import create_parser
import configparser as cp

def test_binance_convert_crypto():
    """Tests the output of binance_convert_crypto"""
    out = hodl.binance_convert_crypto(frm="LTC", to="BTC")
    assert "1 LTC =" in out
    assert "BTC" in out
    # test HTTPError handling
    out = hodl.binance_convert_crypto(frm="ABC", to="DEF")
    assert "[*] error, check you are using " \
           "correct crypto symbols" in out

def test_coinbase_convert_crypto():
    """Tests the output of coinbase_convert_crypto"""
    out = hodl.coinbase_convert_crypto(frm="LTC", to="BTC")
    assert "1 LTC =" in out
    assert "BTC" in out
    # test HTTPError handling
    out = hodl.coinbase_convert_crypto(frm="ABC", to="DEF")
    assert "[*] error, check you are using " \
           "correct crypto symbols" in out

def test_get_price():
    """Tests the output of get_price()"""
    out = hodl.get_price(crypto="BTC", fiat="USD")
    assert "1 BTC =" in out
    assert "USD" in out
    # test HTTPError handling
    out = hodl.get_price(crypto="ABC")
    assert "[*] error, check you are using " \
           "correct crypto and fiat symbols" in out


def test_get_majors():
    """Tests the output of get_majors()"""
    out = hodl.get_majors(fiat="USD")
    assert "1 BTC =" and "USD" in out[0]
    assert "1 BCH =" and "USD" in out[1]
    assert "1 ETH =" and "USD" in out[2]
    assert "1 LTC =" and "USD" in out[3]


def test_set_fiat():
    """Tests the output and behavior of set_fiat()"""
    config = cp.ConfigParser()
    config.read('../hodl/conf/config.ini')
    backup = config.get("currency", "FIAT")
    out = hodl.set_fiat(fiat="CHF")
    config.read('../hodl/conf/config.ini')
    assert "[*] CHF configured as standard fiat" in out
    assert config.get("currency", "FIAT") == "CHF"
    # return to previous settings and test
    hodl.set_fiat(fiat=backup)
    config.read('../hodl/conf/config.ini')
    assert config.get("currency", "FIAT") == backup


def test_record_data(capfd):
    """Tests the behaviour of record_data()"""
    config = cp.ConfigParser()
    config.read('../hodl/conf/config.ini')
    # get previous config value for readings section
    previous_amount = config.get("readings", "btc")
    test_amount = float(previous_amount) + 100
    # set new value for testing purposes
    hodl.record_data("readings", "btc", str(test_amount))
    config.read('../hodl/conf/config.ini')
    assert config.get("readings", "btc") == str(test_amount)
    # return to previous settings and test
    hodl.record_data("readings", "btc", previous_amount)
    config.read('../hodl/conf/config.ini')
    assert config.get("readings", "btc") == previous_amount
    # get previous config value for portfolio section
    previous_amount = config.get("portfolio", "btc")
    test_amount = float(previous_amount) + 100
    # set new value for testing purposes
    hodl.record_data("portfolio", "btc", test_amount)
    out, err = capfd.readouterr()
    assert "[*] BTC portfolio value set at {} coins".format(test_amount) in out
    config.read('../hodl/conf/config.ini')
    assert config.get("portfolio", "btc") == str(test_amount)
    # return to previous settings and test
    hodl.record_data("portfolio", "btc", previous_amount)
    config.read('../hodl/conf/config.ini')
    assert config.get("portfolio", "btc") == previous_amount
    # test exception handling
    hodl.record_data("portfolio", "btc", "test")
    out, err = capfd.readouterr()
    assert "HODL: error: invalid choice: test (please supply a number)" in out
    hodl.record_data("portfolio", "btc", -1)
    out, err = capfd.readouterr()
    assert "HODL: error: invalid choice: -1 (please supply a positive number)" in out


def test_print_portfolio_value(capfd):
    config = cp.ConfigParser()
    config.read('../hodl/conf/config.ini')
    holding = float(config.get("portfolio", "btc")) * float(config.get("readings", "btc"))
    test_statement = "[*] {} portfolio value: ".format("BTC") + "{0:.2f} USD\n".format(holding)
    hodl.print_portfolio_value("btc")
    out, err = capfd.readouterr()
    assert test_statement == out


def test_print_report(capfd):
    """Tests behavious and output of print_report()"""
    config = cp.ConfigParser()
    config.read('../hodl/conf/config.ini')
    original_amount = config.get("readings", "btc")
    # set testing base amount
    config.set("readings", "btc", str(0))
    with open('../hodl/conf/config.ini', 'w') as configfile:
        config.write(configfile)
    # get previous config value
    base_amount = config.get("readings", "btc")
    test_amount = float(base_amount) + 100
    # set new value for testing purposes
    hodl.record_data("readings", "btc", str(test_amount))
    config.read('../hodl/conf/config.ini')
    assert config.get("readings", "btc") == str(test_amount)
    # test no change report
    hodl.print_report("1 BTC = 100 USD", alignment=1)
    out, err = capfd.readouterr()
    print(out)
    assert "no change" in out
    # test increase report
    hodl.print_report("1 BTC = 120 USD", alignment=1)
    out, err = capfd.readouterr()
    assert "increase" in out
    # test decrease report
    hodl.print_report("1 BTC = 80 USD", alignment=1)
    out, err = capfd.readouterr()
    assert "decrease" in out
    # return to previous settings and test
    hodl.record_data("readings", "btc", original_amount)
    config.read('../hodl/conf/config.ini')
    assert config.get("readings", "btc") == original_amount


def test_main():
    """Tests the output and behaviour of test_main()"""
    parser = create_parser()
    args = parser.parse_args(['-c', 'ltc'])
    assert args.crypto == 'ltc'
    args = parser.parse_args(['-f', 'GBP'])
    assert args.fiat == 'GBP'
    args = parser.parse_args(['-sf', 'USD'])
    assert args.set_fiat == 'USD'
    args = parser.parse_args(['-cp', 'ltc', '2'])
    assert args.configure_portfolio[0] == 'ltc'
    assert args.configure_portfolio[1] == "2"
    # test incorrect values
    with pytest.raises(ValueError):
        parser.parse_args(['-f', 'fake_code'])
    with pytest.raises(ValueError):
        parser.parse_args(['-sf', 'fake_code'])
    with pytest.raises(ValueError):
        parser.parse_args(['-c', 'fake_code'])
    with pytest.raises(ValueError):
        parser.parse_args(["-sf", "USD", "-f", "USD"])
