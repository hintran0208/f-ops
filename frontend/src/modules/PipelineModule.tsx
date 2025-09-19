import React, { useState, useRef, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  RocketLaunchIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  EyeIcon,
  ArrowTopRightOnSquareIcon,
  CodeBracketIcon,
  BugAntIcon,
  CloudArrowUpIcon,
  FolderOpenIcon,
  DocumentDuplicateIcon,
  PencilIcon,
  CheckIcon,
  ArrowPathIcon,
  TrashIcon
} from '@heroicons/react/24/outline'
import { pipelineApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import CodeEditor from '../components/CodeEditor'
import { usePersistence } from '../hooks/usePersistence'
import { useToast } from '../components/Toast'

interface PipelineFormData {
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

export default function PipelineModule() {
  const [result, setResult] = useState<PipelineResult | null>(null)
  const [showFilePreview, setShowFilePreview] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])
  const [editingFile, setEditingFile] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState<string>('')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const persistence = usePersistence()
  const { showToast, ToastContainer } = useToast()

  const { register, handleSubmit, watch, formState: { errors } } = useForm<PipelineFormData>({
    defaultValues: {
      repo_url: '',
      target: 'k8s',
      environments: ['staging'],
      stack: 'auto-detect',
      org_standards: 'default'
    }
  })

  const selectedTarget = watch('target')

  // Get supported targets (reusing infrastructure targets for now)
  const { data: targets } = useQuery({
    queryKey: ['pipeline', 'targets'],
    queryFn: pipelineApi.getTargets
  })

  // Generate pipeline mutation
  const generateMutation = useMutation({
    mutationFn: (data: PipelineFormData) => pipelineApi.generate({
      repo_url: data.repo_url,
      target: data.target,
      environments: data.environments,
      stack: data.stack,
      org_standards: data.org_standards
    }),
    onSuccess: (response) => {
      console.log('Pipeline generation response:', response)
      setResult(response)
      showToast('Pipeline generated successfully!', 'success')
    },
    onError: (error: any) => {
      showToast(`Pipeline generation failed: ${error.message}`, 'error')
    }
  })

  // Create PR mutation
  const createPrMutation = useMutation({
    mutationFn: (data: any) => pipelineApi.createPR(data),
    onSuccess: (response) => {
      setResult(prev => prev ? { ...prev, pr_url: response.pr_url } : null)
      showToast('PR created successfully!', 'success')
    },
    onError: (error: any) => {
      showToast(`PR creation failed: ${error.message}`, 'error')
    }
  })

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: (files: FileList) => pipelineApi.uploadFiles(files),
    onSuccess: (response) => {
      setUploadedFiles(response.files)
      showToast(`Successfully uploaded ${response.files.length} files`, 'success')
    },
    onError: (error: any) => {
      showToast(`Upload failed: ${error.message}`, 'error')
    }
  })

  // Save file mutation
  const saveFileMutation = useMutation({
    mutationFn: (data: { file_path: string; content: string }) =>
      pipelineApi.saveFile(data.file_path, data.content),
    onSuccess: () => {
      setEditingFile(null)
      setEditedContent('')
      showToast('File saved successfully', 'success')
    },
    onError: (error: any) => {
      showToast(`Save failed: ${error.message}`, 'error')
    }
  })

  const onSubmit = (data: PipelineFormData) => {
    generateMutation.mutate(data)
  }

  const handleCreatePr = () => {
    if (!result) return

    const formData = watch()
    createPrMutation.mutate({
      repo_url: formData.repo_url,
      target: formData.target,
      environments: formData.environments,
      stack: formData.stack,
      pipeline_files: result.pipeline_files,
      security_scan: result.security_scan,
      slo_gates: result.slo_gates,
      citations: result.citations
    })
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files && files.length > 0) {
      uploadMutation.mutate(files)
    }
  }

  const handleEditFile = (filePath: string, content: string) => {
    // Check if there's existing content to restore
    const savedContent = persistence.loadFileContent(filePath)
    setEditingFile(filePath)
    setEditedContent(savedContent || content)
  }

  const handleSaveFile = () => {
    if (editingFile) {
      saveFileMutation.mutate({
        file_path: editingFile,
        content: editedContent
      })
      // Clear the saved content after successful save
      persistence.clearFileContent(editingFile)
      setHasUnsavedChanges(false)
    }
  }

  const handleContentChange = (content: string) => {
    setEditedContent(content)
    setHasUnsavedChanges(true)
  }

  const handleCancelEdit = () => {
    if (hasUnsavedChanges) {
      if (window.confirm('You have unsaved changes. Discard them?')) {
        if (editingFile) {
          persistence.clearFileContent(editingFile)
        }
        setEditingFile(null)
        setEditedContent('')
        setHasUnsavedChanges(false)
      }
    } else {
      setEditingFile(null)
      setEditedContent('')
    }
  }

  const handleCopyFile = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
      showToast('Content copied to clipboard', 'success')
    } catch (error) {
      console.error('Failed to copy:', error)
      showToast('Failed to copy content', 'error')
    }
  }

  // Persistence and auto-save
  useEffect(() => {
    // Load saved state on mount
    const saved = persistence.loadState()
    if (saved) {
      if (saved.result) setResult(saved.result)
      if (saved.uploadedFiles) setUploadedFiles(saved.uploadedFiles)
      if (saved.editingFile) setEditingFile(saved.editingFile)
      if (saved.editedContent) setEditedContent(saved.editedContent)
      setShowFilePreview(Boolean(saved.result?.pipeline_files))
    }
  }, []) // Empty dependency array - only run once on mount

  // Auto-save state changes
  useEffect(() => {
    const cleanup = persistence.autoSave({
      result,
      uploadedFiles,
      editingFile,
      editedContent,
      formData: watch()
    })
    return cleanup
  }, [result, uploadedFiles, editingFile, editedContent]) // Removed persistence and watch from dependencies

  // Save file content separately for recovery
  useEffect(() => {
    if (editingFile && editedContent) {
      persistence.saveFileContent(editingFile, editedContent)
      setHasUnsavedChanges(true)
    }
  }, [editingFile, editedContent, persistence])

  // Warn about unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?'
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges])

  const handleClearData = () => {
    if (window.confirm('This will clear all data including unsaved changes. Continue?')) {
      persistence.clearState()
      setResult(null)
      setUploadedFiles([])
      setEditingFile(null)
      setEditedContent('')
      setHasUnsavedChanges(false)
      setShowFilePreview(false)
    }
  }

  return (
    <>
      <ToastContainer />
      <div className="px-4 sm:px-0">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <RocketLaunchIcon className="h-8 w-8 text-f-ops-600 mr-3" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Pipeline Agent</h1>
              <p className="mt-2 text-gray-600">
                Generate CI/CD pipelines with security scans and SLO gates
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {hasUnsavedChanges && (
              <div className="flex items-center text-amber-600 text-sm">
                <ArrowPathIcon className="w-4 h-4 mr-1" />
                Auto-saving...
              </div>
            )}
            <button
              type="button"
              onClick={handleClearData}
              className="btn-secondary text-sm py-1 px-3 flex items-center"
              title="Clear all data"
            >
              <TrashIcon className="w-4 h-4 mr-1" />
              Clear
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Configuration Form */}
        <div className="lg:col-span-4">
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Pipeline Configuration
            </h2>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload Project Files (Optional)
                </label>
                <div
                  className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <CloudArrowUpIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">
                    Drop files here or click to browse
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Supports individual files or ZIP archives
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  accept=".js,.ts,.json,.yml,.yaml,.md,.txt,.zip"
                />
                {uploadedFiles.length > 0 && (
                  <div className="mt-2 p-2 bg-green-50 rounded border border-green-200">
                    <p className="text-sm text-green-700">
                      ✅ Uploaded {uploadedFiles.length} files successfully
                    </p>
                  </div>
                )}
                {uploadMutation.isPending && (
                  <div className="mt-2 flex items-center text-sm text-blue-600">
                    <LoadingSpinner className="w-4 h-4 mr-2" />
                    Uploading files...
                  </div>
                )}
              </div>

              {/* Repository URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Repository URL
                </label>
                <input
                  type="url"
                  {...register('repo_url', {
                    required: 'Repository URL is required',
                    pattern: {
                      value: /^https?:\/\/.+/,
                      message: 'Please enter a valid URL'
                    }
                  })}
                  className="form-input"
                  placeholder="https://github.com/user/repo"
                />
                {errors.repo_url && (
                  <p className="mt-1 text-sm text-red-600">{errors.repo_url.message}</p>
                )}
              </div>

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

              {/* Stack Detection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Technology Stack
                </label>
                <select
                  {...register('stack')}
                  className="form-select"
                >
                  <option value="auto-detect">Auto-detect from repository</option>
                  <option value="node">Node.js</option>
                  <option value="python">Python</option>
                  <option value="java">Java</option>
                  <option value="golang">Go</option>
                  <option value="dotnet">.NET</option>
                  <option value="static">Static Site</option>
                </select>
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

              {/* Organization Standards */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization Standards
                </label>
                <select
                  {...register('org_standards')}
                  className="form-select"
                >
                  <option value="default">Default Standards</option>
                  <option value="enterprise">Enterprise Security</option>
                  <option value="startup">Startup Minimal</option>
                  <option value="fintech">Financial Services</option>
                  <option value="healthcare">Healthcare Compliance</option>
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
                    Generating Pipeline...
                  </div>
                ) : (
                  'Generate CI/CD Pipeline'
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
                    Pipeline Generation Results
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

                {/* Stack Detection Results */}
                {result.detected_stack && (
                  <div className="bg-blue-50 rounded-lg p-4 mb-4">
                    <h3 className="font-medium text-blue-900 mb-2">Detected Technology Stack</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-blue-700 font-medium">Language:</span>{' '}
                        <span className="text-blue-600">{result.detected_stack.language}</span>
                      </div>
                      {result.detected_stack.framework && (
                        <div>
                          <span className="text-blue-700 font-medium">Framework:</span>{' '}
                          <span className="text-blue-600">{result.detected_stack.framework}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-blue-700 font-medium">Containerized:</span>{' '}
                        <span className="text-blue-600">
                          {result.detected_stack.dockerfile ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div>
                        <span className="text-blue-700 font-medium">Package Manager:</span>{' '}
                        <span className="text-blue-600">{result.detected_stack.package_manager}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {result.pipeline_files && (
                    <div className="bg-green-50 rounded-lg p-4">
                      <h3 className="font-medium text-green-900 mb-2">Pipeline Files</h3>
                      <div className="text-2xl font-bold text-green-700">
                        {Object.keys(result.pipeline_files).length}
                      </div>
                      <div className="text-sm text-green-600">Files generated</div>
                    </div>
                  )}

                  {result.security_scan && (
                    <div className="bg-purple-50 rounded-lg p-4">
                      <h3 className="font-medium text-purple-900 mb-2">Security Scans</h3>
                      <div className="text-2xl font-bold text-purple-700">
                        {result.security_scan.enabled_scans?.length || 0}
                      </div>
                      <div className="text-sm text-purple-600">Security checks enabled</div>
                    </div>
                  )}

                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900 mb-2">Citations</h3>
                    <div className="text-2xl font-bold text-gray-700">
                      {result.citations.length}
                    </div>
                    <div className="text-sm text-gray-600">KB sources referenced</div>
                  </div>
                </div>

                {/* File Preview Toggle */}
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={() => {
                      console.log('Toggle clicked, current state:', showFilePreview)
                      console.log('Pipeline files:', result.pipeline_files)
                      setShowFilePreview(!showFilePreview)
                    }}
                    className="btn-secondary"
                  >
                    <EyeIcon className="w-4 h-4 mr-2" />
                    {showFilePreview ? 'Hide' : 'Show'} Generated Files
                  </button>
                </div>
              </div>

              {/* File Preview with Edit/Copy */}
              {showFilePreview && result?.pipeline_files ? (
                <div className="card p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Generated Pipeline Files
                  </h3>

                  <div className="space-y-3">
                    {result.pipeline_files && typeof result.pipeline_files === 'object' && Object.entries(result.pipeline_files).map(([path, content]) => (
                      <div key={path} className="border rounded-lg">
                        <div className="p-3 bg-gray-50 flex items-center justify-between">
                          <div className="flex items-center">
                            <CodeBracketIcon className="w-4 h-4 mr-2 text-gray-500" />
                            <span className="font-mono text-sm font-medium">{path}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <button
                              type="button"
                              onClick={() => handleCopyFile(content)}
                              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
                              title="Copy to clipboard"
                            >
                              <DocumentDuplicateIcon className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleEditFile(path, content)}
                              className="p-1 text-gray-500 hover:text-gray-700 transition-colors"
                              title="Edit file"
                            >
                              <PencilIcon className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        {editingFile === path ? (
                          <div className="border-t">
                            <div className="p-4">
                              <div className="mb-3 flex items-center justify-between">
                                <h4 className="font-medium text-gray-900">
                                  Editing: {path}
                                </h4>
                                {hasUnsavedChanges && (
                                  <span className="text-amber-600 text-sm flex items-center">
                                    <ArrowPathIcon className="w-3 h-3 mr-1" />
                                    Unsaved changes
                                  </span>
                                )}
                              </div>
                              <CodeEditor
                                value={editedContent}
                                onChange={handleContentChange}
                                language="yaml"
                                height={400}
                              />
                              <div className="mt-3 flex items-center space-x-2">
                                <button
                                  type="button"
                                  onClick={handleSaveFile}
                                  disabled={saveFileMutation.isPending}
                                  className="btn-primary text-sm py-1 px-3 disabled:opacity-50"
                                >
                                  {saveFileMutation.isPending ? (
                                    <div className="flex items-center">
                                      <LoadingSpinner className="w-3 h-3 mr-1" />
                                      Saving...
                                    </div>
                                  ) : (
                                    <div className="flex items-center">
                                      <CheckIcon className="w-3 h-3 mr-1" />
                                      Save Changes
                                    </div>
                                  )}
                                </button>
                                <button
                                  type="button"
                                  onClick={handleCancelEdit}
                                  className="btn-secondary text-sm py-1 px-3"
                                >
                                  Cancel
                                </button>
                                {hasUnsavedChanges && (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (editingFile) {
                                        const original = result?.pipeline_files?.[editingFile] || ''
                                        setEditedContent(original)
                                        setHasUnsavedChanges(false)
                                      }
                                    }}
                                    className="text-gray-500 hover:text-gray-700 text-sm"
                                  >
                                    Reset to original
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <pre className="p-4 text-xs overflow-x-auto bg-gray-900 text-gray-100 border-t">
                            {content}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Security Scan Results */}
              {result.security_scan && (
                <div className="card p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <BugAntIcon className="w-5 h-5 mr-2" />
                    Security Scan Configuration
                  </h2>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <h4 className="font-medium text-purple-900 mb-2">Enabled Security Checks</h4>
                    <ul className="text-sm text-purple-700 space-y-1">
                      {result.security_scan.enabled_scans?.map((scan: string, idx: number) => (
                        <li key={idx} className="flex items-center">
                          <CheckCircleIcon className="w-4 h-4 mr-2 text-purple-600" />
                          {scan}
                        </li>
                      ))}
                    </ul>
                  </div>
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
                    type="button"
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
                      'Create PR with Pipeline Files'
                    )}
                  </button>
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center">
                      <CheckCircleIcon className="w-5 h-5 text-green-400 mr-2" />
                      <span className="text-green-800 font-medium">
                        PR created successfully with pipeline configuration
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
              <RocketLaunchIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Ready to Generate Pipeline
              </h3>
              <p className="text-gray-500">
                Configure your pipeline settings and click "Generate CI/CD Pipeline" to get started.
              </p>
            </div>
          )}
        </div>
        </div>
      </div>
    </>
  )
}