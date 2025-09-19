import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  CloudIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  EyeIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline'
import { infrastructureApi } from '../services/api'
import TerraformPlanViewer from '../components/TerraformPlanViewer'
import HelmDryRunViewer from '../components/HelmDryRunViewer'
import LoadingSpinner from '../components/LoadingSpinner'

interface InfrastructureFormData {
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

export default function InfrastructureModule() {
  const [result, setResult] = useState<InfrastructureResult | null>(null)
  const [showFilePreview, setShowFilePreview] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm<InfrastructureFormData>({
    defaultValues: {
      target: 'k8s',
      environments: ['staging'],
      domain: '',
      registry: 'docker.io/myorg',
      secrets_strategy: 'aws-secrets-manager'
    }
  })

  const selectedTarget = watch('target')

  // Get supported targets
  const { data: targets } = useQuery({
    queryKey: ['infrastructure', 'targets'],
    queryFn: infrastructureApi.getTargets
  })

  // Get secrets strategies
  const { data: secretsStrategies } = useQuery({
    queryKey: ['infrastructure', 'secrets-strategies'],
    queryFn: infrastructureApi.getSecretsStrategies
  })

  // Generate infrastructure mutation
  const generateMutation = useMutation({
    mutationFn: (data: InfrastructureFormData) => infrastructureApi.generate({
      target: data.target,
      environments: data.environments,
      domain: data.domain || `app-${data.target}.example.com`,
      registry: data.registry,
      secrets_strategy: data.secrets_strategy
    }),
    onSuccess: (response) => {
      setResult(response)
    }
  })

  // Create PR mutation
  const createPrMutation = useMutation({
    mutationFn: (data: any) => infrastructureApi.createPR(data),
    onSuccess: (response) => {
      setResult(prev => prev ? { ...prev, pr_url: response.pr_url } : null)
    }
  })

  const onSubmit = (data: InfrastructureFormData) => {
    generateMutation.mutate(data)
  }

  const handleCreatePr = () => {
    if (!result) return

    const formData = watch()
    createPrMutation.mutate({
      repo_url: 'https://github.com/user/repo', // This would come from form or context
      target: formData.target,
      environments: formData.environments,
      domain: formData.domain || `app-${formData.target}.example.com`,
      terraform: result.terraform,
      helm: result.helm,
      terraform_plan: result.terraform_plan,
      helm_dry_run: result.helm_dry_run,
      citations: result.citations
    })
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-8">
        <div className="flex items-center">
          <CloudIcon className="h-8 w-8 text-f-ops-600 mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Infrastructure Agent</h1>
            <p className="mt-2 text-gray-600">
              Generate Terraform modules and Helm charts with dry-run validation
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Configuration Form */}
        <div className="lg:col-span-4">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Infrastructure Configuration
            </h2>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Target Platform */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Platform
                </label>
                <select
                  {...register('target', { required: 'Target platform is required' })}
                  className="form-select"
                >
                  {targets?.targets.map((target: any) => (
                    <option key={target.name} value={target.name}>
                      {target.display_name}
                    </option>
                  ))}
                </select>
                {errors.target && (
                  <p className="mt-1 text-sm text-red-600">{errors.target.message}</p>
                )}
              </div>

              {/* Environments */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Environments
                </label>
                <div className="space-y-2">
                  {['staging', 'prod'].map(env => (
                    <label key={env} className="flex items-center">
                      <input
                        type="checkbox"
                        value={env}
                        {...register('environments', {
                          required: 'At least one environment is required'
                        })}
                        className="h-4 w-4 text-f-ops-600 focus:ring-f-ops-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{env}</span>
                    </label>
                  ))}
                </div>
                {errors.environments && (
                  <p className="mt-1 text-sm text-red-600">{errors.environments.message}</p>
                )}
              </div>

              {/* Domain */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Domain
                </label>
                <input
                  type="text"
                  {...register('domain')}
                  className="form-input"
                  placeholder={`app-${selectedTarget}.example.com`}
                />
              </div>

              {/* Container Registry */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Container Registry
                </label>
                <input
                  type="text"
                  {...register('registry')}
                  className="form-input"
                  placeholder="docker.io/myorg"
                />
              </div>

              {/* Secrets Strategy */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secrets Strategy
                </label>
                <select
                  {...register('secrets_strategy')}
                  className="form-select"
                >
                  {secretsStrategies?.strategies.map((strategy: any) => (
                    <option key={strategy.name} value={strategy.name}>
                      {strategy.display_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={generateMutation.isPending}
                className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generateMutation.isPending ? (
                  <div className="flex items-center justify-center">
                    <LoadingSpinner className="w-4 h-4 mr-2" />
                    Generating...
                  </div>
                ) : (
                  'Generate Infrastructure'
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8">
          {result ? (
            <div className="space-y-6">
              {/* Status Summary */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Generation Results
                  </h2>
                  <div className="flex items-center space-x-2">
                    {result.success ? (
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                    ) : (
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />
                    )}
                    <span className={`text-sm font-medium ${
                      result.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {result.success ? 'Success' : 'Failed'}
                    </span>
                  </div>
                </div>

                <p className="text-gray-600 mb-4">{result.message}</p>

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {result.terraform_plan && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <h3 className="font-medium text-blue-900 mb-2">Terraform Plan</h3>
                      <div className="space-y-1 text-sm">
                        <div className="text-green-600">
                          + {result.terraform_plan.summary?.add || 0} to add
                        </div>
                        <div className="text-yellow-600">
                          ~ {result.terraform_plan.summary?.change || 0} to change
                        </div>
                        <div className="text-red-600">
                          - {result.terraform_plan.summary?.destroy || 0} to destroy
                        </div>
                      </div>
                    </div>
                  )}

                  {result.helm_dry_run && (
                    <div className="bg-purple-50 rounded-lg p-4">
                      <h3 className="font-medium text-purple-900 mb-2">Helm Dry-Run</h3>
                      <div className="space-y-1 text-sm">
                        <div className="text-purple-700">
                          Status: {result.helm_dry_run.status}
                        </div>
                        <div className="text-purple-700">
                          Manifests: {result.helm_dry_run.manifests?.length || 0}
                        </div>
                        <div className={`${
                          result.helm_dry_run.lint?.passed ? 'text-green-600' : 'text-red-600'
                        }`}>
                          Lint: {result.helm_dry_run.lint?.passed ? 'Passed' : 'Failed'}
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Citations</h3>
                    <div className="text-sm text-gray-600">
                      {result.citations.length} KB sources referenced
                    </div>
                  </div>
                </div>

                {/* File Preview Toggle */}
                <div className="mt-4">
                  <button
                    onClick={() => setShowFilePreview(!showFilePreview)}
                    className="btn-secondary"
                  >
                    <EyeIcon className="w-4 h-4 mr-2" />
                    {showFilePreview ? 'Hide' : 'Show'} Generated Files
                  </button>
                </div>
              </div>

              {/* File Preview */}
              {showFilePreview && (result.terraform || result.helm) && (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Generated Files Preview
                  </h3>

                  {result.terraform && (
                    <div className="mb-6">
                      <h4 className="font-medium text-gray-900 mb-2">Terraform Files</h4>
                      <div className="space-y-2">
                        {Object.entries(result.terraform).slice(0, 3).map(([path, content]) => (
                          <details key={path} className="border rounded">
                            <summary className="p-2 bg-gray-50 cursor-pointer font-mono text-sm">
                              {path}
                            </summary>
                            <pre className="p-4 text-xs overflow-x-auto bg-gray-900 text-gray-100">
                              {content.slice(0, 500)}
                              {content.length > 500 && '...'}
                            </pre>
                          </details>
                        ))}
                        {Object.keys(result.terraform).length > 3 && (
                          <p className="text-sm text-gray-500">
                            ... and {Object.keys(result.terraform).length - 3} more files
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {result.helm && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Helm Chart Files</h4>
                      <div className="space-y-2">
                        {Object.entries(result.helm).slice(0, 3).map(([path, content]) => (
                          <details key={path} className="border rounded">
                            <summary className="p-2 bg-gray-50 cursor-pointer font-mono text-sm">
                              {path}
                            </summary>
                            <pre className="p-4 text-xs overflow-x-auto bg-gray-900 text-gray-100">
                              {content.slice(0, 500)}
                              {content.length > 500 && '...'}
                            </pre>
                          </details>
                        ))}
                        {Object.keys(result.helm).length > 3 && (
                          <p className="text-sm text-gray-500">
                            ... and {Object.keys(result.helm).length - 3} more files
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Terraform Plan Results */}
              {result.terraform_plan && (
                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    Terraform Plan Results
                  </h2>
                  <TerraformPlanViewer plan={result.terraform_plan} />
                </div>
              )}

              {/* Helm Dry-Run Results */}
              {result.helm_dry_run && (
                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">
                    Helm Dry-Run Results
                  </h2>
                  <HelmDryRunViewer dryRun={result.helm_dry_run} />
                </div>
              )}

              {/* Citations */}
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <DocumentTextIcon className="w-5 h-5 inline mr-2" />
                  Knowledge Base Citations
                </h3>
                {result.citations.length > 0 ? (
                  <ul className="space-y-2">
                    {result.citations.map((citation, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-gray-400 mr-2">•</span>
                        <span>{citation}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm">No citations available</p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="card p-6">
                {!result.pr_url ? (
                  <button
                    onClick={handleCreatePr}
                    disabled={createPrMutation.isPending}
                    className="w-full btn-success disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {createPrMutation.isPending ? (
                      <div className="flex items-center justify-center">
                        <LoadingSpinner className="w-4 h-4 mr-2" />
                        Creating PR...
                      </div>
                    ) : (
                      'Create PR with Dry-Run Artifacts'
                    )}
                  </button>
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <CheckCircleIcon className="w-5 h-5 text-green-400 mr-2" />
                      <span className="text-green-800 font-medium">
                        PR created successfully with validation artifacts
                      </span>
                    </div>
                    <a
                      href={result.pr_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center text-green-700 hover:text-green-900"
                    >
                      View PR
                      <ArrowTopRightOnSquareIcon className="w-4 h-4 ml-1" />
                    </a>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card p-12 text-center">
              <CloudIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Ready to Generate Infrastructure
              </h3>
              <p className="text-gray-500">
                Configure your infrastructure settings and click "Generate Infrastructure" to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}