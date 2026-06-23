import json
import sqlite3
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime

from database.connection import get_connection
from stages.stage2_intent import IntentExtractionResult, IntentActor, IntentFeature
from core.naming import CanonicalNamingEngine

# --- STAGE 3 DATA MODELS ---

class RecommendationSource(BaseModel):
    source_type: Literal["industry_pattern", "community_innovation", "user_requirement", "logical_inference"]
    source_description: str
    relevance_score: float


class FeatureExplanation(BaseModel):
    feature_name: str
    what_it_does: str
    why_recommended: str
    business_value: str
    source: RecommendationSource
    source_reliability: float
    recommendation_confidence: float
    innovation_origin: Literal["industry", "community", "user_created"]
    relevance_score: float


class RecommendedFeature(BaseModel):
    name: str
    description: str
    actor_involved: str
    explanation: FeatureExplanation


class RecommendedActor(BaseModel):
    name: str
    description: str
    relevance_score: float
    why_needed: str


class RecommendedWorkflow(BaseModel):
    name: str
    description: str
    steps: List[str]
    actor_involved: str
    why_needed: str


class RecommendedPermission(BaseModel):
    actor: str
    action: str
    description: str
    why_needed: str


class RecommendedInnovation(BaseModel):
    innovation_id: str
    name: str
    description: str
    acceptance_rate: float
    impact_score: float
    innovation_origin: Literal["industry", "community", "user_created"] = "community"
    why_recommended: str


class BlueprintRecommendation(BaseModel):
    app_type: str = Field(..., description="The application type category")
    recommended_actors: List[RecommendedActor] = Field(default_factory=list)
    recommended_features: List[RecommendedFeature] = Field(default_factory=list)
    recommended_workflows: List[RecommendedWorkflow] = Field(default_factory=list)
    recommended_permissions: List[RecommendedPermission] = Field(default_factory=list)
    recommended_innovations: List[RecommendedInnovation] = Field(default_factory=list)
    confidence_score: float


class BlueprintModification(BaseModel):
    action: Literal["ADD", "REMOVE", "EDIT"]
    component_type: Literal["actor", "feature", "workflow", "permission", "innovation"]
    name: str
    details: Dict[str, Any]
    timestamp: str


class ApprovedBlueprint(BaseModel):
    project_id: str
    app_type: str = Field(..., description="The application type category")
    actors: List[RecommendedActor] = Field(default_factory=list)
    features: List[RecommendedFeature] = Field(default_factory=list)
    workflows: List[RecommendedWorkflow] = Field(default_factory=list)
    permissions: List[RecommendedPermission] = Field(default_factory=list)
    innovations: List[RecommendedInnovation] = Field(default_factory=list)
    approval_history: List[Dict[str, Any]] = Field(default_factory=list)
    modifications: List[BlueprintModification] = Field(default_factory=list)


# --- RANKING ENGINE ---

class RecommendationRankingEngine:
    @staticmethod
    def rank_features(features: List[RecommendedFeature]) -> List[RecommendedFeature]:
        """Deterministically ranks features: highest relevance first, then highest confidence, then name."""
        features.sort(key=lambda x: (
            -x.explanation.relevance_score,
            -x.explanation.recommendation_confidence,
            x.name
        ))
        return features

    @staticmethod
    def rank_actors(actors: List[RecommendedActor]) -> List[RecommendedActor]:
        """Ranks actors by relevance score, then by name."""
        actors.sort(key=lambda x: (-x.relevance_score, x.name))
        return actors

    @staticmethod
    def rank_innovations(innovations: List[RecommendedInnovation]) -> List[RecommendedInnovation]:
        """Ranks innovations by impact score, then by acceptance rate, then by name."""
        innovations.sort(key=lambda x: (-x.impact_score, -x.acceptance_rate, x.name))
        return innovations


# --- MAIN RECOMMENDATION ENGINE ---

class BlueprintRecommendationEngine:
    @staticmethod
    def _calculate_similarity(words_a: List[str], words_b: List[str]) -> float:
        """Computes Jaccard token similarity for clean deterministic ranking."""
        set_a = set(w.lower() for w in words_a if len(w) > 2)
        set_b = set(w.lower() for w in words_b if len(w) > 2)
        if not set_a or not set_b:
            return 0.0
        intersection = set_a.intersection(set_b)
        union = set_a.union(set_b)
        return round(len(intersection) / len(union), 2)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Splits string into alphanumeric tokens."""
        import re
        return re.findall(r"\b\w+\b", text.lower())

    @staticmethod
    def _compute_reliability(source_type: str) -> float:
        """Helper to get constant source reliability values."""
        reliability_map = {
            "user_requirement": 1.0,
            "industry_pattern": 0.95,
            "community_innovation": 0.85,
            "logical_inference": 0.75
        }
        return reliability_map.get(source_type, 0.50)

    @classmethod
    def calculate_confidence(cls, source_type: str, category_match: float, similarity: float, acceptance_rate: float, impact_score: float) -> float:
        """Computes multi-factor deterministic recommendation confidence."""
        reliability = cls._compute_reliability(source_type)
        confidence = (
            (0.30 * reliability) +
            (0.20 * category_match) +
            (0.20 * similarity) +
            (0.15 * acceptance_rate) +
            (0.15 * (impact_score / 10.0))
        )
        return round(max(0.0, min(1.0, confidence)), 2)

    def recommend_blueprint(self, intent: IntentExtractionResult) -> BlueprintRecommendation:
        """Generates ranked blueprint recommendations matching category and feature similarity."""
        category = intent.app_type
        
        # Tokenize user requirements for similarity scoring
        user_tokens = []
        for feature in intent.features:
            user_tokens.extend(self._tokenize(feature.name))
            user_tokens.extend(self._tokenize(feature.description))
        user_tokens = list(set(user_tokens))

        # Retrieve structures from DB
        industry_features = self._retrieve_industry_patterns(category)
        community_innovs = self._retrieve_community_innovations(category)

        # 1. Map Features & Explanations
        recommended_features: List[RecommendedFeature] = []
        
        # Keep user requested features
        for u_feat in intent.features:
            source = RecommendationSource(
                source_type="user_requirement",
                source_description="Explicitly requested in prompt.",
                relevance_score=1.0
            )
            reliability = self._compute_reliability("user_requirement")
            confidence = self.calculate_confidence("user_requirement", 1.0, 1.0, 1.0, 10.0)
            
            explanation = FeatureExplanation(
                feature_name=u_feat.name,
                what_it_does=u_feat.description,
                why_recommended="Extracted from your core requirements.",
                business_value="Direct fulfillment of custom request.",
                source=source,
                source_reliability=reliability,
                recommendation_confidence=confidence,
                innovation_origin="user_created",
                relevance_score=1.0
            )
            recommended_features.append(RecommendedFeature(
                name=u_feat.name,
                description=u_feat.description,
                actor_involved=u_feat.actor_involved,
                explanation=explanation
            ))

        # Evaluate Industry Patterns
        for ip in industry_features:
            if any(CanonicalNamingEngine.to_pascal_case(u.name) == CanonicalNamingEngine.to_pascal_case(ip["feature_name"]) for u in intent.features):
                continue

            ip_tokens = self._tokenize(ip["feature_name"]) + self._tokenize(ip["description"])
            sim = self._calculate_similarity(user_tokens, ip_tokens)
            relevance = round(0.70 + (0.25 * sim), 2)

            source = RecommendationSource(
                source_type="industry_pattern",
                source_description=f"Industry best practice for {category} applications.",
                relevance_score=relevance
            )
            reliability = self._compute_reliability("industry_pattern")
            confidence = self.calculate_confidence("industry_pattern", 1.0, sim, 1.0, 10.0)

            explanation = FeatureExplanation(
                feature_name=ip["feature_name"],
                what_it_does=ip["description"],
                why_recommended=ip["recommendation_reason"],
                business_value=ip["business_value"],
                source=source,
                source_reliability=reliability,
                recommendation_confidence=confidence,
                innovation_origin="industry",
                relevance_score=relevance
            )
            
            actor = "Admin"
            if "member" in ip["feature_name"].lower() or "user" in ip["feature_name"].lower():
                actor = "GymMember" if "gym" in category.lower() else "User"
            elif "student" in ip["feature_name"].lower():
                actor = "Student"
            elif "patient" in ip["feature_name"].lower():
                actor = "Patient"
            
            recommended_features.append(RecommendedFeature(
                name=ip["feature_name"],
                description=ip["description"],
                actor_involved=actor,
                explanation=explanation
            ))

        # 2. Map Recommended Actors
        recommended_actors: List[RecommendedActor] = []
        for act in intent.actors:
            recommended_actors.append(RecommendedActor(
                name=act.name,
                description=act.description,
                relevance_score=1.0,
                why_needed="Requested actor profile for operations."
            ))
            
        existing_actor_names = {a.name for a in intent.actors}
        if "Admin" not in existing_actor_names:
            recommended_actors.append(RecommendedActor(
                name="Admin",
                description="System administrator overseeing database metrics and accounts.",
                relevance_score=0.90,
                why_needed="Required to manage application entities, records, and access permissions."
            ))

        # 3. Map Recommended Innovations
        recommended_innovations: List[RecommendedInnovation] = []
        for ci in community_innovs:
            ci_tokens = self._tokenize(ci["feature_name"]) + self._tokenize(ci["description"]) + self._tokenize(ci["suggested_with"])
            sim = self._calculate_similarity(user_tokens, ci_tokens)
            relevance = round(ci["acceptance_rate"] * (ci["impact_score"] / 10.0) * (0.5 + 0.5 * sim), 2)
            
            if relevance >= 0.20 and ci["acceptance_rate"] >= 0.60:
                recommended_innovations.append(RecommendedInnovation(
                    innovation_id=ci["innovation_id"],
                    name=ci["feature_name"],
                    description=ci["description"],
                    acceptance_rate=ci["acceptance_rate"],
                    impact_score=ci["impact_score"],
                    innovation_origin=ci["innovation_origin"],
                    why_recommended=f"Highly accepted ({int(ci['acceptance_rate']*100)}% approval) in previous {category} projects. {ci['description']}"
                ))

        # 4. Map Workflows
        recommended_workflows: List[RecommendedWorkflow] = []
        if "gym" in category.lower():
            recommended_workflows.append(RecommendedWorkflow(
                name="ClassBookingFlow",
                description="Sequential steps to book a spot in a class.",
                steps=["Select Class", "Verify Capacity", "Deduct Class Credit", "Log Booking Record", "Send Notification"],
                actor_involved="GymMember",
                why_needed="Core member transaction path."
            ))
            recommended_workflows.append(RecommendedWorkflow(
                name="MembershipPurchaseFlow",
                description="Onboarding billing transaction.",
                steps=["Select Tier Plan", "Verify Payment Gateway", "Set Subscription Active", "Log Account Profile"],
                actor_involved="GymMember",
                why_needed="Enables payment transactions."
            ))
        elif "crm" in category.lower():
            recommended_workflows.append(RecommendedWorkflow(
                name="LeadConversionFlow",
                description="Progressing a sales lead to converted status.",
                steps=["Qualify Lead", "Assess Budget", "Promote Deal Stage", "Generate Customer Record"],
                actor_involved="SalesAgent",
                why_needed="Standard sales progression workflow."
            ))

        # 5. Map Recommended Permissions
        recommended_permissions: List[RecommendedPermission] = []
        for actor in recommended_actors:
            if actor.name == "Admin":
                recommended_permissions.append(RecommendedPermission(
                    actor="Admin",
                    action="ManageAllRecords",
                    description="Full administrative system configurations overrides.",
                    why_needed="Standard admin system access rights."
                ))
            else:
                recommended_permissions.append(RecommendedPermission(
                    actor=actor.name,
                    action="ReadOwnProfile",
                    description="Allows user to view their registered attributes.",
                    why_needed="Enforces fundamental privacy boundaries."
                ))

        # Refactored: Run ranking engine sorting
        recommended_features = RecommendationRankingEngine.rank_features(recommended_features)
        recommended_actors = RecommendationRankingEngine.rank_actors(recommended_actors)
        recommended_innovations = RecommendationRankingEngine.rank_innovations(recommended_innovations)

        return BlueprintRecommendation(
            app_type=category,
            recommended_actors=recommended_actors,
            recommended_features=recommended_features,
            recommended_workflows=recommended_workflows,
            recommended_permissions=recommended_permissions,
            recommended_innovations=recommended_innovations,
            confidence_score=intent.confidence_score
        )

    def _retrieve_industry_patterns(self, category: str) -> List[Dict[str, Any]]:
        patterns = []
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT feature_name, description, business_value, recommendation_reason 
                FROM industry_patterns 
                WHERE LOWER(category) = LOWER(?);
                """,
                (category,)
            )
            for row in cursor.fetchall():
                patterns.append({
                    "feature_name": row["feature_name"],
                    "description": row["description"],
                    "business_value": row["business_value"],
                    "recommendation_reason": row["recommendation_reason"]
                })
        return patterns

    def _retrieve_community_innovations(self, category: str) -> List[Dict[str, Any]]:
        innovs = []
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT innovation_id, feature_name, description, acceptance_rate, impact_score, times_suggested, suggested_with, innovation_origin 
                FROM community_innovations 
                WHERE LOWER(category) = LOWER(?);
                """,
                (category,)
            )
            for row in cursor.fetchall():
                innovs.append({
                    "innovation_id": row["innovation_id"],
                    "feature_name": row["feature_name"],
                    "description": row["description"],
                    "acceptance_rate": row["acceptance_rate"],
                    "impact_score": row["impact_score"],
                    "times_suggested": row["times_suggested"],
                    "suggested_with": row["suggested_with"],
                    "innovation_origin": row["innovation_origin"]
                })
        return innovs

    # --- WORKFLOW & TRANSACTION LAYER ---

    def create_approved_blueprint(self, project_id: str, recommendation: BlueprintRecommendation) -> ApprovedBlueprint:
        return ApprovedBlueprint(
            project_id=project_id,
            app_type=recommendation.app_type,
            actors=recommendation.recommended_actors,
            features=recommendation.recommended_features,
            workflows=recommendation.recommended_workflows,
            permissions=recommendation.recommended_permissions,
            innovations=recommendation.recommended_innovations,
            approval_history=[],
            modifications=[]
        )

    def record_approval_action(self, db_conn: sqlite3.Connection, project_id: str, item_type: str, item_name: str, status: Literal["approved", "rejected"]):
        """Persists user approvals using race-condition free parameter calculations."""
        cursor = db_conn.cursor()
        action_id = f"app_{project_id}_{item_type}_{item_name}_{int(datetime.now().timestamp())}"
        cursor.execute(
            """
            INSERT INTO approval_history (id, project_id, item_type, item_name, status)
            VALUES (?, ?, ?, ?, ?);
            """,
            (action_id, project_id, item_type, item_name, status)
        )

        if item_type == "innovation":
            # 1. Fetch current counts in Python first to avoid SQLite update-order race conditions
            cursor.execute(
                """
                SELECT innovation_id, approval_count, rejection_count, impact_score 
                FROM community_innovations 
                WHERE feature_name = ?;
                """,
                (item_name,)
            )
            row = cursor.fetchone()
            if row:
                innov_id = row["innovation_id"]
                orig_approval = row["approval_count"]
                orig_rejection = row["rejection_count"]
                impact = row["impact_score"]

                new_approval = orig_approval
                new_rejection = orig_rejection
                last_approved_at = None
                last_rejected_at = None

                # Compute updates
                if status == "approved":
                    new_approval += 1
                    last_approved_at = datetime.now().isoformat()
                else:
                    new_rejection += 1
                    last_rejected_at = datetime.now().isoformat()

                total_responses = new_approval + new_rejection
                new_rate = round(new_approval / total_responses, 2) if total_responses > 0 else 0.0
                new_score = round(new_rate * impact, 2)

                # 2. Write back updates deterministically
                if status == "approved":
                    cursor.execute(
                        """
                        UPDATE community_innovations 
                        SET approval_count = ?, 
                            times_suggested = times_suggested + 1,
                            acceptance_rate = ?,
                            community_score = ?,
                            last_approved_at = ?
                        WHERE innovation_id = ?;
                        """,
                        (new_approval, new_rate, new_score, last_approved_at, innov_id)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE community_innovations 
                        SET rejection_count = ?, 
                            times_suggested = times_suggested + 1,
                            acceptance_rate = ?,
                            community_score = ?,
                            last_rejected_at = ?
                        WHERE innovation_id = ?;
                        """,
                        (new_rejection, new_rate, new_score, last_rejected_at, innov_id)
                    )

    def record_modification_action(self, db_conn: sqlite3.Connection, project_id: str, action: Literal["ADD", "REMOVE", "EDIT"], component_type: str, name: str, details: Dict[str, Any]):
        cursor = db_conn.cursor()
        mod_id = f"mod_{project_id}_{component_type}_{name}_{int(datetime.now().timestamp())}"
        cursor.execute(
            """
            INSERT INTO blueprint_modifications (id, project_id, action, component_type, name, details)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (mod_id, project_id, action, component_type, name, json.dumps(details))
        )

    def apply_modifications(self, blueprint: ApprovedBlueprint, modification: BlueprintModification) -> ApprovedBlueprint:
        blueprint.modifications.append(modification)
        
        if modification.component_type == "feature":
            if modification.action == "ADD":
                source = RecommendationSource(
                    source_type="user_requirement",
                    source_description="Manually added by user.",
                    relevance_score=1.0
                )
                reliability = self._compute_reliability("user_requirement")
                confidence = self.calculate_confidence("user_requirement", 1.0, 1.0, 1.0, 10.0)
                
                explanation = FeatureExplanation(
                    feature_name=modification.name,
                    what_it_does=modification.details.get("description", ""),
                    why_recommended="Custom user extension.",
                    business_value="Fulfills specialized custom application scope.",
                    source=source,
                    source_reliability=reliability,
                    recommendation_confidence=confidence,
                    innovation_origin="user_created",
                    relevance_score=1.0
                )
                blueprint.features.append(RecommendedFeature(
                    name=modification.name,
                    description=modification.details.get("description", ""),
                    actor_involved=modification.details.get("actor_involved", "User"),
                    explanation=explanation
                ))
            elif modification.action == "REMOVE":
                blueprint.features = [f for f in blueprint.features if f.name != modification.name]
            elif modification.action == "EDIT":
                for f in blueprint.features:
                    if f.name == modification.name:
                        f.description = modification.details.get("description", f.description)
                        f.actor_involved = modification.details.get("actor_involved", f.actor_involved)

        elif modification.component_type == "actor":
            if modification.action == "ADD":
                blueprint.actors.append(RecommendedActor(
                    name=modification.name,
                    description=modification.details.get("description", ""),
                    relevance_score=1.0,
                    why_needed="Manually added user operational profile."
                ))
            elif modification.action == "REMOVE":
                blueprint.actors = [a for a in blueprint.actors if a.name != modification.name]
            elif modification.action == "EDIT":
                for a in blueprint.actors:
                    if a.name == modification.name:
                        a.description = modification.details.get("description", a.description)

        elif modification.component_type == "workflow":
            if modification.action == "ADD":
                blueprint.workflows.append(RecommendedWorkflow(
                    name=modification.name,
                    description=modification.details.get("description", ""),
                    steps=modification.details.get("steps", []),
                    actor_involved=modification.details.get("actor_involved", "User"),
                    why_needed="Manually added workflow."
                ))
            elif modification.action == "REMOVE":
                blueprint.workflows = [w for w in blueprint.workflows if w.name != modification.name]
            elif modification.action == "EDIT":
                for w in blueprint.workflows:
                    if w.name == modification.name:
                        w.description = modification.details.get("description", w.description)
                        w.steps = modification.details.get("steps", w.steps)
                        w.actor_involved = modification.details.get("actor_involved", w.actor_involved)

        elif modification.component_type == "innovation":
            if modification.action == "ADD":
                blueprint.innovations.append(RecommendedInnovation(
                    innovation_id=modification.details.get("innovation_id", "custom_inn"),
                    name=modification.name,
                    description=modification.details.get("description", ""),
                    acceptance_rate=1.0,
                    impact_score=10.0,
                    innovation_origin="user_created",
                    why_recommended="Manually added innovation."
                ))
            elif modification.action == "REMOVE":
                blueprint.innovations = [i for i in blueprint.innovations if i.name != modification.name]

        return blueprint
