// GenesisAI API Client Layer
// Integrates Axios with the FastAPI compiler backend and supports high-fidelity mock data fallback.

import axios from "axios";
import { API_BASE_URL } from "./config";
import {
  ApiResponse,
  FinalCompiledApplication,
  ValidationReport,
  RepairReport,
  ExecutionSimulationReport,
  DashboardScreen,
  ArchitectureMapScreen,
  VersionHistoryEvolutionScreen,
  AIArchitectScreen
} from "./frontend_models";
import * as mockData from "./mock_data";

// Change this flag to toggle between mock data and real API calls
export const USE_MOCK_DATA = false;

// Create Axios client instance
const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

/**
 * Standardized wrapper that simulates request lifecycle and injects latency for mock mode.
 */
async function requestWrapper<T>(
  apiCall: () => Promise<{ data: T }>,
  mockValue: T
): Promise<ApiResponse<T>> {
  if (USE_MOCK_DATA) {
    // Simulate network latency (500ms) for high-fidelity loading state animations
    await new Promise((resolve) => setTimeout(resolve, 500));
    return {
      success: true,
      data: mockValue
    };
  }

  try {
    const response = await apiCall();
    return {
      success: true,
      data: response.data
    };
  } catch (error: any) {
    console.error("API Error:", error);
    const errorMessage =
      error.response?.data?.detail || error.message || "An unexpected error occurred.";
    return {
      success: false,
      error: errorMessage
    };
  }
}

/**
 * Compiles a new project prompt or propagates evolutionary requirement changes.
 * POST /demo/compile
 */
export async function compileProject(
  prompt: string,
  executionMode: string = "BALANCED",
  intelligenceMode: string = "HYBRID"
): Promise<ApiResponse<FinalCompiledApplication>> {
  return requestWrapper(
    () =>
      client.post<FinalCompiledApplication>("/demo/compile", {
        prompt,
        execution_mode: executionMode,
        intelligence_mode: intelligenceMode
      }),
    mockData.mockFinalCompiledApplication
  );
}

/**
 * Run architectural validation checks against a project.
 * POST /validate
 */
export async function validateProject(
  projectId: string
): Promise<ApiResponse<ValidationReport>> {
  return requestWrapper(
    () =>
      client.post<ValidationReport>("/validate", {
        project_id: projectId
      }),
    mockData.mockValidationRepairData.validation_report
  );
}

/**
 * Trigger autonomous self-healing repairs for compilation or schema issues.
 * POST /repair
 */
export async function repairProject(
  projectId: string
): Promise<ApiResponse<RepairReport>> {
  return requestWrapper(
    () =>
      client.post<RepairReport>("/repair", {
        project_id: projectId
      }),
    mockData.mockRepairReport
  );
}

/**
 * Executes a simulated execution of workflows inside the sandbox.
 * POST /simulate
 */
export async function simulateProject(
  projectId: string
): Promise<ApiResponse<ExecutionSimulationReport>> {
  return requestWrapper(
    () =>
      client.post<ExecutionSimulationReport>("/simulate", {
        project_id: projectId
      }),
    mockData.mockSimulationData.simulation_report
  );
}

/**
 * Fetch top-level dashboard telemetry and compilation performance history.
 * GET /dashboard
 */
export async function getDashboard(): Promise<ApiResponse<DashboardScreen>> {
  return requestWrapper(
    () => client.get<DashboardScreen>("/dashboard"),
    mockData.mockDashboardData
  );
}

/**
 * Retrieve the detailed node/edge dependency layout representing the architecture map canvas.
 * GET /architecture/{project_id}
 */
export async function getArchitecture(
  projectId: string
): Promise<ApiResponse<ArchitectureMapScreen>> {
  return requestWrapper(
    () => client.get<ArchitectureMapScreen>(`/architecture/${projectId}`),
    mockData.mockArchitectureData
  );
}

/**
 * Retrieve the AI Requirements Intelligence report for a project.
 * GET /ai-architect/{project_id}
 */
export async function getAIArchitectReport(
  projectId: string
): Promise<ApiResponse<AIArchitectScreen>> {
  return requestWrapper(
    () => client.get<AIArchitectScreen>(`/ai-architect/${projectId}`),
    { report: mockData.mockAIArchitectReport }
  );
}

/**
 * Fetch the complete requirement version list and evolution timeline.
 * GET /versions/{project_id}
 */
export async function getVersions(
  projectId: string
): Promise<ApiResponse<VersionHistoryEvolutionScreen>> {
  return requestWrapper(
    () => client.get<VersionHistoryEvolutionScreen>(`/versions/${projectId}`),
    mockData.mockTimelineData
  );
}

/**
 * Fetch the full compiled details for a specific project.
 * GET /project/{project_id}
 */
export async function getProject(
  projectId: string
): Promise<ApiResponse<FinalCompiledApplication>> {
  return requestWrapper(
    () => client.get<FinalCompiledApplication>(`/project/${projectId}`),
    mockData.mockFinalCompiledApplication
  );
}
