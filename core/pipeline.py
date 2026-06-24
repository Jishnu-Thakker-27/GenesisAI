import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel

from core.contracts import PipelineTrace, FinalCompiledApplication
from stages.stage2_intent import IntentExtractionEngine, IntentExtractionResult
from stages.stage3_recommend import BlueprintRecommendationEngine, ApprovedBlueprint, RecommendedActor, RecommendedFeature, RecommendedWorkflow, RecommendedPermission, RecommendedInnovation
from stages.stage4_system import MasterSpecificationBuilder, MasterSpecification
from stages.stage5_schema import CompiledSchemaBundleBuilder, CompiledSchemaBundle
from stages.stage6_validate import ValidationEngine, ValidationReport
from stages.stage7_repair import RepairEngine, RepairReport
from stages.stage8_execution import ExecutionSimulator, ExecutionSimulationReport
from stages.stage9_change import RequirementChangeEngine, RequirementChangeReport, RequirementChangeRequest
from stages.stage10_requirements_intelligence import RequirementsIntelligenceEngine, AIArchitectReport, IntelligenceMode
from core.naming import CanonicalNamingEngine

class GenesisPipeline:
    def __init__(self, execution_mode: str = "BALANCED", intelligence_mode: IntelligenceMode = "HYBRID"):
        self.execution_mode = execution_mode
        self.intelligence_mode = intelligence_mode
        self.prompt: Optional[str] = None
        self.intent: Optional[IntentExtractionResult] = None
        self.ai_architect_report: Optional[AIArchitectReport] = None
        self.blueprint: Optional[ApprovedBlueprint] = None
        self.system_design: Optional[MasterSpecification] = None
        self.schema_bundle: Optional[CompiledSchemaBundle] = None
        self.validation_report: Optional[ValidationReport] = None
        self.repair_report: Optional[RepairReport] = None
        self.simulation_report: Optional[ExecutionSimulationReport] = None
        self.evolution_summary: Optional[RequirementChangeReport] = None
        self.traces: List[PipelineTrace] = []
        self.start_time: float = 0.0
        self.execution_time: float = 0.0

    def run_pipeline(
        self,
        prompt: str,
        execution_mode: Optional[str] = None,
        intelligence_mode: Optional[IntelligenceMode] = None
    ) -> FinalCompiledApplication:
        if execution_mode:
            self.execution_mode = execution_mode
        if intelligence_mode:
            self.intelligence_mode = intelligence_mode
        self.prompt = prompt
        self.traces = []
        self.start_time = time.time()
        
        # 1. Run intent extraction
        self.run_intent_phase()

        # 2. Run requirements intelligence before blueprint recommendation
        self.run_requirements_intelligence_phase()
        
        # 3. Run blueprint recommendation
        self.run_blueprint_phase()
        
        # 4. Run system design specification
        self.run_system_design_phase()

        # 5. Enrich AI architect report with the concrete architecture trace
        self.enrich_architecture_reasoning_trace()
        
        # 6. Run schema compilation
        self.run_schema_phase()
        
        # 7. Run validation phase
        self.run_validation_phase()
        
        # 8. Run repair phase
        self.run_repair_phase()
        
        # 9. Run simulation phase
        self.run_simulation_phase()
        
        # 10. Run evolution phase
        self.run_evolution_phase()
        
        self.execution_time = time.time() - self.start_time
        
        # Combine all phase outputs into FinalCompiledApplication
        now = datetime.now().isoformat()
        app = FinalCompiledApplication(
            project_id=self.blueprint.project_id if self.blueprint else f"proj_{int(time.time())}",
            app_name=self.intent.app_name if self.intent else "GenesisApp",
            app_type=self.intent.app_type if self.intent else "Generic",
            prompt=self.prompt,
            intent=self.intent,
            ai_architect_report=self.ai_architect_report,
            blueprint=self.blueprint,
            system_design=self.system_design,
            schema_bundle=self.schema_bundle,
            validation_report=self.validation_report,
            repair_report=self.repair_report,
            simulation_report=self.simulation_report,
            evolution_summary=self.evolution_summary,
            pipeline_traces=self.traces,
            execution_mode=self.execution_mode,
            created_at=now,
            updated_at=now
        )
        return app

    def run_intent_phase(self, prompt: Optional[str] = None) -> IntentExtractionResult:
        if prompt is not None:
            self.prompt = prompt
        if not self.prompt:
            raise ValueError("Prompt is not set.")
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        try:
            engine = IntentExtractionEngine(api_key="")
            self.intent = engine.extract_intent(self.prompt)
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Intent Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.intent

    def run_requirements_intelligence_phase(self, intent: Optional[IntentExtractionResult] = None) -> AIArchitectReport:
        if intent is not None:
            self.intent = intent
        if not self.intent or not self.prompt:
            raise ValueError("Intent and prompt are required for requirements intelligence.")

        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        try:
            self.ai_architect_report = RequirementsIntelligenceEngine.analyze(
                self.prompt,
                self.intent,
                self.intelligence_mode
            )
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="AI Requirements Intelligence Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.ai_architect_report

    def enrich_architecture_reasoning_trace(self) -> Optional[AIArchitectReport]:
        if self.ai_architect_report and self.blueprint and self.system_design:
            self.ai_architect_report = RequirementsIntelligenceEngine.attach_architecture_trace(
                self.ai_architect_report,
                self.blueprint,
                self.system_design
            )
        return self.ai_architect_report

    def run_blueprint_phase(self, intent: Optional[IntentExtractionResult] = None) -> ApprovedBlueprint:
        if intent is not None:
            self.intent = intent
        if not self.intent:
            raise ValueError("Intent is not set.")
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        try:
            engine = BlueprintRecommendationEngine()
            recommendation = engine.recommend_blueprint(self.intent)
            
            project_id = f"proj_{int(time.time())}"
            self.blueprint = ApprovedBlueprint(
                project_id=project_id,
                app_type=recommendation.app_type,
                actors=recommendation.recommended_actors,
                features=recommendation.recommended_features,
                workflows=recommendation.recommended_workflows,
                permissions=recommendation.recommended_permissions,
                innovations=recommendation.recommended_innovations
            )
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Blueprint Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.blueprint

    def run_system_design_phase(self, blueprint: Optional[ApprovedBlueprint] = None) -> MasterSpecification:
        if blueprint is not None:
            self.blueprint = blueprint
        if not self.blueprint:
            raise ValueError("Blueprint is not set.")
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        try:
            self.system_design = MasterSpecificationBuilder.compile_specification(self.blueprint)
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="System Design Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.system_design

    def run_schema_phase(self, spec: Optional[MasterSpecification] = None) -> CompiledSchemaBundle:
        if spec is not None:
            self.system_design = spec
        if not self.system_design:
            raise ValueError("System design specification is not set.")
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        try:
            self.schema_bundle = CompiledSchemaBundleBuilder.compile_bundle(self.system_design)
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Schema Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.schema_bundle

    def run_validation_phase(
        self,
        bundle: Optional[CompiledSchemaBundle] = None,
        spec: Optional[MasterSpecification] = None,
        blueprint: Optional[ApprovedBlueprint] = None
    ) -> ValidationReport:
        if bundle is not None:
            self.schema_bundle = bundle
        if spec is not None:
            self.system_design = spec
        if blueprint is not None:
            self.blueprint = blueprint
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        
        if self.execution_mode == "FAST":
            self.validation_report = ValidationReport(is_valid=True, errors=[], warnings=[], execution_time=0.0)
            self.traces.append(PipelineTrace(
                phase_name="Validation Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=0.0,
                status="SKIPPED",
                errors=[],
                warnings=[]
            ))
            return self.validation_report
            
        if not self.schema_bundle or not self.system_design or not self.blueprint:
            raise ValueError("Missing dependencies for validation phase.")
            
        try:
            self.validation_report = ValidationEngine.validate(
                self.schema_bundle, self.system_design, self.blueprint
            )
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Validation Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.validation_report

    def run_repair_phase(
        self,
        bundle: Optional[CompiledSchemaBundle] = None,
        spec: Optional[MasterSpecification] = None,
        blueprint: Optional[ApprovedBlueprint] = None
    ) -> Optional[RepairReport]:
        if bundle is not None:
            self.schema_bundle = bundle
        if spec is not None:
            self.system_design = spec
        if blueprint is not None:
            self.blueprint = blueprint
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        
        if self.execution_mode == "FAST":
            self.repair_report = None
            self.traces.append(PipelineTrace(
                phase_name="Repair Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=0.0,
                status="SKIPPED",
                errors=[],
                warnings=[]
            ))
            return self.repair_report
            
        if not self.schema_bundle or not self.system_design or not self.blueprint:
            raise ValueError("Missing dependencies for repair phase.")
            
        try:
            if self.validation_report and not self.validation_report.is_valid:
                repair_rep, rep_bundle, rep_spec, metrics = RepairEngine.repair(
                    self.schema_bundle, self.system_design, self.blueprint
                )
                
                if self.execution_mode == "HIGH_QUALITY" and not repair_rep.revalidation_results.is_valid:
                    repair_rep2, rep_bundle2, rep_spec2, metrics2 = RepairEngine.repair(
                        rep_bundle, rep_spec, self.blueprint
                    )
                    repair_rep.repair_candidates_generated = repair_rep.repair_candidates_generated + repair_rep2.repair_candidates_generated
                    repair_rep.repair_actions_executed = repair_rep.repair_actions_executed + repair_rep2.repair_actions_executed
                    repair_rep.successful_repairs = repair_rep.successful_repairs + repair_rep2.successful_repairs
                    repair_rep.failed_repairs = repair_rep.failed_repairs + repair_rep2.failed_repairs
                    repair_rep.revalidation_results = repair_rep2.revalidation_results
                    rep_bundle = rep_bundle2
                    rep_spec = rep_spec2
                    
                self.repair_report = repair_rep
                self.schema_bundle = rep_bundle
                self.system_design = rep_spec
                status = "SUCCESS"
            else:
                self.repair_report = None
                status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Repair Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.repair_report

    def run_simulation_phase(
        self,
        bundle: Optional[CompiledSchemaBundle] = None,
        spec: Optional[MasterSpecification] = None,
        blueprint: Optional[ApprovedBlueprint] = None
    ) -> ExecutionSimulationReport:
        if bundle is not None:
            self.schema_bundle = bundle
        if spec is not None:
            self.system_design = spec
        if blueprint is not None:
            self.blueprint = blueprint
            
        if not self.schema_bundle or not self.system_design:
            raise ValueError("Missing dependencies for simulation phase.")
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        try:
            self.simulation_report = ExecutionSimulator.simulate(
                self.schema_bundle, self.system_design, self.blueprint
            )
            status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Execution Simulator",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.simulation_report

    def run_evolution_phase(
        self,
        blueprint: Optional[ApprovedBlueprint] = None,
        spec: Optional[MasterSpecification] = None,
        bundle: Optional[CompiledSchemaBundle] = None,
        request: Optional[RequirementChangeRequest] = None
    ) -> Optional[RequirementChangeReport]:
        if blueprint is not None:
            self.blueprint = blueprint
        if spec is not None:
            self.system_design = spec
        if bundle is not None:
            self.schema_bundle = bundle
            
        if not self.blueprint or not self.system_design or not self.schema_bundle:
            raise ValueError("Missing dependencies for evolution phase.")
            
        start_str = datetime.now().isoformat()
        t0 = time.time()
        errors = []
        
        if request is None and self.blueprint:
            app_type_lower = self.blueprint.app_type.lower()
            if "gym" in app_type_lower:
                request = RequirementChangeRequest(
                    change_id="demo_evo_gym",
                    change_type="ADD_FEATURE",
                    description="Add SubscriptionPlan feature",
                    payload={"name": "SubscriptionPlan", "description": "Subscription schemes for gym"}
                )
            elif "crm" in app_type_lower:
                request = RequirementChangeRequest(
                    change_id="demo_evo_crm",
                    change_type="ADD_FEATURE",
                    description="Add CustomerFeedback feature",
                    payload={"name": "CustomerFeedback", "description": "Customer comments and feedback"}
                )
            elif "hospital" in app_type_lower or "medical" in app_type_lower:
                request = RequirementChangeRequest(
                    change_id="demo_evo_hospital",
                    change_type="ADD_FEATURE",
                    description="Add BillingInvoice feature",
                    payload={"name": "BillingInvoice", "description": "Track billing and patient payments"}
                )
            elif "school" in app_type_lower or "education" in app_type_lower:
                request = RequirementChangeRequest(
                    change_id="demo_evo_school",
                    change_type="ADD_FEATURE",
                    description="Add AttendanceRecord feature",
                    payload={"name": "AttendanceRecord", "description": "Track student attendance logs"}
                )
            elif "inventory" in app_type_lower or "stock" in app_type_lower:
                request = RequirementChangeRequest(
                    change_id="demo_evo_inventory",
                    change_type="ADD_FEATURE",
                    description="Add StockAlert feature",
                    payload={"name": "StockAlert", "description": "Notify when stock is below threshold"}
                )
            else:
                request = RequirementChangeRequest(
                    change_id="demo_evo_generic",
                    change_type="ADD_FEATURE",
                    description="Add UserProfile feature",
                    payload={"name": "UserProfile", "description": "Extended user profile fields"}
                )
                
        try:
            if request:
                self.evolution_summary = RequirementChangeEngine.apply_change(
                    self.blueprint, self.system_design, self.schema_bundle, request
                )
                status = "SUCCESS"
            else:
                self.evolution_summary = None
                status = "SUCCESS"
        except Exception as e:
            status = "FAILED"
            errors.append(str(e))
            raise e
        finally:
            duration = (time.time() - t0) * 1000.0
            self.traces.append(PipelineTrace(
                phase_name="Requirement Evolution Engine",
                start_time=start_str,
                end_time=datetime.now().isoformat(),
                duration_ms=duration,
                status=status,
                errors=errors,
                warnings=[]
            ))
        return self.evolution_summary
