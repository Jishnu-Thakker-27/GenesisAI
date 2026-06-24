import pytest
import sqlite3
import json
from config import DB_PATH
from stages.stage2_intent import IntentExtractionResult, IntentActor, IntentFeature
from stages.stage10_requirements_intelligence import AIArchitectReport, ArchitectConfidenceScores
from stages.stage11_pattern_intelligence import PatternIntelligenceEngine

def test_dna_calculation():
    # 1. Test CRUD and Scheduling matching
    entities = ["Member", "Trainer", "ClassBooking"]
    workflows = ["Book Class", "Cancel Reservation"]
    rules = ["Cancellations must be done 2 hours in advance"]
    
    dna = PatternIntelligenceEngine.calculate_dna(entities, workflows, rules)
    assert dna.crud > 0
    assert dna.scheduling > 0
    # Sum should be exactly 100%
    assert round(dna.crud + dna.transaction + dna.scheduling + dna.analytics, 0) == 100.0

def test_project_similarity():
    intent = IntentExtractionResult(
        app_name="MockRestaurantApp",
        app_type="Restaurant Management",
        detected_domain="Restaurant Management",
        detected_subdomain="Ordering",
        confidence_score=0.9,
        entities=["Menu"],
        workflows=["Browse"],
        actors=[],
        features=[]
    )
    
    similar = PatternIntelligenceEngine.find_similar_projects("Build me a restaurant app", intent)
    assert len(similar) > 0
    # The closest match should be restaurant/hospitality
    assert similar[0].domain in ["Restaurant Management", "Hospitality Management"]

def test_missing_requirements_prediction():
    intent = IntentExtractionResult(
        app_name="MockGym",
        app_type="Gym",
        detected_domain="Gym",
        detected_subdomain="Facility Check-In",
        confidence_score=0.9,
        entities=["Member"], # Missing ClassBooking, Trainer
        workflows=["Class Booking"],
        actors=[],
        features=[]
    )
    
    gaps = PatternIntelligenceEngine.predict_missing_requirements("Gym", intent)
    assert len(gaps) > 0
    requirements = [g.requirement for g in gaps]
    # Check if missing entities/workflows from seed Gym domain are predicted
    assert any("Trainer" in r or "Member" in r or "ClassBooking" in r or "Audit" in r for r in requirements)

def test_recommendations_and_explanations():
    intent = IntentExtractionResult(
        app_name="MockGym",
        app_type="Gym",
        detected_domain="Gym",
        detected_subdomain="Facility Check-In",
        confidence_score=0.9,
        entities=["Member"],
        workflows=["Class Booking"],
        actors=[],
        features=[]
    )
    
    rec_ents, rec_wfs = PatternIntelligenceEngine.generate_recommendations("Gym", intent)
    assert len(rec_ents) > 0
    assert len(rec_wfs) > 0
    
    explanations = PatternIntelligenceEngine.explain_decisions("Gym", rec_ents, rec_wfs)
    assert len(explanations) > 0
    assert explanations[0].recommendation is not None
    assert explanations[0].evidence > 0.0

def test_stage11_remains_dormant_in_default_pipeline():
    from database.connection import init_db
    init_db()
    from core.pipeline import GenesisPipeline
    pipeline = GenesisPipeline()
    app = pipeline.run_pipeline("Build me a restaurant app")
    
    # Stage 11 is kept as a future roadmap module, but the default compiler
    # path should not run pattern memory or continuous learning.
    assert app.ai_architect_report is not None
    assert app.ai_architect_report.architecture_dna is None
    assert app.ai_architect_report.similar_projects == []
    assert app.ai_architect_report.requirement_gaps == []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM architecture_memory WHERE project_id = ?", (app.project_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    assert count == 0
