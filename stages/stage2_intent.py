import os
import json
import logging
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Any, Dict
from google import genai
from google.genai import types
from google.genai.errors import APIError

from config import GEMINI_API_KEY, GEMINI_MODEL
from core.naming import CanonicalNamingEngine

logger = logging.getLogger(__name__)

# --- STAGE 2 HARDENED DATA MODELS ---

class RecommendationSource(BaseModel):
    source_type: Literal["industry_pattern", "community_innovation", "user_requirement", "logical_inference"]
    source_description: str


class IntentActor(BaseModel):
    name: str = Field(..., description="Name of the actor in PascalCase (e.g., GymMember, SiteAdmin)")
    description: str = Field(..., description="Role and access description")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class IntentFeature(BaseModel):
    name: str = Field(..., description="Name of the feature")
    description: str = Field(..., description="What the feature allows the user to do")
    actor_involved: str = Field(..., description="Actor associated with this feature")
    source: Optional[RecommendationSource] = Field(None, description="Optional metadata tracing the source of the feature recommendation")

    @field_validator("actor_involved", mode="before")
    @classmethod
    def clean_actor(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class AssumptionModel(BaseModel):
    assumption: str = Field(..., description="Structured assumption detail")
    reason: str = Field(..., description="Rational reason for this assumption")
    source: Literal["industry_best_practice", "logical_inference", "user_hint"]
    confidence: float = Field(..., description="Confidence score for this assumption (0.0 to 1.0)")
    impact_level: Literal["HIGH", "MEDIUM", "LOW"] = Field("MEDIUM", description="How critical this assumption is to core workflows")


class ClarificationQuestion(BaseModel):
    question: str = Field(..., description="Direct question to ask the user")
    category: Literal["permissions", "workflows", "features", "constraints", "general"]
    importance: Literal["high", "medium", "low"]


class ConfidenceBreakdown(BaseModel):
    app_type_score: float = Field(..., description="Completeness of Application Type classification")
    actor_score: float = Field(..., description="Completeness of User Roles definition")
    feature_score: float = Field(..., description="Completeness of Functional Features")
    business_rule_score: float = Field(..., description="Completeness of Business Rules")
    workflow_score: float = Field(..., description="Completeness of Workflow Flow coverage")
    constraint_score: float = Field(..., description="Completeness of Constraints")


class IntentExtractionResult(BaseModel):
    app_name: str = Field(..., description="Proposed name of the application")
    app_type: str = Field(..., description="Identified application category")
    actors: List[IntentActor] = Field(default_factory=list)
    features: List[IntentFeature] = Field(default_factory=list)
    business_rules: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    workflow_gaps: List[str] = Field(default_factory=list, description="Missing workflows or paths that need definition")
    assumptions: List[AssumptionModel] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    clarification_questions: List[ClarificationQuestion] = Field(default_factory=list)
    confidence_score: float = Field(..., description="Blended overall confidence score between 0.0 and 1.0")
    confidence_explanation: List[str] = Field(default_factory=list)
    confidence_breakdown: Optional[ConfidenceBreakdown] = Field(None, description="Granular confidence scores per layer")
    processing_mode: Literal["MODE_A", "MODE_B", "MODE_C"] = Field("MODE_B")

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


# --- PROMPT TEMPLATES ---

SYSTEM_PROMPT = """You are the Intent Extraction Engine of an AI Software Compiler.
Your primary role is to dissect natural language application prompts and organize them into structured components.

You must:
1. Detect the Application Type and suggest a clean, functional App Name.
2. Identify distinct Actors/Roles involved in the application.
3. Extract core Features mapping them to actors, and mark their source.
4. Extract Business Rules and technical constraints.
5. Identify Gaps or missing details in the prompt (e.g., roles, flows, database requirements).
6. Detect Workflow Gaps specifically (e.g., Membership Purchase Flow, Class Booking Flow).
7. Provide logical, structured assumptions to fill missing slots, including their impact levels.
8. Generate high-quality clarification questions to resolve critical gaps.
9. Assess the prompt completeness and generate a confidence score with explanations.

Rules:
- Actors must have PascalCase names.
- Normalize actor references in features, assumptions, and workflows.
- Maintain high logical consistency across all extracted fields.
"""

INTENT_USER_PROMPT = """Analyze the following user prompt for application development:

\"\"\"
{user_prompt}
\"\"\"

Produce the results matching the required JSON schema.
"""


# --- INTENT EXTRACTION ENGINE ---

class IntentExtractionEngine:
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        
        # Initialize Gemini Client if key is available
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize GenAI client: {e}. Falling back to mock engine.")

    def extract_intent(self, prompt: str) -> IntentExtractionResult:
        """Main entry point to perform structured intent extraction."""
        if not prompt or not prompt.strip():
            raise ValueError("Input prompt cannot be empty.")

        # 1. Attempt Live LLM Generation
        raw_result = None
        if self.client:
            try:
                raw_result = self._call_gemini_api(prompt)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Redirecting to local rule-based extractor.")

        # 2. Fallback to Local Rule-Based Mock Extractor if needed
        if not raw_result:
            raw_result = self._local_rule_based_extraction(prompt)

        # 3. Post-Process via the Confidence & Clarification Engines
        processed_result = self._process_and_refine(raw_result)
        return processed_result

    def _call_gemini_api(self, prompt: str) -> IntentExtractionResult:
        """Performs a schema-constrained call to the Gemini API."""
        contents = INTENT_USER_PROMPT.format(user_prompt=prompt)
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=IntentExtractionResult,
                temperature=0.1,  # Low temperature for deterministic behavior
            )
        )
        # Parse the verified JSON string back into the Pydantic model
        data = json.loads(response.text)
        return IntentExtractionResult(**data)

    def _process_and_refine(self, result: IntentExtractionResult) -> IntentExtractionResult:
        """Applies deterministic confidence calculations and sets the processing mode."""
        # 1. Evaluate Rule-Based Confidence breakdown components
        
        # App Type Complete: 1.0 unless it's generic/contradictory
        if result.app_type in ["Unspecified Platform", "Experimental System"]:
            app_type_score = 0.5
        else:
            app_type_score = 1.0

        # Actor completeness
        if len(result.actors) >= 2:
            actor_score = 1.0
        elif len(result.actors) == 1:
            actor_score = 0.5
        else:
            actor_score = 0.0

        # Feature completeness
        if len(result.features) >= 3:
            feature_score = 1.0
        elif len(result.features) > 0:
            feature_score = 0.7
        else:
            feature_score = 0.0

        # Business Rule completeness
        if len(result.business_rules) >= 2:
            business_rule_score = 1.0
        elif len(result.business_rules) == 1:
            business_rule_score = 0.5
        else:
            business_rule_score = 0.1

        # Workflow coverage based on gaps
        if len(result.workflow_gaps) == 0:
            workflow_score = 1.0
        elif len(result.workflow_gaps) == 1:
            workflow_score = 0.7
        elif len(result.workflow_gaps) == 2:
            workflow_score = 0.4
        else:
            workflow_score = 0.1

        # Constraint completeness
        if len(result.constraints) >= 1:
            constraint_score = 1.0
        else:
            constraint_score = 0.4

        # Assemble granular breakdown
        result.confidence_breakdown = ConfidenceBreakdown(
            app_type_score=round(app_type_score, 2),
            actor_score=round(actor_score, 2),
            feature_score=round(feature_score, 2),
            business_rule_score=round(business_rule_score, 2),
            workflow_score=round(workflow_score, 2),
            constraint_score=round(constraint_score, 2)
        )

        # 2. Derive blended rule score (weighted average)
        derived_score = (
            (0.15 * app_type_score) +
            (0.20 * actor_score) +
            (0.25 * feature_score) +
            (0.15 * business_rule_score) +
            (0.15 * workflow_score) +
            (0.10 * constraint_score)
        )

        # Compute final blended confidence score (60% LLM raw + 40% derived)
        final_score = round((result.confidence_score * 0.6) + (derived_score * 0.4), 2)
        result.confidence_score = final_score

        # 3. Formulate detailed explanations
        deductions = []
        if app_type_score < 1.0:
            deductions.append("Vague or contradictory application type definition.")
        if actor_score < 1.0:
            deductions.append(f"Incomplete user roles profile (actor score: {actor_score}).")
        if feature_score < 1.0:
            deductions.append("Insufficient functional features cataloged.")
        if business_rule_score < 1.0:
            deductions.append("Lack of clearly defined business operational rules.")
        if workflow_score < 1.0:
            deductions.append(f"Underspecified workflow pathways ({len(result.workflow_gaps)} critical gaps).")
        if constraint_score < 1.0:
            deductions.append("Missing technical deployment constraints.")

        result.confidence_explanation = [d for d in deductions if d]
        if final_score >= 0.85:
            result.confidence_explanation.append("High overall structural confidence.")
        elif final_score >= 0.6:
            result.confidence_explanation.append("Moderate structural confidence; proceed with assumptions.")
        else:
            result.confidence_explanation.append("Low structural confidence; requires user clarification.")

        # 4. Enforce processing mode rules
        if final_score >= 0.85:
            result.processing_mode = "MODE_B"  # Assume mode
            result.clarification_questions = []
        elif final_score < 0.6:
            result.processing_mode = "MODE_A"  # Clarify mode
            result.assumptions = []
        else:
            result.processing_mode = "MODE_C"  # Hybrid mode

        return result

    def _local_rule_based_extraction(self, prompt: str) -> IntentExtractionResult:
        """Rule-based mock fallback supporting normal and edge cases for local testing."""
        prompt_lower = prompt.lower()

        # --- CASE 1: Gym Manager App ---
        if "gym" in prompt_lower:
            return IntentExtractionResult(
                app_name="GymFitnessManager",
                app_type="Gym Management",
                actors=[
                    IntentActor(name="GymMember", description="Standard members who book classes"),
                    IntentActor(name="GymTrainer", description="Instructors who host classes"),
                    IntentActor(name="Admin", description="Manages memberships and analytics")
                ],
                features=[
                    IntentFeature(
                        name="BookClass", 
                        description="Enables members to book fitness slots", 
                        actor_involved="GymMember",
                        source=RecommendationSource(source_type="user_requirement", source_description="Extracted directly from requirements")
                    ),
                    IntentFeature(
                        name="CancelBooking", 
                        description="Allows canceling class slot reservations", 
                        actor_involved="GymMember",
                        source=RecommendationSource(source_type="logical_inference", source_description="Implied by reservation booking capability")
                    ),
                    IntentFeature(
                        name="ManageSchedule", 
                        description="Enables trainers to schedule classes", 
                        actor_involved="GymTrainer",
                        source=RecommendationSource(source_type="industry_pattern", source_description="Found in standard scheduling templates")
                    )
                ],
                business_rules=[
                    "Members can book a maximum of 3 classes per day.",
                    "Cancellations must be done at least 2 hours before class starts."
                ],
                constraints=["SQLite database used to store schedules."],
                workflow_gaps=[
                    "Membership Purchase Flow",
                    "Attendance Tracking Flow"
                ],
                assumptions=[
                    AssumptionModel(
                        assumption="Gym runs multiple concurrent classes",
                        reason="Standard gym class setups require multi-trainer tracking",
                        source="industry_best_practice",
                        confidence=0.9,
                        impact_level="HIGH"
                    )
                ],
                missing_information=["Membership types (Silver, Gold, Platinum) definitions."],
                clarification_questions=[
                    ClarificationQuestion(
                        question="Should we support automated waiting lists?",
                        category="workflows",
                        importance="medium"
                    )
                ],
                confidence_score=0.90,
                confidence_explanation=[]
            )

        # --- CASE 2: CRM ---
        elif "crm" in prompt_lower or "customer" in prompt_lower:
            # Edge Case Check: "CRM but do not store customers"
            if "do not store customers" in prompt_lower:
                return IntentExtractionResult(
                    app_name="ConflictCRM",
                    app_type="Customer Relationship Management",
                    actors=[IntentActor(name="Agent", description="Sales person")],
                    features=[
                        IntentFeature(
                            name="LogInteraction", 
                            description="Log contact events", 
                            actor_involved="Agent",
                            source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                        )
                    ],
                    business_rules=["Interactions must specify contact details."],
                    constraints=["Conflicting requirement: CRM without customer storage."],
                    workflow_gaps=["Customer Profile Creation Flow"],
                    assumptions=[],
                    missing_information=["Where do interactions attach if customers are not stored?"],
                    clarification_questions=[
                        ClarificationQuestion(
                            question="How can we run a CRM without a customer database?",
                            category="general",
                            importance="high"
                        )
                    ],
                    confidence_score=0.25,
                    confidence_explanation=[]
                )
            # Normal CRM
            return IntentExtractionResult(
                app_name="SalesCoreCRM",
                app_type="CRM Application",
                actors=[
                    IntentActor(name="SalesAgent", description="Tracks leads and conversions"),
                    IntentActor(name="SalesManager", description="Views team pipeline dashboards")
                ],
                features=[
                    IntentFeature(
                        name="AddCustomer", 
                        description="Create new lead profile", 
                        actor_involved="SalesAgent",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    ),
                    IntentFeature(
                        name="UpdateDealStage", 
                        description="Promote leads through funnel stages", 
                        actor_involved="SalesAgent",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    )
                ],
                business_rules=["Only managers can mark deals as Deleted."],
                constraints=["User accounts must use email login authentication."],
                workflow_gaps=[],
                assumptions=[
                    AssumptionModel(
                        assumption="Deals transition sequentially",
                        reason="Standard pipeline workflows start at prospect and end at won",
                        source="industry_best_practice",
                        confidence=0.95,
                        impact_level="MEDIUM"
                    )
                ],
                missing_information=["Lead scoring weight assignments."],
                clarification_questions=[
                    ClarificationQuestion(
                        question="Should we integrate external email notification triggers?",
                        category="workflows",
                        importance="low"
                    )
                ],
                confidence_score=0.88,
                confidence_explanation=[]
            )

        # --- CASE 3: Hospital/Medical ---
        elif "hospital" in prompt_lower or "medical" in prompt_lower:
            return IntentExtractionResult(
                app_name="HealthSyncPortal",
                app_type="Healthcare Management",
                actors=[
                    IntentActor(name="Patient", description="Book appointments and view records"),
                    IntentActor(name="Doctor", description="Manage appointments and issue prescriptions")
                ],
                features=[
                    IntentFeature(
                        name="RequestAppointment", 
                        description="Request medical slot reservation", 
                        actor_involved="Patient",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    ),
                    IntentFeature(
                        name="WritePrescription", 
                        description="Create prescription notes", 
                        actor_involved="Doctor",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    )
                ],
                business_rules=["Only doctors can write medical records."],
                constraints=["HIPAA compliance guidelines simulated."],
                workflow_gaps=["Patient Intake Flow", "Prescription Dispensation Flow"],
                assumptions=[
                    AssumptionModel(
                        assumption="Prescriptions link to medical inventory",
                        reason="Standard practice for hospital automation systems",
                        source="industry_best_practice",
                        confidence=0.80,
                        impact_level="MEDIUM"
                    )
                ],
                missing_information=["Insurance billing provider integrations."],
                clarification_questions=[
                    ClarificationQuestion(
                        question="Should patients receive auto-reminders via SMS?",
                        category="workflows",
                        importance="medium"
                    )
                ],
                confidence_score=0.82,
                confidence_explanation=[]
            )

        # --- CASE 4: School/Education ---
        elif "school" in prompt_lower or "education" in prompt_lower:
            return IntentExtractionResult(
                app_name="EduPulsePortal",
                app_type="School Information System",
                actors=[
                    IntentActor(name="Student", description="Access grades and classes"),
                    IntentActor(name="Teacher", description="Post assignments and grades")
                ],
                features=[
                    IntentFeature(
                        name="ViewGrades", 
                        description="Check exam scores", 
                        actor_involved="Student",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    ),
                    IntentFeature(
                        name="SubmitAssignment", 
                        description="Upload homework files", 
                        actor_involved="Student",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    ),
                    IntentFeature(
                        name="GradeAssignment", 
                        description="Grade submitted assignments", 
                        actor_involved="Teacher",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    )
                ],
                business_rules=["Grades cannot be modified after semester close."],
                constraints=["Max assignment file upload size is 10MB."],
                workflow_gaps=["Class Registration Flow"],
                assumptions=[
                    AssumptionModel(
                        assumption="Courses map to classrooms",
                        reason="Standard school layout paradigm",
                        source="industry_best_practice",
                        confidence=0.90,
                        impact_level="LOW"
                    )
                ],
                missing_information=["Parent profile access boundaries."],
                clarification_questions=[
                    ClarificationQuestion(
                        question="Do we need real-time student attendance trackers?",
                        category="features",
                        importance="high"
                    )
                ],
                confidence_score=0.87,
                confidence_explanation=[]
            )

        # --- CASE 5: Inventory/Stock ---
        elif "inventory" in prompt_lower or "stock" in prompt_lower:
            return IntentExtractionResult(
                app_name="StockCoreHub",
                app_type="Inventory Management",
                actors=[
                    IntentActor(name="WarehouseAgent", description="Logs arrivals and shipments"),
                    IntentActor(name="ProcurementOfficer", description="Approves buy orders")
                ],
                features=[
                    IntentFeature(
                        name="LogStockArrival", 
                        description="Increments item counts", 
                        actor_involved="WarehouseAgent",
                        source=RecommendationSource(source_type="user_requirement", source_description="Direct requirement")
                    ),
                    IntentFeature(
                        name="InitiateReorder", 
                        description="Drafts low-stock procurement", 
                        actor_involved="WarehouseAgent",
                        source=RecommendationSource(source_type="logical_inference", source_description="Implied action for warehouse")
                    )
                ],
                business_rules=["Reorders require Procurement officer signoff."],
                constraints=["SKU codes must follow ISO-9001 inventory structure."],
                workflow_gaps=["Stock Audit Flow"],
                assumptions=[
                    AssumptionModel(
                        assumption="Stock levels decrement on sales API call",
                        reason="Enables downstream sales updates",
                        source="logical_inference",
                        confidence=0.85,
                        impact_level="HIGH"
                    )
                ],
                missing_information=["Supplier contact profiles schema."],
                clarification_questions=[
                    ClarificationQuestion(
                        question="Do you require barcode scanner support?",
                        category="features",
                        importance="medium"
                    )
                ],
                confidence_score=0.86,
                confidence_explanation=[]
            )

        # --- EDGE CASE: "Everyone is admin but nobody has admin rights" ---
        elif "everyone is admin but nobody has admin rights" in prompt_lower:
            return IntentExtractionResult(
                app_name="ParadoxApp",
                app_type="Experimental System",
                actors=[IntentActor(name="Admin", description="User role")],
                features=[
                    IntentFeature(
                        name="DoNothing", 
                        description="No operations permitted", 
                        actor_involved="Admin",
                        source=RecommendationSource(source_type="user_requirement", source_description="Literal requirement mapping")
                    )
                ],
                business_rules=["Admin actions must fail permission checks."],
                constraints=["Permissions matrix contains conflicting overrides."],
                workflow_gaps=["User Activation Flow"],
                assumptions=[],
                missing_information=["Permission models contradict actor assignments."],
                clarification_questions=[
                    ClarificationQuestion(
                        question="If admins have no permissions, what actions can they execute?",
                        category="permissions",
                        importance="high"
                    )
                ],
                confidence_score=0.15,
                confidence_explanation=[]
            )

        # --- GENERAL VAGUE EDGE CASE: "Build a platform" or similar ---
        else:
            return IntentExtractionResult(
                app_name="GenericPlatform",
                app_type="Unspecified Platform",
                actors=[IntentActor(name="User", description="Standard application user")],
                features=[
                    IntentFeature(
                        name="AccessPlatform", 
                        description="Log in to the system", 
                        actor_involved="User",
                        source=RecommendationSource(source_type="logical_inference", source_description="Baseline access requirement")
                    )
                ],
                business_rules=["Users must accept Terms of Service."],
                constraints=[],
                workflow_gaps=["Platform Registration Flow", "Admin Configuration Flow"],
                assumptions=[],
                missing_information=[
                    "Core business focus (Gym, E-commerce, School etc.).",
                    "Specific actors and distinct roles.",
                    "Functional business workflows."
                ],
                clarification_questions=[
                    ClarificationQuestion(
                        question="What is the primary business vertical or use case of this platform?",
                        category="general",
                        importance="high"
                    ),
                    ClarificationQuestion(
                        question="Which user roles should have administrative access?",
                        category="permissions",
                        importance="high"
                    )
                ],
                confidence_score=0.30,
                confidence_explanation=[]
            )
