from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

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
    risk: str
    severity: RiskLevel
    mitigation: str


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
            risks=risks,
            confidence_scores=scores,
            recommended_architecture_strategy=strategy,
        )

    @classmethod
    def attach_architecture_trace(
        cls,
        report: AIArchitectReport,
        blueprint: ApprovedBlueprint,
        system_design: MasterSpecification,
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
        return report

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

        if "hospital" in prompt_lower or "health" in intent.app_type.lower():
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
                    risk=f"Architecture may encode the wrong {item.category.replace('_', ' ')} scope.",
                    severity="HIGH",
                    mitigation=f"Clarify: {item.description}",
                ))
        if not risks:
            risks.append(ArchitectRisk(
                risk="Low-risk assumptions may still need product owner confirmation before production build-out.",
                severity="LOW",
                mitigation="Keep assumptions visible in the architect report and confirm them during blueprint review.",
            ))
        return risks

    @staticmethod
    def _calculate_confidence(
        intent: IntentExtractionResult,
        missing: List[MissingRequirement],
        assumptions: List[ArchitectAssumption],
    ) -> ArchitectConfidenceScores:
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
