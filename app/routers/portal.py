"""
Customer Portal API Routes
Self-service portal for buyers, sellers, tenants to view their properties and contracts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import hashlib
import secrets
import jwt

from app.database import SessionLocal
from app.models.portal_user import PortalUser, PropertyAccess, PortalActivity
from app.models.property import Property
from app.models.contract import Contract
from app.models.agent import Agent
from app.utils.property_resolver import resolve_property, resolve_property_list, format_property_match

router = APIRouter(prefix="/portal", tags=["portal"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to env
ALGORITHM = "HS256"


# Pydantic Models
class PortalUserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    client_type: Optional[str] = None  # buyer, seller, tenant, landlord


class PortalUserLogin(BaseModel):
    email: EmailStr
    password: str


class PortalUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    client_type: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime


class PropertyAccessResponse(BaseModel):
    id: int
    property_id: int
    access_level: str
    relationship: Optional[str]
    can_view_price: bool
    can_sign_contracts: bool
    property: Optional[dict] = None


# Helper Functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == hashed


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc).timestamp() + 86400 * 7  # 7 days
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> PortalUser:
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(PortalUser).filter(PortalUser.id == payload["user_id"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def log_activity(db: Session, user_id: int, action: str, resource_type: str = None, resource_id: int = None, metadata: str = None):
    """Log portal user activity"""
    activity = PortalActivity(
        portal_user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata
    )
    db.add(activity)
    db.commit()


# ============================================================================
# Authentication Routes
# ============================================================================

@router.post("/auth/register", response_model=PortalUserResponse)
async def register(user_data: PortalUserCreate, db: Session = Depends(get_db)):
    """Register a new portal user"""
    # Check if email exists
    existing = db.query(PortalUser).filter(PortalUser.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = PortalUser(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        client_type=user_data.client_type,
        role="client",
        verification_token=secrets.token_urlsafe(32)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # TODO: Send verification email

    log_activity(db, user.id, "register", metadata=f"Registered as {user_data.client_type}")

    return user


@router.post("/auth/login")
async def login(credentials: PortalUserLogin, db: Session = Depends(get_db)):
    """Login to portal"""
    user = db.query(PortalUser).filter(PortalUser.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    log_activity(db, user.id, "login")

    token = create_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "client_type": user.client_type
        }
    }


@router.get("/auth/me", response_model=PortalUserResponse)
async def get_me(current_user: PortalUser = Depends(get_current_user)):
    """Get current user info"""
    return current_user


# ============================================================================
# Properties Routes
# ============================================================================

@router.get("/properties", response_model=List[PropertyAccessResponse])
async def get_my_properties(
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all properties the user has access to"""
    accesses = db.query(PropertyAccess).filter(
        PropertyAccess.portal_user_id == current_user.id,
        PropertyAccess.is_active == True
    ).all()

    result = []
    for access in accesses:
        property_data = None
        if access.property:
            # Build property response based on permissions
            property_data = {
                "id": access.property.id,
                "title": access.property.title,
                "address": access.property.address,
                "city": access.property.city,
                "state": access.property.state,
                "zip_code": access.property.zip_code,
                "bedrooms": access.property.bedrooms,
                "bathrooms": access.property.bathrooms,
                "square_feet": access.property.square_feet,
                "property_type": access.property.property_type.value if access.property.property_type else None,
                "status": access.property.status.value if access.property.status else None,
            }

            # Only include price if user has permission
            if access.can_view_price:
                property_data["price"] = access.property.price
                property_data["deal_score"] = access.property.deal_score
                property_data["score_grade"] = access.property.score_grade

        result.append(PropertyAccessResponse(
            id=access.id,
            property_id=access.property_id,
            access_level=access.access_level,
            relationship=access.relationship,
            can_view_price=access.can_view_price,
            can_sign_contracts=access.can_sign_contracts,
            property=property_data
        ))

    log_activity(db, current_user.id, "view_properties")

    return result


@router.get("/properties/search/{query}")
async def search_properties(
    query: str,
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search properties by address, city, or identifier"""
    # Get all accessible property IDs
    accessible_property_ids = [
        access.property_id for access in db.query(PropertyAccess).filter(
            PropertyAccess.portal_user_id == current_user.id,
            PropertyAccess.is_active == True
        ).all()
    ]

    # Search for matching properties
    query = query.lower().strip()

    all_matches = []
    for prop_id in accessible_property_ids:
        prop = db.query(Property).filter(Property.id == prop_id).first()
        if prop:
            # Build searchable strings
            searchable = [
                f"{prop.address}, {prop.city}, {prop.state}".lower(),
                f"{prop.address} {prop.city} {prop.state}".lower(),
                f"{prop.address}, {prop.city}".lower(),
                f"{prop.address}".lower(),
                f"{prop.city}, {prop.state}".lower(),
                f"{prop.city}".lower(),
            ]
            # Check if query matches any searchable string
            if any(query in s for s in searchable):
                # Get access info for this property
                access = db.query(PropertyAccess).filter(
                    PropertyAccess.portal_user_id == current_user.id,
                    PropertyAccess.property_id == prop.id,
                    PropertyAccess.is_active == True
                ).first()

                if access:
                    all_matches.append({
                        "id": prop.id,
                        "title": prop.title,
                        "address": prop.address,
                        "city": prop.city,
                        "state": prop.state,
                        "zip_code": prop.zip_code,
                        "access_level": access.access_level,
                        "relationship": access.relationship,
                    })

    log_activity(db, current_user.id, "search_properties", metadata=f"Searched for: {query}")

    return all_matches


@router.get("/properties/by-identifier/{identifier}")
async def get_property_by_identifier(
    identifier: str,
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get property by address or ID (natural language lookup)"""
    # Try to resolve property
    matches = resolve_property_list(db, identifier, current_user.id)

    if len(matches) == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Property not found: '{identifier}'"
        )

    # Filter to only accessible properties
    accessible_matches = []
    for prop in matches:
        access = db.query(PropertyAccess).filter(
            PropertyAccess.portal_user_id == current_user.id,
            PropertyAccess.property_id == prop.id,
            PropertyAccess.is_active == True
        ).first()

        if access:
            accessible_matches.append({
                "id": prop.id,
                "identifier": f"{prop.address}, {prop.city}, {prop.state}",
                "title": prop.title,
                "address": prop.address,
                "city": prop.city,
                "state": prop.state,
                "access_level": access.access_level,
                "relationship": access.relationship,
                "can_view_price": access.can_view_price,
                "can_sign_contracts": access.can_sign_contracts,
            })

    if len(accessible_matches) == 0:
        raise HTTPException(
            status_code=403,
            detail=f"You don't have access to any property matching: '{identifier}'"
        )

    if len(accessible_matches) == 1:
        # Single match - return full property details
        prop = accessible_matches[0]
        # Redirect to the actual property details endpoint would be ideal,
        # but for now let's fetch the full details
        return await get_property_details(prop['id'], current_user, db)
    else:
        # Multiple matches - return list for user to choose
        return {
            "multiple_matches": True,
            "count": len(accessible_matches),
            "matches": accessible_matches
        }


@router.get("/properties/{property_id}")
async def get_property_details(
    property_id: int,
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed property info"""
    access = db.query(PropertyAccess).filter(
        PropertyAccess.portal_user_id == current_user.id,
        PropertyAccess.property_id == property_id,
        PropertyAccess.is_active == True
    ).first()

    if not access:
        raise HTTPException(status_code=403, detail="Access denied to this property")

    property_data = db.query(Property).filter(Property.id == property_id).first()
    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    # Build response based on permissions
    response = {
        "id": property_data.id,
        "title": property_data.title,
        "description": property_data.description,
        "address": property_data.address,
        "city": property_data.city,
        "state": property_data.state,
        "zip_code": property_data.zip_code,
        "bedrooms": property_data.bedrooms,
        "bathrooms": property_data.bathrooms,
        "square_feet": property_data.square_feet,
        "lot_size": property_data.lot_size,
        "year_built": property_data.year_built,
        "property_type": property_data.property_type.value if property_data.property_type else None,
        "status": property_data.status.value if property_data.status else None,
        "access_level": access.access_level,
        "relationship": access.relationship
    }

    # Conditional fields based on permissions
    if access.can_view_price:
        response["price"] = property_data.price
        response["deal_score"] = property_data.deal_score
        response["score_grade"] = property_data.score_grade
        response["score_breakdown"] = property_data.score_breakdown

    if access.can_view_contracts:
        # Include contract summary
        contracts = db.query(Contract).filter(Contract.property_id == property_id).all()
        response["contracts"] = [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "is_required": c.is_required
            }
            for c in contracts
        ]

    log_activity(db, current_user.id, "view_property", "property", property_id)

    return response


# ============================================================================
# Contracts Routes
# ============================================================================

@router.get("/contracts")
async def get_my_contracts(
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all contracts the user has access to"""
    # Get all accessible properties
    accessible_property_ids = [
        access.property_id for access in db.query(PropertyAccess).filter(
            PropertyAccess.portal_user_id == current_user.id,
            PropertyAccess.is_active == True,
            PropertyAccess.can_view_contracts == True
        ).all()
    ]

    contracts = db.query(Contract).filter(
        Contract.property_id.in_(accessible_property_ids)
    ).all()

    result = []
    for contract in contracts:
        # Check access level for this property
        access = db.query(PropertyAccess).filter(
            PropertyAccess.portal_user_id == current_user.id,
            PropertyAccess.property_id == contract.property_id
        ).first()

        result.append({
            "id": contract.id,
            "title": contract.title,
            "property_id": contract.property_id,
            "status": contract.status,
            "is_required": contract.is_required,
            "can_sign": access.can_sign_contracts if access else False,
            "created_at": contract.created_at
        })

    log_activity(db, current_user.id, "view_contracts")

    return result


@router.get("/contracts/{contract_id}")
async def get_contract_details(
    contract_id: int,
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get contract details"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Check access
    access = db.query(PropertyAccess).filter(
        PropertyAccess.portal_user_id == current_user.id,
        PropertyAccess.property_id == contract.property_id,
        PropertyAccess.can_view_contracts == True
    ).first()

    if not access:
        raise HTTPException(status_code=403, detail="Access denied to this contract")

    log_activity(db, current_user.id, "view_contract", "contract", contract_id)

    return {
        "id": contract.id,
        "title": contract.title,
        "description": contract.description,
        "property_id": contract.property_id,
        "status": contract.status,
        "is_required": contract.is_required,
        "docuseal_document_id": contract.docuseal_document_id,
        "docuseal_signing_url": contract.docuseal_signing_url,
        "can_sign": access.can_sign_contracts,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at
    }


# ============================================================================
# Activity Routes
# ============================================================================

@router.get("/activity")
async def get_my_activity(
    limit: int = 50,
    current_user: PortalUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's activity history"""
    activities = db.query(PortalActivity).filter(
        PortalActivity.portal_user_id == current_user.id
    ).order_by(PortalActivity.created_at.desc()).limit(limit).all()

    return [
        {
            "id": a.id,
            "action": a.action,
            "resource_type": a.resource_type,
            "resource_id": a.resource_id,
            "metadata": a.metadata,
            "created_at": a.created_at
        }
        for a in activities
    ]


# ============================================================================
# Management Routes (Agent-side)
# ============================================================================

class GrantAccessRequest(BaseModel):
    email: EmailStr
    property_id: int
    relationship: str  # buyer, seller, tenant, landlord
    access_level: str = "view"  # view, sign, full
    can_view_price: bool = False
    can_sign_contracts: bool = False


@router.post("/access/grant")
async def grant_property_access(
    request: GrantAccessRequest,
    agent_id: int,  # Agent ID for verification
    db: Session = Depends(get_db)
):
    """Agent grants a client access to a property"""
    # Verify agent owns the property
    property = db.query(Property).filter(
        Property.id == request.property_id,
        Property.agent_id == agent_id
    ).first()

    if not property:
        raise HTTPException(status_code=403, detail="Property not found or access denied")

    # Find or create portal user
    user = db.query(PortalUser).filter(PortalUser.email == request.email).first()

    if not user:
        # Create a new user with temporary password
        temp_password = secrets.token_urlsafe(12)
        user = PortalUser(
            email=request.email,
            password_hash=hash_password(temp_password),
            full_name=request.email.split("@")[0],  # Default name
            invited_by_agent_id=agent_id,
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # TODO: Send invitation email with temp password

    # Check if access already exists
    existing_access = db.query(PropertyAccess).filter(
        PropertyAccess.portal_user_id == user.id,
        PropertyAccess.property_id == request.property_id
    ).first()

    if existing_access:
        # Update existing access
        existing_access.access_level = request.access_level
        existing_access.relationship = request.relationship
        existing_access.can_view_price = request.can_view_price
        existing_access.can_sign_contracts = request.can_sign_contracts
        existing_access.is_active = True
    else:
        # Create new access
        access = PropertyAccess(
            portal_user_id=user.id,
            property_id=request.property_id,
            access_level=request.access_level,
            relationship=request.relationship,
            can_view_price=request.can_view_price,
            can_sign_contracts=request.can_sign_contracts
        )
        db.add(access)

    db.commit()

    return {
        "message": "Access granted successfully",
        "user_email": user.email,
        "user_id": user.id,
        "property_id": request.property_id,
        "access_level": request.access_level
    }
