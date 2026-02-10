"""Schemas for the Deal Calculator / Underwriting feature."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Input Models ──────────────────────────────────────────────


class RehabAssumptions(BaseModel):
    tier: Literal["light", "medium", "heavy"] = "medium"
    total_cost_override: float | None = None  # Skip per-sqft calc


class FeeAssumptions(BaseModel):
    closing_cost: float = 5000.0
    holding_cost_per_month: float = 500.0  # insurance, taxes, utilities, HOA
    holding_months: int = 6  # flip=4-6, BRRRR=6-12
    assignment_fee: float = 10000.0  # Wholesale only
    misc_fee: float = 1500.0


class FinancingAssumptions(BaseModel):
    """Loan parameters. Set use_financing=False for all-cash deal."""
    use_financing: bool = False
    down_payment_pct: float = 0.20  # 20% down
    interest_rate: float = 0.07  # 7% annual
    loan_term_years: int = 30
    loan_type: Literal["conventional", "hard_money", "fha", "va", "dscr", "seller_financing"] = "conventional"


class ExpenseAssumptions(BaseModel):
    """Line-item rental expense percentages (of gross rent).
    Replaces the crude 50% rule."""
    property_management_pct: float = 0.08  # 8%
    vacancy_pct: float = 0.05  # 5%
    capex_reserve_pct: float = 0.05  # 5%
    repairs_pct: float = 0.05  # 5%
    insurance_monthly: float = 150.0
    property_tax_monthly: float = 300.0
    hoa_monthly: float = 0.0


class StrategyParams(BaseModel):
    wholesale_arv_pct: float = 0.70
    flip_target_margin: float = 0.20
    rental_arv_pct: float = 0.80
    rental_rent_multiplier: float = 100.0
    # BRRRR
    brrrr_refi_ltv: float = 0.75  # Refinance at 75% of ARV
    brrrr_refi_rate: float = 0.07  # Refi interest rate
    brrrr_refi_term_years: int = 30
    brrrr_seasoning_months: int = 6  # months before refi


class DealCalculatorInput(BaseModel):
    property_id: int
    arv_override: float | None = None
    monthly_rent_override: float | None = None
    sqft_override: int | None = None
    rehab: RehabAssumptions = Field(default_factory=RehabAssumptions)
    fees: FeeAssumptions = Field(default_factory=FeeAssumptions)
    financing: FinancingAssumptions = Field(default_factory=FinancingAssumptions)
    expenses: ExpenseAssumptions = Field(default_factory=ExpenseAssumptions)
    strategy_params: StrategyParams = Field(default_factory=StrategyParams)


# ── Output Models ─────────────────────────────────────────────


class FinancingDetail(BaseModel):
    """Breakdown of loan terms used in calculation."""
    loan_amount: float
    down_payment: float
    monthly_payment: float  # P&I
    interest_rate: float
    loan_term_years: int
    loan_type: str


class ExpenseBreakdown(BaseModel):
    """Line-item monthly expense detail for rental strategies."""
    property_management: float
    vacancy_reserve: float
    capex_reserve: float
    repairs_reserve: float
    insurance: float
    property_tax: float
    hoa: float
    debt_service: float  # 0 if cash
    total_monthly: float


class BRRRRDetail(BaseModel):
    """BRRRR-specific outputs."""
    initial_cash_in: float  # purchase + rehab + fees (before refi)
    refi_loan_amount: float  # ARV × LTV
    cash_back_at_refi: float  # refi proceeds − payoff of initial loan
    cash_left_in_deal: float  # initial cash − cash back
    refi_monthly_payment: float
    monthly_cash_flow_post_refi: float
    annual_cash_flow_post_refi: float
    cash_on_cash_post_refi: float | None  # annual cf / cash left
    infinite_return: bool  # True if cash left ≤ 0 (all money out)


class DealScore(BaseModel):
    """Grade the deal A/B/C/D/F with a score 0-100."""
    score: int  # 0-100
    grade: Literal["A", "B", "C", "D", "F"]
    factors: list[str]  # Explanation bullets


class StrategyResult(BaseModel):
    strategy: Literal["wholesale", "flip", "rental", "brrrr"]
    arv: float
    monthly_rent: float | None = None
    rehab_cost: float
    total_fees: float
    offer_price: float
    total_investment: float  # cash required (after financing)

    # Universal profit metrics
    gross_profit: float | None = None
    net_profit: float | None = None
    roi_percent: float | None = None

    # Financing detail (None if cash)
    financing: FinancingDetail | None = None

    # Expense breakdown (rental/brrrr only)
    expense_breakdown: ExpenseBreakdown | None = None

    # Rental-specific
    monthly_cash_flow: float | None = None
    annual_cash_flow: float | None = None
    cash_on_cash_return: float | None = None
    cap_rate: float | None = None
    break_even_rent: float | None = None

    # Flip-specific
    equity_capture: float | None = None
    holding_costs: float | None = None

    # BRRRR-specific
    brrrr: BRRRRDetail | None = None

    # Deal score
    deal_score: DealScore | None = None

    class Config:
        from_attributes = True


class DataSources(BaseModel):
    arv_source: str
    rent_source: str
    sqft_source: str


class DealCalculatorResponse(BaseModel):
    property_id: int
    property_address: str
    list_price: float | None = None
    arv: float
    monthly_rent: float | None = None
    square_feet: int | None = None
    rehab_cost: float
    data_sources: DataSources
    wholesale: StrategyResult
    flip: StrategyResult
    rental: StrategyResult
    brrrr: StrategyResult | None = None
    recommended_strategy: str
    recommendation_reason: str
    voice_summary: str
    calculated_at: datetime

    class Config:
        from_attributes = True
