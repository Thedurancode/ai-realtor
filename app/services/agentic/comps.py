from datetime import date


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(value, max_value))


def distance_proxy_mi(
    target_zip: str | None,
    candidate_zip: str | None,
    target_city: str | None,
    candidate_city: str | None,
    target_state: str | None,
    candidate_state: str | None,
) -> float:
    if target_zip and candidate_zip and target_zip == candidate_zip:
        return 0.5
    if target_city and candidate_city and target_city.lower() == candidate_city.lower() and target_state and candidate_state and target_state.lower() == candidate_state.lower():
        return 1.5
    if target_state and candidate_state and target_state.lower() == candidate_state.lower():
        return 4.0
    return 50.0


def recency_months(value: date | None, today: date | None = None) -> int:
    if value is None:
        return 999
    today = today or date.today()
    return (today.year - value.year) * 12 + (today.month - value.month)


def passes_hard_filters(
    *,
    distance_mi: float,
    radius_mi: float,
    sale_or_list_date: date | None,
    max_recency_months: int,
    target_sqft: int | None,
    candidate_sqft: int | None,
    target_beds: int | None,
    candidate_beds: int | None,
    target_baths: float | None,
    candidate_baths: float | None,
) -> bool:
    if distance_mi > radius_mi:
        return False

    if recency_months(sale_or_list_date) > max_recency_months:
        return False

    if target_sqft and candidate_sqft:
        lower = target_sqft * 0.75
        upper = target_sqft * 1.25
        if candidate_sqft < lower or candidate_sqft > upper:
            return False

    if target_beds is not None and candidate_beds is not None and abs(target_beds - candidate_beds) > 1:
        return False

    if target_baths is not None and candidate_baths is not None and abs(target_baths - candidate_baths) > 1.0:
        return False

    return True


def similarity_score(
    *,
    distance_mi: float,
    radius_mi: float,
    target_sqft: int | None,
    candidate_sqft: int | None,
    target_beds: int | None,
    candidate_beds: int | None,
    target_baths: float | None,
    candidate_baths: float | None,
    sale_or_list_date: date | None,
) -> float:
    # Weighted deterministic score.
    distance_component = clamp(1.0 - (distance_mi / max(radius_mi, 0.1)))

    sqft_component = 0.5
    if target_sqft and candidate_sqft:
        sqft_component = clamp(1.0 - abs(candidate_sqft - target_sqft) / max(target_sqft, 1))

    bed_component = 0.5
    if target_beds is not None and candidate_beds is not None:
        diff = abs(target_beds - candidate_beds)
        bed_component = 1.0 if diff == 0 else 0.6 if diff == 1 else 0.0

    bath_component = 0.5
    if target_baths is not None and candidate_baths is not None:
        diff = abs(target_baths - candidate_baths)
        bath_component = 1.0 if diff == 0 else 0.6 if diff <= 1 else 0.0

    months = recency_months(sale_or_list_date)
    recency_component = clamp(1.0 - (months / 12.0))

    bed_bath_component = (bed_component + bath_component) / 2.0

    score = (
        (0.35 * distance_component)
        + (0.30 * sqft_component)
        + (0.20 * bed_bath_component)
        + (0.15 * recency_component)
    )

    return round(clamp(score), 6)
