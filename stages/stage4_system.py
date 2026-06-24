import json
import logging
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any, Union
from datetime import datetime

from core.naming import CanonicalNamingEngine
from core.ast import Actor, EntityField, Entity, BusinessRule
from stages.stage3_recommend import ApprovedBlueprint, RecommendedActor, RecommendedFeature

logger = logging.getLogger(__name__)

# --- STAGE 4 LOGICAL AST MODELS ---

class RelationshipDefinition(BaseModel):
    relationship_id: str = Field(..., description="Unique ID e.g., rel_member_booking")
    source_entity: str = Field(..., description="PascalCase source entity")
    target_entity: str = Field(..., description="PascalCase target entity")
    relationship_type: Literal["one-to-one", "one-to-many", "many-to-one", "many-to-many"]
    description: str

    @field_validator("source_entity", "target_entity", mode="before")
    @classmethod
    def clean_entity_names(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class WorkflowDefinition(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow slug")
    workflow_name: str
    description: str = Field("", description="Description of the workflow")
    workflow_steps: List[str] = Field(default_factory=list)
    actors: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list, description="Entities involved in this workflow")
    workflow_dependencies: List[str] = Field(default_factory=list, description="Other workflows this depends on")
    criticality: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class PermissionDefinition(BaseModel):
    role: str = Field(..., description="Role name in PascalCase")
    permissions: List[str] = Field(default_factory=list)
    reason: str


class EntityDefinition(BaseModel):
    entity_id: str = Field(..., description="Unique logical ID e.g., ent_member")
    entity_name: str = Field(..., description="PascalCase entity name")
    name: str = Field(..., description="Alias for backward compatibility")
    description: str
    source: str
    confidence: float
    fields: List[EntityField] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

    @field_validator("entity_name", "name", mode="before")
    @classmethod
    def clean_entity_names(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class BusinessRuleDefinition(BaseModel):
    rule_id: str = Field(..., description="BR_001 style identifier")
    rule: str = Field(..., description="Plain text rule description")
    source: str
    priority: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    affected_entities: List[str] = Field(default_factory=list)
    description: str = "" # compatibility
    enforcement_logic: str = "" # compatibility


class DesignDecision(BaseModel):
    decision_id: str
    decision: str
    reason: str
    source: str
    impact_level: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
    affected_components: List[str] = Field(default_factory=list)


class SystemDesignGraph(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class MasterSpecification(BaseModel):
    app_name: str
    app_type: str
    actors: List[Actor] = Field(default_factory=list)
    entities: List[Union[EntityDefinition, Entity]] = Field(default_factory=list)
    relationships: List[RelationshipDefinition] = Field(default_factory=list)
    workflows: List[WorkflowDefinition] = Field(default_factory=list)
    permissions: List[PermissionDefinition] = Field(default_factory=list)
    business_rules: List[Union[BusinessRuleDefinition, BusinessRule]] = Field(default_factory=list)
    design_decisions: List[DesignDecision] = Field(default_factory=list)
    graph: SystemDesignGraph = Field(default_factory=SystemDesignGraph)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- VALIDATION ENGINE MODELS ---

class ValidationIssue(BaseModel):
    rule_id: str
    category: str
    message: str
    severity: Literal["CRITICAL", "WARNING"]


class MasterSpecificationValidationReport(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    checked_rules_count: int = 10
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- SYSTEM DESIGN ENGINES ---

class EntityDiscoveryEngine:
    @staticmethod
    def discover_entities(blueprint: ApprovedBlueprint, report: Optional[Any] = None) -> List[EntityDefinition]:
        """Discovers logical database entities and populates their fields deterministically based on blueprint category or report entities."""
        category = blueprint.app_type.lower()
        entities_map: Dict[str, EntityDefinition] = {}

        all_predefined_entities = {
            "Menu": EntityDefinition(
                entity_id="ent_menu", entity_name="Menu", name="Menu",
                description="Logical restaurant menu options.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="description", type="string")
                ]
            ),
            "MenuItem": EntityDefinition(
                entity_id="ent_menuitem", entity_name="MenuItem", name="MenuItem",
                description="Individual food/drink options within a menu.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="menu_id", type="relationship", references="Menu.id"),
                    EntityField(name="name", type="string"),
                    EntityField(name="price", type="float")
                ]
            ),
            "Order": EntityDefinition(
                entity_id="ent_order", entity_name="Order", name="Order",
                description="Orders placed by customers.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="customer_id", type="string"),
                    EntityField(name="total_amount", type="float"),
                    EntityField(name="status", type="string")
                ]
            ),
            "Reservation": EntityDefinition(
                entity_id="ent_reservation", entity_name="Reservation", name="Reservation",
                description="Table reservations made by customers.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="customer_id", type="string"),
                    EntityField(name="reservation_time", type="datetime"),
                    EntityField(name="party_size", type="integer")
                ]
            ),
            "Payment": EntityDefinition(
                entity_id="ent_payment", entity_name="Payment", name="Payment",
                description="Payments received for orders.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="order_id", type="relationship", references="Order.id"),
                    EntityField(name="amount", type="float"),
                    EntityField(name="status", type="string")
                ]
            ),
            "Patient": EntityDefinition(
                entity_id="ent_patient", entity_name="Patient", name="Patient",
                description="Logical patient record.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="dob", type="string"),
                    EntityField(name="insurance_provider", type="string")
                ]
            ),
            "Doctor": EntityDefinition(
                entity_id="ent_doctor", entity_name="Doctor", name="Doctor",
                description="Logical doctor record.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="specialization", type="string")
                ]
            ),
            "Appointment": EntityDefinition(
                entity_id="ent_appointment", entity_name="Appointment", name="Appointment",
                description="Patient to doctor appointments slots.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="patient_id", type="relationship", references="Patient.id"),
                    EntityField(name="doctor_id", type="relationship", references="Doctor.id"),
                    EntityField(name="appointment_time", type="datetime")
                ]
            ),
            "MedicalRecord": EntityDefinition(
                entity_id="ent_medicalrecord", entity_name="MedicalRecord", name="MedicalRecord",
                description="Confidential medical history diagnosis log.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="patient_id", type="relationship", references="Patient.id"),
                    EntityField(name="diagnosis", type="string"),
                    EntityField(name="prescription", type="string")
                ]
            ),
            "Prescription": EntityDefinition(
                entity_id="ent_prescription", entity_name="Prescription", name="Prescription",
                description="Prescription notes created by practitioner.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="patient_id", type="relationship", references="Patient.id"),
                    EntityField(name="medication", type="string"),
                    EntityField(name="dosage", type="string")
                ]
            ),
            "Product": EntityDefinition(
                entity_id="ent_product", entity_name="Product", name="Product",
                description="Product catalog inventory ledger.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="sku", type="string"),
                    EntityField(name="name", type="string"),
                    EntityField(name="price", type="float"),
                    EntityField(name="stock_quantity", type="integer")
                ]
            ),
            "Cart": EntityDefinition(
                entity_id="ent_cart", entity_name="Cart", name="Cart",
                description="Shopping cart item list.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="product_id", type="relationship", references="Product.id"),
                    EntityField(name="quantity", type="integer")
                ]
            ),
            "Inventory": EntityDefinition(
                entity_id="ent_inventory", entity_name="Inventory", name="Inventory",
                description="Stock quantities tracking.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="product_id", type="relationship", references="Product.id"),
                    EntityField(name="quantity", type="integer")
                ]
            ),
            "Room": EntityDefinition(
                entity_id="ent_room", entity_name="Room", name="Room",
                description="Hotel room listings.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="room_number", type="string"),
                    EntityField(name="room_type", type="string"),
                    EntityField(name="price_per_night", type="float")
                ]
            ),
            "Booking": EntityDefinition(
                entity_id="ent_booking", entity_name="Booking", name="Booking",
                description="Hotel room reservation log.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="room_id", type="relationship", references="Room.id"),
                    EntityField(name="guest_id", type="string"),
                    EntityField(name="check_in_date", type="datetime")
                ]
            ),
            "Guest": EntityDefinition(
                entity_id="ent_guest", entity_name="Guest", name="Guest",
                description="Guest profile record.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="email", type="string")
                ]
            ),
            "Member": EntityDefinition(
                entity_id="ent_member", entity_name="Member", name="Member",
                description="Gym member details.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="first_name", type="string"),
                    EntityField(name="last_name", type="string"),
                    EntityField(name="email", type="string"),
                    EntityField(name="membership_status", type="string")
                ]
            ),
            "Trainer": EntityDefinition(
                entity_id="ent_trainer", entity_name="Trainer", name="Trainer",
                description="Gym trainer details.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="specialty", type="string")
                ]
            ),
            "ClassSchedule": EntityDefinition(
                entity_id="ent_classschedule", entity_name="ClassSchedule", name="ClassSchedule",
                description="Gym fitness class calendars.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="class_name", type="string"),
                    EntityField(name="trainer_id", type="relationship", references="Trainer.id"),
                    EntityField(name="capacity", type="integer")
                ]
            ),
            "ClassBooking": EntityDefinition(
                entity_id="ent_classbooking", entity_name="ClassBooking", name="ClassBooking",
                description="Gym class slot booking reservation.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="member_id", type="relationship", references="Member.id"),
                    EntityField(name="class_schedule_id", type="relationship", references="ClassSchedule.id"),
                    EntityField(name="booking_date", type="datetime")
                ]
            ),
            "Contact": EntityDefinition(
                entity_id="ent_contact", entity_name="Contact", name="Contact",
                description="CRM client contacts list.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="email", type="string")
                ]
            ),
            "Deal": EntityDefinition(
                entity_id="ent_deal", entity_name="Deal", name="Deal",
                description="CRM pipeline deals progress.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="contact_id", type="relationship", references="Contact.id"),
                    EntityField(name="deal_value", type="float"),
                    EntityField(name="deal_stage", type="string")
                ]
            ),
            "PipelineStage": EntityDefinition(
                entity_id="ent_pipelinestage", entity_name="PipelineStage", name="PipelineStage",
                description="CRM stages config.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="stage_name", type="string")
                ]
            ),
            "Customer": EntityDefinition(
                entity_id="ent_customer", entity_name="Customer", name="Customer",
                description="Logical client lead details record.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="company_name", type="string"),
                    EntityField(name="contact_email", type="string")
                ]
            ),
            "Lead": EntityDefinition(
                entity_id="ent_lead", entity_name="Lead", name="Lead",
                description="Logical sales pipeline deal progress records.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="customer_id", type="relationship", references="Customer.id"),
                    EntityField(name="deal_value", type="float"),
                    EntityField(name="deal_stage", type="string")
                ]
            ),
            "InteractionLog": EntityDefinition(
                entity_id="ent_interactionlog", entity_name="InteractionLog", name="InteractionLog",
                description="Logical log tracking agent communications with leads.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="lead_id", type="relationship", references="Lead.id"),
                    EntityField(name="notes", type="string")
                ]
            ),
            "Student": EntityDefinition(
                entity_id="ent_student", entity_name="Student", name="Student",
                description="School student academic profile.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="grade_level", type="string")
                ]
            ),
            "Teacher": EntityDefinition(
                entity_id="ent_teacher", entity_name="Teacher", name="Teacher",
                description="School teacher details.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="department", type="string")
                ]
            ),
            "Course": EntityDefinition(
                entity_id="ent_course", entity_name="Course", name="Course",
                description="School academic courses catalog.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="title", type="string"),
                    EntityField(name="teacher_id", type="relationship", references="Teacher.id")
                ]
            ),
            "Enrollment": EntityDefinition(
                entity_id="ent_enrollment", entity_name="Enrollment", name="Enrollment",
                description="School course enrollment record.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="student_id", type="relationship", references="Student.id"),
                    EntityField(name="course_id", type="relationship", references="Course.id"),
                    EntityField(name="grade", type="string")
                ]
            ),
            "Grade": EntityDefinition(
                entity_id="ent_grade", entity_name="Grade", name="Grade",
                description="School grades metrics.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="enrollment_id", type="relationship", references="Enrollment.id"),
                    EntityField(name="score", type="string")
                ]
            ),
            "Supplier": EntityDefinition(
                entity_id="ent_supplier", entity_name="Supplier", name="Supplier",
                description="Inventory supplier contact records.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="name", type="string"),
                    EntityField(name="contact_info", type="string")
                ]
            ),
            "StockOrder": EntityDefinition(
                entity_id="ent_stockorder", entity_name="StockOrder", name="StockOrder",
                description="Inventory stock order replenish request.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="product_id", type="relationship", references="Product.id"),
                    EntityField(name="supplier_id", type="relationship", references="Supplier.id"),
                    EntityField(name="quantity", type="integer")
                ]
            ),
            "WarehouseLocation": EntityDefinition(
                entity_id="ent_warehouselocation", entity_name="WarehouseLocation", name="WarehouseLocation",
                description="Inventory stocking bins.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="aisle", type="string"),
                    EntityField(name="bin_code", type="string")
                ]
            ),
            "Listing": EntityDefinition(
                entity_id="ent_listing", entity_name="Listing", name="Listing",
                description="Marketplace vendor listing.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="title", type="string"),
                    EntityField(name="price", type="float")
                ]
            ),
            "Store": EntityDefinition(
                entity_id="ent_store", entity_name="Store", name="Store",
                description="Marketplace seller store registration.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="store_name", type="string")
                ]
            ),
            "Transaction": EntityDefinition(
                entity_id="ent_transaction", entity_name="Transaction", name="Transaction",
                description="Marketplace billing transaction.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="amount", type="float")
                ]
            ),
            "OrderItem": EntityDefinition(
                entity_id="ent_orderitem", entity_name="OrderItem", name="OrderItem",
                description="Marketplace list items.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="listing_id", type="relationship", references="Listing.id"),
                    EntityField(name="quantity", type="integer")
                ]
            ),
            "Account": EntityDefinition(
                entity_id="ent_account", entity_name="Account", name="Account",
                description="Bank account metrics ledger.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="balance", type="float"),
                    EntityField(name="account_type", type="string")
                ]
            ),
            "Card": EntityDefinition(
                entity_id="ent_card", entity_name="Card", name="Card",
                description="Bank account credit/debit card details.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="account_id", type="relationship", references="Account.id"),
                    EntityField(name="card_number", type="string")
                ]
            ),
            "LoanApplication": EntityDefinition(
                entity_id="ent_loanapplication", entity_name="LoanApplication", name="LoanApplication",
                description="Bank credit loan requests.", source="industry_pattern", confidence=1.0,
                fields=[
                    EntityField(name="id", type="string", is_key=True),
                    EntityField(name="amount", type="float"),
                    EntityField(name="status", type="string")
                ]
            )
        }

        # If report has entities, generate using those
        if report and report.entities:
            for ent_name in report.entities:
                if ent_name in all_predefined_entities:
                    entities_map[ent_name] = all_predefined_entities[ent_name]
                else:
                    # Generate a custom entity definition
                    entities_map[ent_name] = EntityDefinition(
                        entity_id=f"ent_{CanonicalNamingEngine.to_snake_case(ent_name)}",
                        entity_name=ent_name,
                        name=ent_name,
                        description=f"Logical system entity representing {ent_name}.",
                        source="user_requirement",
                        confidence=1.0,
                        fields=[
                            EntityField(name="id", type="string", is_key=True),
                            EntityField(name="name", type="string")
                        ]
                    )
        else:
            # Fallback to category-based discovery
            if "gym" in category:
                for k in ["Member", "Trainer", "ClassSchedule", "ClassBooking"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "crm" in category:
                for k in ["Customer", "Lead", "InteractionLog"]:
                    entities_map[k] = all_predefined_entities[k]
            elif ("hospital" in category and "hospitality" not in category) or "medical" in category or "healthcare" in category:
                for k in ["Patient", "Doctor", "Appointment", "MedicalRecord", "Prescription"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "school" in category or "education" in category or "student" in category:
                for k in ["Student", "Teacher", "Course", "Enrollment", "Grade"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "inventory" in category or "stock" in category or "warehouse" in category:
                for k in ["Product", "Supplier", "StockOrder", "WarehouseLocation"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "restaurant" in category or "food" in category:
                for k in ["Menu", "MenuItem", "Order", "Reservation", "Payment"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "ecommerce" in category or "e-commerce" in category or "shop" in category:
                for k in ["Product", "Cart", "Order", "Payment", "Inventory"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "hotel" in category or "booking" in category or "hospitality" in category:
                for k in ["Room", "Booking", "Guest", "Payment"]:
                    entities_map[k] = all_predefined_entities[k]
            elif "banking" in category or "financial" in category:
                for k in ["Account", "Card", "LoanApplication"]:
                    entities_map[k] = all_predefined_entities[k]
            else:
                entities_map["User"] = EntityDefinition(
                    entity_id="ent_user",
                    entity_name="User",
                    name="User",
                    description="Logical standard app user profile.",
                    source="default_policy",
                    confidence=1.0,
                    fields=[
                        EntityField(name="id", type="string", is_key=True),
                        EntityField(name="username", type="string"),
                        EntityField(name="email", type="string")
                    ]
                )

        # Merge any custom entities suggested in blueprint features/innovations
        for feature in blueprint.features:
            entity_name = CanonicalNamingEngine.to_pascal_case(feature.name)
            if entity_name not in entities_map and len(entity_name) > 3:
                entities_map[entity_name] = EntityDefinition(
                    entity_id=f"ent_{CanonicalNamingEngine.to_snake_case(entity_name)}",
                    entity_name=entity_name,
                    name=entity_name,
                    description=feature.description,
                    source="user_requirement",
                    confidence=feature.explanation.recommendation_confidence if hasattr(feature, "explanation") and hasattr(feature.explanation, "recommendation_confidence") else 1.0,
                    fields=[
                        EntityField(name="id", type="string", is_key=True),
                        EntityField(name="name", type="string")
                    ],
                    constraints=[]
                )

        return list(entities_map.values())


class RelationshipDiscoveryEngine:
    @staticmethod
    def discover_relationships(entities: List[EntityDefinition]) -> List[RelationshipDefinition]:
        """Discovers entity relationships by analyzing EntityField reference attributes."""
        relationships: List[RelationshipDefinition] = []
        entity_names = {e.name for e in entities}

        for ent in entities:
            for field in ent.fields:
                if field.type == "relationship" and field.references:
                    target = field.references.split(".")[0]
                    if target in entity_names:
                        rel_id = f"rel_{ent.name.lower()}_{target.lower()}"
                        relationships.append(RelationshipDefinition(
                            relationship_id=rel_id,
                            source_entity=ent.name,
                            target_entity=target,
                            relationship_type="many-to-one",
                            description=f"Links {ent.name} to its parent {target} record."
                        ))
        return relationships


class WorkflowDesigner:
    @staticmethod
    def design_workflows(blueprint: ApprovedBlueprint, report: Optional[Any] = None) -> List[WorkflowDefinition]:
        """Converts blueprint workflows into logical designs, tracking their actor and entity dependencies."""
        workflows: List[WorkflowDefinition] = []
        
        target_workflows = []
        if report and report.workflows:
            bp_wf_map = {w.name.lower(): w for w in blueprint.workflows}
            for wf_name in report.workflows:
                wf_key = wf_name.lower()
                if wf_key in bp_wf_map:
                    target_workflows.append(bp_wf_map[wf_key])
                else:
                    from stages.stage3_recommend import RecommendedWorkflow
                    steps = [f"Start {wf_name}", "Process", "Complete"]
                    actor = "User"
                    
                    # Try to find a matching feature from the blueprint to extract the correct actor
                    matching_feature = None
                    wf_clean = wf_name.lower().replace(" ", "").replace("_", "").replace("-", "")
                    for feat in blueprint.features:
                        feat_clean = feat.name.lower().replace(" ", "").replace("_", "").replace("-", "")
                        if feat_clean in wf_clean or wf_clean in feat_clean:
                            matching_feature = feat
                            break
                    
                    if matching_feature:
                        actor = matching_feature.actor_involved
                    
                    if "order" in wf_key:
                        steps = ["Browse Menu", "Select Items", "Add to Cart", "Submit Order"]
                        if not matching_feature:
                            if "Customer" in [a.name for a in blueprint.actors]:
                                actor = "Customer"
                            elif "Buyer" in [a.name for a in blueprint.actors]:
                                actor = "Buyer"
                            elif "Guest" in [a.name for a in blueprint.actors]:
                                actor = "Guest"
                            else:
                                actor = "User"
                    elif "checkout" in wf_key or "pay" in wf_key:
                        steps = ["Initiate Payment", "Select Payment Method", "Process Transaction", "Confirm Payment"]
                        if not matching_feature:
                            if "Customer" in [a.name for a in blueprint.actors]:
                                actor = "Customer"
                            elif "Buyer" in [a.name for a in blueprint.actors]:
                                actor = "Buyer"
                            elif "Guest" in [a.name for a in blueprint.actors]:
                                actor = "Guest"
                            else:
                                actor = "User"
                    elif "appointment" in wf_key:
                        steps = ["Select Date and Time", "Check Doctor Availability", "Confirm Appointment"]
                        if not matching_feature:
                            actor = "Patient" if "Patient" in [a.name for a in blueprint.actors] else "User"
                    elif "prescription" in wf_key or "consultation" in wf_key:
                        steps = ["Select Patient", "Diagnose Patient", "Write Prescription", "Save Prescription"]
                        if not matching_feature:
                            actor = "Doctor" if "Doctor" in [a.name for a in blueprint.actors] else "User"
                    elif "room" in wf_key or "booking" in wf_key:
                        steps = ["Search Rooms", "Select Room", "Enter Guest Details", "Confirm Booking"]
                        if not matching_feature:
                            actor = "Guest" if "Guest" in [a.name for a in blueprint.actors] else "User"
                    
                    target_workflows.append(RecommendedWorkflow(
                        name=CanonicalNamingEngine.to_pascal_case(wf_name),
                        description=f"Standard sequence for {wf_name}.",
                        steps=steps,
                        actor_involved=actor,
                        why_needed=f"Enables the {wf_name} capability."
                    ))
        else:
            target_workflows = blueprint.workflows

        for wf in target_workflows:
            deps = []
            workflow_deps = []
            name_lower = wf.name.lower()
            
            if "booking" in name_lower or "class" in name_lower:
                deps = ["ClassBooking", "ClassSchedule", "Member"]
            elif "purchase" in name_lower or "membership" in name_lower:
                deps = ["Member"]
            elif "lead" in name_lower:
                deps = ["Lead", "Customer"]
            elif "appointment" in name_lower:
                deps = ["Appointment", "Doctor", "Patient"]
            elif "consultation" in name_lower or "diagnos" in name_lower:
                deps = ["MedicalRecord", "Patient"]
            elif "enroll" in name_lower:
                deps = ["Enrollment", "Course", "Student"]
            elif "grade" in name_lower or "grading" in name_lower:
                deps = ["Enrollment", "Student"]
            elif "receive" in name_lower or "stock" in name_lower:
                deps = ["StockOrder", "Product"]
            elif "order" in name_lower:
                if report and "restaurant" in report.detected_domain.lower():
                    deps = ["Order", "MenuItem", "Menu"]
                else:
                    deps = ["Order", "Product", "Cart"]
            elif "checkout" in name_lower:
                deps = ["Payment", "Order"]

            # Map workflow dependencies to check validation cycles
            if "consultation" in name_lower:
                workflow_deps = ["appointmentschedulingflow"]
            elif "grading" in name_lower:
                workflow_deps = ["courseenrollmentflow"]

            # Determine Criticality
            criticality: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"
            if any(k in name_lower for k in ["booking", "purchase", "scheduling", "enroll", "receive", "fulfill", "conversion", "order", "checkout"]):
                criticality = "HIGH"
            elif "update" in name_lower or "view" in name_lower or "profile" in name_lower:
                criticality = "LOW"

            workflows.append(WorkflowDefinition(
                workflow_id=wf.name.lower(),
                workflow_name=wf.name,
                description=wf.description,
                workflow_steps=wf.steps,
                actors=[wf.actor_involved],
                dependencies=deps,
                workflow_dependencies=workflow_deps,
                criticality=criticality
            ))
        return workflows


class PermissionDesigner:
    @staticmethod
    def design_permissions(blueprint: ApprovedBlueprint, report: Optional[Any] = None) -> List[PermissionDefinition]:
        """Maps logical permissions matrices for approved actors and profiles."""
        permissions: List[PermissionDefinition] = []
        
        target_actors = []
        if report and report.actors:
            bp_act_map = {a.name.lower(): a for a in blueprint.actors}
            for act_name in report.actors:
                act_key = act_name.lower()
                if act_key in bp_act_map:
                    target_actors.append(bp_act_map[act_key])
                else:
                    from stages.stage3_recommend import RecommendedActor
                    target_actors.append(RecommendedActor(
                        name=act_name,
                        description=f"Logical actor profile for {act_name}.",
                        relevance_score=1.0,
                        why_needed=f"Enables access control for {act_name}."
                    ))
        else:
            target_actors = blueprint.actors

        for actor in target_actors:
            perms = []
            reason = ""
            name = actor.name
            if name == "Admin":
                perms = ["ManageAllRecords", "ViewAnalyticsDashboard"]
                reason = "Full database administrative configuration rights."
            elif name == "GymMember":
                perms = ["BookClasses", "CancelBookings", "ReadOwnProfile"]
                reason = "Standard member customer transaction rights."
            elif name == "GymTrainer":
                perms = ["ManageSchedules", "ViewAssignedMembers"]
                reason = "Assigned class management permissions."
            elif name == "SalesAgent":
                perms = ["ManageLeads", "LogInteractions", "ReadOwnProfile"]
                reason = "Sales representative lead management access."
            elif name == "Doctor":
                perms = ["CreateDiagnosis", "ReadMedicalRecords", "ManageAppointments"]
                reason = "Doctor medical access rights."
            elif name == "Patient":
                perms = ["ReadOwnProfile", "ScheduleAppointments"]
                reason = "Patient scheduling and medical overview access."
            elif name == "Teacher":
                perms = ["GradeStudents", "ManageCourses"]
                reason = "Teacher classroom access rights."
            elif name == "Student":
                perms = ["EnrollCourses", "ReadOwnGrades"]
                reason = "Student enrollment access."
            elif name == "WarehouseStaff":
                perms = ["UpdateInventory", "ReadInventory"]
                reason = "Staff stocking logs permissions."
            elif name == "Customer":
                perms = ["BrowseMenu", "PlaceOrder", "Checkout", "ReadOwnProfile"]
                reason = "Customer ordering and checkout rights."
            elif name == "RestaurantOwner":
                perms = ["ManageMenu", "ViewOrders", "ManageRestaurant"]
                reason = "Restaurant owner administrative access."
            elif name == "Buyer":
                perms = ["BrowseProducts", "AddToCart", "Checkout", "ReadOwnProfile"]
                reason = "Buyer marketplace browsing and purchasing rights."
            elif name == "Seller":
                perms = ["ManageProducts", "ViewOrders", "FulfillOrders"]
                reason = "Seller marketplace merchant access."
            elif name == "Guest":
                perms = ["SearchRooms", "BookRoom", "CheckoutRoom", "ReadOwnProfile"]
                reason = "Hotel guest booking access."
            elif name == "HotelManager":
                perms = ["ManageRooms", "ViewBookings", "ManageHotel"]
                reason = "Hotel manager administrative access."
            else:
                perms = ["AccessPortal", "ReadOwnProfile"]
                reason = "Baseline access privileges."

            permissions.append(PermissionDefinition(
                role=name,
                permissions=perms,
                reason=reason
            ))
        return permissions


class BusinessRuleCompiler:
    @staticmethod
    def compile_rules(blueprint: ApprovedBlueprint, report: Optional[Any] = None) -> List[BusinessRuleDefinition]:
        """Compiles rule assertions from intent rules, constraints, and innovations."""
        rules: List[BusinessRuleDefinition] = []
        category = blueprint.app_type.lower()
        domain = report.detected_domain.lower() if (report and report.detected_domain) else category
        
        if "gym" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Members are capped at a maximum of 3 active bookings per day.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["ClassBooking", "Member"],
                description="Members are capped at a maximum of 3 active bookings per day.",
                enforcement_logic="Count(ClassBooking WHERE member_id = Member.id AND date = today) <= 3"
            ))
            rules.append(BusinessRuleDefinition(
                rule_id="BR_002",
                rule="Cancellations are forbidden within 2 hours of class start.",
                source="approved_blueprint",
                priority="MEDIUM",
                affected_entities=["ClassBooking", "ClassSchedule"],
                description="Cancellations are forbidden within 2 hours of class start.",
                enforcement_logic="ClassSchedule.start_time - now() >= 2_hours"
            ))
        elif "crm" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Deals must specify a lead and a valid target customer contact.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Lead", "Customer"],
                description="Deals must specify a lead and a valid target customer contact.",
                enforcement_logic="Lead.customer_id IS NOT NULL"
            ))
        elif ("hospital" in domain and "hospitality" not in domain) or "healthcare" in domain or "medical" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Appointments cannot overlap for the same doctor.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Appointment", "Doctor"],
                description="Appointments cannot overlap for the same doctor.",
                enforcement_logic="Count(Appointment WHERE doctor_id = Doctor.id AND overlap_time) == 0"
            ))
            rules.append(BusinessRuleDefinition(
                rule_id="BR_002",
                rule="Prescriptions require an associated patient and diagnosis.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Prescription", "Patient", "MedicalRecord"],
                description="Prescriptions require an associated patient and diagnosis.",
                enforcement_logic="Prescription.patient_id IS NOT NULL AND MedicalRecord.diagnosis IS NOT NULL"
            ))
        elif "school" in domain or "education" in domain or "student" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Students must be active to enroll in courses.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Student", "Enrollment"],
                description="Students must be active to enroll in courses.",
                enforcement_logic="Student.status == 'active'"
            ))
        elif "inventory" in domain or "stock" in domain or "warehouse" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Stock quantity cannot drop below zero.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Product"],
                description="Stock quantity cannot drop below zero.",
                enforcement_logic="Product.stock_quantity >= 0"
            ))
        elif "restaurant" in domain or "food" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Reservation requires available table.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Reservation"],
                description="Reservation requires available table.",
                enforcement_logic="Reservation.available_table_count > 0"
            ))
            rules.append(BusinessRuleDefinition(
                rule_id="BR_002",
                rule="Paid order required before fulfillment.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Payment", "Order"],
                description="Paid order required before fulfillment.",
                enforcement_logic="Payment.status == 'paid' BEFORE Order.status == 'fulfilled'"
            ))
            rules.append(BusinessRuleDefinition(
                rule_id="BR_003",
                rule="Refund requires manager approval.",
                source="approved_blueprint",
                priority="MEDIUM",
                affected_entities=["Payment", "Order"],
                description="Refund requires manager approval.",
                enforcement_logic="Refund.status == 'approved_by_manager' BEFORE Payment.status == 'refunded'"
            ))
        elif "ecommerce" in domain or "marketplace" in domain or "e-commerce" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Orders must specify a buyer and a valid product checkout item.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Order", "Product"],
                description="Orders must specify a buyer and a valid product checkout item.",
                enforcement_logic="Order.customer_id IS NOT NULL AND Count(Product) >= 1"
            ))
            rules.append(BusinessRuleDefinition(
                rule_id="BR_002",
                rule="Product stock quantity cannot drop below zero.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Product"],
                description="Product stock quantity cannot drop below zero.",
                enforcement_logic="Product.stock_quantity >= 0"
            ))
        elif "hotel" in domain or "booking" in domain:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="Booking check-in date must be in the future.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Booking"],
                description="Booking check-in date must be in the future.",
                enforcement_logic="Booking.check_in_date > now()"
            ))
            rules.append(BusinessRuleDefinition(
                rule_id="BR_002",
                rule="Rooms cannot have overlapping booking reservations.",
                source="approved_blueprint",
                priority="HIGH",
                affected_entities=["Booking", "Room"],
                description="Rooms cannot have overlapping booking reservations.",
                enforcement_logic="Count(Booking WHERE room_id = Room.id AND overlap_time) == 0"
            ))
        else:
            rules.append(BusinessRuleDefinition(
                rule_id="BR_001",
                rule="All operations must comply with baseline security policies.",
                source="default_policy",
                priority="LOW",
                affected_entities=["User"],
                description="All operations must comply with baseline security policies.",
                enforcement_logic="User.id IS NOT NULL"
            ))
        return rules


class DesignDecisionEngine:
    @staticmethod
    def track_decisions(blueprint: ApprovedBlueprint, report: Optional[Any] = None) -> List[DesignDecision]:
        """Tracks the explicit logical justifications for key architectural structures."""
        decisions: List[DesignDecision] = []
        category = blueprint.app_type.lower()
        domain = report.detected_domain.lower() if (report and report.detected_domain) else category

        if "gym" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="ClassBooking connects Member and ClassSchedule.",
                reason="Prevents duplicate direct schedules booking and enables clear auditing logs.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Member", "ClassSchedule", "ClassBooking"]
            ))
            decisions.append(DesignDecision(
                decision_id="DD_002",
                decision="Trainer owns ClassSchedule updates.",
                reason="Required to delegate workload from administrative staff directly to class instructors.",
                source="approved_blueprint",
                impact_level="MEDIUM",
                affected_components=["Trainer", "ClassSchedule"]
            ))
        elif "crm" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="Lead maps to Customer profile.",
                reason="Enables lead tracking without cluttering base customer directories.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Lead", "Customer"]
            ))
        elif ("hospital" in domain and "hospitality" not in domain) or "healthcare" in domain or "medical" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="Doctor manages MedicalRecord updates.",
                reason="HIPAA compliance and clinical accountability require certified practitioners to write records.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Doctor", "MedicalRecord"]
            ))
        elif "school" in domain or "education" in domain or "student" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="Enrollment acts as join table between Student and Course.",
                reason="Supports many-to-many relationship mapping and tracks grades.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Student", "Course", "Enrollment"]
            ))
        elif "inventory" in domain or "stock" in domain or "warehouse" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="StockOrder links Product and Supplier.",
                reason="Auditing requirements dictate tracking all incoming supply runs.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Product", "Supplier", "StockOrder"]
            ))
        elif "restaurant" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="MenuItem is linked to Menu.",
                reason="Enables structured categorization of menu offerings.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["MenuItem", "Menu"]
            ))
        elif "ecommerce" in domain or "marketplace" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="Inventory updates are tied directly to Order fulfillment.",
                reason="Ensures real-time stock levels are accurate across customer orders.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Inventory", "Order"]
            ))
        elif "hotel" in domain:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="Booking links Guest and Room.",
                reason="Required to manage room availability and guest registrations.",
                source="approved_blueprint",
                impact_level="HIGH",
                affected_components=["Booking", "Guest", "Room"]
            ))
        else:
            decisions.append(DesignDecision(
                decision_id="DD_001",
                decision="Generic User model is base actor profile.",
                reason="Standard fallback setup.",
                source="default_policy",
                impact_level="LOW",
                affected_components=["User"]
            ))
        return decisions


class GraphBuilder:
    @staticmethod
    def build_system_graph(actors: List[Actor], entities: List[Union[EntityDefinition, Entity]], relationships: List[RelationshipDefinition], workflows: List[WorkflowDefinition]) -> SystemDesignGraph:
        """Constructs a system design graph, building node and edge lists manually."""
        nodes_list = []
        edges_list = []
        added_nodes = set()

        for actor in actors:
            if actor.name not in added_nodes:
                nodes_list.append({"id": actor.name, "type": "actor", "description": actor.description})
                added_nodes.add(actor.name)

        for ent in entities:
            if ent.name not in added_nodes:
                nodes_list.append({"id": ent.name, "type": "entity", "description": ent.description})
                added_nodes.add(ent.name)

        for wf in workflows:
            if wf.workflow_name not in added_nodes:
                nodes_list.append({"id": wf.workflow_name, "type": "workflow", "description": wf.description})
                added_nodes.add(wf.workflow_name)

        for rel in relationships:
            if rel.source_entity in added_nodes and rel.target_entity in added_nodes:
                edges_list.append({
                    "source": rel.source_entity,
                    "target": rel.target_entity,
                    "type": "relationship",
                    "label": rel.relationship_type
                })

        for wf in workflows:
            for dep in wf.dependencies:
                if dep in added_nodes:
                    edges_list.append({
                        "source": wf.workflow_name,
                        "target": dep,
                        "type": "dependency",
                        "label": "uses"
                    })

            for act in wf.actors:
                if act in added_nodes:
                    edges_list.append({
                        "source": act,
                        "target": wf.workflow_name,
                        "type": "execution",
                        "label": "triggers"
                    })

        return SystemDesignGraph(nodes=nodes_list, edges=edges_list)


# --- ORCHESTRATOR & VALIDATOR ---

class MasterSpecificationBuilder:
    @staticmethod
    def compile_specification(blueprint: ApprovedBlueprint, report: Optional[Any] = None) -> MasterSpecification:
        """Orchestrates all logical engines to build the final MasterSpecification AST."""
        app_name = CanonicalNamingEngine.to_pascal_case(blueprint.project_id)
        
        target_actors = []
        if report and report.actors:
            bp_act_map = {a.name.lower(): a for a in blueprint.actors}
            for act_name in report.actors:
                act_key = act_name.lower()
                if act_key in bp_act_map:
                    target_actors.append(bp_act_map[act_key])
                else:
                    from stages.stage3_recommend import RecommendedActor
                    target_actors.append(RecommendedActor(
                        name=act_name,
                        description=f"Logical actor profile for {act_name}.",
                        relevance_score=1.0,
                        why_needed=f"Enables access control for {act_name}."
                    ))
        else:
            target_actors = blueprint.actors

        actors_list = []
        for a in target_actors:
            perms = []
            if a.name == "Admin":
                perms = ["ManageAllRecords"]
            elif a.name == "GymMember":
                perms = ["BookClasses"]
            elif a.name == "Doctor":
                perms = ["CreateDiagnosis"]
            elif a.name == "Teacher":
                perms = ["GradeStudents"]
            elif a.name == "WarehouseStaff":
                perms = ["UpdateInventory"]
            elif a.name == "Customer":
                perms = ["BrowseMenu", "PlaceOrder", "Checkout"]
            elif a.name == "Buyer":
                perms = ["BrowseProducts", "AddToCart", "Checkout"]
            elif a.name == "Seller":
                perms = ["ManageProducts", "ViewOrders"]
            elif a.name == "Guest":
                perms = ["SearchRooms", "BookRoom"]
            elif a.name == "HotelManager":
                perms = ["ManageRooms", "ViewBookings"]
                
            actors_list.append(Actor(
                name=a.name,
                description=a.description,
                permissions=perms
            ))

        entities = EntityDiscoveryEngine.discover_entities(blueprint, report)
        relationships = RelationshipDiscoveryEngine.discover_relationships(entities)
        workflows = WorkflowDesigner.design_workflows(blueprint, report)
        permissions = PermissionDesigner.design_permissions(blueprint, report)
        rules = BusinessRuleCompiler.compile_rules(blueprint, report)
        decisions = DesignDecisionEngine.track_decisions(blueprint, report)

        entities.sort(key=lambda x: x.name)
        relationships.sort(key=lambda x: x.relationship_id)
        workflows.sort(key=lambda x: x.workflow_id)
        permissions.sort(key=lambda x: x.role)
        rules.sort(key=lambda x: x.rule_id)
        decisions.sort(key=lambda x: x.decision_id)

        graph = GraphBuilder.build_system_graph(actors_list, entities, relationships, workflows)

        return MasterSpecification(
            app_name=app_name,
            app_type=blueprint.app_type,
            actors=actors_list,
            entities=entities,
            relationships=relationships,
            workflows=workflows,
            permissions=permissions,
            business_rules=rules,
            design_decisions=decisions,
            graph=graph,
            metadata={
                "compiled_at": datetime.now().isoformat(),
                "blueprint_project_id": blueprint.project_id
            }
        )

    @staticmethod
    def validate_specification(spec: MasterSpecification) -> MasterSpecificationValidationReport:
        """Performs multi-layered logical design validation checks on the compiled specification."""
        issues: List[ValidationIssue] = []
        
        actor_names = {a.name for a in spec.actors}
        entity_names = {e.name for e in spec.entities}
        workflow_names = {w.workflow_name for w in spec.workflows}

        # 1. VAL_WF_ACTOR
        for wf in spec.workflows:
            for actor in wf.actors:
                if actor not in actor_names:
                    issues.append(ValidationIssue(
                        rule_id="VAL_WF_ACTOR",
                        category="workflows",
                        message=f"Workflow '{wf.workflow_name}' references non-existent actor '{actor}'.",
                        severity="CRITICAL"
                    ))

        # 2. VAL_WF_ENTITY
        for wf in spec.workflows:
            for dep in wf.dependencies:
                if dep not in entity_names:
                    issues.append(ValidationIssue(
                        rule_id="VAL_WF_ENTITY",
                        category="workflows",
                        message=f"Workflow '{wf.workflow_name}' has dependency on non-existent entity '{dep}'.",
                        severity="CRITICAL"
                    ))

        # 3. VAL_REL_SOURCE / VAL_REL_TARGET
        for rel in spec.relationships:
            if rel.source_entity not in entity_names:
                issues.append(ValidationIssue(
                    rule_id="VAL_REL_SOURCE",
                    category="relationships",
                    message=f"Relationship '{rel.relationship_id}' specifies non-existent source entity '{rel.source_entity}'.",
                    severity="CRITICAL"
                ))
            if rel.target_entity not in entity_names:
                issues.append(ValidationIssue(
                    rule_id="VAL_REL_TARGET",
                    category="relationships",
                    message=f"Relationship '{rel.relationship_id}' specifies non-existent target entity '{rel.target_entity}'.",
                    severity="CRITICAL"
                ))

        # 4. VAL_PERM_ROLE
        for perm in spec.permissions:
            if perm.role not in actor_names:
                issues.append(ValidationIssue(
                    rule_id="VAL_PERM_ROLE",
                    category="permissions",
                    message=f"Permission profile references non-existent role '{perm.role}'.",
                    severity="CRITICAL"
                ))

        # 5. VAL_RULE_ENTITY
        for rule in spec.business_rules:
            for aff in rule.affected_entities:
                if aff not in entity_names:
                    issues.append(ValidationIssue(
                        rule_id="VAL_RULE_ENTITY",
                        category="business_rules",
                        message=f"Business rule '{rule.rule_id}' affects non-existent entity '{aff}'.",
                        severity="CRITICAL"
                    ))

        # 6. VAL_DD_SOURCE
        valid_sources = {
            "approved_blueprint", "default_policy", "user_requirement", 
            "community_innovation", "industry_pattern", "logical_inference"
        }
        for dd in spec.design_decisions:
            if dd.source not in valid_sources:
                issues.append(ValidationIssue(
                    rule_id="VAL_DD_SOURCE",
                    category="design_decisions",
                    message=f"Design decision '{dd.decision_id}' specifies invalid source '{dd.source}'.",
                    severity="WARNING"
                ))

        # 7. VAL_DUP_ENTITY
        seen_entities = set()
        for ent in spec.entities:
            ent_name = ent.name
            if ent_name in seen_entities:
                issues.append(ValidationIssue(
                    rule_id="VAL_DUP_ENTITY",
                    category="entities",
                    message=f"Duplicate entity name '{ent_name}' detected.",
                    severity="CRITICAL"
                ))
            seen_entities.add(ent_name)

        # 8. VAL_WF_CYCLE
        visited = {}  # None: unvisited, 0: visiting, 1: visited
        adj = {}
        for wf in spec.workflows:
            normalized_name = wf.workflow_name.lower().replace(" ", "")
            deps = [d.lower().replace(" ", "") for d in getattr(wf, "workflow_dependencies", [])]
            adj[normalized_name] = deps

        def has_cycle(node):
            visited[node] = 0
            for neighbor in adj.get(node, []):
                # Ensure neighbor exists in our adj keys before traversing
                if neighbor in adj:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif visited[neighbor] == 0:
                        return True
            visited[node] = 1
            return False

        for wf in spec.workflows:
            norm_name = wf.workflow_name.lower().replace(" ", "")
            if norm_name not in visited:
                if has_cycle(norm_name):
                    issues.append(ValidationIssue(
                        rule_id="VAL_WF_CYCLE",
                        category="workflows",
                        message=f"Circular workflow dependency detected starting at '{wf.workflow_name}'.",
                        severity="CRITICAL"
                    ))
                    break

        # 9. VAL_PERM_CONFLICT (Privilege Conflict / Escalation Protection)
        for perm in spec.permissions:
            if perm.role != "Admin":
                for action in perm.permissions:
                    if any(kw in action for kw in ["ManageAll", "DeleteDatabase", "OverrideAll"]):
                        issues.append(ValidationIssue(
                            rule_id="VAL_PERM_CONFLICT",
                            category="permissions",
                            message=f"Privilege conflict: non-admin role '{perm.role}' has administrative action '{action}'.",
                            severity="CRITICAL"
                        ))

        # 10. VAL_MISSING_RULE
        critical_keywords = ["booking", "payment", "order", "appointment", "record", "enrollment"]
        rule_affected_entities = set()
        for rule in spec.business_rules:
            for aff in rule.affected_entities:
                rule_affected_entities.add(aff.lower())
                
        for ent in spec.entities:
            ent_name_lower = ent.name.lower()
            if any(keyword in ent_name_lower for keyword in critical_keywords):
                if ent_name_lower not in rule_affected_entities:
                    issues.append(ValidationIssue(
                        rule_id="VAL_MISSING_RULE",
                        category="business_rules",
                        message=f"Warning: Transactional/Critical entity '{ent.name}' has no associated business rules.",
                        severity="WARNING"
                    ))

        is_valid = len([i for i in issues if i.severity == "CRITICAL"]) == 0

        return MasterSpecificationValidationReport(
            is_valid=is_valid,
            issues=issues,
            checked_rules_count=10
        )
