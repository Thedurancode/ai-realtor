"""Deal Calculator service — expert-level underwriting for any property.

Supports: wholesale, flip, rental, BRRRR
Includes: financing modeling, line-item expenses, deal scoring (A-F).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from math import pow as fpow
from statistics import mean
from typing import Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.zillow_enrichment import ZillowEnrichment
from app.schemas.deal_calculator import (
    BRRRRDetail,
    DataSources,
    DealCalculatorInput,
    DealCalculatorResponse,
    DealScore,
    ExpenseAssumptions,
    ExpenseBreakdown,
    FeeAssumptions,
    FinancingAssumptions,
    FinancingDetail,
    RehabAssumptions,
    StrategyParams,
    StrategyResult,
)

logger = logging.getLogger(__name__)

REHAB_PER_SQFT = {"light": 15.0, "medium": 35.0, "heavy": 60.0}
REHAB_DEFAULT_TOTAL = {"light": 25_000.0, "medium": 50_000.0, "heavy": 100_000.0}


# ── Data gathering (fallback chains) ─────────────────────────


def _get_arv(
    db: Session, prop: Property, override: float | None
) -> Tuple[float, str]:
    """Return (arv, source_label). Raises ValueError when nothing found."""

    if override is not None:
        return override, "user_override"

    # Agentic underwriting
    try:
        from app.models.agentic_job import AgenticJob, AgenticJobStatus
        from app.models.agentic_property import ResearchProperty
        from app.models.underwriting import Underwriting

        rp = (
            db.query(ResearchProperty)
            .filter(
                or_(
                    ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                    ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                )
            )
            .first()
        )
        if rp:
            job = (
                db.query(AgenticJob)
                .filter(
                    AgenticJob.research_property_id == rp.id,
                    AgenticJob.status == AgenticJobStatus.COMPLETED,
                )
                .order_by(AgenticJob.completed_at.desc())
                .first()
            )
            if job:
                uw = (
                    db.query(Underwriting)
                    .filter(Underwriting.job_id == job.id)
                    .order_by(Underwriting.id.desc())
                    .first()
                )
                if uw and uw.arv_base:
                    return uw.arv_base, "agentic_underwriting"
    except Exception as exc:
        logger.debug("Underwriting lookup skipped: %s", exc)

    # Zillow Zestimate
    ze = (
        db.query(ZillowEnrichment)
        .filter(ZillowEnrichment.property_id == prop.id)
        .first()
    )
    if ze and ze.zestimate:
        return ze.zestimate, "zillow_zestimate"

    # Comp sales average
    try:
        from app.models.agentic_property import ResearchProperty
        from app.models.comp_sale import CompSale

        rp = (
            db.query(ResearchProperty)
            .filter(
                or_(
                    ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                    ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                )
            )
            .first()
        )
        if rp:
            prices = [
                c.sale_price
                for c in db.query(CompSale)
                .filter(CompSale.research_property_id == rp.id)
                .all()
                if c.sale_price
            ]
            if prices:
                return mean(prices), "comp_sales_avg"
    except Exception as exc:
        logger.debug("Comp sales lookup skipped: %s", exc)

    # List price as last resort
    if prop.price:
        return prop.price, "list_price"

    raise ValueError(
        f"No ARV data for property {prop.id}. Enrich with Zillow or run agentic research first."
    )


def _get_rent(
    db: Session, prop: Property, override: float | None
) -> Tuple[float | None, str]:
    """Return (monthly_rent, source_label). None is acceptable."""

    if override is not None:
        return override, "user_override"

    # Agentic underwriting
    try:
        from app.models.agentic_job import AgenticJob, AgenticJobStatus
        from app.models.agentic_property import ResearchProperty
        from app.models.underwriting import Underwriting

        rp = (
            db.query(ResearchProperty)
            .filter(
                or_(
                    ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                    ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                )
            )
            .first()
        )
        if rp:
            job = (
                db.query(AgenticJob)
                .filter(
                    AgenticJob.research_property_id == rp.id,
                    AgenticJob.status == AgenticJobStatus.COMPLETED,
                )
                .order_by(AgenticJob.completed_at.desc())
                .first()
            )
            if job:
                uw = (
                    db.query(Underwriting)
                    .filter(Underwriting.job_id == job.id)
                    .order_by(Underwriting.id.desc())
                    .first()
                )
                if uw and uw.rent_base:
                    return uw.rent_base, "agentic_underwriting"
    except Exception:
        pass

    # Zillow rent Zestimate
    ze = (
        db.query(ZillowEnrichment)
        .filter(ZillowEnrichment.property_id == prop.id)
        .first()
    )
    if ze and ze.rent_zestimate:
        return ze.rent_zestimate, "zillow_rent_zestimate"

    # Comp rentals average
    try:
        from app.models.agentic_property import ResearchProperty
        from app.models.comp_rental import CompRental

        rp = (
            db.query(ResearchProperty)
            .filter(
                or_(
                    ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                    ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                )
            )
            .first()
        )
        if rp:
            rents = [
                c.rent
                for c in db.query(CompRental)
                .filter(CompRental.research_property_id == rp.id)
                .all()
                if c.rent
            ]
            if rents:
                return mean(rents), "comp_rentals_avg"
    except Exception:
        pass

    return None, "not_available"


def _get_sqft(
    db: Session, prop: Property, override: int | None
) -> Tuple[int | None, str]:
    if override is not None:
        return override, "user_override"
    if prop.square_feet:
        return prop.square_feet, "property_data"
    ze = (
        db.query(ZillowEnrichment)
        .filter(ZillowEnrichment.property_id == prop.id)
        .first()
    )
    if ze and ze.living_area:
        return int(ze.living_area), "zillow_enrichment"
    return None, "not_available"


# ── Shared helpers ────────────────────────────────────────────


def _calc_rehab(rehab: RehabAssumptions, sqft: int | None) -> float:
    if rehab.total_cost_override is not None:
        return rehab.total_cost_override
    if sqft:
        return sqft * REHAB_PER_SQFT[rehab.tier]
    return REHAB_DEFAULT_TOTAL[rehab.tier]


def _monthly_mortgage(principal: float, annual_rate: float, term_years: int) -> float:
    """Standard amortized monthly payment (P&I)."""
    if principal <= 0 or annual_rate <= 0 or term_years <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = term_years * 12
    return principal * (r * fpow(1 + r, n)) / (fpow(1 + r, n) - 1)


def _calc_financing(
    purchase_price: float, fin: FinancingAssumptions
) -> FinancingDetail | None:
    """Build financing detail. Returns None when paying cash."""
    if not fin.use_financing or purchase_price <= 0:
        return None
    down = purchase_price * fin.down_payment_pct
    loan = purchase_price - down
    pmt = _monthly_mortgage(loan, fin.interest_rate, fin.loan_term_years)
    return FinancingDetail(
        loan_amount=round(loan, 2),
        down_payment=round(down, 2),
        monthly_payment=round(pmt, 2),
        interest_rate=fin.interest_rate,
        loan_term_years=fin.loan_term_years,
        loan_type=fin.loan_type,
    )


def _calc_expense_breakdown(
    monthly_rent: float | None,
    exp: ExpenseAssumptions,
    debt_service: float,
) -> ExpenseBreakdown | None:
    """Line-item monthly expenses for rental/BRRRR strategies."""
    if monthly_rent is None:
        return None
    pm = monthly_rent * exp.property_management_pct
    vac = monthly_rent * exp.vacancy_pct
    capex = monthly_rent * exp.capex_reserve_pct
    repairs = monthly_rent * exp.repairs_pct
    total = pm + vac + capex + repairs + exp.insurance_monthly + exp.property_tax_monthly + exp.hoa_monthly + debt_service
    return ExpenseBreakdown(
        property_management=round(pm, 2),
        vacancy_reserve=round(vac, 2),
        capex_reserve=round(capex, 2),
        repairs_reserve=round(repairs, 2),
        insurance=exp.insurance_monthly,
        property_tax=exp.property_tax_monthly,
        hoa=exp.hoa_monthly,
        debt_service=round(debt_service, 2),
        total_monthly=round(total, 2),
    )


def _holding_costs(fees: FeeAssumptions) -> float:
    return fees.holding_cost_per_month * fees.holding_months


# ── Deal scoring ──────────────────────────────────────────────


def _score_strategy(result: StrategyResult) -> DealScore:
    """Score 0-100 and grade A-F based on multiple factors."""
    score = 50  # start neutral
    factors: list[str] = []

    # ── Positive factors ──
    if result.offer_price > 0:
        factors.append("Positive offer price")
    else:
        score -= 30
        factors.append("Negative offer price — deal doesn't work")

    if result.strategy == "wholesale":
        if result.net_profit and result.net_profit >= 10_000:
            score += 15
            factors.append(f"${result.net_profit:,.0f} assignment fee")
        elif result.net_profit and result.net_profit >= 5_000:
            score += 5
            factors.append(f"${result.net_profit:,.0f} assignment fee (thin)")

    if result.strategy == "flip":
        if result.roi_percent is not None:
            if result.roi_percent >= 25:
                score += 25
                factors.append(f"{result.roi_percent:.1f}% ROI — excellent")
            elif result.roi_percent >= 15:
                score += 15
                factors.append(f"{result.roi_percent:.1f}% ROI — good")
            elif result.roi_percent >= 10:
                score += 5
                factors.append(f"{result.roi_percent:.1f}% ROI — marginal")
            else:
                score -= 10
                factors.append(f"{result.roi_percent:.1f}% ROI — weak")
        if result.net_profit and result.net_profit >= 50_000:
            score += 10
            factors.append(f"${result.net_profit:,.0f} net profit")

    if result.strategy in ("rental", "brrrr"):
        if result.monthly_cash_flow is not None:
            if result.monthly_cash_flow >= 400:
                score += 20
                factors.append(f"${result.monthly_cash_flow:,.0f}/mo cash flow — strong")
            elif result.monthly_cash_flow >= 200:
                score += 10
                factors.append(f"${result.monthly_cash_flow:,.0f}/mo cash flow — decent")
            elif result.monthly_cash_flow > 0:
                score += 2
                factors.append(f"${result.monthly_cash_flow:,.0f}/mo cash flow — thin")
            else:
                score -= 15
                factors.append(f"Negative cash flow: ${result.monthly_cash_flow:,.0f}/mo")
        if result.cap_rate is not None:
            if result.cap_rate >= 8:
                score += 10
                factors.append(f"{result.cap_rate:.1f}% cap rate — excellent")
            elif result.cap_rate >= 5:
                score += 5
                factors.append(f"{result.cap_rate:.1f}% cap rate — average")
            else:
                score -= 5
                factors.append(f"{result.cap_rate:.1f}% cap rate — below average")
        if result.cash_on_cash_return is not None and result.cash_on_cash_return >= 12:
            score += 10
            factors.append(f"{result.cash_on_cash_return:.1f}% CoC return — strong")

    if result.strategy == "brrrr" and result.brrrr:
        if result.brrrr.infinite_return:
            score += 20
            factors.append("Infinite return — all cash recovered at refi")
        elif result.brrrr.cash_left_in_deal < result.brrrr.initial_cash_in * 0.25:
            score += 10
            factors.append("Recovered >75% of cash at refi")

    # Clamp 0-100
    score = max(0, min(100, score))

    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    return DealScore(score=score, grade=grade, factors=factors)


# ── Strategy calculators ──────────────────────────────────────


def _calc_wholesale(
    arv: float,
    rehab_cost: float,
    fees: FeeAssumptions,
    params: StrategyParams,
) -> StrategyResult:
    holding = _holding_costs(fees)
    total_fees = fees.closing_cost + holding + fees.assignment_fee + fees.misc_fee
    offer = (arv * params.wholesale_arv_pct) - rehab_cost - total_fees
    net_profit = fees.assignment_fee

    result = StrategyResult(
        strategy="wholesale",
        arv=arv,
        rehab_cost=round(rehab_cost, 2),
        total_fees=round(total_fees, 2),
        offer_price=round(offer, 2),
        total_investment=0,
        gross_profit=round(net_profit, 2),
        net_profit=round(net_profit, 2),
        roi_percent=None,
    )
    result.deal_score = _score_strategy(result)
    return result


def _calc_flip(
    arv: float,
    rehab_cost: float,
    fees: FeeAssumptions,
    params: StrategyParams,
    fin: FinancingAssumptions,
) -> StrategyResult:
    holding = _holding_costs(fees)
    total_fees = fees.closing_cost + holding + fees.misc_fee
    offer = (arv * (1.0 - params.flip_target_margin)) - rehab_cost - total_fees
    offer = max(offer, 0)

    financing = _calc_financing(offer, fin)
    if financing:
        # With financing: cash in = down payment + rehab + fees + interest during hold
        interest_during_hold = financing.monthly_payment * fees.holding_months
        total_investment = financing.down_payment + rehab_cost + total_fees + interest_during_hold
        # Profit accounts for loan payoff
        net_profit = arv - offer - rehab_cost - total_fees - interest_during_hold
    else:
        total_investment = offer + rehab_cost + total_fees
        net_profit = arv - total_investment

    roi = (net_profit / total_investment * 100) if total_investment > 0 else None
    equity_capture = arv - offer

    result = StrategyResult(
        strategy="flip",
        arv=arv,
        rehab_cost=round(rehab_cost, 2),
        total_fees=round(total_fees, 2),
        offer_price=round(offer, 2),
        total_investment=round(total_investment, 2),
        gross_profit=round(arv - offer, 2),
        net_profit=round(net_profit, 2),
        roi_percent=round(roi, 1) if roi is not None else None,
        equity_capture=round(equity_capture, 2),
        holding_costs=round(holding, 2),
        financing=financing,
    )
    result.deal_score = _score_strategy(result)
    return result


def _calc_rental(
    arv: float,
    monthly_rent: float | None,
    rehab_cost: float,
    fees: FeeAssumptions,
    params: StrategyParams,
    fin: FinancingAssumptions,
    exp: ExpenseAssumptions,
) -> StrategyResult:
    holding = _holding_costs(fees)
    total_fees = fees.closing_cost + holding + fees.misc_fee

    # Offer price
    arv_cap = arv * params.rental_arv_pct
    if monthly_rent is not None:
        rent_cap = monthly_rent * params.rental_rent_multiplier
        offer = min(arv_cap, rent_cap) - rehab_cost - total_fees
    else:
        offer = arv_cap - rehab_cost - total_fees
    offer = max(offer, 0)

    financing = _calc_financing(offer, fin)
    debt_service = financing.monthly_payment if financing else 0.0
    expense_bkdn = _calc_expense_breakdown(monthly_rent, exp, debt_service)

    if financing:
        total_investment = financing.down_payment + rehab_cost + total_fees
    else:
        total_investment = offer + rehab_cost + total_fees

    monthly_cash_flow = None
    annual_cash_flow = None
    coc = None
    cap_rate = None
    break_even = None
    net_profit = None

    if monthly_rent is not None and expense_bkdn is not None:
        monthly_cash_flow = round(monthly_rent - expense_bkdn.total_monthly, 2)
        annual_cash_flow = round(monthly_cash_flow * 12, 2)
        net_profit = annual_cash_flow
        if total_investment > 0:
            coc = round(annual_cash_flow / total_investment * 100, 1)
        # Cap rate uses NOI (before debt service)
        noi = (monthly_rent - (expense_bkdn.total_monthly - debt_service)) * 12
        if offer > 0:
            cap_rate = round(noi / offer * 100, 1)
        break_even = round(expense_bkdn.total_monthly, 2)

    result = StrategyResult(
        strategy="rental",
        arv=arv,
        monthly_rent=monthly_rent,
        rehab_cost=round(rehab_cost, 2),
        total_fees=round(total_fees, 2),
        offer_price=round(offer, 2),
        total_investment=round(total_investment, 2),
        gross_profit=round(arv - offer, 2) if offer > 0 else None,
        net_profit=net_profit,
        roi_percent=coc,
        financing=financing,
        expense_breakdown=expense_bkdn,
        monthly_cash_flow=monthly_cash_flow,
        annual_cash_flow=annual_cash_flow,
        cash_on_cash_return=coc,
        cap_rate=cap_rate,
        break_even_rent=break_even,
    )
    result.deal_score = _score_strategy(result)
    return result


def _calc_brrrr(
    arv: float,
    monthly_rent: float | None,
    rehab_cost: float,
    fees: FeeAssumptions,
    params: StrategyParams,
    fin: FinancingAssumptions,
    exp: ExpenseAssumptions,
) -> StrategyResult | None:
    """Buy, Rehab, Rent, Refinance, Repeat."""
    if monthly_rent is None:
        return None

    holding = _holding_costs(fees)
    total_fees = fees.closing_cost + holding + fees.misc_fee

    # Purchase with initial financing (often hard money for BRRRR)
    arv_cap = arv * params.rental_arv_pct
    rent_cap = monthly_rent * params.rental_rent_multiplier
    offer = min(arv_cap, rent_cap) - rehab_cost - total_fees
    offer = max(offer, 0)

    # Initial financing (hard money or cash during rehab)
    initial_fin = _calc_financing(offer, fin)
    if initial_fin:
        initial_cash_in = initial_fin.down_payment + rehab_cost + total_fees
    else:
        initial_cash_in = offer + rehab_cost + total_fees

    # ── Refinance step ──
    refi_loan_amount = arv * params.brrrr_refi_ltv
    refi_monthly = _monthly_mortgage(
        refi_loan_amount, params.brrrr_refi_rate, params.brrrr_refi_term_years
    )

    # Pay off initial loan (if any) from refi proceeds
    initial_loan_balance = initial_fin.loan_amount if initial_fin else 0.0
    cash_back = refi_loan_amount - initial_loan_balance
    cash_left = initial_cash_in - cash_back
    infinite_return = cash_left <= 0

    # Post-refi expense breakdown uses refi debt service
    expense_bkdn = _calc_expense_breakdown(monthly_rent, exp, refi_monthly)
    monthly_cf_post = monthly_rent - expense_bkdn.total_monthly if expense_bkdn else 0.0
    annual_cf_post = monthly_cf_post * 12

    coc_post = None
    if cash_left > 0:
        coc_post = round(annual_cf_post / cash_left * 100, 1)

    brrrr_detail = BRRRRDetail(
        initial_cash_in=round(initial_cash_in, 2),
        refi_loan_amount=round(refi_loan_amount, 2),
        cash_back_at_refi=round(cash_back, 2),
        cash_left_in_deal=round(max(cash_left, 0), 2),
        refi_monthly_payment=round(refi_monthly, 2),
        monthly_cash_flow_post_refi=round(monthly_cf_post, 2),
        annual_cash_flow_post_refi=round(annual_cf_post, 2),
        cash_on_cash_post_refi=coc_post,
        infinite_return=infinite_return,
    )

    # Cap rate (NOI / purchase price, before debt)
    noi = (monthly_rent - (expense_bkdn.total_monthly - refi_monthly)) * 12 if expense_bkdn else 0.0
    cap_rate = round(noi / offer * 100, 1) if offer > 0 else None

    # Total investment = cash left in deal after refi
    total_inv = max(cash_left, 0)

    result = StrategyResult(
        strategy="brrrr",
        arv=arv,
        monthly_rent=monthly_rent,
        rehab_cost=round(rehab_cost, 2),
        total_fees=round(total_fees, 2),
        offer_price=round(offer, 2),
        total_investment=round(total_inv, 2),
        gross_profit=round(arv - offer, 2),
        net_profit=round(annual_cf_post, 2),
        roi_percent=coc_post,
        financing=initial_fin,
        expense_breakdown=expense_bkdn,
        monthly_cash_flow=round(monthly_cf_post, 2),
        annual_cash_flow=round(annual_cf_post, 2),
        cash_on_cash_return=coc_post,
        cap_rate=cap_rate,
        break_even_rent=round(expense_bkdn.total_monthly, 2) if expense_bkdn else None,
        brrrr=brrrr_detail,
    )
    result.deal_score = _score_strategy(result)
    return result


# ── Recommendation ────────────────────────────────────────────


def _recommend(
    wholesale: StrategyResult,
    flip: StrategyResult,
    rental: StrategyResult,
    brrrr: StrategyResult | None,
) -> Tuple[str, str]:
    """Pick best strategy by deal score, break ties by profit."""
    candidates: dict[str, StrategyResult] = {
        "wholesale": wholesale,
        "flip": flip,
        "rental": rental,
    }
    if brrrr:
        candidates["brrrr"] = brrrr

    # Filter to strategies with positive offer price
    viable = {k: v for k, v in candidates.items() if v.offer_price > 0}
    if not viable:
        return "wholesale", "No strategy shows positive numbers at current assumptions."

    best_name = max(
        viable,
        key=lambda k: (viable[k].deal_score.score if viable[k].deal_score else 0, viable[k].net_profit or 0),
    )
    best = viable[best_name]

    reasons = {
        "wholesale": f"Wholesale earns ${best.net_profit:,.0f} assignment fee with zero capital at risk (Grade {best.deal_score.grade}).",
        "flip": f"Flip yields ${best.net_profit:,.0f} profit ({best.roi_percent or 0:.1f}% ROI, Grade {best.deal_score.grade}).",
        "rental": f"Rental generates ${best.monthly_cash_flow or 0:,.0f}/mo cash flow ({best.cash_on_cash_return or 0:.1f}% CoC, Grade {best.deal_score.grade}).",
        "brrrr": (
            f"BRRRR generates ${best.monthly_cash_flow or 0:,.0f}/mo after refi"
            + (" with infinite return — all cash recovered" if best.brrrr and best.brrrr.infinite_return else f" ({best.cash_on_cash_return or 0:.1f}% CoC)")
            + f" (Grade {best.deal_score.grade})."
        ),
    }
    return best_name, reasons.get(best_name, "")


# ── Voice summary ─────────────────────────────────────────────


def _voice_summary(
    address: str,
    recommended: str,
    reason: str,
    wholesale: StrategyResult,
    flip: StrategyResult,
    rental: StrategyResult,
    brrrr: StrategyResult | None,
    arv: float,
    arv_source: str,
    rehab_tier: str,
) -> str:
    parts = [
        f"Deal analysis for {address}.",
        f"ARV ${arv:,.0f} from {arv_source.replace('_', ' ')}. Rehab: {rehab_tier}.",
        f"I recommend {recommended}. {reason}",
        f"Wholesale: ${wholesale.offer_price:,.0f} offer, ${wholesale.net_profit or 0:,.0f} profit, Grade {wholesale.deal_score.grade}." if wholesale.deal_score else "",
        f"Flip: ${flip.offer_price:,.0f} offer, ${flip.net_profit or 0:,.0f} profit, {flip.roi_percent or 0:.1f}% ROI, Grade {flip.deal_score.grade}." if flip.deal_score else "",
    ]
    if rental.monthly_cash_flow is not None and rental.deal_score:
        parts.append(
            f"Rental: ${rental.offer_price:,.0f} offer, ${rental.monthly_cash_flow:,.0f}/mo cash flow, {rental.cap_rate or 0:.1f}% cap rate, Grade {rental.deal_score.grade}."
        )
    if brrrr and brrrr.brrrr and brrrr.deal_score:
        if brrrr.brrrr.infinite_return:
            parts.append(f"BRRRR: ${brrrr.offer_price:,.0f} offer, infinite return, ${brrrr.monthly_cash_flow or 0:,.0f}/mo after refi, Grade {brrrr.deal_score.grade}.")
        else:
            parts.append(f"BRRRR: ${brrrr.offer_price:,.0f} offer, ${brrrr.monthly_cash_flow or 0:,.0f}/mo after refi, Grade {brrrr.deal_score.grade}.")
    return " ".join(p for p in parts if p)


# ── Main entry point ──────────────────────────────────────────


def calculate_deal(
    db: Session, calc_input: DealCalculatorInput
) -> DealCalculatorResponse:
    prop = db.query(Property).filter(Property.id == calc_input.property_id).first()
    if not prop:
        raise ValueError(f"Property {calc_input.property_id} not found")

    address = f"{prop.address}, {prop.city}, {prop.state}"

    # Gather data
    arv, arv_src = _get_arv(db, prop, calc_input.arv_override)
    rent, rent_src = _get_rent(db, prop, calc_input.monthly_rent_override)
    sqft, sqft_src = _get_sqft(db, prop, calc_input.sqft_override)

    rehab_cost = _calc_rehab(calc_input.rehab, sqft)

    # Calculate all strategies
    wholesale = _calc_wholesale(arv, rehab_cost, calc_input.fees, calc_input.strategy_params)
    flip = _calc_flip(arv, rehab_cost, calc_input.fees, calc_input.strategy_params, calc_input.financing)
    rental = _calc_rental(arv, rent, rehab_cost, calc_input.fees, calc_input.strategy_params, calc_input.financing, calc_input.expenses)
    brrrr = _calc_brrrr(arv, rent, rehab_cost, calc_input.fees, calc_input.strategy_params, calc_input.financing, calc_input.expenses)

    recommended, reason = _recommend(wholesale, flip, rental, brrrr)

    voice = _voice_summary(
        address, recommended, reason,
        wholesale, flip, rental, brrrr,
        arv, arv_src, calc_input.rehab.tier,
    )

    return DealCalculatorResponse(
        property_id=prop.id,
        property_address=address,
        list_price=prop.price,
        arv=arv,
        monthly_rent=rent,
        square_feet=sqft,
        rehab_cost=rehab_cost,
        data_sources=DataSources(
            arv_source=arv_src,
            rent_source=rent_src,
            sqft_source=sqft_src,
        ),
        wholesale=wholesale,
        flip=flip,
        rental=rental,
        brrrr=brrrr,
        recommended_strategy=recommended,
        recommendation_reason=reason,
        voice_summary=voice,
        calculated_at=datetime.now(timezone.utc),
    )


class DealCalculatorService:
    """Wrapper for deal calculator functions to provide a service interface."""

    @staticmethod
    def calculate_deal(db: Session, calc_input: DealCalculatorInput) -> DealCalculatorResponse:
        """Calculate deal metrics for a property."""
        return calculate_deal(db, calc_input)


# Singleton instance for imports
deal_calculator_service = DealCalculatorService()


# Singleton instance for imports
deal_calculator_service = DealCalculatorService()
