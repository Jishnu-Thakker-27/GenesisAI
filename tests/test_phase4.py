import pytest
from datetime import datetime

from stages.stage2_intent import IntentExtractionResult, IntentActor, IntentFeature
from stages.stage3_recommend import BlueprintRecommendation, RecommendedActor, RecommendedFeature, FeatureExplanation, RecommendationSource, RecommendedWorkflow, RecommendedPermission, RecommendedInnovation, ApprovedBlueprint
from stages.stage4_system import (
    MasterSpecificationBuilder, RelationshipDefinition, WorkflowDefinition,
    PermissionDefinition, DesignDecision, SystemDesignGraph, MasterSpecification,
    ValidationIssue, EntityDefinition, BusinessRuleDefinition
)
from core.ast import Actor, Entity, EntityField, BusinessRule


@pytest.fixture
def sample_approved_gym_blueprint() -> ApprovedBlueprint:
    rec_member = RecommendedActor(name="GymMember", description="A gym member", relevance_score=1.0, why_needed="Book classes")
    rec_admin = RecommendedActor(name="Admin", description="Admin user", relevance_score=0.90, why_needed="Manage gym")
    
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="BookClass", what_it_does="Book slot", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="BookClass", description="Book class slots", actor_involved="GymMember", explanation=explanation)
    
    rec_wf = RecommendedWorkflow(
        name="ClassBookingFlow", description="Book spot", steps=["Select", "Confirm"], actor_involved="GymMember", why_needed="Core flow"
    )
    
    rec_perm = RecommendedPermission(actor="GymMember", action="BookClass", description="Book slots", why_needed="Required")
    
    rec_inn = RecommendedInnovation(
        innovation_id="inn_c01", name="AI Trainer Matching", description="Match trainers", acceptance_rate=0.89, impact_score=9.1, why_recommended="High rating"
    )
    
    return ApprovedBlueprint(
        project_id="test_gym_project",
        app_type="Gym",
        actors=[rec_member, rec_admin],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[rec_perm],
        innovations=[rec_inn]
    )


# --- MULTI-DOMAIN AND SCHEMA FIELD TESTS ---

def test_gym_domain_compilation(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Check entities
    entity_names = {e.name for e in spec.entities}
    assert "Member" in entity_names
    assert "Trainer" in entity_names
    assert "ClassSchedule" in entity_names
    assert "ClassBooking" in entity_names
    
    # Check workflow criticality
    booking_wf = next(w for w in spec.workflows if w.workflow_name == "ClassBookingFlow")
    assert booking_wf.criticality == "HIGH"
    
    # Check design decision affected components
    dd_booking = next(d for d in spec.design_decisions if d.decision_id == "DD_001")
    assert "Member" in dd_booking.affected_components
    assert "ClassBooking" in dd_booking.affected_components


def test_crm_domain_compilation():
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
    bp = ApprovedBlueprint(
        project_id="test_crm_project",
        app_type="CRM",
        actors=[rec_agent],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    entity_names = {e.name for e in spec.entities}
    assert "Customer" in entity_names
    assert "Lead" in entity_names
    assert "InteractionLog" in entity_names
    
    lead_wf = next(w for w in spec.workflows if w.workflow_name == "LeadConversionFlow")
    assert lead_wf.criticality == "HIGH"
    
    rel_ids = {r.relationship_id for r in spec.relationships}
    assert "rel_lead_customer" in rel_ids


def test_hospital_domain_compilation():
    rec_doc = RecommendedActor(name="Doctor", description="Practitioner", relevance_score=1.0, why_needed="Treat patients")
    source = RecommendationSource(source_type="user_requirement", source_description="direct", relevance_score=1.0)
    explanation = FeatureExplanation(
        feature_name="AppointmentScheduling", what_it_does="Schedule", why_recommended="needed", business_value="rev",
        source=source, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created", relevance_score=1.0
    )
    rec_feat = RecommendedFeature(name="AppointmentScheduling", description="Manage appointments", actor_involved="Doctor", explanation=explanation)
    rec_wf = RecommendedWorkflow(
        name="AppointmentSchedulingFlow", description="Schedule appt", steps=["Request", "Book"], actor_involved="Patient", why_needed="Access flow"
    )
    bp = ApprovedBlueprint(
        project_id="test_hospital_project",
        app_type="Hospital",
        actors=[rec_doc],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    entity_names = {e.name for e in spec.entities}
    assert "Patient" in entity_names
    assert "Doctor" in entity_names
    assert "Appointment" in entity_names
    assert "MedicalRecord" in entity_names
    
    appt_wf = next(w for w in spec.workflows if w.workflow_name == "AppointmentSchedulingFlow")
    assert appt_wf.criticality == "HIGH"


def test_school_domain_compilation():
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
    bp = ApprovedBlueprint(
        project_id="test_school_project",
        app_type="School",
        actors=[rec_student],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    entity_names = {e.name for e in spec.entities}
    assert "Student" in entity_names
    assert "Teacher" in entity_names
    assert "Course" in entity_names
    assert "Enrollment" in entity_names


def test_inventory_domain_compilation():
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
    bp = ApprovedBlueprint(
        project_id="test_inventory_project",
        app_type="Inventory",
        actors=[rec_staff],
        features=[rec_feat],
        workflows=[rec_wf],
        permissions=[],
        innovations=[]
    )
    
    spec = MasterSpecificationBuilder.compile_specification(bp)
    entity_names = {e.name for e in spec.entities}
    assert "Product" in entity_names
    assert "Supplier" in entity_names
    assert "StockOrder" in entity_names


# --- ENGINE VALIDATION & DISCOVERY TESTS ---

def test_entity_and_relationship_discovery(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Gym App should discover: Member, Trainer, ClassSchedule, ClassBooking
    entity_names = {e.name for e in spec.entities}
    assert "Member" in entity_names
    assert "Trainer" in entity_names
    assert "ClassSchedule" in entity_names
    assert "ClassBooking" in entity_names
    
    # Verify Trainer relationship field
    schedule = next(e for e in spec.entities if e.name == "ClassSchedule")
    trainer_id_field = next(f for f in schedule.fields if f.name == "trainer_id")
    assert trainer_id_field.type == "relationship"
    assert trainer_id_field.references == "Trainer.id"

    # Verify RelationshipDiscoveryEngine connects ClassBooking -> Member and ClassSchedule -> Trainer
    rel_ids = {r.relationship_id for r in spec.relationships}
    assert "rel_classbooking_member" in rel_ids
    assert "rel_classschedule_trainer" in rel_ids


def test_workflow_permission_rule_design(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Verify Workflows
    assert len(spec.workflows) == 1
    wf = spec.workflows[0]
    assert wf.workflow_name == "ClassBookingFlow"
    assert "GymMember" in wf.actors
    assert "ClassBooking" in wf.dependencies

    # Verify Permissions
    roles = {p.role for p in spec.permissions}
    assert "GymMember" in roles
    assert "Admin" in roles
    member_perm = next(p for p in spec.permissions if p.role == "GymMember")
    assert "BookClasses" in member_perm.permissions

    # Verify Business Rules compilation
    assert len(spec.business_rules) >= 2
    rule_ids = {r.rule_id for r in spec.business_rules}
    assert "BR_001" in rule_ids


def test_design_decisions_and_graph(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Design Decisions check
    assert len(spec.design_decisions) >= 2
    decision_ids = {d.decision_id for d in spec.design_decisions}
    assert "DD_001" in decision_ids

    # SystemDesignGraph check
    graph = spec.graph
    assert len(graph.nodes) > 0
    assert len(graph.edges) > 0
    
    # Check node types
    node_types = {n["type"] for n in graph.nodes}
    assert "actor" in node_types
    assert "entity" in node_types
    assert "workflow" in node_types

    # Check edge labels
    edge_types = {e["type"] for e in graph.edges}
    assert "relationship" in edge_types
    assert "dependency" in edge_types
    assert "execution" in edge_types


# --- LOGICAL AST VALIDATOR TESTS ---

def test_logical_validation_success(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is True
    assert len(report.issues) == 0


def test_logical_validation_wf_actor_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    invalid_wf = WorkflowDefinition(
        workflow_id="bad_wf",
        workflow_name="Bad Flow",
        workflow_steps=["Step 1"],
        actors=["UnknownRole"],
        dependencies=["Member"]
    )
    spec.workflows.append(invalid_wf)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_WF_ACTOR" for i in report.issues)


def test_logical_validation_wf_entity_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    invalid_wf = WorkflowDefinition(
        workflow_id="bad_wf_entity",
        workflow_name="Bad Entity Flow",
        workflow_steps=["Step 1"],
        actors=["GymMember"],
        dependencies=["GhostEntity"]
    )
    spec.workflows.append(invalid_wf)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_WF_ENTITY" for i in report.issues)


def test_logical_validation_rel_target_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    invalid_rel = RelationshipDefinition(
        relationship_id="rel_member_ghost",
        source_entity="Member",
        target_entity="GhostEntity",
        relationship_type="one-to-many",
        description="Invalid relationship"
    )
    spec.relationships.append(invalid_rel)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_REL_TARGET" for i in report.issues)


def test_logical_validation_perm_role_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    invalid_perm = PermissionDefinition(
        role="GhostRole",
        permissions=["DeleteDatabase"],
        reason="None"
    )
    spec.permissions.append(invalid_perm)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_PERM_ROLE" for i in report.issues)


def test_logical_validation_rule_entity_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    invalid_rule = BusinessRule(
        rule_id="BR_999",
        description="Ghost rules",
        affected_entities=["GhostEntity"],
        enforcement_logic="1 == 1"
    )
    spec.business_rules.append(invalid_rule)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_RULE_ENTITY" for i in report.issues)


def test_logical_validation_decision_source_warning(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    invalid_dd = DesignDecision(
        decision_id="DD_999",
        decision="Use spaces instead of tabs",
        reason="Readability",
        source="invalid_source_label",
        impact_level="LOW",
        affected_components=[]
    )
    spec.design_decisions.append(invalid_dd)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is True  # Warning does not invalidate
    assert any(i.rule_id == "VAL_DD_SOURCE" and i.severity == "WARNING" for i in report.issues)


# --- NEW VALIDATION LAYER RULE TESTS ---

def test_logical_validation_duplicate_entity_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Add a duplicate entity named Member
    dup_ent = EntityDefinition(
        entity_id="ent_member_dup",
        entity_name="Member",
        name="Member",
        description="Duplicate Member entity",
        source="test",
        confidence=1.0,
        fields=[]
    )
    spec.entities.append(dup_ent)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_DUP_ENTITY" for i in report.issues)


def test_logical_validation_wf_cycle_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Setup circular dependencies between workflows
    spec.workflows = [
        WorkflowDefinition(
            workflow_id="wf_a",
            workflow_name="WorkflowA",
            workflow_dependencies=["workflowb"],
            criticality="HIGH"
        ),
        WorkflowDefinition(
            workflow_id="wf_b",
            workflow_name="WorkflowB",
            workflow_dependencies=["workflowa"],
            criticality="HIGH"
        )
    ]
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_WF_CYCLE" for i in report.issues)


def test_logical_validation_perm_conflict_failure(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Assign an administrative command ("DeleteDatabase") to a non-admin role ("GymMember")
    conflict_perm = PermissionDefinition(
        role="GymMember",
        permissions=["DeleteDatabase", "ReadOwnProfile"],
        reason="Assigned to normal user"
    )
    spec.permissions.append(conflict_perm)
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is False
    assert any(i.rule_id == "VAL_PERM_CONFLICT" for i in report.issues)


def test_logical_validation_missing_rule_warning(sample_approved_gym_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(sample_approved_gym_blueprint)
    
    # Clear rules so that ClassBooking has no rules affecting it
    spec.business_rules = []
    
    report = MasterSpecificationBuilder.validate_specification(spec)
    assert report.is_valid is True  # WARNING level issue only
    assert any(i.rule_id == "VAL_MISSING_RULE" and i.severity == "WARNING" for i in report.issues)
