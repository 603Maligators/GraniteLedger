import pathlib

from graniteledger.integrations.gmail_intake.parser import parse_csv


def test_parse_csv_variants():
    sample = pathlib.Path('tests/fixtures/sample.csv')
    parsed = parse_csv(sample)
    assert parsed.totals['grand_total'] == 25.00
    assert parsed.lines[0]['qty'] == 2
