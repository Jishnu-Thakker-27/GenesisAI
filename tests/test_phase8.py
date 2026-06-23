import pytest
import os
import json
from datetime import datetime
from typing import Dict, Any

from stages.stage3_recommend import ApprovedBlueprint, RecommendedActor, RecommendedFeature, FeatureExplanation, RecommendationSource, RecommendedWorkflow, RecommendedPermission
from stages.stage4_system import MasterSpecificationBuilder, WorkflowDefinition, BusinessRuleDefinition, MasterSpecification
from stages.stage5_schema import CompiledSchemaBundleBuilder, DatabaseTableDefinition, ColumnDefinition, CompiledSchemaBundle, TraceabilityMetadata, AuthRuleDefinition
from stages.stage8_execution import (
    SimulationState, SimulationAction, SimulationTrace, StateTransitionRule,
    BusinessRuleViolation, FailureClassification, ExecutionSimulationReport,
    DeterminismReport, EvaluationLeaderboardEntry, EvaluationReport,
    DatabaseSimulator, AuthSimulator, APISimulator, BusinessRuleSimulator,
    WorkflowSimulator, ExecutionSimulator, EvaluationFramework, EvaluationDataset
)

@pytest.fixture
def gym_approved_blueprint() -> ApprovedBlueprint:
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

# --- 1. SIMULATION STATE & ACTION MODELS TESTS ---

def test_simulation_models():
    state = SimulationState(
        state_id="sim_state_001",
        current_actor="GymMember",
        current_entity="ClassBooking",
        current_workflow_step="Select Class",
        available_actions=["BookClass", "CancelBooking"],
        context={"class_id": "c1"}
    )
    assert state.state_id == "sim_state_001"
    assert state.current_actor == "GymMember"
    assert state.context["class_id"] == "c1"

    action = SimulationAction(
        action_id="act_001",
        actor="GymMember",
        action="BookClass",
        target="ClassBooking",
        preconditions=["has_active_membership"],
        expected_result="Booking created"
    )
    assert action.action_id == "act_001"
    assert action.expected_result == "Booking created"

    trace = SimulationTrace(
        actor="GymMember",
        action="BookClass",
        outcome="SUCCESS",
        reason="Preconditions met.",
        affected_components=["class_booking"]
    )
    assert trace.outcome == "SUCCESS"
    assert len(trace.affected_components) == 1

# --- 2. DATABASE SIMULATOR TESTS ---

def test_database_simulator():
    trace = TraceabilityMetadata(source_ast_version="v1.0")

    # Define simple database table schema
    member_table = DatabaseTableDefinition(
        table_name="member",
        columns=[
            ColumnDefinition(name="id", type="string", is_primary_key=True, is_nullable=False),
            ColumnDefinition(name="name", type="string", is_primary_key=False, is_nullable=False),
            ColumnDefinition(name="email", type="string", is_primary_key=False, is_nullable=True),
        ],
        primary_keys=["id"],
        foreign_keys=[],
        indexes=[],
        source_entity="Member",
        traceability=trace
    )
    booking_table = DatabaseTableDefinition(
        table_name="class_booking",
        columns=[
            ColumnDefinition(name="id", type="string", is_primary_key=True, is_nullable=False),
            ColumnDefinition(name="member_id", type="string", is_primary_key=False, is_nullable=False),
            ColumnDefinition(name="status", type="string", is_primary_key=False, is_nullable=False)
        ],
        primary_keys=["id"],
        foreign_keys=[{
            "column": "member_id",
            "references_table": "member",
            "references_column": "id"
        }],
        indexes=[],
        source_entity="ClassBooking",
        traceability=trace
    )
    
    db_sim = DatabaseSimulator([member_table, booking_table])
    
    # Test insertion
    success, msg = db_sim.insert("member", {"id": "m1", "name": "Alice", "email": "alice@gmail.com"})
    assert success is True
    
    # Test duplication primary key
    success, msg = db_sim.insert("member", {"id": "m1", "name": "Duplicate Alice"})
    assert success is False
    assert "already exists" in msg

    # Test nullability violation
    success, msg = db_sim.insert("member", {"id": "m2", "email": "no-name@gmail.com"})
    assert success is False
    assert "Nullability constraint violation" in msg

    # Test select
    rows = db_sim.select("member", {"id": "m1"})
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"

    # Test foreign key violation
    success, msg = db_sim.insert("class_booking", {"id": "b1", "member_id": "m_invalid", "status": "PENDING"})
    assert success is False
    assert "Foreign key violation" in msg

    # Test successful foreign key insert
    success, msg = db_sim.insert("class_booking", {"id": "b1", "member_id": "m1", "status": "PENDING"})
    assert success is True

    # Test update
    success, msg = db_sim.update("member", "m1", {"email": "alice_updated@gmail.com"})
    assert success is True
    assert db_sim.select("member", {"id": "m1"})[0]["email"] == "alice_updated@gmail.com"

    # Test update foreign key failure
    success, msg = db_sim.update("class_booking", "b1", {"member_id": "m_invalid"})
    assert success is False
    assert "Foreign key violation on update" in msg

    # Test delete restrict (cannot delete member if class_booking refers to it)
    success, msg = db_sim.delete("member", "m1")
    assert success is False
    assert "Foreign key restrict" in msg

    # Delete booking first, then delete member
    success, msg = db_sim.delete("class_booking", "b1")
    assert success is True
    success, msg = db_sim.delete("member", "m1")
    assert success is True

# --- 3. AUTH SIMULATOR TESTS ---

def test_auth_simulator():
    trace = TraceabilityMetadata(source_ast_version="v1.0")
    auth_schema = [
        AuthRuleDefinition(
            rule_id="r1",
            role="GymMember",
            permissions=["BookClass", "execute_class_booking_flow", "DeleteUser"],
            restricted_actions=["DeleteUser"],
            traceability=trace
        ),
        AuthRuleDefinition(
            rule_id="r2",
            role="Admin",
            permissions=["ManageAllRecords"],
            restricted_actions=[],
            traceability=trace
        )
    ]
    
    # Test Admin access
    ok, msg = AuthSimulator.check_permission("Admin", "DeleteUser", auth_schema)
    assert ok is True

    # Test GymMember allowed action
    ok, msg = AuthSimulator.check_permission("GymMember", "BookClass", auth_schema)
    assert ok is True

    # Test GymMember missing permission
    ok, msg = AuthSimulator.check_permission("GymMember", "ViewAdminDashboard", auth_schema)
    assert ok is False
    assert "lacks permission" in msg

    # Test GymMember explicitly restricted action
    ok, msg = AuthSimulator.check_permission("GymMember", "DeleteUser", auth_schema)
    assert ok is False
    assert "explicitly restricted" in msg

# --- 4. API SIMULATOR TESTS ---

def test_api_simulator(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    db_sim = DatabaseSimulator(bundle.database_schema)
    
    # Test API call GET all members
    ok, msg, res = APISimulator.simulate_call("GET", "/api/v1/members", {}, "Admin", bundle, db_sim)
    assert ok is True
    assert isinstance(res, list)

    # Test API call POST (creates new record)
    body = {
        "id": "member_val_charlie",
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@gmail.com",
        "membership_status": "ACTIVE"
    }
    ok, msg, res = APISimulator.simulate_call("POST", "/api/v1/members", body, "Admin", bundle, db_sim)
    assert ok is True
    assert res["id"] == "member_val_charlie"

    # Test GET single record
    ok, msg, res_get = APISimulator.simulate_call("GET", "/api/v1/members/member_val_charlie", {}, "Admin", bundle, db_sim)
    assert ok is True
    assert res_get["first_name"] == "Charlie"

    # Test PUT update record
    body_update = {
        "first_name": "Charlie Updated",
        "last_name": "Brown",
        "email": "charlie@gmail.com",
        "membership_status": "ACTIVE"
    }
    ok, msg, res_put = APISimulator.simulate_call("PUT", "/api/v1/members/member_val_charlie", body_update, "Admin", bundle, db_sim)
    assert ok is True
    
    # Test GET updated record
    ok, msg, res_get_updated = APISimulator.simulate_call("GET", "/api/v1/members/member_val_charlie", {}, "Admin", bundle, db_sim)
    assert res_get_updated["first_name"] == "Charlie Updated"

    # Test DELETE record
    ok, msg, res_del = APISimulator.simulate_call("DELETE", "/api/v1/members/member_val_charlie", {}, "Admin", bundle, db_sim)
    assert ok is True
    
    # Test GET deleted record (should fail)
    ok, msg, res_get_deleted = APISimulator.simulate_call("GET", "/api/v1/members/member_val_charlie", {}, "Admin", bundle, db_sim)
    assert ok is False
    assert "not found" in msg

# --- 5. BUSINESS RULE SIMULATOR TESTS ---

def test_business_rule_simulator():
    trace = TraceabilityMetadata(source_ast_version="v1.0")
    tbl_cols = [
        ColumnDefinition(name="id", type="string", is_primary_key=True, is_nullable=False),
        ColumnDefinition(name="member_id", type="string", is_primary_key=False, is_nullable=False)
    ]
    booking_table = DatabaseTableDefinition(
        table_name="class_booking",
        columns=tbl_cols,
        primary_keys=["id"],
        foreign_keys=[],
        indexes=[],
        source_entity="ClassBooking",
        traceability=trace
    )
    
    enroll_cols = [
        ColumnDefinition(name="id", type="string", is_primary_key=True, is_nullable=False),
        ColumnDefinition(name="course_id", type="string", is_primary_key=False, is_nullable=False)
    ]
    enrollment_table = DatabaseTableDefinition(
        table_name="enrollment",
        columns=enroll_cols,
        primary_keys=["id"],
        foreign_keys=[],
        indexes=[],
        source_entity="Enrollment",
        traceability=trace
    )

    db_sim = DatabaseSimulator([booking_table, enrollment_table])
    
    # Gym rule: cap of 3 bookings per member
    rule_gym = BusinessRuleDefinition(
        rule_id="BR_001",
        rule="Daily bookings cap of 3 classes",
        source="GymRequirement",
        affected_entities=["ClassBooking"],
        description="Max 3 bookings"
    )
    
    # Check rule when member has 0 bookings
    viol = BusinessRuleSimulator.verify_rule(rule_gym, "class_booking", {"id": "b1", "member_id": "m1"}, db_sim)
    assert viol is None

    # Insert 3 bookings for m1
    db_sim.insert("class_booking", {"id": "b1", "member_id": "m1"})
    db_sim.insert("class_booking", {"id": "b2", "member_id": "m1"})
    db_sim.insert("class_booking", {"id": "b3", "member_id": "m1"})

    # Check rule for booking #4
    viol = BusinessRuleSimulator.verify_rule(rule_gym, "class_booking", {"id": "b4", "member_id": "m1"}, db_sim)
    assert viol is not None
    assert viol.severity == "CRITICAL"
    assert "exceeds daily booking cap" in viol.message

    # School rule: enrollment capacity limit of 2
    rule_school = BusinessRuleDefinition(
        rule_id="BR_002",
        rule="Enrollment capacity limit",
        source="SchoolRequirement",
        affected_entities=["Enrollment"],
        description="Max 2 students"
    )
    
    # Insert 2 enrollments
    db_sim.insert("enrollment", {"id": "e1", "course_id": "c1"})
    db_sim.insert("enrollment", {"id": "e2", "course_id": "c1"})

    # Check rule for 3rd enrollment
    viol = BusinessRuleSimulator.verify_rule(rule_school, "enrollment", {"id": "e3", "course_id": "c1"}, db_sim)
    assert viol is not None
    assert "exceeds maximum class capacity" in viol.message

# --- 6. WORKFLOW & HIGH LEVEL EXECUTION SIMULATOR TESTS ---

def test_workflow_and_execution_simulator(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)

    # Run execution simulator
    report = ExecutionSimulator.simulate(bundle, spec, gym_approved_blueprint)
    
    assert isinstance(report, ExecutionSimulationReport)
    assert "ClassBookingFlow" in report.workflows_executed
    assert report.successful_steps > 0
    assert report.failed_steps == 0
    assert report.success_rate == 100.0
    assert len(report.simulation_traces) > 0
    
    # Check that traces contain successful step log details
    assert any(t.outcome == "SUCCESS" for t in report.simulation_traces)

# --- 7. EVALUATION FRAMEWORK & CONFIGURATOR TESTS ---

def test_cost_vs_quality_modes(gym_approved_blueprint):
    # Test FAST Mode (Compile, Simulate - no validation or repairs)
    bundle, spec, latency, repairs, v_fails, s_rep, f_rep = EvaluationFramework.run_pipeline(
        "Build a gym management system with class schedules and slot booking.",
        mode="FAST",
        app_type="Gym"
    )
    assert repairs == 0
    assert v_fails == 0

    # Test BALANCED Mode (Compile, Validate, Repair Once, Simulate)
    bundle, spec, latency, repairs, v_fails, s_rep, f_rep = EvaluationFramework.run_pipeline(
        "Build a gym management system with class schedules and slot booking.",
        mode="BALANCED",
        app_type="Gym"
    )
    # Balanced should run validation and repairs if needed. Since our mock pipeline generates a clean bundle,
    # repairs could be 0 but validation checks were active.
    assert isinstance(bundle, CompiledSchemaBundle)

    # Test HIGH_QUALITY Mode (Compile, Validate, Multi-pass Repair, Simulate, Business Rules, Determinism)
    bundle, spec, latency, repairs, v_fails, s_rep, f_rep = EvaluationFramework.run_pipeline(
        "Build a gym management system.",
        mode="HIGH_QUALITY",
        app_type="Gym"
    )
    assert isinstance(spec, MasterSpecification)

def test_evaluation_framework_and_leaderboard():
    # Make sure leaderboard file path is cleaned up before and after test
    leaderboard_file = EvaluationFramework.LEADERBOARD_PATH
    if os.path.exists(leaderboard_file):
        os.remove(leaderboard_file)

    try:
        # Run subset evaluation or mock evaluation to verify reports and leaderboard logging
        report, leaderboard = EvaluationFramework.evaluate(mode="BALANCED")
        
        assert isinstance(report, EvaluationReport)
        assert report.prompt_count == 20
        assert report.success_rate >= 0.0
        assert report.average_latency > 0
        assert report.repair_success_rate >= 0.0
        assert report.business_rule_pass_rate >= 0.0
        assert report.validation_pass_rate >= 0.0
        assert isinstance(report.failure_classification, FailureClassification)

        # Leaderboard checks
        assert len(leaderboard) > 0
        assert os.path.exists(leaderboard_file)
        
        # Load from disk to verify persistence
        with open(leaderboard_file, "r") as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["mode"] == "BALANCED"
            
    finally:
        if os.path.exists(leaderboard_file):
            os.remove(leaderboard_file)

# --- 8. DETERMINISM REPORT TESTS ---

def test_determinism_reports():
    leaderboard_file = EvaluationFramework.LEADERBOARD_PATH
    if os.path.exists(leaderboard_file):
        os.remove(leaderboard_file)

    try:
        # HIGH_QUALITY runs determinism checks (same prompt 5 times)
        report, leaderboard = EvaluationFramework.evaluate(mode="HIGH_QUALITY")
        
        assert len(report.determinism_reports) > 0
        det_rep = report.determinism_reports[0]
        assert isinstance(det_rep, DeterminismReport)
        assert det_rep.matching_runs == 5
        assert det_rep.determinism_score == 1.0
        assert report.determinism_score == 1.0

    finally:
        if os.path.exists(leaderboard_file):
            os.remove(leaderboard_file)

# --- 9. STATE TRANSITION VALIDATION TESTS ---

def test_state_transition_validation():
    trace = TraceabilityMetadata(source_ast_version="v1.0")
    booking_table = DatabaseTableDefinition(
        table_name="class_booking",
        columns=[
            ColumnDefinition(name="id", type="string", is_primary_key=True, is_nullable=False),
            ColumnDefinition(name="status", type="string", is_primary_key=False, is_nullable=False)
        ],
        primary_keys=["id"],
        foreign_keys=[],
        indexes=[],
        source_entity="ClassBooking",
        traceability=trace
    )
    db_sim = DatabaseSimulator([booking_table])
    
    state_rules = [
        StateTransitionRule(entity="ClassBooking", from_state="PENDING", to_state="CONFIRMED", allowed=True),
        StateTransitionRule(entity="ClassBooking", from_state="CONFIRMED", to_state="PENDING", allowed=False)
    ]
    
    wf = WorkflowDefinition(
        workflow_id="wf_confirm",
        workflow_name="Confirm Booking Flow",
        workflow_steps=["Select Class", "Confirm Reservation"],
        actors=["GymMember"],
        dependencies=["ClassBooking"]
    )
    
    spec = MasterSpecification(
        app_name="Gym",
        app_type="Gym",
        actors=[],
        entities=[],
        relationships=[],
        workflows=[wf],
        permissions=[],
        business_rules=[],
        design_decisions=[]
    )
    
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # PENDING -> CONFIRMED (Allowed)
    s_ok, s_fail, traces, viols = WorkflowSimulator.simulate_workflow(
        wf, "GymMember", bundle, spec, db_sim, state_rules
    )
    assert s_fail == 0
    
    # CONFIRMED -> PENDING (Rejected)
    wf_invalid = WorkflowDefinition(
        workflow_id="wf_reopen",
        workflow_name="Reopen Booking Flow",
        workflow_steps=["Select Class", "Confirm Reservation", "Reopen Reservation"],
        actors=["GymMember"],
        dependencies=["ClassBooking"]
    )
    spec.workflows = [wf_invalid]
    
    db_sim2 = DatabaseSimulator([booking_table])
    s_ok2, s_fail2, traces2, viols2 = WorkflowSimulator.simulate_workflow(
        wf_invalid, "GymMember", bundle, spec, db_sim2, state_rules
    )
    assert s_fail2 == 1
    assert any("State Transition Rejected" in t.reason for t in traces2 if t.outcome == "FAILED")
