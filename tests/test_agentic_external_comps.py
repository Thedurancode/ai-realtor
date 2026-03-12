from app.services.agentic.workers.comps_workers import extract_comp_entries_from_text


def test_extract_external_sale_entries_from_text():
    text = (
        "123 Main St, Newark, NJ 07102 $450,000 3 beds 2 baths 1,500 sqft "
        "listed Mar 1, 2026 "
        "124 Main St, Newark, NJ 07102 $430,000 3 beds 2 baths 1,450 sqft listed Feb 12, 2026"
    )

    rows = extract_comp_entries_from_text(
        text=text,
        comp_type="sale",
        source_url="https://example.com/sales",
        published_date="2026-03-15T00:00:00.000Z",
    )

    assert len(rows) >= 2
    assert rows[0]["price"] >= 430000
    assert rows[0]["city"] == "Newark"


def test_extract_external_rental_entries_from_text():
    text = (
        "555 Elm St, Newark, NJ 07103 $2,400 /mo 2 beds 1 baths 900 sqft 15 days on Zillow "
        "556 Elm St, Newark, NJ 07103 $2,250 /mo 2 beds 1 baths 880 sqft 9 days on Zillow"
    )

    rows = extract_comp_entries_from_text(
        text=text,
        comp_type="rental",
        source_url="https://example.com/rentals",
        published_date="2026-03-15T00:00:00.000Z",
    )

    assert len(rows) >= 2
    assert rows[0]["price"] <= 3000
    assert rows[0]["zip_code"] == "07103"
