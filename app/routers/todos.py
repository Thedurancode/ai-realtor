from datetime import datetime, timedelta, date
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.property import Property
from app.models.contact import Contact
from app.models.todo import Todo, TodoStatus, TodoPriority
from app.schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoCreateFromVoice,
    TodoUpdateFromVoice,
    TodoVoiceResponse,
    TodoListVoiceResponse,
)

router = APIRouter(prefix="/todos", tags=["todos"])


# Status aliases for voice input
STATUS_ALIASES = {
    "pending": TodoStatus.PENDING,
    "todo": TodoStatus.PENDING,
    "not started": TodoStatus.PENDING,
    "in progress": TodoStatus.IN_PROGRESS,
    "in-progress": TodoStatus.IN_PROGRESS,
    "working on": TodoStatus.IN_PROGRESS,
    "doing": TodoStatus.IN_PROGRESS,
    "completed": TodoStatus.COMPLETED,
    "done": TodoStatus.COMPLETED,
    "finished": TodoStatus.COMPLETED,
    "complete": TodoStatus.COMPLETED,
    "cancelled": TodoStatus.CANCELLED,
    "canceled": TodoStatus.CANCELLED,
    "cancelled": TodoStatus.CANCELLED,
}

# Priority aliases for voice input
PRIORITY_ALIASES = {
    "low": TodoPriority.LOW,
    "normal": TodoPriority.MEDIUM,
    "medium": TodoPriority.MEDIUM,
    "high": TodoPriority.HIGH,
    "important": TodoPriority.HIGH,
    "urgent": TodoPriority.URGENT,
    "critical": TodoPriority.URGENT,
    "asap": TodoPriority.URGENT,
}


def parse_natural_date(date_input: str) -> date | None:
    """
    Parse natural language dates like 'friday', 'tomorrow', 'next week', 'in 3 days'.
    Returns a date object or None if parsing fails.
    """
    if not date_input:
        return None

    date_input = date_input.lower().strip()
    today = date.today()

    # Handle "today"
    if date_input in ["today", "now"]:
        return today

    # Handle "tomorrow"
    if date_input == "tomorrow":
        return today + timedelta(days=1)

    # Handle "yesterday"
    if date_input == "yesterday":
        return today - timedelta(days=1)

    # Handle day names (monday, tuesday, etc.)
    weekdays = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6,
    }

    if date_input in weekdays:
        target_weekday = weekdays[date_input]
        current_weekday = today.weekday()
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    # Handle "next [day]"
    next_match = re.match(r"next (monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)", date_input)
    if next_match:
        day_name = next_match.group(1)
        target_weekday = weekdays[day_name]
        current_weekday = today.weekday()
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        days_ahead += 7  # Add extra week for "next"
        return today + timedelta(days=days_ahead)

    # Handle "in X days/weeks/months"
    in_match = re.match(r"in (\d+) (day|days|week|weeks|month|months)", date_input)
    if in_match:
        amount = int(in_match.group(1))
        unit = in_match.group(2)
        if unit.startswith("day"):
            return today + timedelta(days=amount)
        elif unit.startswith("week"):
            return today + timedelta(weeks=amount)
        elif unit.startswith("month"):
            return today + relativedelta(months=amount)

    # Handle "next week/month/year"
    if date_input == "next week":
        return today + timedelta(weeks=1)
    if date_input == "next month":
        return today + relativedelta(months=1)
    if date_input == "next year":
        return today + relativedelta(years=1)

    # Handle "this friday", "this weekend", etc.
    this_match = re.match(r"this (monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)", date_input)
    if this_match:
        day_name = this_match.group(1)
        target_weekday = weekdays[day_name]
        current_weekday = today.weekday()
        days_ahead = target_weekday - current_weekday
        if days_ahead < 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    # Try parsing with dateutil as fallback (handles "jan 15", "15 january", etc.)
    try:
        parsed_date = date_parser.parse(date_input, fuzzy=True)
        # If year not specified and date is in the past, assume next year
        if parsed_date.year == today.year and parsed_date.date() < today:
            parsed_date = parsed_date.replace(year=today.year + 1)
        return parsed_date.date()
    except:
        pass

    return None


def format_date_for_voice(due_date: date) -> str:
    """Format date for voice output."""
    today = date.today()
    delta = (due_date - today).days

    if delta == 0:
        return "today"
    elif delta == 1:
        return "tomorrow"
    elif delta == -1:
        return "yesterday"
    elif 0 < delta <= 7:
        return due_date.strftime("%A")  # Day name like "Friday"
    elif delta > 7 and delta <= 14:
        return f"next {due_date.strftime('%A')}"
    else:
        return due_date.strftime("%B %d")  # Like "January 15"


def parse_status(status_input: str) -> TodoStatus:
    """Parse status from voice input, handling aliases."""
    status_lower = status_input.lower().strip()
    if status_lower in STATUS_ALIASES:
        return STATUS_ALIASES[status_lower]
    # Try direct enum match
    try:
        return TodoStatus(status_lower)
    except ValueError:
        return TodoStatus.PENDING


def parse_priority(priority_input: str) -> TodoPriority:
    """Parse priority from voice input, handling aliases."""
    priority_lower = priority_input.lower().strip()
    if priority_lower in PRIORITY_ALIASES:
        return PRIORITY_ALIASES[priority_lower]
    # Try direct enum match
    try:
        return TodoPriority(priority_lower)
    except ValueError:
        return TodoPriority.MEDIUM


def format_status_for_voice(status: TodoStatus) -> str:
    """Format status for voice output."""
    return status.value.replace("_", " ")


def format_priority_for_voice(priority: TodoPriority) -> str:
    """Format priority for voice output."""
    return priority.value


@router.post("/", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a todo for a property."""
    property = db.query(Property).filter(Property.id == todo.property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Validate contact if provided
    if todo.contact_id:
        contact = db.query(Contact).filter(Contact.id == todo.contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        if contact.property_id != todo.property_id:
            raise HTTPException(
                status_code=400,
                detail="Contact must belong to the same property as the todo"
            )

    new_todo = Todo(
        property_id=todo.property_id,
        contact_id=todo.contact_id,
        title=todo.title,
        description=todo.description,
        status=todo.status,
        priority=todo.priority,
        due_date=todo.due_date,
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo


@router.post("/voice", response_model=TodoVoiceResponse, status_code=201)
def create_todo_from_voice(
    request: TodoCreateFromVoice, db: Session = Depends(get_db)
):
    """
    Voice-optimized todo creation.
    Example: "add a todo for 141 throop: schedule inspection"
    Example: "add high priority todo for throop: fix roof leak"
    """
    # Find property by partial address
    query = request.address_query.lower()
    property = db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{request.address_query}'. Please add the property first.",
        )

    # Parse priority if provided
    priority = (
        parse_priority(request.priority)
        if request.priority
        else TodoPriority.MEDIUM
    )

    # Parse due date if provided
    due_date = None
    if request.due_date:
        due_date = parse_natural_date(request.due_date)

    # Validate contact if provided
    if request.contact_id:
        contact = db.query(Contact).filter(Contact.id == request.contact_id).first()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        if contact.property_id != property.id:
            raise HTTPException(
                status_code=400,
                detail="Contact must belong to the same property as the todo"
            )

    # Create todo
    new_todo = Todo(
        property_id=property.id,
        contact_id=request.contact_id,
        title=request.title,
        status=TodoStatus.PENDING,
        priority=priority,
        due_date=due_date,
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)

    # Build voice confirmation
    priority_text = format_priority_for_voice(priority)
    voice_confirmation = f"Got it. I've added a {priority_text} priority todo for {property.address}: {request.title}"

    if due_date:
        date_text = format_date_for_voice(due_date)
        voice_confirmation += f", due {date_text}"

    return TodoVoiceResponse(
        todo=new_todo,
        voice_confirmation=voice_confirmation,
    )


@router.patch("/voice", response_model=TodoVoiceResponse)
def update_todo_from_voice(
    request: TodoUpdateFromVoice, db: Session = Depends(get_db)
):
    """
    Voice-optimized todo update.
    Example: "mark todo 3 as completed"
    Example: "update todo 2 status to in progress"
    """
    todo = db.query(Todo).filter(Todo.id == request.todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo {request.todo_id} not found")

    property = db.query(Property).filter(Property.id == todo.property_id).first()

    # Update status if provided
    if request.status:
        new_status = parse_status(request.status)
        todo.status = new_status

        # Set completed_at if marking as completed
        if new_status == TodoStatus.COMPLETED and not todo.completed_at:
            todo.completed_at = datetime.now()

    # Update priority if provided
    if request.priority:
        todo.priority = parse_priority(request.priority)

    db.commit()
    db.refresh(todo)

    # Build voice confirmation
    status_text = format_status_for_voice(todo.status)
    voice_confirmation = f"Updated todo for {property.address}. Status is now {status_text}."

    return TodoVoiceResponse(
        todo=todo,
        voice_confirmation=voice_confirmation,
    )


@router.get("/property/{property_id}", response_model=TodoListVoiceResponse)
def list_todos_for_property(
    property_id: int,
    status: TodoStatus | None = None,
    contact_id: int | None = None,
    db: Session = Depends(get_db),
):
    """List all todos for a property with optional status and contact filters."""
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    todos_query = db.query(Todo).filter(Todo.property_id == property_id)

    if status:
        todos_query = todos_query.filter(Todo.status == status)

    if contact_id:
        todos_query = todos_query.filter(Todo.contact_id == contact_id)

    todos = todos_query.order_by(Todo.priority.desc(), Todo.created_at).all()

    if not todos:
        status_text = f"{format_status_for_voice(status)} " if status else ""
        voice_summary = f"No {status_text}todos found for {property.address}."
    else:
        # Group by status for summary
        status_counts = {}
        for t in todos:
            status_text = format_status_for_voice(t.status)
            status_counts[status_text] = status_counts.get(status_text, 0) + 1

        status_parts = [
            f"{count} {status}" for status, count in status_counts.items()
        ]
        voice_summary = (
            f"Found {len(todos)} todo{'s' if len(todos) > 1 else ''} "
            f"for {property.address}: {', '.join(status_parts)}."
        )

    return TodoListVoiceResponse(
        todos=todos,
        voice_summary=voice_summary,
    )


@router.get("/contact/{contact_id}", response_model=TodoListVoiceResponse)
def list_todos_for_contact(
    contact_id: int,
    status: TodoStatus | None = None,
    db: Session = Depends(get_db),
):
    """List all todos for a specific contact with optional status filter."""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    todos_query = db.query(Todo).filter(Todo.contact_id == contact_id)

    if status:
        todos_query = todos_query.filter(Todo.status == status)

    todos = todos_query.order_by(Todo.priority.desc(), Todo.created_at).all()

    if not todos:
        status_text = f"{format_status_for_voice(status)} " if status else ""
        voice_summary = f"No {status_text}todos found for {contact.name}."
    else:
        # Group by status for summary
        status_counts = {}
        for t in todos:
            status_text = format_status_for_voice(t.status)
            status_counts[status_text] = status_counts.get(status_text, 0) + 1

        status_parts = [
            f"{count} {status}" for status, count in status_counts.items()
        ]
        voice_summary = (
            f"Found {len(todos)} todo{'s' if len(todos) > 1 else ''} "
            f"for {contact.name}: {', '.join(status_parts)}."
        )

    return TodoListVoiceResponse(
        todos=todos,
        voice_summary=voice_summary,
    )


@router.get("/voice/search", response_model=TodoListVoiceResponse)
def search_todos_voice(
    address_query: str,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Voice search for todos.
    Example: "what are the todos for 141 throop"
    Example: "show me pending todos for throop"
    """
    query = address_query.lower()
    property = db.query(Property).filter(Property.address.ilike(f"%{query}%")).first()

    if not property:
        raise HTTPException(
            status_code=404,
            detail=f"No property found matching '{address_query}'.",
        )

    todos_query = db.query(Todo).filter(Todo.property_id == property.id)

    if status:
        parsed_status = parse_status(status)
        todos_query = todos_query.filter(Todo.status == parsed_status)

    todos = todos_query.order_by(Todo.priority.desc(), Todo.created_at).all()

    if status:
        status_text = format_status_for_voice(parse_status(status))
        if not todos:
            voice_summary = f"No {status_text} todos for {property.address}."
        else:
            todo_titles = [f"{t.title}" for t in todos[:5]]
            voice_summary = f"{len(todos)} {status_text} todo{'s' if len(todos) > 1 else ''} for {property.address}: {', '.join(todo_titles)}."
    else:
        if not todos:
            voice_summary = f"No todos found for {property.address}."
        else:
            # Group by status
            status_counts = {}
            for t in todos:
                status_text = format_status_for_voice(t.status)
                status_counts[status_text] = status_counts.get(status_text, 0) + 1

            status_parts = [
                f"{count} {status}" for status, count in status_counts.items()
            ]
            voice_summary = f"Todos for {property.address}: {', '.join(status_parts)}."

    return TodoListVoiceResponse(
        todos=todos,
        voice_summary=voice_summary,
    )


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a todo by ID."""
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    """Update a todo."""
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = todo.model_dump(exclude_unset=True)

    # Set completed_at if marking as completed
    if "status" in update_data and update_data["status"] == TodoStatus.COMPLETED:
        if not db_todo.completed_at:
            update_data["completed_at"] = datetime.now()

    for field, value in update_data.items():
        setattr(db_todo, field, value)

    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo."""
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(db_todo)
    db.commit()
    return None
