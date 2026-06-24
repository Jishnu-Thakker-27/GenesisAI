import pytest
from core.pipeline import GenesisPipeline
from core.contracts import FinalCompiledApplication


def test_restaurant_domain_intelligence():
    pipeline = GenesisPipeline(execution_mode="BALANCED", intelligence_mode="HYBRID")
    app_res = pipeline.run_pipeline("Build me a restaurant app")
    
    assert isinstance(app_res, FinalCompiledApplication)
    
    # 1. Intent Extraction & Domain Detection
    intent = app_res.intent
    assert intent.detected_domain == "Restaurant Management"
    assert intent.detected_subdomain == "Food Ordering & Reservations"
    assert intent.domain_confidence == 0.94
    
    # Verify expected actors
    actor_names = {a.name for a in intent.actors}
    assert "Customer" in actor_names
    assert "RestaurantOwner" in actor_names
    
    # Verify expected entities
    assert "Menu" in intent.entities
    assert "MenuItem" in intent.entities
    assert "Order" in intent.entities
    assert "Reservation" in intent.entities
    assert "Payment" in intent.entities
    
    # Verify expected workflows
    assert "Browse Menu" in intent.workflows
    assert "Place Order" in intent.workflows
    assert "Checkout" in intent.workflows

    # 2. Requirements Intelligence Report Verification
    report = app_res.ai_architect_report
    assert report.detected_domain == "Restaurant Management"
    assert report.detected_subdomain == "Food Ordering & Reservations"
    assert report.confidence_score > 0
    
    # Non-empty verification
    assert len(report.confidence_explanation) > 0
    assert len(report.ambiguities) > 0
    assert len(report.assumptions) > 0
    assert len(report.clarification_questions) > 0
    assert len(report.risks) > 0
    assert len(report.reasoning_trace) > 0
    
    # Verify confidence explanation has domain and Order workflow details
    assert any("Restaurant Management" in exp for exp in report.confidence_explanation)
    assert any("Order" in exp or "order" in exp.lower() for exp in report.confidence_explanation)
    
    # Verify structured ambiguities
    assert any(amb.category == "Business Logic" for amb in report.ambiguities)
    assert any(amb.severity in ("HIGH", "MEDIUM", "LOW") for amb in report.ambiguities)
    assert any(len(amb.issue) > 0 for amb in report.ambiguities)

    # 3. Spec Compilation & Verification using Report as Source of Truth
    spec = app_res.system_design
    
    spec_entities = {e.name for e in spec.entities}
    spec_workflows = {w.workflow_name for w in spec.workflows}
    spec_actors = {a.name for a in spec.actors}
    
    # Check reports is source of truth
    assert spec_entities == set(report.entities)
    assert spec_workflows == set(report.workflows)
    assert spec_actors == set(report.actors)

    # Generic check
    assert "AccessPlatform" not in spec_entities
    assert "User" not in spec_entities
    assert "GenericPlatform" not in spec_entities


def test_hospital_domain_intelligence():
    pipeline = GenesisPipeline(execution_mode="BALANCED", intelligence_mode="HYBRID")
    app_res = pipeline.run_pipeline("Build me a hospital management system")
    
    assert isinstance(app_res, FinalCompiledApplication)
    
    intent = app_res.intent
    assert intent.detected_domain == "Healthcare"
    assert intent.detected_subdomain == "Patient Care & Appointment Scheduling"
    
    actor_names = {a.name for a in intent.actors}
    assert "Patient" in actor_names
    assert "Doctor" in actor_names
    assert "Admin" in actor_names
    
    assert "Patient" in intent.entities
    assert "Doctor" in intent.entities
    assert "Appointment" in intent.entities
    assert "MedicalRecord" in intent.entities
    assert "Prescription" in intent.entities
    
    assert "Schedule Appointment" in intent.workflows
    assert "Consultation" in intent.workflows
    assert "Prescription Management" in intent.workflows

    report = app_res.ai_architect_report
    assert report.detected_domain == "Healthcare"
    assert report.confidence_score > 0
    assert len(report.confidence_explanation) > 0
    assert len(report.ambiguities) > 0
    assert len(report.assumptions) > 0
    assert len(report.clarification_questions) > 0
    assert len(report.risks) > 0
    assert len(report.reasoning_trace) > 0

    spec = app_res.system_design
    assert {e.name for e in spec.entities} == set(report.entities)
    assert {w.workflow_name for w in spec.workflows} == set(report.workflows)
    assert {a.name for a in spec.actors} == set(report.actors)


def test_ecommerce_domain_intelligence():
    pipeline = GenesisPipeline(execution_mode="BALANCED", intelligence_mode="HYBRID")
    app_res = pipeline.run_pipeline("Build me an ecommerce marketplace")
    
    assert isinstance(app_res, FinalCompiledApplication)
    
    intent = app_res.intent
    assert intent.detected_domain == "E-Commerce"
    assert intent.detected_subdomain == "Digital Retail & Cart Management"
    
    actor_names = {a.name for a in intent.actors}
    assert "Buyer" in actor_names
    assert "Seller" in actor_names
    assert "Admin" in actor_names
    
    assert "Product" in intent.entities
    assert "Cart" in intent.entities
    assert "Order" in intent.entities
    assert "Payment" in intent.entities
    assert "Inventory" in intent.entities
    
    assert "Browse Products" in intent.workflows
    assert "Add To Cart" in intent.workflows
    assert "Checkout" in intent.workflows
    assert "Order Fulfillment" in intent.workflows

    report = app_res.ai_architect_report
    assert report.detected_domain == "E-Commerce"
    assert report.confidence_score > 0
    assert len(report.confidence_explanation) > 0
    assert len(report.ambiguities) > 0
    assert len(report.assumptions) > 0
    assert len(report.clarification_questions) > 0
    assert len(report.risks) > 0
    assert len(report.reasoning_trace) > 0

    spec = app_res.system_design
    assert {e.name for e in spec.entities} == set(report.entities)
    assert {w.workflow_name for w in spec.workflows} == set(report.workflows)
    assert {a.name for a in spec.actors} == set(report.actors)


def test_hotel_domain_intelligence():
    pipeline = GenesisPipeline(execution_mode="BALANCED", intelligence_mode="HYBRID")
    app_res = pipeline.run_pipeline("Build me a hotel booking platform")
    
    assert isinstance(app_res, FinalCompiledApplication)
    
    intent = app_res.intent
    assert intent.detected_domain == "Hospitality Management"
    assert intent.detected_subdomain == "Room Reservation & Guest Lodging"
    
    actor_names = {a.name for a in intent.actors}
    assert "Guest" in actor_names
    assert "HotelManager" in actor_names
    
    assert "Room" in intent.entities
    assert "Booking" in intent.entities
    assert "Guest" in intent.entities
    assert "Payment" in intent.entities
    
    assert "Search Rooms" in intent.workflows
    assert "Book Room" in intent.workflows
    assert "Payment" in intent.workflows
    assert "Check In" in intent.workflows

    report = app_res.ai_architect_report
    assert report.detected_domain == "Hospitality Management"
    assert report.confidence_score > 0
    assert len(report.confidence_explanation) > 0
    assert len(report.ambiguities) > 0
    assert len(report.assumptions) > 0
    assert len(report.clarification_questions) > 0
    assert len(report.risks) > 0
    assert len(report.reasoning_trace) > 0

    spec = app_res.system_design
    assert {e.name for e in spec.entities} == set(report.entities)
    assert {w.workflow_name for w in spec.workflows} == set(report.workflows)
    assert {a.name for a in spec.actors} == set(report.actors)
