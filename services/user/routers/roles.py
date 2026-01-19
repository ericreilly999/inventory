"""Roles router for User Service."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from shared.database.config import get_db
from shared.models.user import Role, User
from shared.logging.config import get_logger
from ..schemas import RoleCreate, RoleUpdate, RoleResponse, MessageResponse
from ..dependencies import get_current_user, require_role_admin

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=RoleResponse, dependencies=[Depends(require_role_admin)])
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new role."""
    
    # Check if role name already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )
    
    # Create new role
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    logger.info(
        "Role created",
        role_id=str(role.id),
        role_name=role.name,
        created_by=str(current_user.id)
    )
    
    return RoleResponse.from_orm(role)


@router.get("/", response_model=List[RoleResponse], dependencies=[Depends(require_role_admin)])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List roles with optional filtering."""
    
    query = db.query(Role)
    
    # Search filter
    if search:
        search_filter = or_(
            Role.name.ilike(f"%{search}%"),
            Role.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply pagination
    roles = query.offset(skip).limit(limit).all()
    
    return [RoleResponse.from_orm(role) for role in roles]


@router.get("/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_role_admin)])
async def get_role(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    """Get role by ID."""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return RoleResponse.from_orm(role)


@router.put("/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_role_admin)])
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update role information."""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check for name conflicts
    if role_data.name and role_data.name != role.name:
        existing = db.query(Role).filter(
            and_(
                Role.name == role_data.name,
                Role.id != role_id
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists"
            )
        role.name = role_data.name
    
    # Update other fields
    if role_data.description is not None:
        role.description = role_data.description
    
    if role_data.permissions is not None:
        role.permissions = role_data.permissions
    
    db.commit()
    db.refresh(role)
    
    logger.info(
        "Role updated",
        role_id=str(role.id),
        role_name=role.name,
        updated_by=str(current_user.id)
    )
    
    return RoleResponse.from_orm(role)


@router.delete("/{role_id}", response_model=MessageResponse, dependencies=[Depends(require_role_admin)])
async def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete role if no users are assigned to it."""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if any users are assigned to this role
    users_with_role = db.query(User).filter(User.role_id == role_id).first()
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role with assigned users"
        )
    
    db.delete(role)
    db.commit()
    
    logger.info(
        "Role deleted",
        role_id=str(role_id),
        role_name=role.name,
        deleted_by=str(current_user.id)
    )
    
    return MessageResponse(message="Role deleted successfully")


@router.get("/{role_id}/users", response_model=List[dict], dependencies=[Depends(require_role_admin)])
async def get_role_users(
    role_id: UUID,
    db: Session = Depends(get_db)
):
    """Get users assigned to a specific role."""
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    users = db.query(User).filter(User.role_id == role_id).all()
    
    return [
        {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "active": user.active
        }
        for user in users
    ]