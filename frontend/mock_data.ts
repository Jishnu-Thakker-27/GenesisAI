// GenesisAI Frontend Mock Data
// Replicates the exact values, metrics, logs, and structures visible in the Stitch screens.

import {
  DashboardScreen,
  CompilerScreen,
  ValidationRepairScreen,
  ArchitectureMapScreen,
  ExecutionVerificationScreen,
  VersionHistoryEvolutionScreen,
  FinalCompiledApplication,
  PipelineTrace,
  ValidationError,
  RepairReport,
  ExecutionSimulationReport,
  RequirementChangeReport,
  AIArchitectReport
} from "./frontend_models";

export const mockPipelineTraces: PipelineTrace[] = [
  {
    phase_name: "Intent Extraction",
    start_time: "2026-06-23T20:00:00Z",
    end_time: "2026-06-23T20:00:01Z",
    duration_ms: 120,
    status: "SUCCESS",
    errors: [],
    warnings: []
  },
  {
    phase_name: "Blueprint Recommendation",
    start_time: "2026-06-23T20:00:01Z",
    end_time: "2026-06-23T20:00:02Z",
    duration_ms: 340,
    status: "SUCCESS",
    errors: [],
    warnings: []
  },
  {
    phase_name: "System Design",
    start_time: "2026-06-23T20:00:02Z",
    end_time: "2026-06-23T20:00:04Z",
    duration_ms: 1200,
    status: "SUCCESS",
    errors: [],
    warnings: []
  },
  {
    phase_name: "Schema Generation",
    start_time: "2026-06-23T20:00:04Z",
    end_time: "2026-06-23T20:00:05Z",
    duration_ms: 850,
    status: "SUCCESS",
    errors: [],
    warnings: []
  },
  {
    phase_name: "Validation",
    start_time: "2026-06-23T20:00:05Z",
    end_time: "2026-06-23T20:00:05Z",
    duration_ms: 15,
    status: "SUCCESS",
    errors: [],
    warnings: []
  },
  {
    phase_name: "Repair",
    start_time: "2026-06-23T20:00:05Z",
    end_time: "2026-06-23T20:00:06Z",
    duration_ms: 450,
    status: "SUCCESS",
    errors: [],
    warnings: []
  },
  {
    phase_name: "Simulation",
    start_time: "2026-06-23T20:00:06Z",
    end_time: "2026-06-23T20:00:07Z",
    duration_ms: 680,
    status: "SUCCESS",
    errors: [],
    warnings: []
  }
];

export const mockDashboardData: DashboardScreen = {
  success_rate: 98.0,
  validation_rate: 100.0,
  repair_rate: 88.0,
  simulation_rate: 97.0,
  recent_projects: [
    {
      project_id: "proj_01",
      prompt: "Gym Management System with Bookings and Payments",
      final_status: "SUCCESS",
      created_at: "2 hours ago",
      updated_at: "2 hours ago",
      engine_path: "genesisai/core-engine",
      status: "Active",
      impact: 0.992
    }
  ],
  pipeline_statistics: {
    total_projects: 1,
    successful_compilations: 1,
    failed_compilations: 0,
    validation_pass_rate: 100.0,
    repair_success_rate: 88.0,
    simulation_pass_rate: 97.0,
    average_latency: 1200.0,
    total_versions_created: 18
  }
};

export const mockCompilerData: CompilerScreen = {
  prompt: "Add tiered pricing logic and loyalty discount validators across the Booking ecosystem.",
  intent: {
    intent_extracted: "Add pricing tiers and loyalty validation",
    confidence: 0.96
  },
  blueprint: {
    recommended_features: ["TieredPricing", "LoyaltyDiscountValidator"],
    blueprint_integrity: 0.98
  },
  system_design: {
    schema_version: "2.4.0-alpha",
    entities: [
      {
        name: "Booking",
        fields: {
          id: "string",
          user_id: "string",
          price: "float",
          discount_applied: "boolean",
          status: "string"
        }
      }
    ],
    relationships: [
      {
        relationship_id: "rel_booking_user",
        source_entity: "Booking",
        target_entity: "User",
        relationship_type: "Many-to-One",
        description: "A Booking is owned by a User"
      }
    ],
    workflows: [
      {
        workflow_name: "Create Booking",
        steps: ["Initialize", "Validate Loyalty", "Apply Tier Pricing", "Save"],
        actors: ["Member", "Admin"],
        dependencies: ["User", "Booking"]
      }
    ]
  },
  schema_bundle: {
    database_schema: [
      {
        table_name: "bookings_table",
        columns: [
          { name: "id", type: "VARCHAR(255)", constraints: ["PRIMARY KEY"] },
          { name: "user_id", type: "VARCHAR(255)", constraints: ["FOREIGN KEY"] },
          { name: "price", type: "DECIMAL(10,2)", constraints: [] }
        ]
      }
    ],
    api_schema: [
      {
        endpoint_id: "api_post_bookings",
        method: "POST",
        path: "/bookings",
        source_entity: "Booking"
      }
    ],
    ui_schema: [
      {
        view_id: "ui_booking_form",
        view_name: "BookingForm",
        components: ["InputFields", "SubmitButton"]
      }
    ]
  },
  compiler_logs: [
    "[10:14:02] INFO: Parsing input evolution prompt...",
    "[10:14:03] INFO: Intent extraction complete. Confidence 0.96",
    "[10:14:04] INFO: Resolving blueprint changes. Injected 2 new features.",
    "[10:14:05] INFO: Generating master_spec.json structure...",
    "[10:14:06] INFO: Compiling schema bundle..."
  ]
};

export const mockValidationError: ValidationError[] = [
  {
    error_id: "val_err_002",
    error_code: "AUTH_CONTEXT_DRIFT",
    severity: "HIGH",
    layer: "Auth",
    component: "/api/v1/evolution",
    message: "Authorization scopes are missing required validation roles.",
    source_component: "APIEndpoint:api_post_evolution",
    repair_hint: "Inject GENESIS_ROLES validation middleware to authorization handler."
  }
];

export const mockValidationRepairData: ValidationRepairScreen = {
  validation_report: {
    is_valid: false,
    errors: mockValidationError,
    warnings: [],
    critical_count: 0,
    high_count: 1,
    medium_count: 0,
    low_count: 0,
    validated_components: [
      "JSON Schema Structural Integrity",
      "Required Fields Completeness",
      "Null Reference Safety",
      "Type Mismatch Resolution",
      "Unique ID Collision Audit",
      "Dependency Cycle Exclosure",
      "Permission Boundary Check",
      "Endpoint Accessibility Scan",
      "DB Foreign Key Verification",
      "UI Event Handlers Safety"
    ],
    timestamp: "2026-06-23T20:00:05Z"
  },
  validation_score: 98.0,
  errors: mockValidationError,
  warnings: [],
  repairs: [
    {
      repair_id: "rep_20A_2026",
      task_id: "20A-2026 / Auth Context Drift",
      confidence: 0.94,
      broken_schema: `{
  "path": "/api/v1/evolution",
  "method": "POST",
  "auth": {
    "required": true
  }
}`,
      repaired_schema: `{
  "path": "/api/v1/evolution",
  "method": "POST",
  "auth": {
    "required": true,
    "injected_roles": ["GENESIS_ROLES"]
  }
}`
    }
  ],
  repair_history: [
    {
      timestamp: "16:02:12",
      message: "REPAIR Applied targeted patch to endpoint authorization."
    }
  ]
};

export const mockArchitectureData: ArchitectureMapScreen = {
  nodes: [
    { id: "Admin", label: "Admin (Actor)", type: "Actor" },
    { id: "/bookings", label: "/bookings (API)", type: "API" },
    { id: "bookings_table", label: "bookings_table (DB)", type: "DB" },
    { id: "BookingForm", label: "BookingForm (UI)", type: "UI" }
  ],
  edges: [
    { id: "e1", source: "Admin", target: "/bookings", type: "CALLS" },
    { id: "e2", source: "/bookings", target: "bookings_table", type: "WRITES_TO" },
    { id: "e3", source: "BookingForm", target: "/bookings", type: "SUBMITS_TO" }
  ],
  entity_relationships: [
    {
      relationship_id: "rel_booking_user",
      source: "Booking",
      target: "User",
      type: "Many-to-One",
      description: "A Booking is owned by a User"
    }
  ],
  workflow_relationships: [
    {
      workflow_id: "wf_create_booking",
      name: "Create Booking",
      steps: ["Initialize", "Validate Loyalty", "Apply Tier Pricing", "Save"],
      actors: ["Member", "Admin"],
      dependencies: ["User", "Booking"]
    }
  ],
  dependency_graph: {
    changed_component: "Booking",
    directly_affected: ["User", "BookingForm"],
    indirectly_affected: ["PaymentProcessor"],
    dependency_depth: 2
  }
};

export const mockSimulationData: ExecutionVerificationScreen = {
  simulation_report: {
    simulation_id: "sim_99x",
    workflows_executed: ["Create Booking", "Cancel Booking"],
    successful_steps: 12,
    failed_steps: 0,
    permission_failures: 0,
    contract_failures: 0,
    validation_failures: 0,
    repair_failures: 0,
    business_rule_failures: 0,
    success_rate: 97.0,
    simulation_traces: [
      {
        timestamp: "2026-06-23T20:10:00Z",
        actor: "GymMember",
        action: "BookClass",
        outcome: "SUCCESS",
        reason: "Active subscription found",
        affected_components: ["Booking", "Schedule"]
      },
      {
        timestamp: "2026-06-23T20:10:05Z",
        actor: "GymMember",
        action: "DeleteUser",
        outcome: "FAILED",
        reason: "Permission Denied",
        affected_components: ["User"]
      }
    ]
  },
  workflow_results: [
    { name: "User Request Received", status: "Verified", duration: "3ms", log: "Header validation valid" },
    { name: "Authentication Service", status: "Verified", duration: "12ms", log: "OAuth2 Token Valid" },
    { name: "Business Rule Validation", status: "Verified", duration: "9ms", log: "12/12 Rules passed" },
    { name: "API Processing Core", status: "Processing", duration: "45ms", log: "Load 12%" }
  ],
  permission_results: [
    { entity: "Booking", from_state: "PENDING", to_state: "CONFIRMED", allowed: true },
    { entity: "Booking", from_state: "CONFIRMED", to_state: "PENDING", allowed: false }
  ],
  execution_metrics: {
    avg_execution_time: 18.5,
    success_probability: 0.9884,
    failure_rate: "LOW",
    critical_paths_secure: "2/3 Secure"
  }
};

export const mockTimelineData: VersionHistoryEvolutionScreen = {
  versions: [
    {
      version_id: "v1.2.8",
      parent_version: "v1.2.6",
      created_at: "2 hours ago",
      change_summary: "Premium Booking Rules - Tiered pricing logic and loyalty validators."
    },
    {
      version_id: "v1.2.6",
      parent_version: "v1.2.4",
      created_at: "15 Aug 2023",
      change_summary: "Heuristic Circular Ref Patch applied to Booking Schema."
    },
    {
      version_id: "v1.2.4",
      parent_version: "v1.0.0",
      created_at: "14 Aug 2023",
      change_summary: "Dependency Optimization for compilation latency."
    }
  ],
  change_reports: [
    {
      change_id: "chg_v1.2.8",
      version_info: {
        version_id: "v1.2.8",
        parent_version: "v1.2.6",
        created_at: "2 hours ago",
        change_summary: "Premium Booking Rules - Tiered pricing logic and loyalty validators."
      },
      diffs: [
        {
          component: "BookingSchema",
          before_state: "basic_pricing: true",
          after_state: "tiered_pricing: true, loyalty_validation: true",
          change_reason: "Premium Booking rules requirements"
        }
      ],
      impact_report: {
        affected_components: ["Booking", "User", "BookingForm", "PricingEngine"],
        unaffected_components: ["NotificationService"],
        estimated_effort: "Medium",
        impact_score: {
          entities_changed: 1,
          workflows_changed: 1,
          apis_changed: 2,
          permissions_changed: 0,
          business_rules_changed: 2,
          score: 42.0,
          impact_level: "MEDIUM"
        },
        dependency_graph: {
          changed_component: "Booking",
          directly_affected: ["User", "BookingForm"],
          indirectly_affected: ["PaymentProcessor"],
          dependency_depth: 2,
          direct_dependencies: ["User"],
          indirect_dependencies: []
        }
      },
      risk_assessment: {
        risk_level: "MEDIUM",
        affected_components: ["Booking", "PricingEngine"],
        affected_workflows: ["Create Booking"],
        affected_entities: ["Booking"],
        validation_risk: 0.12,
        repair_risk: 0.05,
        simulation_risk: 0.08,
        overall_risk_score: 0.25
      },
      effectiveness: {
        components_modified: ["Booking"],
        components_preserved: ["User", "NotificationService"],
        validation_passed: true,
        repair_required: false,
        simulation_passed: true,
        rollback_required: false,
        risk_level: "MEDIUM",
        impact_level: "MEDIUM",
        complexity_level: "MEDIUM"
      },
      conflicts_report: {
        is_valid: true,
        conflicts: []
      },
      updated_blueprint: null,
      updated_spec: null,
      updated_bundle: null
    }
  ],
  risk_assessments: [
    {
      risk_level: "MEDIUM",
      affected_components: ["Booking", "PricingEngine"],
      affected_workflows: ["Create Booking"],
      affected_entities: ["Booking"],
      validation_risk: 0.12,
      repair_risk: 0.05,
      simulation_risk: 0.08,
      overall_risk_score: 0.25
    }
  ],
  impact_analysis: [
    {
      affected_components: ["Booking", "User", "BookingForm", "PricingEngine"],
      unaffected_components: ["NotificationService"],
      estimated_effort: "Medium",
      impact_score: {
        entities_changed: 1,
        workflows_changed: 1,
        apis_changed: 2,
        permissions_changed: 0,
        business_rules_changed: 2,
        score: 42.0,
        impact_level: "MEDIUM"
      },
      dependency_graph: {
        changed_component: "Booking",
        directly_affected: ["User", "BookingForm"],
        indirectly_affected: ["PaymentProcessor"],
        dependency_depth: 2,
        direct_dependencies: ["User"],
        indirect_dependencies: []
      }
    }
  ],
  evolution_timeline: [
    {
      version_id: "v1.2.8",
      change_summary: "Premium Booking Rules",
      impact_level: "LOW",
      risk_level: "MEDIUM",
      timestamp: "2 hours ago"
    },
    {
      version_id: "v1.2.6",
      change_summary: "Heuristic Circular Ref Patch",
      impact_level: "MEDIUM",
      risk_level: "LOW",
      timestamp: "15 Aug 2023"
    },
    {
      version_id: "v1.2.4",
      change_summary: "Dependency Optimization",
      impact_level: "HIGH",
      risk_level: "HIGH",
      timestamp: "14 Aug 2023"
    }
  ]
};

export const mockAIArchitectReport: AIArchitectReport = {
  mode: "HYBRID",
  ambiguity_score: 0.68,
  missing_information: [
    {
      category: "workflows",
      description: "Membership purchase, class booking, attendance, and cancellation flows need full rules.",
      impact: "MEDIUM"
    },
    {
      category: "integrations",
      description: "Payment gateway and notification integrations are not specified.",
      impact: "MEDIUM"
    }
  ],
  assumptions_made: [
    {
      assumption: "Admin console required",
      confidence: 0.88,
      reason: "Operational systems need administrative record management and access control.",
      risk_level: "LOW",
      source: "requirements_intelligence"
    },
    {
      assumption: "External integrations will be modeled as replaceable adapters",
      confidence: 0.7,
      reason: "Adapter boundaries preserve deployment compatibility until provider choices are known.",
      risk_level: "MEDIUM",
      source: "requirements_intelligence"
    }
  ],
  clarification_questions: [
    {
      question: "Should attendance tracking be included in the first version?",
      category: "workflows",
      priority: "HIGH"
    }
  ],
  risks: [
    {
      risk: "Architecture may encode the wrong workflow scope.",
      severity: "HIGH",
      mitigation: "Clarify attendance and cancellation rules before production build-out."
    }
  ],
  confidence_scores: {
    prompt_completeness: 0.64,
    architecture_confidence: 0.8,
    requirement_confidence: 0.7,
    assumption_confidence: 0.79,
    overall_score: 0.73
  },
  architecture_reasoning_trace: [
    {
      component: "ClassBooking",
      component_type: "Entity",
      reason: "Generated because class scheduling requires reservation records."
    },
    {
      component: "MembershipPurchaseFlow",
      component_type: "Workflow",
      reason: "Generated because payment transactions are needed for member onboarding."
    }
  ],
  recommended_architecture_strategy:
    "Proceed with a hybrid architecture: ask critical questions, isolate uncertain integrations, and auto-assume low-risk defaults."
};

// Full FinalCompiledApplication matching compile output for mock runs
export const mockFinalCompiledApplication: FinalCompiledApplication = {
  project_id: "proj_01",
  app_name: "GymManagementSystem",
  app_type: "Backend API",
  prompt: "Gym Management System with Bookings and Payments",
  intent: mockCompilerData.intent,
  ai_architect_report: mockAIArchitectReport,
  blueprint: mockCompilerData.blueprint,
  system_design: mockCompilerData.system_design,
  schema_bundle: mockCompilerData.schema_bundle,
  validation_report: mockValidationRepairData.validation_report,
  repair_report: null,
  simulation_report: mockSimulationData.simulation_report,
  evolution_summary: mockTimelineData.change_reports[0],
  pipeline_traces: mockPipelineTraces,
  execution_mode: "BALANCED",
  created_at: "2026-06-23T20:00:00Z",
  updated_at: "2026-06-23T20:10:00Z"
};

export const mockRepairReport: RepairReport = {
  repair_id: "rep_20A_2026",
  validation_errors_received: mockValidationError,
  repair_candidates_generated: [
    {
      candidate_id: "cand_01",
      error_id: "val_err_002",
      repair_strategy: "strat_api_auth",
      confidence: 0.94,
      target_components: ["/api/v1/evolution"],
      estimated_impact: "LOW",
      repair_type: "UPDATE"
    }
  ],
  repair_actions_executed: [
    {
      action_id: "act_01",
      candidate_id: "cand_01",
      action_description: "Inject GENESIS_ROLES validation middleware to authorization handler.",
      affected_components: ["/api/v1/evolution"],
      before_state: "basic auth",
      after_state: "auth with GENESIS_ROLES",
      success: true
    }
  ],
  successful_repairs: [
    {
      action_id: "act_01",
      candidate_id: "cand_01",
      action_description: "Inject GENESIS_ROLES validation middleware to authorization handler.",
      affected_components: ["/api/v1/evolution"],
      before_state: "basic auth",
      after_state: "auth with GENESIS_ROLES",
      success: true
    }
  ],
  failed_repairs: [],
  revalidation_results: {
    is_valid: true,
    errors: [],
    warnings: [],
    critical_count: 0,
    high_count: 0,
    medium_count: 0,
    low_count: 0,
    validated_components: ["Auth"],
    timestamp: "2026-06-23T20:05:00Z"
  },
  timestamp: "2026-06-23T20:05:00Z"
};
