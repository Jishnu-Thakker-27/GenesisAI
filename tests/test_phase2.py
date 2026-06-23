import os
import re
import pytest
from pydantic import ValidationError

from stages.stage2_intent import (
    IntentExtractionEngine, IntentExtractionResult, IntentActor, IntentFeature,
    AssumptionModel, RecommendationSource, ConfidenceBreakdown
)


# --- BASIC INITIATION TESTS ---

def test_intent_engine_init_without_key():
    engine = IntentExtractionEngine(api_key="")
    assert engine.client is None


# --- EXTRACTION VALUE NORMALIZATION & VALIDATION TESTS ---

def test_intent_actor_normalization():
    actor = IntentActor(name="member role", description="Gym customer")
    assert actor.name == "MemberRole"

def test_intent_feature_normalization():
    source = RecommendationSource(source_type="user_requirement", source_description="Direct")
    feature = IntentFeature(name="book a class", description="Reserved a slot", actor_involved="gym trainer", source=source)
    assert feature.actor_involved == "GymTrainer"
    assert feature.source.source_type == "user_requirement"

def test_assumption_impact_validation():
    # Test valid impact levels
    asn = AssumptionModel(
        assumption="Gym has members",
        reason="Implicit",
        source="logical_inference",
        confidence=0.9,
        impact_level="HIGH"
    )
    assert asn.impact_level == "HIGH"

    # Test invalid impact levels (should raise ValidationError)
    with pytest.raises(ValidationError):
        AssumptionModel(
            assumption="Gym has members",
            reason="Implicit",
            source="logical_inference",
            confidence=0.9,
            impact_level="CRITICAL" # Invalid
        )


# --- EXTRACTION FUNCTIONALITY TESTS (Normal Cases) ---

def test_extraction_gym_normal():
    engine = IntentExtractionEngine(api_key="")
    result = engine.extract_intent("Build a gym scheduling application with booking slots")
    
    assert result.app_name == "GymFitnessManager"
    assert result.app_type == "Gym Management"
    assert len(result.actors) == 3
    assert any(actor.name == "GymMember" for actor in result.actors)
    
    # Workflow Gap check
    assert len(result.workflow_gaps) == 2
    assert "Membership Purchase Flow" in result.workflow_gaps
    
    # Confidence breakdown check
    breakdown = result.confidence_breakdown
    assert breakdown is not None
    assert breakdown.app_type_score == 1.0
    assert breakdown.actor_score == 1.0
    assert breakdown.feature_score == 1.0
    assert breakdown.workflow_score == 0.4  # Deducted due to 2 workflow gaps
    assert breakdown.constraint_score == 1.0

    # Verification of processing mode for high confidence (>= 0.85)
    assert result.confidence_score >= 0.85
    assert result.processing_mode == "MODE_B"  # Assume mode
    assert len(result.clarification_questions) == 0  # Questions cleared
    assert len(result.assumptions) > 0
    assert result.assumptions[0].impact_level == "HIGH"


def test_extraction_crm_normal():
    engine = IntentExtractionEngine(api_key="")
    result = engine.extract_intent("Build a sales crm system to manage customers")
    
    assert result.app_name == "SalesCoreCRM"
    assert result.app_type == "CRM Application"
    assert result.confidence_score >= 0.85
    assert result.processing_mode == "MODE_B"
    assert len(result.clarification_questions) == 0
    assert result.confidence_breakdown.workflow_score == 1.0  # 0 gaps


# --- EXTRACTION FUNCTIONALITY TESTS (Edge Cases) ---

def test_extraction_vague_prompt():
    engine = IntentExtractionEngine(api_key="")
    result = engine.extract_intent("Build a platform")
    
    assert result.app_name == "GenericPlatform"
    assert result.confidence_score < 0.60
    assert result.processing_mode == "MODE_A"  # Clarification mode
    assert len(result.assumptions) == 0  # Assumptions cleared
    assert len(result.clarification_questions) > 0
    assert len(result.workflow_gaps) == 2


def test_extraction_conflicting_crm():
    engine = IntentExtractionEngine(api_key="")
    result = engine.extract_intent("Make a CRM but do not store customers")
    
    assert result.app_name == "ConflictCRM"
    assert result.confidence_score < 0.60
    assert result.processing_mode == "MODE_A"
    assert len(result.clarification_questions) > 0
    assert any(q.category == "general" for q in result.clarification_questions)


def test_extraction_everyone_is_admin():
    engine = IntentExtractionEngine(api_key="")
    result = engine.extract_intent("Everyone is admin but nobody has admin rights")
    
    assert result.app_name == "ParadoxApp"
    assert result.confidence_score < 0.60
    assert result.processing_mode == "MODE_A"
    assert any(q.category == "permissions" for q in result.clarification_questions)


# --- CONFIDENCE DEDUCTION LOGIC TESTS ---

def test_confidence_breakdown_deduction():
    # Construct a payload with low metrics and verify the breakdown calculations
    raw = IntentExtractionResult(
        app_name="TestApp",
        app_type="Unspecified Platform",
        actors=[],  # 0.0 actor_score
        features=[],  # 0.0 feature_score
        business_rules=[],  # 0.1 business_rule_score
        constraints=[],  # 0.4 constraint_score
        workflow_gaps=["Gap 1", "Gap 2", "Gap 3"],  # 0.1 workflow_score
        assumptions=[],
        missing_information=["Missing data 1", "Missing data 2"],
        clarification_questions=[],
        confidence_score=0.9  # Raw high score
    )
    engine = IntentExtractionEngine(api_key="")
    processed = engine._process_and_refine(raw)
    
    # Let's inspect confidence_breakdown
    cbd = processed.confidence_breakdown
    assert cbd.app_type_score == 0.5
    assert cbd.actor_score == 0.0
    assert cbd.feature_score == 0.0
    assert cbd.business_rule_score == 0.1
    assert cbd.workflow_score == 0.1
    assert cbd.constraint_score == 0.4

    # Derived score = (0.15*0.5) + (0.2*0) + (0.25*0) + (0.15*0.1) + (0.15*0.1) + (0.1*0.4)
    #               = 0.075 + 0 + 0 + 0.015 + 0.015 + 0.04 = 0.145
    # Blended score = (0.9 * 0.6) + (0.145 * 0.4) = 0.54 + 0.058 = 0.598 -> rounded to 0.60
    assert processed.confidence_score == 0.60
    assert processed.processing_mode == "MODE_C"


# --- MOCK & PLACEHOLDER SCAVENGER SCAN ---

def test_placeholder_existence():
    """Scavenger test to ensure no placeholder ellipses or pass statements are left in stage2_intent.py."""
    stage2_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stages", "stage2_intent.py")
    
    with open(stage2_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for raw ellipses outside of strings
    # We check if there are triple dots '...' that are not inside quotes or comments
    # To keep it simple, we check that no raw line has just '...' or 'pass' or 'TODO'
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        # Ensure no lines are literally '...' or 'pass' or contain 'TODO'
        assert stripped != "...", f"Placeholder found in stage2_intent.py:L{idx}: {line}"
        assert stripped != "pass", f"Placeholder 'pass' found in stage2_intent.py:L{idx}: {line}"
        assert "TODO" not in line, f"TODO comment found in stage2_intent.py:L{idx}: {line}"
        assert "NotImplementedError" not in line, f"Incomplete implementation exception found in stage2_intent.py:L{idx}: {line}"
