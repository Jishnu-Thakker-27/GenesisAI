import json
import pytest
from datetime import datetime

from database.connection import get_connection, init_db
from stages.stage2_intent import IntentExtractionResult, IntentActor, IntentFeature
from stages.stage3_recommend import (
    BlueprintRecommendationEngine, BlueprintModification, ApprovedBlueprint, RecommendationSource,
    RecommendationRankingEngine, RecommendedFeature, FeatureExplanation
)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


# --- SIMILARITY & METRIC CALCULATION TESTS ---

def test_jaccard_similarity():
    assert BlueprintRecommendationEngine._calculate_similarity(["gym", "booking"], ["gym", "booking"]) == 1.0
    assert BlueprintRecommendationEngine._calculate_similarity(["gym", "booking"], ["gym", "trainer", "schedule"]) == 0.25
    assert BlueprintRecommendationEngine._calculate_similarity(["hospital"], ["gym", "booking"]) == 0.0


def test_recommendation_confidence_calculation():
    # User requirement should have 1.0 confidence
    assert BlueprintRecommendationEngine.calculate_confidence("user_requirement", 1.0, 1.0, 1.0, 10.0) == 1.0

    # Industry pattern with 0.8 similarity
    # Confidence = 0.3*0.95 + 0.2*1.0 + 0.2*0.8 + 0.15*1.0 + 0.15*1.0 = 0.285 + 0.2 + 0.16 + 0.15 + 0.15 = 0.945 -> rounded 0.95
    conf = BlueprintRecommendationEngine.calculate_confidence("industry_pattern", 1.0, 0.8, 1.0, 10.0)
    assert conf == 0.95

    # Community innovation with 0.5 similarity, 0.85 acceptance, and 8.0 impact
    # Confidence = 0.3*0.85 + 0.2*1.0 + 0.2*0.5 + 0.15*0.85 + 0.15*0.80 = 0.255 + 0.2 + 0.10 + 0.1275 + 0.12 = 0.8025 -> rounded 0.80
    conf_comm = BlueprintRecommendationEngine.calculate_confidence("community_innovation", 1.0, 0.5, 0.85, 8.0)
    assert conf_comm == 0.80


# --- RANKING ENGINE TESTS ---

def test_ranking_engine_features():
    source_usr = RecommendationSource(source_type="user_requirement", source_description="user", relevance_score=1.0)
    source_ind = RecommendationSource(source_type="industry_pattern", source_description="industry", relevance_score=0.85)

    feat_low_rel = RecommendedFeature(
        name="low_relevance",
        description="low",
        actor_involved="Admin",
        explanation=FeatureExplanation(
            feature_name="low_relevance", what_it_does="low", why_recommended="low", business_value="low",
            source=source_ind, source_reliability=0.95, recommendation_confidence=0.90, innovation_origin="industry",
            relevance_score=0.80
        )
    )
    feat_high_rel = RecommendedFeature(
        name="high_relevance",
        description="high",
        actor_involved="Admin",
        explanation=FeatureExplanation(
            feature_name="high_relevance", what_it_does="high", why_recommended="high", business_value="high",
            source=source_usr, source_reliability=1.0, recommendation_confidence=1.0, innovation_origin="user_created",
            relevance_score=1.0
        )
    )
    feat_mid_rel_low_conf = RecommendedFeature(
        name="mid_relevance_low_conf",
        description="mid",
        actor_involved="Admin",
        explanation=FeatureExplanation(
            feature_name="mid_relevance_low_conf", what_it_does="mid", why_recommended="mid", business_value="mid",
            source=source_ind, source_reliability=0.95, recommendation_confidence=0.70, innovation_origin="industry",
            relevance_score=0.90
        )
    )
    feat_mid_rel_high_conf = RecommendedFeature(
        name="mid_relevance_high_conf",
        description="mid",
        actor_involved="Admin",
        explanation=FeatureExplanation(
            feature_name="mid_relevance_high_conf", what_it_does="mid", why_recommended="mid", business_value="mid",
            source=source_ind, source_reliability=0.95, recommendation_confidence=0.90, innovation_origin="industry",
            relevance_score=0.90
        )
    )

    unordered = [feat_low_rel, feat_high_rel, feat_mid_rel_low_conf, feat_mid_rel_high_conf]
    ordered = RecommendationRankingEngine.rank_features(unordered)

    # Expected order:
    # 1. high_relevance (relevance: 1.0)
    # 2. mid_relevance_high_conf (relevance: 0.90, confidence: 0.90)
    # 3. mid_relevance_low_conf (relevance: 0.90, confidence: 0.70)
    # 4. low_relevance (relevance: 0.80)
    assert ordered[0].name == "high_relevance"
    assert ordered[1].name == "mid_relevance_high_conf"
    assert ordered[2].name == "mid_relevance_low_conf"
    assert ordered[3].name == "low_relevance"


# --- RETRIEVAL & ANTI-LEAKAGE TESTS ---

def test_recommendation_leaking_prevention():
    engine = BlueprintRecommendationEngine()
    
    gym_intent = IntentExtractionResult(
        app_name="GymApp",
        app_type="Gym",
        actors=[IntentActor(name="GymMember", description="Member")],
        features=[IntentFeature(name="Book slots", description="Book class slot reservations", actor_involved="GymMember")],
        confidence_score=0.90
    )
    
    recs = engine.recommend_blueprint(gym_intent)
    
    assert any("Attendance" in f.name for f in recs.recommended_features)
    assert any("Scheduling" in f.name for f in recs.recommended_features)
    assert not any("Contact Management" == f.name for f in recs.recommended_features)
    assert not any("Predictive Stock Alert" == i.name for i in recs.recommended_innovations)


# --- EXPLAINABILITY GENERATION TESTS ---

def test_explainability_elements_populated():
    engine = BlueprintRecommendationEngine()
    
    gym_intent = IntentExtractionResult(
        app_name="GymApp",
        app_type="Gym",
        actors=[IntentActor(name="GymMember", description="Member")],
        features=[IntentFeature(name="Book slots", description="Book class slot reservations", actor_involved="GymMember")],
        confidence_score=0.90
    )
    
    recs = engine.recommend_blueprint(gym_intent)
    
    for f in recs.recommended_features:
        exp = f.explanation
        assert exp.source_reliability in [0.75, 0.85, 0.95, 1.0]
        assert exp.recommendation_confidence >= 0.0 and exp.recommendation_confidence <= 1.0
        assert exp.innovation_origin in ["industry", "community", "user_created"]
        assert len(exp.business_value) > 0


# --- TRANSACTION & APPROVAL FLOW TESTS ---

def test_database_approval_workflow():
    engine = BlueprintRecommendationEngine()
    
    intent = IntentExtractionResult(
        app_name="GymFitness",
        app_type="Gym",
        actors=[IntentActor(name="GymMember", description="Member")],
        features=[IntentFeature(name="BookClass", description="Book class slots", actor_involved="GymMember")],
        confidence_score=0.90
    )
    
    recs = engine.recommend_blueprint(intent)
    blueprint = engine.create_approved_blueprint("project_123", recs)
    
    # Verify initial stats of innovation in database
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT approval_count, rejection_count, acceptance_rate, innovation_origin, community_score, last_approved_at FROM community_innovations WHERE innovation_id = 'inn_c01';")
        row = cursor.fetchone()
        orig_approval = row["approval_count"]
        orig_rejection = row["rejection_count"]
        orig_origin = row["innovation_origin"]
        orig_score = row["community_score"]

    # Record user approval action
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (id, name, description) VALUES ('project_123', 'Test Gym', 'Desc');")
        engine.record_approval_action(conn, "project_123", "innovation", "AI Trainer Matching", "approved")
        
    # Check if approval counts and acceptance rates updated dynamically
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT approval_count, rejection_count, acceptance_rate, community_score, last_approved_at FROM community_innovations WHERE innovation_id = 'inn_c01';")
        row = cursor.fetchone()
        assert row["approval_count"] == orig_approval + 1
        assert row["rejection_count"] == orig_rejection
        assert row["acceptance_rate"] == round((orig_approval + 1) / (orig_approval + 1 + orig_rejection), 2)
        assert row["community_score"] == round(row["acceptance_rate"] * 9.1, 2)
        assert row["last_approved_at"] is not None

        # Check approval_history log entry
        cursor.execute("SELECT COUNT(*) FROM approval_history WHERE project_id = 'project_123' AND item_name = 'AI Trainer Matching';")
        assert cursor.fetchone()[0] == 1


# --- RUNTIME MODIFICATION TESTS ---

def test_blueprint_modification_workflow():
    engine = BlueprintRecommendationEngine()
    
    intent = IntentExtractionResult(
        app_name="SalesCRM",
        app_type="CRM",
        actors=[IntentActor(name="SalesAgent", description="Agent")],
        features=[IntentFeature(name="AddCustomer", description="Create customer lead", actor_involved="SalesAgent")],
        confidence_score=0.90
    )
    
    recs = engine.recommend_blueprint(intent)
    blueprint = engine.create_approved_blueprint("project_crm", recs)
    
    # 1. TEST ADD FEATURE MODIFICATION
    mod_add = BlueprintModification(
        action="ADD",
        component_type="feature",
        name="AutomatedEmailFollowUp",
        details={"description": "Sends auto-reminders after 3 days of no contact", "actor_involved": "SalesAgent"},
        timestamp=str(datetime.now())
    )
    
    # Log modification in database
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO projects (id, name, description) VALUES ('project_crm', 'CRM Project', 'Desc');")
        engine.record_modification_action(conn, "project_crm", "ADD", "feature", "AutomatedEmailFollowUp", mod_add.details)
    
    # Apply to runtime AST
    blueprint = engine.apply_modifications(blueprint, mod_add)
    
    # Verify addition
    assert any(f.name == "AutomatedEmailFollowUp" for f in blueprint.features)
    added_feat = next(f for f in blueprint.features if f.name == "AutomatedEmailFollowUp")
    assert added_feat.description == "Sends auto-reminders after 3 days of no contact"
    assert added_feat.explanation.source.source_type == "user_requirement"
    assert added_feat.explanation.recommendation_confidence == 1.0

    # Verify modification logging
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT action, component_type, details FROM blueprint_modifications WHERE project_id = 'project_crm';")
        row = cursor.fetchone()
        assert row["action"] == "ADD"
        assert row["component_type"] == "feature"

    # 2. TEST REMOVE FEATURE MODIFICATION
    mod_remove = BlueprintModification(
        action="REMOVE",
        component_type="feature",
        name="AddCustomer",
        details={},
        timestamp=str(datetime.now())
    )
    blueprint = engine.apply_modifications(blueprint, mod_remove)
    assert not any(f.name == "AddCustomer" for f in blueprint.features)
