import axios, { AxiosInstance } from 'axios';
import chalk from 'chalk';

export interface PipelineRequest {
  repo_url: string;
  target?: string;        // Optional - for auto mode, backend decides
  environments?: string[]; // Optional - for auto mode, backend decides
  mode?: string;          // 'auto' or 'manual'
  local_path?: string;    // For local repositories, the actual file system path
}

export interface PipelineResponse {
  pr_url: string;
  citations: string[];
  validation_status: string;
  pipeline_file: string;
  stack: Record<string, any>;
  success: boolean;
  target?: string;        // AI-selected deployment target
  environments?: string[]; // AI-selected environments
  pipeline_type?: string;  // AI-determined pipeline type
}

export interface KBSearchRequest {
  query: string;
  collections?: string[];
  limit?: number;
}

export interface KBSearchResponse {
  query: string;
  results: Array<Record<string, any>>;
  count: number;
}

export interface KBConnectRequest {
  uri: string;
}

export interface KBConnectResponse {
  success: boolean;
  uri: string;
  documents: number;
  collections: string[];
  source_type: string;
  note?: string;
}

export interface StackAnalysisResponse {
  repo_url: string;
  stack: Record<string, any>;
  supported: boolean;
}

export interface IntelligentPipelineRequest {
  local_path: string;
  target?: string;
  environments?: string[];
  use_analysis?: boolean;
}

export interface IntelligentPipelineResponse {
  pipeline_file: string;
  pipeline_content: string;
  analysis_summary: Record<string, any>;
  recommendations_applied: string[];
  rag_sources: string[];
  validation_status: string;
  success: boolean;
  quality_improvements: string[];
  error?: string;
}

export class FopsApiClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 120000, // 2 minutes timeout for AI operations
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for debugging (disabled for cleaner output)
    this.client.interceptors.request.use(
      (config) => {
        // Removed verbose logging for cleaner CLI output
        return config;
      },
      (error) => {
        console.error(chalk.red('❌ Request Error:'), error.message);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        // Removed verbose logging for cleaner CLI output
        return response;
      },
      (error) => {
        if (error.code === 'ECONNREFUSED') {
          console.error(chalk.red('❌ Connection Error: F-Ops backend is not running'));
          console.log(chalk.yellow('💡 Please start the backend server:'));
          console.log(chalk.cyan('   cd backend && python -m uvicorn app.main:app --reload --port 8000'));
        } else if (error.response) {
          console.error(chalk.red(`❌ API Error: ${error.response.status} ${error.response.statusText}`));
          if (error.response.data?.detail) {
            console.error(chalk.red('   Details:'), error.response.data.detail);
          }
        } else {
          console.error(chalk.red('❌ Network Error:'), error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Check if the F-Ops backend is healthy
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.client.get('/api/pipeline/health');
      return response.data.status === 'healthy';
    } catch (error) {
      return false;
    }
  }

  /**
   * Generate CI/CD pipeline using RAG-powered AI
   */
  async generatePipeline(request: PipelineRequest): Promise<PipelineResponse> {
    try {
      const response = await this.client.post<PipelineResponse>('/api/pipeline/generate', request);
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to generate pipeline: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Analyze repository stack without generating pipeline
   */
  async analyzeRepositoryStack(repoUrl: string): Promise<StackAnalysisResponse> {
    try {
      // Encode the repo URL for the path parameter
      const encodedRepoUrl = encodeURIComponent(repoUrl);
      const response = await this.client.get<StackAnalysisResponse>(`/api/pipeline/stack-analysis/${encodedRepoUrl}`);
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to analyze repository: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Search knowledge base
   */
  async searchKnowledgeBase(request: KBSearchRequest): Promise<KBSearchResponse> {
    try {
      const response = await this.client.post<KBSearchResponse>('/api/kb/search', request);
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to search knowledge base: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Connect and ingest documentation
   */
  async connectKnowledgeBase(request: KBConnectRequest): Promise<KBConnectResponse> {
    try {
      const response = await this.client.post<KBConnectResponse>('/api/kb/connect', request);
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to connect knowledge base: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Get knowledge base statistics
   */
  async getKnowledgeBaseStats(): Promise<any> {
    try {
      const response = await this.client.get('/api/kb/stats');
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to get knowledge base stats: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Generate intelligent CI/CD pipeline using comprehensive analysis and RAG
   */
  async generateIntelligentPipeline(request: IntelligentPipelineRequest): Promise<IntelligentPipelineResponse> {
    try {
      const response = await this.client.post<IntelligentPipelineResponse>('/api/pipeline/intelligent-generate', request);
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to generate intelligent pipeline: ${error.response?.data?.detail || error.message}`);
    }
  }

  /**
   * Perform comprehensive AI analysis of codebase
   */
  async comprehensiveAnalysis(request: { local_path: string }): Promise<any> {
    try {
      const response = await this.client.post('/api/pipeline/comprehensive-analysis', request);
      return response.data;
    } catch (error: any) {
      throw new Error(`Failed to perform comprehensive analysis: ${error.response?.data?.detail || error.message}`);
    }
  }
}