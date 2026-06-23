import os
import tempfile
import pytest
from pydantic import ValidationError

from core.naming import CanonicalNamingEngine
from core.ast import (
    Actor, EntityField, Entity, APIEndpoint, UIView, BusinessRule,
    MasterSpecification, ValidationError as SpecValidationError
)
from config import DB_PATH
from database.connection import init_db, get_connection


# --- CanonicalNamingEngine Tests ---

def test_naming_engine_sanitize():
    assert CanonicalNamingEngine.sanitize("Hello, World!") == "Hello World"
    assert CanonicalNamingEngine.sanitize("gym_class_booking") == "gym class booking"
    assert CanonicalNamingEngine.sanitize("member-profile") == "member profile"

def test_naming_engine_to_pascal_case():
    assert CanonicalNamingEngine.to_pascal_case("gym class booking") == "GymClassBooking"
    assert CanonicalNamingEngine.to_pascal_case("member-profile") == "MemberProfile"
    assert CanonicalNamingEngine.to_pascal_case("user_auth") == "UserAuth"
    assert CanonicalNamingEngine.to_pascal_case("") == ""

def test_naming_engine_to_snake_case():
    assert CanonicalNamingEngine.to_snake_case("Gym Class Booking") == "gym_class_booking"
    # Test Camel/Pascal detection
    assert CanonicalNamingEngine.to_snake_case("GymClassBooking") == "gym_class_booking"
    assert CanonicalNamingEngine.to_snake_case("member-profile") == "member_profile"
    assert CanonicalNamingEngine.to_snake_case("") == ""

def test_naming_engine_to_kebab_case():
    assert CanonicalNamingEngine.to_kebab_case("Gym Class Booking") == "gym-class-booking"
    assert CanonicalNamingEngine.to_kebab_case("") == ""

def test_naming_engine_sanitize_endpoint_path():
    assert CanonicalNamingEngine.sanitize_endpoint_path("/api/v1/gym class bookings/{bookingId}") == "/api/v1/gym-class-bookings/{booking_id}"
    assert CanonicalNamingEngine.sanitize_endpoint_path("bookings/{id}") == "bookings/{id}"
    assert CanonicalNamingEngine.sanitize_endpoint_path("") == "/"


# --- AST & Pydantic Validation Tests ---

def test_actor_name_normalization():
    actor = Actor(name="gym trainer", description="Teaches classes")
    assert actor.name == "GymTrainer"  # Auto-formatted to PascalCase

def test_entity_and_fields_normalization():
    field = EntityField(name="Booking Date", type="datetime")
    assert field.name == "booking_date"
    assert field.type == "datetime"

    with pytest.raises(ValidationError):
        # Invalid type should fail validation
        EntityField(name="invalid_field", type="unknown_type")

    entity = Entity(
        name="class booking",
        description="Booking record",
        fields=[field],
        constraints=["Unique booking_date per user"]
    )
    assert entity.name == "ClassBooking"

def test_endpoint_normalization():
    endpoint = APIEndpoint(
        path="/api/v1/create booking/{bookingId}",
        method="post",
        request_body_entity="class booking",
        response_body_entity="booking confirmation",
        roles_allowed=["gym member"],
        description="Creates a new booking"
    )
    assert endpoint.path == "/api/v1/create-booking/{booking_id}"
    assert endpoint.method == "POST"
    assert endpoint.request_body_entity == "ClassBooking"
    assert endpoint.response_body_entity == "BookingConfirmation"

    with pytest.raises(ValidationError):
        # Invalid method should fail
        APIEndpoint(
            path="/test",
            method="PATCH_UNKNOWN",
            roles_allowed=["admin"],
            description="fail"
        )

def test_ui_view_normalization():
    view = UIView(
        name="booking form",
        type="form",
        actor="gym member",
        entity_source="booking",
        actions=["SubmitBooking"]
    )
    assert view.name == "BookingForm"
    assert view.type == "Form"
    assert view.actor == "GymMember"
    assert view.entity_source == "Booking"


# --- Database Setup & Seeding Tests ---

def test_database_initialization():
    # Use a temporary database file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db_path = tmp.name
    
    # Override global DB_PATH for the test
    import database.connection
    original_db_path = database.connection.DB_PATH
    database.connection.DB_PATH = temp_db_path
    
    try:
        init_db()
        
        # Verify tables and seed data
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check innovations table count
            cursor.execute("SELECT COUNT(*) FROM innovations;")
            count = cursor.fetchone()[0]
            assert count == 4
            
            # Check a specific innovation
            cursor.execute("SELECT name, category, acceptance_rate FROM innovations WHERE id = 'inn_001';")
            row = cursor.fetchone()
            assert row["name"] == "AI Trainer Matching"
            assert row["category"] == "Gym"
            assert row["acceptance_rate"] == 0.89
            
    finally:
        # Restore configuration and clean up file
        database.connection.DB_PATH = original_db_path
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
