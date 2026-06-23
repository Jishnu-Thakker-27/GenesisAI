from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Any, Optional
from core.naming import CanonicalNamingEngine

# --- BASE AST COMPONENT MODELS ---

class Actor(BaseModel):
    name: str = Field(..., description="Unique name of the actor/role (e.g., Admin, Member)")
    description: str = Field(..., description="Role and responsibilities of this actor")
    permissions: List[str] = Field(default_factory=list, description="List of logical actions permitted")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class EntityField(BaseModel):
    name: str = Field(..., description="Field name in snake_case")
    type: str = Field(..., description="Data type: string, integer, float, boolean, datetime, relationship")
    required: bool = True
    is_key: bool = False
    references: Optional[str] = Field(None, description="Format: EntityName.field_name for foreign keys")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_snake_case(v)
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"string", "integer", "float", "boolean", "datetime", "relationship"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Type must be one of {allowed}, got {v}")
        return v_lower


class Entity(BaseModel):
    name: str = Field(..., description="Entity name in PascalCase")
    description: str = Field(..., description="Description of the business concept")
    fields: List[EntityField] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list, description="Logical constraints on this entity")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class APIEndpoint(BaseModel):
    path: str = Field(..., description="API Path (e.g., /bookings)")
    method: str = Field(..., description="GET, POST, PUT, DELETE")
    request_body_entity: Optional[str] = Field(None, description="PascalCase Entity name representing request body")
    response_body_entity: Optional[str] = Field(None, description="PascalCase Entity name representing response")
    roles_allowed: List[str] = Field(..., description="Actors permitted to use this route")
    description: str

    @field_validator("path", mode="before")
    @classmethod
    def clean_path(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.sanitize_endpoint_path(v)
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed = {"GET", "POST", "PUT", "DELETE"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Method must be one of {allowed}")
        return v_upper

    @field_validator("request_body_entity", "response_body_entity", mode="before")
    @classmethod
    def clean_entities(cls, v: Any) -> Optional[str]:
        if isinstance(v, str) and v:
            return CanonicalNamingEngine.to_pascal_case(v)
        return v


class UIView(BaseModel):
    name: str = Field(..., description="PascalCase name of view")
    type: str = Field(..., description="Form, Table, Dashboard, Details")
    actor: str = Field(..., description="Actor who views this screen")
    entity_source: str = Field(..., description="Primary entity rendering this UI")
    actions: List[str] = Field(default_factory=list, description="Interaction triggers (e.g., BookClass)")

    @field_validator("name", "actor", "entity_source", mode="before")
    @classmethod
    def clean_pascal_fields(cls, v: Any) -> str:
        if isinstance(v, str):
            return CanonicalNamingEngine.to_pascal_case(v)
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"Form", "Table", "Dashboard", "Details"}
        v_cap = v.capitalize()
        if v_cap not in allowed:
            raise ValueError(f"UI type must be one of {allowed}, got {v}")
        return v_cap


class BusinessRule(BaseModel):
    rule_id: str = Field(..., description="Unique rule identifier e.g., BR_001")
    description: str = Field(..., description="High level plain text rule description")
    affected_entities: List[str] = Field(default_factory=list)
    enforcement_logic: str = Field(..., description="Declarative logic or pseudocode expression")

    @field_validator("affected_entities", mode="before")
    @classmethod
    def clean_affected_entities(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [CanonicalNamingEngine.to_pascal_case(x) if isinstance(x, str) else x for x in v]
        return v


# --- MASTER SPECIFICATION AST ---

class MasterSpecification(BaseModel):
    app_name: str
    app_type: str
    actors: List[Actor] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    endpoints: List[APIEndpoint] = Field(default_factory=list)
    ui_views: List[UIView] = Field(default_factory=list)
    business_rules: List[BusinessRule] = Field(default_factory=list)


# --- VALIDATION ENGINE MODELS ---

class ValidationError(BaseModel):
    validation_type: str = Field(..., description="Category of validation (e.g., JSON, API_DB_Symmetry, Dependency)")
    target_node: str = Field(..., description="Node name or path where validation failed")
    error_message: str = Field(..., description="Diagnostics explanation")
    severity: str = Field("CRITICAL", description="Severity of the error: CRITICAL, WARNING")


class ValidationReport(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    checked_nodes_count: int = 0
    execution_time_ms: float = 0.0


# --- REPAIR ENGINE MODELS ---

class RepairInstruction(BaseModel):
    target_node: str = Field(..., description="Spec node modified (e.g., 'Entity:Booking')")
    modification_type: str = Field(..., description="ADD, MODIFY, DELETE")
    patch: Dict[str, Any] = Field(..., description="Keys/values to merge into the node")


class RepairPlan(BaseModel):
    detected_errors: List[ValidationError] = Field(default_factory=list)
    instructions: List[RepairInstruction] = Field(default_factory=list)
    rationale: str = Field(..., description="Logical explanation of why this repair solves the diagnostics")
