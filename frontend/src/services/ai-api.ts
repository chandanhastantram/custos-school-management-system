import apiClient from "@/lib/api-client";

// Types
export interface DoubtSolverRequest {
  question: string;
  subject: string;
  context?: string;
}

export interface DoubtSolverResponse {
  answer: string;
  steps: string[];
  examples?: string[];
  related_concepts: string[];
  practice_problems: string[];
}

export interface LessonPlanRequest {
  subject: string;
  topic: string;
  grade_level: number;
  duration_minutes?: number;
}

export interface LessonPlanResponse {
  objectives: string[];
  introduction: string;
  content: string[];
  activities: string[];
  assessment: string[];
  homework: string;
  resources: string[];
}

export interface GenerateQuestionsRequest {
  subject: string;
  topic: string;
  question_type: string;
  count: number;
  difficulty?: string;
}

export interface Question {
  question: string;
  type: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
}

// AI API Service
export const aiApi = {
  // Doubt Solver (Students)
  async solveDoubt(request: DoubtSolverRequest): Promise<DoubtSolverResponse> {
    const response = await apiClient.post("/ai/doubt-solver", request);
    return response.data;
  },

  // Lesson Plan Generation (Teachers)
  async generateLessonPlan(request: LessonPlanRequest): Promise<LessonPlanResponse> {
    const response = await apiClient.post("/ai/lesson-plan/generate", request);
    return response.data;
  },

  // Question Generation (Teachers)
  async generateQuestions(request: GenerateQuestionsRequest): Promise<Question[]> {
    const response = await apiClient.post("/ai/generate-questions", request);
    return response.data.questions || [];
  },

  // Get AI Usage Stats
  async getUsage(): Promise<{ ai_requests_used: number; ai_requests_limit: number }> {
    const response = await apiClient.get("/ai/usage");
    return response.data;
  },
};

export default aiApi;
