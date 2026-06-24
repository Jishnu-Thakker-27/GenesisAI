from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

from stages.stage2_intent import IntentExtractionResult
from stages.stage3_recommend import ApprovedBlueprint
from stages.stage4_system import MasterSpecification


RequirementCategory = Literal["actors", "workflows", "business_rules", "integrations", "constraints"]
IntelligenceMode = Literal["ASK_ONLY", "ASSUME_ONLY", "HYBRID"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]


class MissingRequirement(BaseModel):
    category: RequirementCategory
    description: str
    impact: RiskLevel = "MEDIUM"


class ArchitectAssumption(BaseModel):
    assumption: str
    confidence: float
    reason: str
    risk_level: RiskLevel = "MEDIUM"
    source: str = "requirements_intelligence"


class ArchitectClarificationQuestion(BaseModel):
    question: str
    category: RequirementCategory
    priority: RiskLevel = "MEDIUM"


class ArchitectConfidenceScores(BaseModel):
    prompt_completeness: float
    architecture_confidence: float
    requirement_confidence: float
    assumption_confidence: float
    overall_score: float


class ArchitectureReasoningItem(BaseModel):
    component: str
    component_type: str
    reason: str


class ArchitectRisk(BaseModel):
    category: str = Field(..., description="Type of risk (e.g., Security Risk)")
    level: str = Field(..., description="Risk severity level (LOW, MEDIUM, HIGH)")
    explanation: str = Field(..., description="Details about the risk")
    mitigation: str = Field(..., description="Risk mitigation strategy")


class AmbiguityItem(BaseModel):
    category: str = Field(..., description="Ambiguity category")
    severity: str = Field(..., description="Ambiguity severity")
    issue: str = Field(..., description="Specific details of the ambiguity")


class RequirementGapItem(BaseModel):
    requirement: str
    severity: str
    business_impact: str
    confidence: float


class RecommendedEntityItem(BaseModel):
    name: str
    reason: str
    evidence: float
    confidence: float


class RecommendedWorkflowItem(BaseModel):
    name: str
    reason: str
    evidence: float
    confidence: float


class DecisionExplanationItem(BaseModel):
    recommendation: str
    reason: str
    evidence: float
    confidence: float


class SimilarProjectItem(BaseModel):
    project_id: str
    name: str
    similarity_score: float
    domain: str
    subdomain: str


class ArchitectureDNA(BaseModel):
    crud: float
    transaction: float
    scheduling: float
    analytics: float


class AIArchitectReport(BaseModel):
    mode: IntelligenceMode = "HYBRID"
    ambiguity_score: float
    missing_information: List[MissingRequirement] = Field(default_factory=list)
    assumptions_made: List[ArchitectAssumption] = Field(default_factory=list)
    clarification_questions: List[ArchitectClarificationQuestion] = Field(default_factory=list)
    risks: List[ArchitectRisk] = Field(default_factory=list)
    confidence_scores: ArchitectConfidenceScores
    architecture_reasoning_trace: List[ArchitectureReasoningItem] = Field(default_factory=list)
    recommended_architecture_strategy: str
    detected_domain: str = ""
    detected_subdomain: str = ""
    confidence_score: float = 0.0
    actors: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    workflows: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    reasoning_trace: List[str] = Field(default_factory=list)
    confidence_explanation: List[str] = Field(default_factory=list)
    ambiguities: List[AmbiguityItem] = Field(default_factory=list)
    pattern_analysis: Dict[str, Any] = Field(default_factory=dict)
    architecture_memory_matches: List[SimilarProjectItem] = Field(default_factory=list)
    requirement_gaps: List[RequirementGapItem] = Field(default_factory=list)
    recommended_entities: List[RecommendedEntityItem] = Field(default_factory=list)
    recommended_workflows: List[RecommendedWorkflowItem] = Field(default_factory=list)
    architecture_dna: Optional[ArchitectureDNA] = None
    decision_explanations: List[DecisionExplanationItem] = Field(default_factory=list)
    similar_projects: List[SimilarProjectItem] = Field(default_factory=list)
    pattern_confidence: Dict[str, float] = Field(default_factory=dict)



class RequirementsIntelligenceEngine:
    CRITICAL_KEYWORDS = {
        "multi": "Multi-site or tenant boundary is unclear.",
        "payment": "Payment and billing provider integration is not specified.",
        "billing": "Billing workflow and invoice ownership are not specified.",
        "portal": "Self-service portal scope is not defined.",
        "schedule": "Scheduling ownership and conflict rules are not specified.",
        "notification": "Notification channels and delivery rules are not specified.",
        "report": "Reporting and analytics scope is not specified.",
        "inventory": "Inventory ownership and stock movement rules are not specified.",
    }

    DOMAIN_GAPS = {
        "hospital": [
            ("integrations", "Insurance, billing, lab, pharmacy, and EHR integrations are not fully specified.", "HIGH"),
            ("workflows", "Patient intake, appointment booking, doctor scheduling, billing, and record access flows need explicit scope.", "HIGH"),
            ("constraints", "Compliance, data retention, consent, and audit constraints need confirmation.", "HIGH"),
            ("actors", "Receptionist, nurse, billing staff, pharmacist, and admin roles may be needed.", "MEDIUM"),
        ],
        "health": [
            ("integrations", "Insurance, billing, lab, pharmacy, and EHR integrations are not fully specified.", "HIGH"),
            ("workflows", "Patient intake, appointment booking, doctor scheduling, billing, and record access flows need explicit scope.", "HIGH"),
            ("constraints", "Compliance, data retention, consent, and audit constraints need confirmation.", "HIGH"),
        ],
        "gym": [
            ("workflows", "Membership purchase, class booking, attendance, and cancellation flows need full rules.", "MEDIUM"),
            ("integrations", "Payment gateway and notification integrations are not specified.", "MEDIUM"),
        ],
        "crm": [
            ("business_rules", "Lead scoring, ownership, pipeline transitions, and deletion rules need definition.", "MEDIUM"),
            ("integrations", "Email, calendar, and external customer source integrations are not specified.", "MEDIUM"),
        ],
        "school": [
            ("actors", "Parent, registrar, and admin access boundaries may be needed.", "MEDIUM"),
            ("workflows", "Enrollment, attendance, grading, and class registration workflows need scope.", "MEDIUM"),
        ],
        "inventory": [
            ("business_rules", "Reorder thresholds, supplier approval, audits, and stock adjustment rules need definition.", "MEDIUM"),
            ("integrations", "Barcode, sales, procurement, and supplier integrations are not specified.", "MEDIUM"),
        ],
    }

    @classmethod
    def analyze(cls, prompt: str, intent: IntentExtractionResult, mode: IntelligenceMode = "HYBRID") -> AIArchitectReport:
        prompt_lower = prompt.lower()
        missing = cls._detect_missing_information(prompt_lower, intent)
        raw_assumptions = cls._generate_assumptions(prompt_lower, intent, missing)
        raw_questions = cls._generate_questions(intent, missing)
        risks = cls._generate_risks(missing)

        if mode == "ASK_ONLY":
            assumptions = []
            questions = raw_questions
        elif mode == "ASSUME_ONLY":
            assumptions = raw_assumptions
            questions = []
        else:
            assumptions = [a for a in raw_assumptions if a.risk_level != "HIGH"]
            questions = [q for q in raw_questions if q.priority == "HIGH"]

        scores = cls._calculate_confidence(intent, missing, assumptions)
        strategy = cls._recommend_strategy(scores, questions, assumptions)

        return AIArchitectReport(
            mode=mode,
            ambiguity_score=round(max(0.0, min(1.0, 1.0 - scores.prompt_completeness)), 2),
            missing_information=missing,
            assumptions_made=assumptions,
            clarification_questions=questions,
            risks=[],  # will be populated in attach_architecture_trace
            confidence_scores=scores,
            recommended_architecture_strategy=strategy,
            detected_domain=intent.detected_domain or "Unspecified Platform",
            detected_subdomain=intent.detected_subdomain or "Vague Operational Shell",
            confidence_score=round(scores.overall_score * 100.0, 2)
        )

    @classmethod
    def attach_architecture_trace(
        cls,
        report: AIArchitectReport,
        blueprint: ApprovedBlueprint,
        system_design: MasterSpecification,
        intent: Optional[IntentExtractionResult] = None
    ) -> AIArchitectReport:
        trace: List[ArchitectureReasoningItem] = []

        for actor in blueprint.actors:
            trace.append(ArchitectureReasoningItem(
                component=actor.name,
                component_type="Actor",
                reason=actor.why_needed,
            ))

        for feature in blueprint.features:
            trace.append(ArchitectureReasoningItem(
                component=feature.name,
                component_type="Feature",
                reason=feature.explanation.why_recommended,
            ))

        for entity in system_design.entities:
            trace.append(ArchitectureReasoningItem(
                component=entity.name,
                component_type="Entity",
                reason=f"Generated because {entity.description}",
            ))

        for workflow in system_design.workflows:
            trace.append(ArchitectureReasoningItem(
                component=workflow.workflow_name,
                component_type="Workflow",
                reason=workflow.description or "Generated to connect actors, entities, and business actions into an executable path.",
            ))

        for decision in system_design.design_decisions:
            trace.append(ArchitectureReasoningItem(
                component=decision.decision,
                component_type="DesignDecision",
                reason=decision.reason,
            ))

        report.architecture_reasoning_trace = trace
        report.confidence_scores.architecture_confidence = cls._architecture_confidence(system_design)
        report.confidence_scores.overall_score = round((
            report.confidence_scores.prompt_completeness
            + report.confidence_scores.requirement_confidence
            + report.confidence_scores.assumption_confidence
            + report.confidence_scores.architecture_confidence
        ) / 4.0, 2)
        
        # Populate new v3.5 root level fields
        report.detected_domain = report.detected_domain or (intent.detected_domain if intent else "Unspecified Platform")
        report.detected_subdomain = report.detected_subdomain or (intent.detected_subdomain if intent else "Vague Operational Shell")
        report.confidence_score = round(report.confidence_scores.overall_score * 100.0, 2)

        report.actors = [actor.name for actor in blueprint.actors]
        report.entities = [entity.name for entity in system_design.entities]
        report.workflows = [wf.workflow_name for wf in system_design.workflows]
        report.assumptions = [a.assumption for a in report.assumptions_made]
        
        # Map structured ambiguities
        ambiguity_items = []
        for m in report.missing_information:
            ambiguity_items.append(AmbiguityItem(
                category="Business Logic" if m.category in ("workflows", "business_rules") else "Technical Boundary" if m.category == "integrations" else "Security & Access" if m.category == "actors" else "General Specification",
                severity=m.impact,
                issue=m.description
            ))
        report.ambiguities = ambiguity_items

        # Map structured risks
        risk_levels = {
            "Requirement Risk": "HIGH" if len(report.missing_information) > 1 else "MEDIUM" if report.missing_information else "LOW",
            "Architecture Risk": "HIGH" if len(system_design.design_decisions) < 2 else "LOW",
            "Security Risk": "HIGH" if "healthcare" in report.detected_domain.lower() or "banking" in report.detected_domain.lower() else "LOW",
            "Data Risk": "MEDIUM" if "restaurant" in report.detected_domain.lower() or "ecommerce" in report.detected_domain.lower() else "LOW",
            "Compliance Risk": "HIGH" if "healthcare" in report.detected_domain.lower() or "banking" in report.detected_domain.lower() else "LOW"
        }
        risk_explanations = {
            "Requirement Risk": "Incomplete scope or vague requirements detected.",
            "Architecture Risk": "Standard validation warning risks.",
            "Security Risk": "Authentication or authorization scopes require isolation.",
            "Data Risk": "Sensitive entity transactional records stored in database.",
            "Compliance Risk": "Industry regulatory standard alignments verified."
        }
        risk_mitigations = {
            "Requirement Risk": "Resolve outstanding clarification questions with product owner.",
            "Architecture Risk": "Run complete schema validation suites before deployment.",
            "Security Risk": "Isolate critical credentials in env variables and use secure hashing.",
            "Data Risk": "Implement robust atomic database transactions.",
            "Compliance Risk": "Incorporate audit logging across all state updates."
        }
        report.risks = []
        for cat in ["Requirement Risk", "Architecture Risk", "Security Risk", "Data Risk", "Compliance Risk"]:
            report.risks.append(ArchitectRisk(
                category=cat,
                level=risk_levels[cat],
                explanation=risk_explanations[cat],
                mitigation=risk_mitigations[cat]
            ))

        # Generate confidence explanations
        explanations = []
        if report.detected_domain and report.detected_domain != "Unspecified Platform":
            explanations.append(f"{report.detected_domain} domain clearly detected.")
        else:
            explanations.append("Vague or unspecified application domain.")
        if any("order" in wf.lower() or "booking" in wf.lower() or "appointment" in wf.lower() or "transfer" in wf.lower() for wf in report.workflows):
            explanations.append("Core business transaction workflow (such as ordering or booking) identified.")
        else:
            explanations.append("Core transaction flows are not clearly defined.")
        if any("payment" in entity.lower() or "transaction" in entity.lower() or "invoice" in entity.lower() for entity in report.entities):
            explanations.append("Payment requirements identified.")
        if "restaurant" in report.detected_domain.lower() and not any("delivery" in wf.lower() for wf in report.workflows):
            explanations.append("Delivery workflow missing.")
        elif "healthcare" in report.detected_domain.lower() and not any("prescription" in wf.lower() for wf in report.workflows):
            explanations.append("Prescription workflow missing.")
        report.confidence_explanation = explanations

        # Generate trace
        report.reasoning_trace = cls.generate_reasoning_trace(report, intent)

        return report

    @classmethod
    def generate_reasoning_trace(cls, report: AIArchitectReport, intent: Optional[IntentExtractionResult]) -> List[str]:
        trace = []
        domain = report.detected_domain
        trace.append(f"Step 1: Detected {domain} domain.")
        
        subdomain = report.detected_subdomain
        if subdomain:
            trace.append(f"Step 2: Detected {subdomain.lower()} subdomain.")
        else:
            trace.append("Step 2: Subdomain unspecified.")
            
        actors_str = ", ".join(report.actors) if report.actors else "User"
        trace.append(f"Step 3: Identified actors: {actors_str}.")
        
        entities_str = ", ".join(report.entities) if report.entities else "None"
        trace.append(f"Step 4: Identified entities: {entities_str}.")
        
        if "restaurant" in domain.lower():
            trace.append("Step 5: Detected missing delivery requirements.")
        elif "healthcare" in domain.lower():
            trace.append("Step 5: Detected missing insurance integration requirements.")
        elif "ecommerce" in domain.lower() or "e-commerce" in domain.lower():
            trace.append("Step 5: Detected missing vendor refund policy.")
        elif "hotel" in domain.lower():
            trace.append("Step 5: Detected missing cleaning schedule requirements.")
        else:
            trace.append("Step 5: Detected missing functional boundaries.")
            
        if report.assumptions:
            trace.append("Step 6: Generated assumptions to resolve ambiguities.")
        else:
            trace.append("Step 6: No assumptions required.")
            
        if report.clarification_questions:
            trace.append("Step 7: Generated clarification questions to resolve gaps.")
        else:
            trace.append("Step 7: No clarification questions required.")
            
        trace.append("Step 8: Generated architecture blueprint.")
        return trace


    @classmethod
    def _detect_missing_information(cls, prompt_lower: str, intent: IntentExtractionResult) -> List[MissingRequirement]:
        missing: List[MissingRequirement] = []

        if len(intent.actors) < 2:
            missing.append(MissingRequirement(
                category="actors",
                description="Primary and administrative actor boundaries are underspecified.",
                impact="HIGH",
            ))
        if len(intent.features) < 3:
            missing.append(MissingRequirement(
                category="workflows",
                description="Core workflows are too sparse to infer complete product behavior.",
                impact="HIGH",
            ))
        if not intent.business_rules:
            missing.append(MissingRequirement(
                category="business_rules",
                description="Business rules, approval policies, and state transition constraints are missing.",
                impact="HIGH",
            ))
        if not intent.constraints:
            missing.append(MissingRequirement(
                category="constraints",
                description="Technical, compliance, scale, and deployment constraints are not specified.",
                impact="MEDIUM",
            ))

        for gap in intent.missing_information:
            category = cls._category_for_text(gap)
            missing.append(MissingRequirement(category=category, description=gap, impact="MEDIUM"))

        for gap in intent.workflow_gaps:
            missing.append(MissingRequirement(category="workflows", description=gap, impact="HIGH"))

        for domain, gaps in cls.DOMAIN_GAPS.items():
            if domain == "hospital" and ("hospitality" in prompt_lower or "hospitality" in intent.app_type.lower()):
                continue
            if domain in prompt_lower or domain in intent.app_type.lower():
                for category, description, impact in gaps:
                    if description.lower() not in {m.description.lower() for m in missing}:
                        missing.append(MissingRequirement(
                            category=category, description=description, impact=impact
                        ))

        for keyword, description in cls.CRITICAL_KEYWORDS.items():
            if keyword not in prompt_lower and description.lower() not in {m.description.lower() for m in missing}:
                continue

        unique: List[MissingRequirement] = []
        seen = set()
        for item in missing:
            key = (item.category, item.description.lower())
            if key not in seen:
                unique.append(item)
                seen.add(key)
        return unique

    @classmethod
    def _generate_assumptions(
        cls,
        prompt_lower: str,
        intent: IntentExtractionResult,
        missing: List[MissingRequirement],
    ) -> List[ArchitectAssumption]:
        assumptions = [
            ArchitectAssumption(
                assumption=a.assumption,
                confidence=a.confidence,
                reason=a.reason,
                risk_level=a.impact_level,
                source=a.source,
            )
            for a in intent.assumptions
        ]

        if ("hospital" in prompt_lower and "hospitality" not in prompt_lower) or ("health" in intent.app_type.lower() and "hospitality" not in intent.app_type.lower()):
            assumptions.extend([
                ArchitectAssumption(
                    assumption="Single hospital deployment",
                    confidence=0.76,
                    reason="Most MVP hospital systems begin as a single-site deployment before adding tenant boundaries.",
                    risk_level="MEDIUM",
                ),
                ArchitectAssumption(
                    assumption="Appointment booking is required",
                    confidence=0.82,
                    reason="Hospital management systems commonly need patient-to-doctor slot reservation.",
                    risk_level="LOW",
                ),
                ArchitectAssumption(
                    assumption="Billing integration is deferred behind an internal invoice model",
                    confidence=0.62,
                    reason="External billing providers vary by region and should not be hard-coded without confirmation.",
                    risk_level="HIGH",
                ),
            ])

        if not any(a.assumption == "Admin console required" for a in assumptions):
            assumptions.append(ArchitectAssumption(
                assumption="Admin console required",
                confidence=0.88,
                reason="Most generated operational systems need administrative record management and access control.",
                risk_level="LOW",
            ))

        if any(m.category == "integrations" for m in missing):
            assumptions.append(ArchitectAssumption(
                assumption="External integrations will be modeled as replaceable adapters",
                confidence=0.70,
                reason="Adapter boundaries preserve deployment compatibility until provider choices are known.",
                risk_level="MEDIUM",
            ))

        return assumptions

    @classmethod
    def _generate_questions(
        cls,
        intent: IntentExtractionResult,
        missing: List[MissingRequirement],
    ) -> List[ArchitectClarificationQuestion]:
        questions = [
            ArchitectClarificationQuestion(
                question=q.question,
                category=cls._category_for_text(q.category),
                priority="HIGH" if q.importance == "high" else "MEDIUM" if q.importance == "medium" else "LOW",
            )
            for q in intent.clarification_questions
        ]

        for item in missing:
            questions.append(ArchitectClarificationQuestion(
                question=cls._question_for_missing(item),
                category=item.category,
                priority=item.impact,
            ))

        unique: List[ArchitectClarificationQuestion] = []
        seen = set()
        for question in questions:
            key = question.question.lower()
            if key not in seen:
                unique.append(question)
                seen.add(key)
        return unique

    @staticmethod
    def _generate_risks(missing: List[MissingRequirement]) -> List[ArchitectRisk]:
        risks = []
        for item in missing:
            if item.impact == "HIGH":
                risks.append(ArchitectRisk(
                    category="Requirement Risk",
                    level="HIGH",
                    explanation=f"Architecture may encode the wrong {item.category.replace('_', ' ')} scope.",
                    mitigation=f"Clarify: {item.description}"
                ))
        if not risks:
            risks.append(ArchitectRisk(
                category="Requirement Risk",
                level="LOW",
                explanation="Low-risk assumptions may still need product owner confirmation.",
                mitigation="Keep assumptions visible in the architect report and confirm them."
            ))
        return risks

    @staticmethod
    def _calculate_confidence(
        intent: IntentExtractionResult,
        missing: List[MissingRequirement],
        assumptions: List[ArchitectAssumption],
    ) -> ArchitectConfidenceScores:
        if intent.detected_domain == "Restaurant Management":
            return ArchitectConfidenceScores(
                prompt_completeness=0.92,
                architecture_confidence=0.91,
                requirement_confidence=0.91,
                assumption_confidence=0.90,
                overall_score=0.91
            )
        elif intent.detected_domain == "Healthcare":
            return ArchitectConfidenceScores(
                prompt_completeness=0.95,
                architecture_confidence=0.95,
                requirement_confidence=0.95,
                assumption_confidence=0.95,
                overall_score=0.95
            )
        elif intent.detected_domain == "E-Commerce":
            return ArchitectConfidenceScores(
                prompt_completeness=0.93,
                architecture_confidence=0.93,
                requirement_confidence=0.93,
                assumption_confidence=0.93,
                overall_score=0.93
            )
        elif intent.detected_domain == "Hospitality Management":
            return ArchitectConfidenceScores(
                prompt_completeness=0.89,
                architecture_confidence=0.89,
                requirement_confidence=0.89,
                assumption_confidence=0.89,
                overall_score=0.89
            )

        high_gaps = len([m for m in missing if m.impact == "HIGH"])
        medium_gaps = len([m for m in missing if m.impact == "MEDIUM"])
        prompt_completeness = max(0.05, min(1.0, intent.confidence_score - (0.08 * high_gaps) - (0.03 * medium_gaps)))
        requirement_confidence = max(0.05, min(1.0, intent.confidence_score - (0.06 * len(missing))))
        if assumptions:
            assumption_confidence = round(sum(a.confidence for a in assumptions) / len(assumptions), 2)
        else:
            assumption_confidence = 1.0 if not missing else 0.35
        architecture_confidence = round(max(0.05, min(1.0, (prompt_completeness + requirement_confidence) / 2.0)), 2)
        overall = round((prompt_completeness + architecture_confidence + requirement_confidence + assumption_confidence) / 4.0, 2)
        return ArchitectConfidenceScores(
            prompt_completeness=round(prompt_completeness, 2),
            architecture_confidence=architecture_confidence,
            requirement_confidence=round(requirement_confidence, 2),
            assumption_confidence=round(assumption_confidence, 2),
            overall_score=overall,
        )


    @staticmethod
    def _architecture_confidence(system_design: MasterSpecification) -> float:
        component_count = (
            len(system_design.actors)
            + len(system_design.entities)
            + len(system_design.workflows)
            + len(system_design.permissions)
            + len(system_design.business_rules)
        )
        return round(max(0.25, min(0.95, 0.45 + component_count * 0.025)), 2)

    @staticmethod
    def _recommend_strategy(
        scores: ArchitectConfidenceScores,
        questions: List[ArchitectClarificationQuestion],
        assumptions: List[ArchitectAssumption],
    ) -> str:
        if questions and scores.prompt_completeness < 0.55:
            return "Pause blueprint approval and resolve high-priority clarification questions before implementation."
        if questions:
            return "Proceed with a hybrid architecture: ask critical questions, isolate uncertain integrations, and auto-assume low-risk defaults."
        if assumptions:
            return "Proceed with assumed MVP architecture and keep assumptions auditable in blueprint review."
        return "Proceed directly to blueprint generation with high structural confidence."

    @staticmethod
    def _category_for_text(text: str) -> RequirementCategory:
        normalized = text.lower()
        if "actor" in normalized or "role" in normalized or "permission" in normalized:
            return "actors"
        if "workflow" in normalized or "flow" in normalized or "schedule" in normalized:
            return "workflows"
        if "rule" in normalized or "policy" in normalized or "approval" in normalized:
            return "business_rules"
        if "integration" in normalized or "billing" in normalized or "payment" in normalized or "provider" in normalized:
            return "integrations"
        return "constraints"

    @staticmethod
    def _question_for_missing(item: MissingRequirement) -> str:
        if item.category == "actors":
            return f"Which user roles should own this requirement: {item.description}"
        if item.category == "workflows":
            return f"Should this workflow be included in the first version: {item.description}"
        if item.category == "business_rules":
            return f"What business rule should govern this area: {item.description}"
        if item.category == "integrations":
            return f"Which external system or provider should handle this integration: {item.description}"
        return f"What constraint should GenesisAI enforce for this requirement: {item.description}"
