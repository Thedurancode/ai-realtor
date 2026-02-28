"""Tests for the offer service (business logic)."""

from app.services import offer_service
from app.models.offer import Offer, OfferStatus


class TestCreateOffer:
    def test_create_sets_submitted(self, db, sample_property):
        from app.schemas.offer import OfferCreate
        payload = OfferCreate(
            property_id=sample_property.id,
            offer_price=300000,
        )
        offer = offer_service.create_offer(db, payload)
        assert offer.status == OfferStatus.SUBMITTED
        assert offer.submitted_at is not None
        assert offer.offer_price == 300000

    def test_create_with_expiry(self, db, sample_property):
        from app.schemas.offer import OfferCreate
        payload = OfferCreate(
            property_id=sample_property.id,
            offer_price=300000,
            expires_in_hours=24,
        )
        offer = offer_service.create_offer(db, payload)
        assert offer.expires_at is not None

    def test_create_invalid_property(self, db):
        import pytest
        from app.schemas.offer import OfferCreate
        payload = OfferCreate(property_id=99999, offer_price=100000)
        with pytest.raises(ValueError, match="not found"):
            offer_service.create_offer(db, payload)

    def test_create_unknown_financing_type(self, db, sample_property):
        from app.schemas.offer import OfferCreate
        payload = OfferCreate(
            property_id=sample_property.id,
            offer_price=300000,
            financing_type="unknown_type",
        )
        offer = offer_service.create_offer(db, payload)
        # Unknown types should fall back to OTHER
        from app.models.offer import FinancingType
        assert offer.financing_type == FinancingType.OTHER


class TestCounterOffer:
    def test_counter_submitted(self, db, sample_offer):
        from app.schemas.offer import CounterOfferCreate
        payload = CounterOfferCreate(offer_price=340000)
        counter = offer_service.counter_offer(db, sample_offer.id, payload)
        assert counter.parent_offer_id == sample_offer.id
        assert counter.offer_price == 340000

        # Parent should be marked as countered
        db.refresh(sample_offer)
        assert sample_offer.status == OfferStatus.COUNTERED

    def test_counter_nonexistent(self, db):
        import pytest
        from app.schemas.offer import CounterOfferCreate
        payload = CounterOfferCreate(offer_price=100000)
        with pytest.raises(ValueError, match="not found"):
            offer_service.counter_offer(db, 99999, payload)

    def test_counter_accepted_offer_fails(self, db, sample_offer):
        import pytest
        from app.schemas.offer import CounterOfferCreate

        # First accept the offer
        sample_offer.status = OfferStatus.ACCEPTED
        db.commit()

        payload = CounterOfferCreate(offer_price=340000)
        with pytest.raises(ValueError, match="Cannot counter"):
            offer_service.counter_offer(db, sample_offer.id, payload)


class TestAcceptOffer:
    def test_accept(self, db, sample_offer):
        offer = offer_service.accept_offer(db, sample_offer.id)
        assert offer.status == OfferStatus.ACCEPTED
        assert offer.responded_at is not None

    def test_accept_nonexistent(self, db):
        import pytest
        with pytest.raises(ValueError, match="not found"):
            offer_service.accept_offer(db, 99999)


class TestRejectOffer:
    def test_reject(self, db, sample_offer):
        offer = offer_service.reject_offer(db, sample_offer.id)
        assert offer.status == OfferStatus.REJECTED

    def test_reject_nonexistent(self, db):
        import pytest
        with pytest.raises(ValueError, match="not found"):
            offer_service.reject_offer(db, 99999)


class TestWithdrawOffer:
    def test_withdraw(self, db, sample_offer):
        offer = offer_service.withdraw_offer(db, sample_offer.id)
        assert offer.status == OfferStatus.WITHDRAWN

    def test_withdraw_nonexistent(self, db):
        import pytest
        with pytest.raises(ValueError, match="not found"):
            offer_service.withdraw_offer(db, 99999)


class TestListOffers:
    def test_list_all(self, db, sample_offer):
        offers = offer_service.list_offers(db)
        assert len(offers) >= 1

    def test_list_by_property(self, db, sample_offer, sample_property):
        offers = offer_service.list_offers(db, property_id=sample_property.id)
        assert len(offers) >= 1
        for o in offers:
            assert o.property_id == sample_property.id

    def test_list_by_status(self, db, sample_offer):
        offers = offer_service.list_offers(db, status="submitted")
        assert len(offers) >= 1


class TestGetOffer:
    def test_get_existing(self, db, sample_offer):
        offer = offer_service.get_offer(db, sample_offer.id)
        assert offer is not None
        assert offer.id == sample_offer.id

    def test_get_nonexistent(self, db):
        offer = offer_service.get_offer(db, 99999)
        assert offer is None
