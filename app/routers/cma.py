from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.comp_sale import CompSale
from app.models.comp_rental import CompRental
from app.schemas.cma import CMAResponse

router = APIRouter(prefix="/cma", tags=["cma"])


def _build_cma(db: Session, property_id: int) -> CMAResponse:
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    sales = (
        db.query(CompSale)
        .filter(CompSale.property_id == property_id)
        .order_by(CompSale.similarity_score.desc().nullslast())
        .limit(10)
        .all()
    )
    rentals = (
        db.query(CompRental)
        .filter(CompRental.property_id == property_id)
        .limit(10)
        .all()
    )

    sale_prices = [s.sold_price for s in sales if s.sold_price]
    avg_price = sum(sale_prices) / len(sale_prices) if sale_prices else None
    sorted_prices = sorted(sale_prices)
    median_price = sorted_prices[len(sorted_prices) // 2] if sorted_prices else None

    sqft_prices = []
    for s in sales:
        if s.sold_price and s.sqft and s.sqft > 0:
            sqft_prices.append(s.sold_price / s.sqft)
    avg_ppsf = sum(sqft_prices) / len(sqft_prices) if sqft_prices else None

    low = min(sale_prices) if sale_prices else None
    high = max(sale_prices) if sale_prices else None

    comp_sales_data = [
        {
            "address": s.address,
            "sold_price": s.sold_price,
            "sold_date": str(s.sold_date) if s.sold_date else None,
            "sqft": s.sqft,
            "bedrooms": s.beds,
            "bathrooms": s.baths,
            "similarity_score": s.similarity_score,
        }
        for s in sales
    ]

    comp_rentals_data = [
        {
            "address": r.address,
            "rent": r.rent,
            "sqft": r.sqft,
            "bedrooms": r.beds,
            "bathrooms": r.baths,
        }
        for r in rentals
    ]

    voice_parts = [f"CMA for {prop.address}."]
    if avg_price:
        voice_parts.append(f"Average comp price is ${avg_price:,.0f}.")
    if len(sale_prices) > 0:
        voice_parts.append(f"Based on {len(sale_prices)} comparable sales.")

    return CMAResponse(
        property_id=property_id,
        address=prop.address,
        suggested_price_low=low,
        suggested_price_high=high,
        average_comp_price=avg_price,
        median_comp_price=median_price,
        price_per_sqft=avg_ppsf,
        comparable_sales=comp_sales_data,
        comparable_rentals=comp_rentals_data,
        market_trends={},
        ai_analysis="",
        voice_summary=" ".join(voice_parts),
    )


@router.post("/property/{property_id}/generate", response_model=CMAResponse)
def generate_cma(property_id: int, db: Session = Depends(get_db)):
    return _build_cma(db, property_id)


@router.get("/property/{property_id}", response_model=CMAResponse)
def get_cma(property_id: int, db: Session = Depends(get_db)):
    return _build_cma(db, property_id)
