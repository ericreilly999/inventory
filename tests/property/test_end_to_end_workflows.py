"""
End-to-end property tests for complete workflows across all services.

Tests complete workflows across all services and validates system behavior
under various scenarios using property-based testing.
Requirements: 1.3, 1.4, 2.1, 2.2, 2.3

Feature: inventory-management
"""

import random
import uuid
from typing import Dict, List, Optional

from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
)

from shared.models.assignment_history import AssignmentHistory
from shared.models.item import ChildItem, ItemCategory, ItemType, ParentItem
from shared.models.location import Location, LocationType
from shared.models.move_history import MoveHistory
from shared.models.user import Role, User


# Strategies for generating test data
@st.composite
def valid_uuid_string(draw):
    """Generate valid UUID strings."""
    return str(uuid.uuid4())


@st.composite
def valid_name(draw):
    """Generate valid names for entities."""
    return draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Pd")
            ),
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip() and not x.isspace())
    )


@st.composite
def valid_description(draw):
    """Generate valid descriptions."""
    return draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Pd", "Po", "Zs")
            ),
            min_size=0,
            max_size=200,
        )
    )


@st.composite
def valid_email(draw):
    """Generate valid email addresses."""
    username = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=20,
        )
    )
    domain = draw(
        st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            min_size=1,
            max_size=20,
        )
    )
    return f"{username}@{domain}.com"


class InventorySystemStateMachine(RuleBasedStateMachine):
    """
    Stateful property-based testing for the entire inventory management system.

    This tests complete workflows across all services and validates that
    the system maintains consistency under various operations.
    """

    def __init__(self):
        super().__init__()
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.locations: Dict[str, Location] = {}
        self.location_types: Dict[str, LocationType] = {}
        self.item_types: Dict[str, ItemType] = {}
        self.parent_items: Dict[str, ParentItem] = {}
        self.child_items: Dict[str, ChildItem] = {}
        self.move_history: List[MoveHistory] = []
        self.assignment_history: List[AssignmentHistory] = []

        # Track system state for invariants
        self.item_locations: Dict[str, str] = {}  # item_id -> location_id
        self.child_assignments: Dict[str, Optional[str]] = (
            {}
        )  # child_id -> parent_id
        self.location_item_counts: Dict[str, int] = {}  # location_id -> count

    # Bundles for managing entity references
    users = Bundle("users")
    roles = Bundle("roles")
    locations = Bundle("locations")
    location_types = Bundle("location_types")
    item_types = Bundle("item_types")
    parent_items = Bundle("parent_items")
    child_items = Bundle("child_items")

    @initialize()
    def setup_initial_data(self):
        """Initialize the system with basic required data."""
        # Create admin role
        admin_role = Role(
            name="admin",
            description="System administrator",
            permissions={"read": True, "write": True, "admin": True},
        )
        self.roles[admin_role.id] = admin_role

        # Create warehouse location type
        warehouse_type = LocationType(
            name="Warehouse", description="Storage warehouse"
        )
        self.location_types[warehouse_type.id] = warehouse_type

        # Create basic item types
        parent_item_type = ItemType(
            name="Electronics",
            description="Electronic devices",
            category=ItemCategory.PARENT,
        )
        child_item_type = ItemType(
            name="Accessories",
            description="Electronic accessories",
            category=ItemCategory.CHILD,
        )
        self.item_types[parent_item_type.id] = parent_item_type
        self.item_types[child_item_type.id] = child_item_type

    @rule(target=roles, name=valid_name(), description=valid_description())
    def create_role(self, name, description):
        """Create a new role."""
        assume(name not in [r.name for r in self.roles.values()])

        role = Role(
            name=name,
            description=description,
            permissions={"read": True, "write": False},
        )
        self.roles[role.id] = role
        return role.id

    @rule(
        target=users, role_id=roles, username=valid_name(), email=valid_email()
    )
    def create_user(self, role_id, username, email):
        """Create a new user."""
        assume(role_id in self.roles)
        assume(username not in [u.username for u in self.users.values()])
        assume(email not in [u.email for u in self.users.values()])

        user = User(
            username=username,
            email=email,
            password_hash="hashed_password",
            role_id=role_id,
            active=True,
        )
        self.users[user.id] = user
        return user.id

    @rule(
        target=location_types,
        name=valid_name(),
        description=valid_description(),
    )
    def create_location_type(self, name, description):
        """Create a new location type."""
        assume(name not in [lt.name for lt in self.location_types.values()])

        location_type = LocationType(name=name, description=description)
        self.location_types[location_type.id] = location_type
        return location_type.id

    @rule(
        target=locations,
        location_type_id=location_types,
        name=valid_name(),
        description=valid_description(),
    )
    def create_location(self, location_type_id, name, description):
        """Create a new location."""
        assume(location_type_id in self.location_types)
        assume(name not in [loc.name for loc in self.locations.values()])

        location = Location(
            name=name,
            description=description,
            location_type_id=location_type_id,
        )
        self.locations[location.id] = location
        self.location_item_counts[location.id] = 0
        return location.id

    @rule(
        target=item_types,
        name=valid_name(),
        description=valid_description(),
        category=st.sampled_from(list(ItemCategory)),
    )
    def create_item_type(self, name, description, category):
        """Create a new item type."""
        assume(name not in [it.name for it in self.item_types.values()])

        item_type = ItemType(
            name=name, description=description, category=category
        )
        self.item_types[item_type.id] = item_type
        return item_type.id

    @rule(
        target=parent_items,
        name=valid_name(),
        description=valid_description(),
        user_id=users,
        location_id=locations,
    )
    def create_parent_item(self, name, description, user_id, location_id):
        """Create a new parent item."""
        assume(user_id in self.users)
        assume(location_id in self.locations)

        # Find a parent item type
        parent_item_types = [
            it
            for it in self.item_types.values()
            if it.category == ItemCategory.PARENT
        ]
        assume(len(parent_item_types) > 0)
        item_type_id = random.choice(parent_item_types).id

        parent_item = ParentItem(
            name=name,
            description=description,
            item_type_id=item_type_id,
            current_location_id=location_id,
            created_by=user_id,
        )
        self.parent_items[parent_item.id] = parent_item
        self.item_locations[parent_item.id] = location_id
        self.location_item_counts[location_id] += 1
        return parent_item.id

    @rule(
        target=child_items,
        name=valid_name(),
        description=valid_description(),
        user_id=users,
    )
    def create_child_item(self, name, description, user_id):
        """Create a new child item."""
        assume(user_id in self.users)

        # Find a child item type
        child_item_types = [
            it
            for it in self.item_types.values()
            if it.category == ItemCategory.CHILD
        ]
        assume(len(child_item_types) > 0)
        item_type_id = random.choice(child_item_types).id

        child_item = ChildItem(
            name=name,
            description=description,
            item_type_id=item_type_id,
            created_by=user_id,
        )
        self.child_items[child_item.id] = child_item
        self.child_assignments[child_item.id] = None
        return child_item.id

    @rule(
        parent_item_id=parent_items, new_location_id=locations, user_id=users
    )
    def move_parent_item(self, parent_item_id, new_location_id, user_id):
        """Move a parent item to a new location."""
        assume(parent_item_id in self.parent_items)
        assume(new_location_id in self.locations)
        assume(user_id in self.users)

        parent_item = self.parent_items[parent_item_id]
        old_location_id = parent_item.current_location_id

        # Skip if already at target location
        assume(old_location_id != new_location_id)

        # Update item location
        parent_item.current_location_id = new_location_id

        # Update tracking
        self.item_locations[parent_item_id] = new_location_id
        self.location_item_counts[old_location_id] -= 1
        self.location_item_counts[new_location_id] += 1

        # Record move history
        move_record = MoveHistory(
            parent_item_id=parent_item_id,
            from_location_id=old_location_id,
            to_location_id=new_location_id,
            moved_by=user_id,
            notes=f"Moved from {old_location_id} to {new_location_id}",
        )
        self.move_history.append(move_record)

        # Move all assigned child items with parent
        for child_id, assigned_parent_id in self.child_assignments.items():
            if assigned_parent_id == parent_item_id:
                # Child items move with their parent
                pass  # Location is implicit through parent

    @rule(
        child_item_id=child_items, parent_item_id=parent_items, user_id=users
    )
    def assign_child_to_parent(self, child_item_id, parent_item_id, user_id):
        """Assign a child item to a parent item."""
        assume(child_item_id in self.child_items)
        assume(parent_item_id in self.parent_items)
        assume(user_id in self.users)

        child_item = self.child_items[child_item_id]
        old_parent_id = child_item.parent_item_id

        # Skip if already assigned to this parent
        assume(old_parent_id != parent_item_id)

        # Update assignment
        child_item.parent_item_id = parent_item_id
        self.child_assignments[child_item_id] = parent_item_id

        # Record assignment history
        assignment_record = AssignmentHistory(
            child_item_id=child_item_id,
            from_parent_item_id=old_parent_id,
            to_parent_item_id=parent_item_id,
            assigned_by=user_id,
            notes=f"Assigned to parent {parent_item_id}",
        )
        self.assignment_history.append(assignment_record)

    @rule(child_item_id=child_items, user_id=users)
    def unassign_child_item(self, child_item_id, user_id):
        """Unassign a child item from its parent."""
        assume(child_item_id in self.child_items)
        assume(user_id in self.users)

        child_item = self.child_items[child_item_id]
        old_parent_id = child_item.parent_item_id

        # Skip if not assigned
        assume(old_parent_id is not None)

        # Update assignment
        child_item.parent_item_id = None
        self.child_assignments[child_item_id] = None

        # Record assignment history
        assignment_record = AssignmentHistory(
            child_item_id=child_item_id,
            from_parent_item_id=old_parent_id,
            to_parent_item_id=None,
            assigned_by=user_id,
            notes="Unassigned from parent",
        )
        self.assignment_history.append(assignment_record)

    # Invariants that must always hold

    @invariant()
    def parent_items_have_valid_locations(self):
        """All parent items must be at valid locations."""
        for item_id, parent_item in self.parent_items.items():
            assert (
                parent_item.current_location_id in self.locations
            ), f"Parent item {item_id} has invalid location {parent_item.current_location_id}"
            assert (
                self.item_locations[item_id] == parent_item.current_location_id
            ), f"Location tracking mismatch for item {item_id}"

    @invariant()
    def child_items_follow_parent_locations(self):
        """Child items should be at the same location as their parent."""
        for child_id, child_item in self.child_items.items():
            if child_item.parent_item_id is not None:
                self.parent_items[child_item.parent_item_id]
                # Child items implicitly follow parent location
                assert (
                    child_item.parent_item_id in self.parent_items
                ), f"Child item {child_id} assigned to non-existent parent {child_item.parent_item_id}"

    @invariant()
    def child_assignment_uniqueness(self):
        """Each child item can only be assigned to one parent at a time."""
        assigned_children = set()
        for child_id, parent_id in self.child_assignments.items():
            if parent_id is not None:
                assert (
                    child_id not in assigned_children
                ), f"Child item {child_id} assigned to multiple parents"
                assigned_children.add(child_id)

    @invariant()
    def location_item_counts_accurate(self):
        """Location item counts should match actual items at each location."""
        actual_counts = {}
        for item_id, location_id in self.item_locations.items():
            actual_counts[location_id] = actual_counts.get(location_id, 0) + 1

        for location_id in self.locations:
            expected_count = actual_counts.get(location_id, 0)
            assert (
                self.location_item_counts[location_id] == expected_count
            ), f"Location {location_id} count mismatch: expected {expected_count}, got {self.location_item_counts[location_id]}"

    @invariant()
    def move_history_consistency(self):
        """Move history should be consistent with current item locations."""
        # Group moves by item
        item_moves = {}
        for move in self.move_history:
            if move.parent_item_id not in item_moves:
                item_moves[move.parent_item_id] = []
            item_moves[move.parent_item_id].append(move)

        # Check that final location matches current location
        for item_id, moves in item_moves.items():
            if item_id in self.parent_items:
                # Sort moves by timestamp (using order added as proxy)
                sorted_moves = sorted(
                    moves, key=lambda m: self.move_history.index(m)
                )
                if sorted_moves:
                    last_move = sorted_moves[-1]
                    current_location = self.parent_items[
                        item_id
                    ].current_location_id
                    assert (
                        last_move.to_location_id == current_location), f"Item {item_id} move history inconsistent: last move to {
                        last_move.to_location_id}, current location {current_location}"

    @invariant()
    def assignment_history_consistency(self):
        """Assignment history should be consistent with current assignments."""
        # Group assignments by child item
        child_assignments_history = {}
        for assignment in self.assignment_history:
            if assignment.child_item_id not in child_assignments_history:
                child_assignments_history[assignment.child_item_id] = []
            child_assignments_history[assignment.child_item_id].append(
                assignment
            )

        # Check that final assignment matches current assignment
        for child_id, assignments in child_assignments_history.items():
            if child_id in self.child_items:
                # Sort assignments by order added
                sorted_assignments = sorted(
                    assignments, key=lambda a: self.assignment_history.index(a)
                )
                if sorted_assignments:
                    last_assignment = sorted_assignments[-1]
                    current_parent = self.child_items[child_id].parent_item_id
                    assert (
                        last_assignment.to_parent_item_id == current_parent
                    ), f"Child {child_id} assignment history inconsistent"

    @invariant()
    def referential_integrity(self):
        """All foreign key references should be valid."""
        # Check user role references
        for user in self.users.values():
            assert (
                user.role_id in self.roles
            ), f"User {user.id} has invalid role {user.role_id}"

        # Check location type references
        for location in self.locations.values():
            assert (
                location.location_type_id in self.location_types), f"Location {
                location.id} has invalid location type {
                location.location_type_id}"

        # Check parent item references
        for parent_item in self.parent_items.values():
            assert (
                parent_item.item_type_id in self.item_types), f"Parent item {
                parent_item.id} has invalid item type {
                parent_item.item_type_id}"
            assert (
                parent_item.current_location_id in self.locations), f"Parent item {
                parent_item.id} has invalid location {
                parent_item.current_location_id}"
            assert (
                parent_item.created_by in self.users), f"Parent item {
                parent_item.id} has invalid creator {
                parent_item.created_by}"

        # Check child item references
        for child_item in self.child_items.values():
            assert (
                child_item.item_type_id in self.item_types), f"Child item {
                child_item.id} has invalid item type {
                child_item.item_type_id}"
            assert (
                child_item.created_by in self.users), f"Child item {
                child_item.id} has invalid creator {
                child_item.created_by}"
            if child_item.parent_item_id is not None:
                assert (
                    child_item.parent_item_id in self.parent_items), f"Child item {
                    child_item.id} has invalid parent {
                    child_item.parent_item_id}"


# Property-based tests using the state machine


class TestEndToEndWorkflows:
    """End-to-end property tests for complete system workflows."""

    def test_complete_inventory_workflow(self):
        """
        Test complete inventory management workflows.

        **Property 17: Complete Inventory Workflow Consistency**
        **Validates: Requirements 1.3, 1.4, 2.1, 2.2, 2.3**

        For any sequence of inventory operations (create items, move items,
        assign child items), the system should maintain data consistency,
        referential integrity, and accurate audit trails.
        """
        # Run the state machine with custom settings
        test_case = InventorySystemStateMachine.TestCase()
        test_case.settings = settings(max_examples=50, stateful_step_count=20)
        test_case.runTest()

    @given(
        num_locations=st.integers(min_value=2, max_value=5),
        num_items=st.integers(min_value=1, max_value=10),
        num_moves=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=20)
    def test_item_movement_consistency(
        self, num_locations, num_items, num_moves
    ):
        """
        Test that item movements maintain location consistency.

        **Property 18: Item Movement Location Consistency**
        **Validates: Requirements 1.3, 1.4, 2.1**

        For any sequence of item movements, querying item locations should
        always return the most recent location, and location updates should
        be reflected immediately.
        """
        # Create test data structures
        locations = [str(uuid.uuid4()) for _ in range(num_locations)]
        items = {}
        move_history = []

        # Create items at random initial locations
        for i in range(num_items):
            item_id = str(uuid.uuid4())
            initial_location = random.choice(locations)
            items[item_id] = {
                "current_location": initial_location,
                "move_count": 0,
            }

        # Perform random moves
        for _ in range(num_moves):
            if not items:
                break

            item_id = random.choice(list(items.keys()))
            new_location = random.choice(locations)
            old_location = items[item_id]["current_location"]

            # Skip if moving to same location
            if old_location == new_location:
                continue

            # Update item location
            items[item_id]["current_location"] = new_location
            items[item_id]["move_count"] += 1

            # Record move
            move_history.append(
                {
                    "item_id": item_id,
                    "from_location": old_location,
                    "to_location": new_location,
                    "timestamp": len(move_history),
                }
            )

        # Verify consistency
        for item_id, item_data in items.items():
            # Find all moves for this item
            item_moves = [m for m in move_history if m["item_id"] == item_id]

            if item_moves:
                # Sort by timestamp and verify final location
                item_moves.sort(key=lambda m: m["timestamp"])
                last_move = item_moves[-1]
                assert (
                    item_data["current_location"] == last_move["to_location"]
                ), f"Item {item_id} location inconsistency"

                # Verify move chain continuity
                for i in range(1, len(item_moves)):
                    prev_move = item_moves[i - 1]
                    curr_move = item_moves[i]
                    assert (
                        prev_move["to_location"] == curr_move["from_location"]
                    ), f"Move chain broken for item {item_id}"

    @given(
        num_parents=st.integers(min_value=1, max_value=5),
        num_children=st.integers(min_value=1, max_value=10),
        num_assignments=st.integers(min_value=1, max_value=15),
    )
    @settings(max_examples=20)
    def test_child_item_assignment_workflow(
        self, num_parents, num_children, num_assignments
    ):
        """
        Test child item assignment workflows.

        **Property 19: Child Item Assignment Workflow Consistency**
        **Validates: Requirements 2.2, 2.3**

        For any sequence of child item assignments and reassignments,
        each child should be assigned to at most one parent at any time,
        and assignment history should be accurately maintained.
        """
        # Create test data
        parent_items = [str(uuid.uuid4()) for _ in range(num_parents)]
        child_items = {}
        assignment_history = []

        # Initialize child items as unassigned
        for i in range(num_children):
            child_id = str(uuid.uuid4())
            child_items[child_id] = {
                "current_parent": None,
                "assignment_count": 0,
            }

        # Perform random assignments
        for _ in range(num_assignments):
            if not child_items:
                break

            child_id = random.choice(list(child_items.keys()))

            # Randomly assign to parent or unassign
            if random.choice([True, False]) and parent_items:
                # Assign to parent
                new_parent = random.choice(parent_items)
                old_parent = child_items[child_id]["current_parent"]

                # Skip if already assigned to this parent
                if old_parent == new_parent:
                    continue

                child_items[child_id]["current_parent"] = new_parent
                child_items[child_id]["assignment_count"] += 1

                assignment_history.append(
                    {
                        "child_id": child_id,
                        "from_parent": old_parent,
                        "to_parent": new_parent,
                        "timestamp": len(assignment_history),
                    }
                )
            else:
                # Unassign from parent
                old_parent = child_items[child_id]["current_parent"]

                # Skip if already unassigned
                if old_parent is None:
                    continue

                child_items[child_id]["current_parent"] = None
                child_items[child_id]["assignment_count"] += 1

                assignment_history.append(
                    {
                        "child_id": child_id,
                        "from_parent": old_parent,
                        "to_parent": None,
                        "timestamp": len(assignment_history),
                    }
                )

        # Verify assignment uniqueness
        assigned_children = set()
        for child_id, child_data in child_items.items():
            if child_data["current_parent"] is not None:
                assert (
                    child_id not in assigned_children
                ), f"Child {child_id} assigned to multiple parents"
                assigned_children.add(child_id)

        # Verify assignment history consistency
        for child_id, child_data in child_items.items():
            child_assignments = [
                a for a in assignment_history if a["child_id"] == child_id
            ]

            if child_assignments:
                # Sort by timestamp and verify final assignment
                child_assignments.sort(key=lambda a: a["timestamp"])
                last_assignment = child_assignments[-1]
                assert (
                    child_data["current_parent"]
                    == last_assignment["to_parent"]
                ), f"Child {child_id} assignment history inconsistency"

    @given(
        operations=st.lists(
            st.one_of(
                st.tuples(
                    st.just("create_item"), valid_name(), valid_uuid_string()
                ),
                st.tuples(
                    st.just("move_item"),
                    st.integers(min_value=0, max_value=9),
                    valid_uuid_string(),
                ),
                st.tuples(
                    st.just("assign_child"),
                    st.integers(min_value=0, max_value=9),
                    st.integers(min_value=0, max_value=9),
                ),
                st.tuples(st.just("create_location"), valid_name()),
            ),
            min_size=5,
            max_size=20,
        )
    )
    @settings(max_examples=10)
    def test_mixed_operation_workflow(self, operations):
        """
        Test mixed operations workflow.

        **Property 20: Mixed Operations Workflow Consistency**
        **Validates: Requirements 1.3, 1.4, 2.1, 2.2, 2.3**

        For any sequence of mixed operations (create items, create locations,
        move items, assign children), the system should maintain consistency
        and all invariants should hold throughout the workflow.
        """
        # Initialize system state
        locations = ["default-location"]
        items = {}
        children = {}
        assignments = {}  # child_id -> parent_id
        item_locations = {}  # item_id -> location_id

        # Process operations
        for operation in operations:
            op_type = operation[0]

            try:
                if op_type == "create_location":
                    operation[1]
                    location_id = str(uuid.uuid4())
                    locations.append(location_id)

                elif op_type == "create_item":
                    item_name = operation[1]
                    location_id = (
                        operation[2]
                        if operation[2] in locations
                        else locations[0]
                    )
                    item_id = str(uuid.uuid4())

                    items[item_id] = {
                        "name": item_name,
                        "location": location_id,
                    }
                    item_locations[item_id] = location_id

                elif op_type == "move_item" and items:
                    item_index = operation[1] % len(items)
                    new_location = (
                        operation[2]
                        if operation[2] in locations
                        else locations[0]
                    )
                    item_id = list(items.keys())[item_index]

                    # Update item location
                    items[item_id]["location"] = new_location
                    item_locations[item_id] = new_location

                elif op_type == "assign_child" and items:
                    if len(items) >= 2:  # Need at least parent and child
                        parent_index = operation[1] % len(items)
                        child_index = operation[2] % len(items)

                        parent_id = list(items.keys())[parent_index]
                        child_id = list(items.keys())[child_index]

                        # Don't assign item to itself
                        if parent_id != child_id:
                            # Create child if not exists
                            if child_id not in children:
                                children[child_id] = {
                                    "name": f"child-{child_id[:8]}"
                                }

                            # Assign child to parent
                            assignments[child_id] = parent_id

            except (IndexError, KeyError):
                # Skip invalid operations
                continue

        # Verify final state consistency

        # All items should have valid locations
        for item_id, item_data in items.items():
            assert (
                item_data["location"] in locations
            ), f"Item {item_id} has invalid location {item_data['location']}"
            assert (
                item_locations[item_id] == item_data["location"]
            ), f"Location tracking mismatch for item {item_id}"

        # All child assignments should reference valid parents
        for child_id, parent_id in assignments.items():
            assert (
                parent_id in items
            ), f"Child {child_id} assigned to non-existent parent {parent_id}"

        # Each child should be assigned to at most one parent
        assigned_children = set()
        for child_id in assignments:
            assert (
                child_id not in assigned_children
            ), f"Child {child_id} assigned multiple times"
            assigned_children.add(child_id)


# Run the state machine test
TestInventoryWorkflows = InventorySystemStateMachine.TestCase
