import pathlib
import pytest

pdfplumber = pytest.importorskip('pdfplumber')

from graniteledger.integrations.gmail_intake.parser import parse_pdf


def test_parse_pdf_extracts_lines_and_totals(tmp_path):
    sample = pathlib.Path('tests/fixtures/sample.pdf')
    parsed = parse_pdf(sample)
    assert parsed.success
    assert parsed.totals['grand_total'] == 25.00
    assert parsed.lines[0]['sku'] == 'COL-1LB'
