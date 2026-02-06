from datetime import date

from app.services.agentic.comps import (
    distance_proxy_mi,
    passes_hard_filters,
    similarity_score,
)


def test_distance_proxy_prefers_same_zip():
    same_zip = distance_proxy_mi("07102", "07102", "Newark", "Newark", "NJ", "NJ")
    same_city = distance_proxy_mi("07102", "07103", "Newark", "Newark", "NJ", "NJ")
    assert same_zip < same_city


def test_hard_filter_rejects_old_comp():
    allowed = passes_hard_filters(
        distance_mi=0.5,
        radius_mi=1.0,
        sale_or_list_date=date.today().replace(day=1),
        max_recency_months=12,
        target_sqft=1500,
        candidate_sqft=1450,
        target_beds=3,
        candidate_beds=3,
        target_baths=2.0,
        candidate_baths=2.0,
    )
    rejected = passes_hard_filters(
        distance_mi=0.5,
        radius_mi=1.0,
        sale_or_list_date=date(2020, 1, 1),
        max_recency_months=12,
        target_sqft=1500,
        candidate_sqft=1450,
        target_beds=3,
        candidate_beds=3,
        target_baths=2.0,
        candidate_baths=2.0,
    )
    assert allowed is True
    assert rejected is False


def test_similarity_score_monotonic_for_distance():
    closer = similarity_score(
        distance_mi=0.5,
        radius_mi=1.0,
        target_sqft=1500,
        candidate_sqft=1500,
        target_beds=3,
        candidate_beds=3,
        target_baths=2.0,
        candidate_baths=2.0,
        sale_or_list_date=date.today(),
    )
    farther = similarity_score(
        distance_mi=0.9,
        radius_mi=1.0,
        target_sqft=1500,
        candidate_sqft=1500,
        target_beds=3,
        candidate_beds=3,
        target_baths=2.0,
        candidate_baths=2.0,
        sale_or_list_date=date.today(),
    )
    assert closer > farther
