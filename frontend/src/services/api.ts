const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface InfrastructureGenerateRequest {
  target: string
  environments: string[]
  domain: string
  registry: string
  secrets_strategy: string
}

interface InfrastructureResult {
  success: boolean
  terraform?: Record<string, string>
  helm?: Record<string, string>
  terraform_plan?: any
  helm_dry_run?: any
  citations: string[]
  message: string
}

interface CreatePRRequest {
  repo_url: string
  target: string
  environments: string[]
  domain: string
  terraform?: Record<string, string>
  helm?: Record<string, string>
  terraform_plan?: any
  helm_dry_run?: any
  citations: string[]
}

interface CreatePRResponse {
  pr_url: string
}

interface Target {
  name: string
  display_name: string
  description: string
}

interface TargetsResponse {
  targets: Target[]
}

interface SecretsStrategy {
  name: string
  display_name: string
  description: string
}

interface SecretsStrategiesResponse {
  strategies: SecretsStrategy[]
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new ApiError(response.status, errorData.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const infrastructureApi = {
  async getTargets(): Promise<TargetsResponse> {
    return apiRequest<TargetsResponse>('/api/infrastructure/targets')
  },

  async getSecretsStrategies(): Promise<SecretsStrategiesResponse> {
    return apiRequest<SecretsStrategiesResponse>('/api/infrastructure/secrets-strategies')
  },

  async generate(data: InfrastructureGenerateRequest): Promise<InfrastructureResult> {
    return apiRequest<InfrastructureResult>('/api/infrastructure/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async validate(data: InfrastructureGenerateRequest): Promise<{ valid: boolean; errors: string[] }> {
    return apiRequest<{ valid: boolean; errors: string[] }>('/api/infrastructure/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async createPR(data: CreatePRRequest): Promise<CreatePRResponse> {
    return apiRequest<CreatePRResponse>('/api/infrastructure/create-pr', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async getTerraformPlan(data: InfrastructureGenerateRequest): Promise<any> {
    return apiRequest<any>('/api/infrastructure/terraform/plan', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async getHelmDryRun(data: InfrastructureGenerateRequest): Promise<any> {
    return apiRequest<any>('/api/infrastructure/helm/dry-run', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

interface PipelineGenerateRequest {
  repo_url: string
  target: string
  environments: string[]
  stack: string
  org_standards: string
}

interface PipelineResult {
  success: boolean
  pipeline_files?: Record<string, string>
  security_scan?: any
  slo_gates?: any
  citations: string[]
  message: string
  detected_stack?: {
    language: string
    framework?: string
    dockerfile: boolean
    package_manager: string
  }
}

interface PipelineCreatePRRequest {
  repo_url: string
  target: string
  environments: string[]
  stack: string
  pipeline_files?: Record<string, string>
  security_scan?: any
  slo_gates?: any
  citations: string[]
}

export const pipelineApi = {
  async getTargets(): Promise<TargetsResponse> {
    return apiRequest<TargetsResponse>('/api/pipeline/targets')
  },

  async generate(data: PipelineGenerateRequest): Promise<PipelineResult> {
    return apiRequest<PipelineResult>('/api/pipeline/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async validate(data: PipelineGenerateRequest): Promise<{ valid: boolean; errors: string[] }> {
    return apiRequest<{ valid: boolean; errors: string[] }>('/api/pipeline/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async createPR(data: PipelineCreatePRRequest): Promise<CreatePRResponse> {
    return apiRequest<CreatePRResponse>('/api/pipeline/create-pr', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  async detectStack(repo_url: string): Promise<any> {
    return apiRequest<any>('/api/pipeline/detect-stack', {
      method: 'POST',
      body: JSON.stringify({ repo_url }),
    })
  },

  async uploadFiles(files: FileList): Promise<any> {
    const formData = new FormData()
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i])
    }

    const response = await fetch(`${API_BASE_URL}/api/pipeline/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new ApiError(response.status, errorData.detail || `HTTP ${response.status}`)
    }

    return response.json()
  },

  async saveFile(file_path: string, content: string, local_path?: string): Promise<any> {
    return apiRequest<any>('/api/pipeline/save-file', {
      method: 'POST',
      body: JSON.stringify({ file_path, content, local_path }),
    })
  }
}

export const kbApi = {
  // Placeholder for future Knowledge Base API
  async search(query: string): Promise<any> {
    return apiRequest<any>('/api/kb/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  },

  async connect(uri: string): Promise<any> {
    return apiRequest<any>('/api/kb/connect', {
      method: 'POST',
      body: JSON.stringify({ uri }),
    })
  }
}

export { ApiError }