import pytest
from datetime import datetime

from stages.stage2_intent import IntentExtractionResult, IntentActor, IntentFeature
from stages.stage3_recommend import (
    BlueprintRecommendation, RecommendedActor, RecommendedFeature, FeatureExplanation,
    RecommendationSource, RecommendedWorkflow, RecommendedPermission, RecommendedInnovation, ApprovedBlueprint
)
from stages.stage4_system import (
    MasterSpecificationBuilder, RelationshipDefinition, WorkflowDefinition,
    PermissionDefinition, DesignDecision, SystemDesignGraph, MasterSpecification,
    EntityDefinition, BusinessRuleDefinition
)
from stages.stage5_schema import (
    CompiledSchemaBundleBuilder, DatabaseTableDefinition, APIEndpointDefinition,
    UIViewDefinition, AuthRuleDefinition, SchemaContract, ConsistencyViolation,
    CrossLayerConsistencyEngine, DatabaseSchemaCompiler, APISchemaCompiler,
    TraceabilityMetadata
)
from core.ast import Actor, Entity, EntityField, BusinessRule


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


# --- 5 DOMAINS COMPILATION & TRACEABILITY TESTS ---

def test_gym_bundle_compilation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Verify report & metrics
    assert bundle.compilation_report.is_valid is True
    assert len(bundle.compilation_report.errors) == 0
    assert "Member" in bundle.compilation_report.compiled_entities
    assert "ClassBookingFlow" in bundle.compilation_report.compiled_workflows
    
    # Verify DB compilation
    tables = {t.table_name: t for t in bundle.database_schema}
    assert "member" in tables
    assert "class_booking" in tables
    
    member_tbl = tables["member"]
    assert any(c.name == "email" for c in member_tbl.columns)
    
    # Verify API compilation
    apis = {a.endpoint_id: a for a in bundle.api_schema}
    assert "create_member" in apis
    assert "get_member_list" in apis
    assert "execute_classbookingflow" in apis
    
    # Verify UI compilation
    views = {v.view_id: v for v in bundle.ui_schema}
    assert "view_classbookingflow" in views
    booking_view = views["view_classbookingflow"]
    assert "POST /api/v1/class-bookings" in booking_view.linked_endpoints
    
    # Verify Auth compilation
    rules = {r.role: r for r in bundle.auth_schema}
    assert "Admin" in rules
    assert "GymMember" in rules
    
    # Verify Traceability preservation
    assert member_tbl.traceability.source_entity == "Member"
    assert member_tbl.traceability.source_ast_version == "test_gym_project"
    assert member_tbl.traceability.compiler_phase == "Database Schema Compiler"
    
    # Verify CompilationArtifacts
    assert len(bundle.artifacts) > 0
    member_art = next(a for a in bundle.artifacts if a.generated_component == "Table:member")
    assert member_art.source_component == "Entity:Member"
    assert member_art.artifact_type == "database_table"


def test_crm_bundle_compilation():
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
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    assert bundle.compilation_report.is_valid is True
    tables = {t.table_name: t for t in bundle.database_schema}
    assert "customer" in tables
    assert "lead" in tables
    assert "interaction_log" in tables


def test_hospital_bundle_compilation():
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
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    assert bundle.compilation_report.is_valid is True
    tables = {t.table_name: t for t in bundle.database_schema}
    assert "patient" in tables
    assert "doctor" in tables
    assert "appointment" in tables
    assert "medical_record" in tables


def test_school_bundle_compilation():
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
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    assert bundle.compilation_report.is_valid is True
    tables = {t.table_name: t for t in bundle.database_schema}
    assert "student" in tables
    assert "teacher" in tables
    assert "course" in tables
    assert "enrollment" in tables


def test_inventory_bundle_compilation():
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
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    assert bundle.compilation_report.is_valid is True
    tables = {t.table_name: t for t in bundle.database_schema}
    assert "product" in tables
    assert "supplier" in tables
    assert "stock_order" in tables


# --- LAYER COMPILATION EDGE CASES ---

def test_missing_entity_violation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Introduce a missing entity constraint by deleting a table from DB schema but keeping it in spec
    tables_corrupted = [t for t in bundle.database_schema if t.table_name != "member"]
    
    violations = CrossLayerConsistencyEngine.verify(
        spec, tables_corrupted, bundle.api_schema, bundle.ui_schema, bundle.auth_schema, bundle.contracts
    )
    assert any(v.layer_b == "Database" and "member" in v.message.lower() for v in violations)


def test_duplicate_entities_compilation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    
    # Duplicate 'Member' in entities
    dup_member = EntityDefinition(
        entity_id="ent_member_dup",
        entity_name="Member",
        name="Member",
        description="Duplicate",
        source="test",
        confidence=1.0,
        fields=[]
    )
    spec.entities.append(dup_member)
    
    # Running compiler will preserve deterministic list but validation checks duplicate tables
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    assert bundle.compilation_report.is_valid is False
    assert any("duplicate entity" in err.lower() for err in bundle.compilation_report.errors)


def test_missing_permissions_role_violation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Remove GymMember auth rule to trigger permissions mismatch violation
    auth_corrupted = [a for a in bundle.auth_schema if a.role != "GymMember"]
    
    violations = CrossLayerConsistencyEngine.verify(
        spec, bundle.database_schema, bundle.api_schema, bundle.ui_schema, auth_corrupted, bundle.contracts
    )
    assert any(v.layer_b == "Auth" and "gymmember" in v.message.lower() for v in violations)


def test_broken_relationships_violation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Corrupt Database foreign key definitions on ClassBooking (remove foreign keys references)
    db_corrupted = []
    for t in bundle.database_schema:
        if t.table_name == "class_booking":
            db_corrupted.append(DatabaseTableDefinition(
                table_name=t.table_name,
                columns=t.columns,
                primary_keys=t.primary_keys,
                foreign_keys=[], # Empty
                constraints=t.constraints,
                indexes=t.indexes,
                source_entity=t.source_entity,
                traceability=t.traceability
            ))
        else:
            db_corrupted.append(t)
            
    # Rel list in spec expects a relationship ClassBooking -> Member
    violations = CrossLayerConsistencyEngine.verify(
        spec, db_corrupted, bundle.api_schema, bundle.ui_schema, bundle.auth_schema, bundle.contracts
    )
    assert any(v.violation_id.startswith("viol_db_relationship_") for v in violations)


def test_broken_endpoint_links_violation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Corrupt UI view linked_endpoints with a non-existent endpoint path
    ui_corrupted = []
    for ui in bundle.ui_schema:
        ui_corrupted.append(UIViewDefinition(
            view_id=ui.view_id,
            view_name=ui.view_name,
            components=ui.components,
            actions=ui.actions,
            required_permissions=ui.required_permissions,
            source_workflow=ui.source_workflow,
            linked_endpoints=["POST /api/v1/ghost_route"], # Broken
            traceability=ui.traceability
        ))
        
    violations = CrossLayerConsistencyEngine.verify(
        spec, bundle.database_schema, bundle.api_schema, ui_corrupted, bundle.auth_schema, bundle.contracts
    )
    assert any(v.violation_id.startswith("viol_ui_link_") for v in violations)


def test_missing_traceability_violation(gym_approved_blueprint):
    spec = MasterSpecificationBuilder.compile_specification(gym_approved_blueprint)
    bundle = CompiledSchemaBundleBuilder.compile_bundle(spec)
    
    # Corrupt a table by stripping its traceability source
    db_corrupted = []
    for t in bundle.database_schema:
        if t.table_name == "member":
            db_corrupted.append(DatabaseTableDefinition(
                table_name=t.table_name,
                columns=t.columns,
                primary_keys=t.primary_keys,
                foreign_keys=t.foreign_keys,
                constraints=t.constraints,
                indexes=t.indexes,
                source_entity=t.source_entity,
                traceability=TraceabilityMetadata(source_ast_version="v1.0") # Missing source_entity
            ))
        else:
            db_corrupted.append(t)
            
    violations = CrossLayerConsistencyEngine.verify(
        spec, db_corrupted, bundle.api_schema, bundle.ui_schema, bundle.auth_schema, bundle.contracts
    )
    assert any(v.violation_id.startswith("viol_trace_db_") for v in violations)
