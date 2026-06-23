import pytest
import os
import json
import copy
from datetime import datetime
from typing import Dict, Any

from stages.stage3_recommend import ApprovedBlueprint, RecommendedActor, RecommendedFeature, FeatureExplanation, RecommendationSource, RecommendedWorkflow, RecommendedPermission
from stages.stage4_system import MasterSpecificationBuilder, WorkflowDefinition, BusinessRuleDefinition, MasterSpecification
from stages.stage5_schema import CompiledSchemaBundleBuilder, DatabaseTableDefinition, ColumnDefinition, CompiledSchemaBundle, TraceabilityMetadata, AuthRuleDefinition
from stages.stage9_change import (
    RequirementChangeRequest, ChangeSet, ChangeDependencyGraph, ChangeImpactScore,
    ChangeComplexityScore, ImpactAnalysisReport, ChangeConflict, ConflictDetectionReport,
    ChangeRiskAssessment, RequirementVersion, RollbackPoint, ChangeDiff, ChangeEffectivenessReport,
    EvolutionTimelineEntry, EvolutionTimeline, RequirementChangeReport, ChangeDetector,
    ChangeDependencyGraphBuilder, ConflictDetectionEngine, ChangeComplexityScoreCalculator,
    ChangeRiskAssessmentEngine, ChangePropagationEngine, ChangeSafetyEngine,
    EvolutionTimelineManager, RequirementChangeEngine
)

@pytest.fixture(autouse=True)
def clean_timeline():
    # Cleanup timeline file before and after tests
    timeline_file = EvolutionTimelineManager.TIMELINE_PATH
    if os.path.exists(timeline_file):
        os.remove(timeline_file)
    yield
    if os.path.exists(timeline_file):
        os.remove(timeline_file)


# --- FIXTURES FOR 5 DOMAINS ---

@pytest.fixture
def gym_domain_blueprint() -> ApprovedBlueprint:
    rec_member = RecommendedActor(name="GymMember", description="A gym member", relevance_score=1.0, why_needed="Book classes")
    rec_admin = RecommendedActor(name="Admin", description="Admin user", relevance_score=0.90, why_needed="Manage gym")
    
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="BookClass", what_it_does="Book slot", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="BookClass", description="Book class slots", actor_involved="GymMember", explanation=explanation)
    
    rec_wf = RecommendedWorkflow(
        name="ClassBookingFlow", description="Book spot", steps=["Select Class", "Verify Capacity", "Log Booking Record"], actor_involved="GymMember", why_needed="Core flow"
    )
    
    rec_perm = RecommendedPermission(actor="GymMember", action="BookClass", description="Book slots", why_needed="Required")
    
    return ApprovedBlueprint(
        project_id="test_gym_project",
        app_type="Gym",
        actors=[rec_member, rec_admin],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[rec_perm],
        innovations=[]
    )


@pytest.fixture
def crm_domain_blueprint() -> ApprovedBlueprint:
    rec_agent = RecommendedActor(name="SalesAgent", description="Sales agent", relevance_score=1.0, why_needed="Track leads")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="LeadTracking", what_it_does="Track lead", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="LeadTracking", description="Sales funnel lead tracking", actor_involved="SalesAgent", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="LeadConversionFlow", description="Convert lead", steps=["Qualify", "Convert"], actor_involved="SalesAgent", why_needed="Funnel flow"
    )
    
    return ApprovedBlueprint(
        project_id="test_crm_project",
        app_type="CRM",
        actors=[rec_agent],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )


@pytest.fixture
def hospital_domain_blueprint() -> ApprovedBlueprint:
    rec_doc = RecommendedActor(name="Doctor", description="Practitioner", relevance_score=1.0, why_needed="Treat patients")
    rec_patient = RecommendedActor(name="Patient", description="Patient profile", relevance_score=1.0, why_needed="Book appointments")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="AppointmentScheduling", what_it_does="Schedule", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="AppointmentScheduling", description="Manage appointments", actor_involved="Doctor", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="AppointmentSchedulingFlow", description="Schedule appt", steps=["Request Appointment", "Book Appointment"], actor_involved="Patient", why_needed="Access flow"
    )
    
    return ApprovedBlueprint(
        project_id="test_hospital_project",
        app_type="Hospital",
        actors=[rec_doc, rec_patient],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )


@pytest.fixture
def school_domain_blueprint() -> ApprovedBlueprint:
    rec_student = RecommendedActor(name="Student", description="Student profile", relevance_score=1.0, why_needed="Learn")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="CourseEnrollment", what_it_does="Enroll", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="CourseEnrollment", description="Enroll in courses", actor_involved="Student", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="CourseEnrollmentFlow", description="Enroll workflow", steps=["Choose", "Add"], actor_involved="Student", why_needed="Course flow"
    )
    
    return ApprovedBlueprint(
        project_id="test_school_project",
        app_type="School",
        actors=[rec_student],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )


@pytest.fixture
def inventory_domain_blueprint() -> ApprovedBlueprint:
    rec_staff = RecommendedActor(name="WarehouseStaff", description="Staff profile", relevance_score=1.0, why_needed="Manage goods")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="ReceiveStock", what_it_does="Stock", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="ReceiveStock", description="Stock levels management", actor_involved="WarehouseStaff", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="ReceiveStockFlow", description="Receive stock run", steps=["Arrive", "Unload"], actor_involved="WarehouseStaff", why_needed="Inventory flow"
    )
    
    return ApprovedBlueprint(
        project_id="test_inventory_project",
        app_type="Inventory",
        actors=[rec_staff],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )


# --- REQUIRED TEST CASES ---

# 1. test_only_affected_components_change
def test_only_affected_components_change(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Propose safety check between identical bundles
    report = ImpactAnalysisReport(
        affected_components=[],
        unaffected_components=["Table:member", "API:get_member_list"],
        estimated_effort="Low",
        impact_score=ChangeImpactScore()
    )
    
    bundle_copied = copy.deepcopy(bundle)
    
    # Should be safe since nothing changed
    assert ChangeSafetyEngine.verify_safety(bundle, bundle_copied, report) is True
    
    # Modify a preserved component (member columns)
    member_table = next(t for t in bundle_copied.database_schema if t.table_name == "member")
    member_table.columns.append(
        ColumnDefinition(name="unsafe_col", type="string", is_primary_key=False, is_nullable=True)
    )
    
    # Should fail safety checks since member was marked unaffected but changed
    assert ChangeSafetyEngine.verify_safety(bundle, bundle_copied, report) is False


# 2. test_rollback_after_simulation_failure
def test_rollback_after_simulation_failure(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Propose a workflow change that introduces a state transition violation
    # Transitioning COMPLETED -> PENDING is disallowed by default state transition rules
    req = RequirementChangeRequest(
        change_id="change_sim_fail",
        change_type="MODIFY_WORKFLOW",
        description="Modify workflow to include disallowed transition",
        payload={
            "name": "ClassBookingFlow",
            "workflow_steps": ["Select Class", "Confirm Booking", "Complete Booking", "Reopen Booking"]
        }
    )
    
    report = RequirementChangeEngine.apply_change(gym_domain_blueprint, spec, bundle, req)
    
    # Should roll back because simulation fails on step "Reopen Booking" due to state transition rejection
    assert report.effectiveness.rollback_required is True
    assert report.effectiveness.simulation_passed is False
    assert report.updated_bundle is None
    assert report.updated_spec is None


# 3. test_conflict_severity_classification
def test_conflict_severity_classification(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)

    # Entity Removal Conflict: removing 'Member' while referenced by 'ClassBooking'
    changes = ChangeSet(removed=["Member"])
    report = ConflictDetectionEngine.detect_conflicts(spec, bundle, changes)
    
    assert report.is_valid is False
    assert len(report.conflicts) > 0
    # The conflict severity must be HIGH (blocking)
    assert report.conflicts[0].severity == "HIGH"
    assert report.conflicts[0].conflict_type == "ENTITY_REMOVAL"


# 4. test_evolution_timeline_ordering
def test_evolution_timeline_ordering(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Start with empty timeline
    timeline = EvolutionTimelineManager.load_timeline()
    assert len(timeline.entries) == 0
    
    # Apply change 1
    req1 = RequirementChangeRequest(
        change_id="ver_1.1",
        change_type="ADD_FEATURE",
        description="Add custom schedules",
        payload={"name": "CustomSchedule"}
    )
    report1 = RequirementChangeEngine.apply_change(gym_domain_blueprint, spec, bundle, req1)
    assert report1.effectiveness.rollback_required is False
    
    # Apply change 2 using updated spec and bundle
    req2 = RequirementChangeRequest(
        change_id="ver_1.2",
        change_type="ADD_FEATURE",
        description="Add trainer specialties",
        payload={"name": "Specialty"}
    )
    report2 = RequirementChangeEngine.apply_change(
        report1.updated_blueprint, report1.updated_spec, report1.updated_bundle, req2
    )
    assert report2.effectiveness.rollback_required is False
    
    # Load timeline and verify chronological ordering (ver_1.1 before ver_1.2)
    timeline_reloaded = EvolutionTimelineManager.load_timeline()
    assert len(timeline_reloaded.entries) == 2
    assert timeline_reloaded.entries[0].version_id == "ver_1.1"
    assert timeline_reloaded.entries[1].version_id == "ver_1.2"


# 5. test_change_complexity_scoring
def test_change_complexity_scoring(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Propose low complexity change (adding single Guest actor)
    req_low = RequirementChangeRequest(
        change_id="change_guest",
        change_type="ADD_ACTOR",
        description="Add a Guest actor",
        payload={"name": "Guest"}
    )
    changes_low = ChangeDetector.detect_changes(gym_domain_blueprint, req_low)
    dep_graph_low = ChangeDependencyGraphBuilder.build_graph(spec, bundle, changes_low)
    imp_score_low, complexity_low = ChangeComplexityScoreCalculator.calculate(dep_graph_low, changes_low)
    
    assert complexity_low.complexity_level == "LOW"
    assert imp_score_low.impact_level == "LOW"
    assert complexity_low.score >= 0.0


# 6. test_dependency_graph_generation
def test_dependency_graph_generation(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Modify BookClass feature
    req = RequirementChangeRequest(
        change_id="change_mod_feat",
        change_type="MODIFY_FEATURE",
        description="Modify BookClass feature description",
        payload={"name": "BookClass", "description": "New description"}
    )
    changes = ChangeDetector.detect_changes(gym_domain_blueprint, req)
    dep_graph = ChangeDependencyGraphBuilder.build_graph(spec, bundle, changes)
    
    # Assert dependency graph generates fields correctly
    assert dep_graph.changed_component == "BookClass"
    assert dep_graph.dependency_depth >= 1
    affected_names = [d.split(":")[-1] for d in dep_graph.directly_affected + dep_graph.indirectly_affected]
    assert any("book_class" in name for name in affected_names)


# 7. test_incremental_update_gym
def test_incremental_update_gym(gym_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Add SubscriptionPlan incrementally
    req = RequirementChangeRequest(
        change_id="gym_update_001",
        change_type="ADD_FEATURE",
        description="Add SubscriptionPlan feature",
        payload={"name": "SubscriptionPlan", "description": "Subscription schemes for gym"}
    )
    report = RequirementChangeEngine.apply_change(gym_domain_blueprint, spec, bundle, req)
    
    assert report.effectiveness.rollback_required is False
    assert report.effectiveness.validation_passed is True
    assert report.updated_bundle is not None
    
    table_names = {t.table_name for t in report.updated_bundle.database_schema}
    assert "subscription_plan" in table_names


# 8. test_incremental_update_crm
def test_incremental_update_crm(crm_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(crm_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Add CustomerFeedback incrementally
    req = RequirementChangeRequest(
        change_id="crm_update_001",
        change_type="ADD_FEATURE",
        description="Add customer feedback feature",
        payload={"name": "CustomerFeedback", "description": "Customer comments and feedback"}
    )
    report = RequirementChangeEngine.apply_change(crm_domain_blueprint, spec, bundle, req)
    
    assert report.effectiveness.rollback_required is False
    assert report.effectiveness.validation_passed is True
    assert report.updated_bundle is not None
    
    table_names = {t.table_name for t in report.updated_bundle.database_schema}
    assert "customer_feedback" in table_names


# 9. test_incremental_update_hospital
def test_incremental_update_hospital(hospital_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(hospital_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Add BillingInvoice incrementally
    req = RequirementChangeRequest(
        change_id="hospital_update_001",
        change_type="ADD_FEATURE",
        description="Add billing and invoicing",
        payload={"name": "BillingInvoice", "description": "Track billing and patient payments"}
    )
    report = RequirementChangeEngine.apply_change(hospital_domain_blueprint, spec, bundle, req)
    
    assert report.effectiveness.rollback_required is False
    assert report.effectiveness.validation_passed is True
    assert report.updated_bundle is not None
    
    table_names = {t.table_name for t in report.updated_bundle.database_schema}
    assert "billing_invoice" in table_names


# 10. test_incremental_update_school
def test_incremental_update_school(school_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(school_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Add AttendanceRecord incrementally
    req = RequirementChangeRequest(
        change_id="school_update_001",
        change_type="ADD_FEATURE",
        description="Add student attendance tracking",
        payload={"name": "AttendanceRecord", "description": "Track student attendance logs"}
    )
    report = RequirementChangeEngine.apply_change(school_domain_blueprint, spec, bundle, req)
    
    assert report.effectiveness.rollback_required is False
    assert report.effectiveness.validation_passed is True
    assert report.updated_bundle is not None
    
    table_names = {t.table_name for t in report.updated_bundle.database_schema}
    assert "attendance_record" in table_names


# 11. test_incremental_update_inventory
def test_incremental_update_inventory(inventory_domain_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(inventory_domain_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Add StockAlert incrementally
    req = RequirementChangeRequest(
        change_id="inventory_update_001",
        change_type="ADD_FEATURE",
        description="Add stock alerts feature",
        payload={"name": "StockAlert", "description": "Notify when stock is below threshold"}
    )
    report = RequirementChangeEngine.apply_change(inventory_domain_blueprint, spec, bundle, req)
    
    assert report.effectiveness.rollback_required is False
    assert report.effectiveness.validation_passed is True
    assert report.updated_bundle is not None
    
    table_names = {t.table_name for t in report.updated_bundle.database_schema}
    assert "stock_alert" in table_names
