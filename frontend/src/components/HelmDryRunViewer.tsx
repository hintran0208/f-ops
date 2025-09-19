import React, { useState } from 'react'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  DocumentTextIcon,
  CubeIcon,
  ClockIcon,
  BugAntIcon,
  CodeBracketIcon
} from '@heroicons/react/24/outline'

interface HelmManifest {
  apiVersion: string
  kind: string
  metadata: {
    name: string
    namespace?: string
    labels?: Record<string, string>
    annotations?: Record<string, string>
  }
  spec?: any
  data?: any
  stringData?: any
}

interface HelmLintResult {
  passed: boolean
  errors: string[]
  warnings: string[]
  info: string[]
}

interface HelmDryRun {
  status: string
  manifests: HelmManifest[]
  notes?: string
  lint: HelmLintResult
  hooks: HelmManifest[]
  timestamp: string
  chart_name: string
  chart_version: string
  release_name: string
  namespace: string
  values_used: any
}

interface HelmDryRunViewerProps {
  dryRun: HelmDryRun
}

export default function HelmDryRunViewer({ dryRun }: HelmDryRunViewerProps) {
  const [expandedManifests, setExpandedManifests] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<'overview' | 'manifests' | 'lint' | 'values'>('overview')

  const toggleManifest = (key: string) => {
    const newExpanded = new Set(expandedManifests)
    if (newExpanded.has(key)) {
      newExpanded.delete(key)
    } else {
      newExpanded.add(key)
    }
    setExpandedManifests(newExpanded)
  }

  const getKindIcon = (kind: string) => {
    const kindIcons: Record<string, any> = {
      'Deployment': CubeIcon,
      'Service': DocumentTextIcon,
      'ConfigMap': CodeBracketIcon,
      'Secret': CodeBracketIcon,
      'Ingress': DocumentTextIcon,
      'ServiceAccount': DocumentTextIcon,
      'Pod': CubeIcon,
      'Job': ClockIcon,
      'CronJob': ClockIcon
    }
    const Icon = kindIcons[kind] || CubeIcon
    return <Icon className="w-4 h-4" />
  }

  const getKindColor = (kind: string) => {
    const kindColors: Record<string, string> = {
      'Deployment': 'text-blue-600 bg-blue-50 border-blue-200',
      'Service': 'text-green-600 bg-green-50 border-green-200',
      'ConfigMap': 'text-purple-600 bg-purple-50 border-purple-200',
      'Secret': 'text-red-600 bg-red-50 border-red-200',
      'Ingress': 'text-yellow-600 bg-yellow-50 border-yellow-200',
      'ServiceAccount': 'text-gray-600 bg-gray-50 border-gray-200',
      'Pod': 'text-indigo-600 bg-indigo-50 border-indigo-200',
      'Job': 'text-orange-600 bg-orange-50 border-orange-200',
      'CronJob': 'text-pink-600 bg-pink-50 border-pink-200'
    }
    return kindColors[kind] || 'text-gray-600 bg-gray-50 border-gray-200'
  }

  const formatYaml = (obj: any): string => {
    return JSON.stringify(obj, null, 2)
  }

  const groupManifestsByKind = (manifests: HelmManifest[]) => {
    return manifests.reduce((groups, manifest) => {
      const kind = manifest.kind
      if (!groups[kind]) {
        groups[kind] = []
      }
      groups[kind].push(manifest)
      return groups
    }, {} as Record<string, HelmManifest[]>)
  }

  const manifestGroups = groupManifestsByKind(dryRun.manifests || [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {dryRun.status === 'success' ? (
            <CheckCircleIcon className="w-6 h-6 text-green-500" />
          ) : (
            <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Helm Dry-Run Results
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <ClockIcon className="w-4 h-4 mr-1" />
                {new Date(dryRun.timestamp).toLocaleString()}
              </span>
              <span>{dryRun.chart_name} v{dryRun.chart_version}</span>
              <span>→ {dryRun.release_name}/{dryRun.namespace}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center">
            <CubeIcon className="w-5 h-5 text-blue-600 mr-2" />
            <div>
              <div className="text-2xl font-bold text-blue-900">
                {dryRun.manifests?.length || 0}
              </div>
              <div className="text-sm text-blue-700">Manifests</div>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="flex items-center">
            <DocumentTextIcon className="w-5 h-5 text-purple-600 mr-2" />
            <div>
              <div className="text-2xl font-bold text-purple-900">
                {Object.keys(manifestGroups).length}
              </div>
              <div className="text-sm text-purple-700">Resource Types</div>
            </div>
          </div>
        </div>

        <div className={`rounded-lg p-4 border ${
          dryRun.lint?.passed
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center">
            {dryRun.lint?.passed ? (
              <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <XCircleIcon className="w-5 h-5 text-red-600 mr-2" />
            )}
            <div>
              <div className={`text-2xl font-bold ${
                dryRun.lint?.passed ? 'text-green-900' : 'text-red-900'
              }`}>
                {dryRun.lint?.passed ? 'PASS' : 'FAIL'}
              </div>
              <div className={`text-sm ${
                dryRun.lint?.passed ? 'text-green-700' : 'text-red-700'
              }`}>
                Lint Check
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="flex items-center">
            <ClockIcon className="w-5 h-5 text-gray-600 mr-2" />
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {dryRun.hooks?.length || 0}
              </div>
              <div className="text-sm text-gray-700">Hooks</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: DocumentTextIcon },
            { id: 'manifests', name: 'Manifests', icon: CubeIcon },
            { id: 'lint', name: 'Lint Results', icon: BugAntIcon },
            { id: 'values', name: 'Values', icon: CodeBracketIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-f-ops-500 text-f-ops-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Resource Summary */}
          <div>
            <h4 className="text-lg font-medium text-gray-900 mb-4">Resource Summary</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(manifestGroups).map(([kind, manifests]) => (
                <div key={kind} className={`rounded-lg p-3 border ${getKindColor(kind)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getKindIcon(kind)}
                      <span className="font-medium">{kind}</span>
                    </div>
                    <span className="text-lg font-bold">{manifests.length}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Release Notes */}
          {dryRun.notes && (
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-4">Release Notes</h4>
              <div className="bg-gray-50 rounded-lg p-4 border">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {dryRun.notes}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'manifests' && (
        <div className="space-y-4">
          {Object.entries(manifestGroups).map(([kind, manifests]) => (
            <div key={kind}>
              <h4 className="text-lg font-medium text-gray-900 mb-3">
                {kind} ({manifests.length})
              </h4>
              <div className="space-y-2">
                {manifests.map((manifest, idx) => {
                  const manifestKey = `${kind}-${manifest.metadata.name}-${idx}`
                  return (
                    <div
                      key={manifestKey}
                      className={`border rounded-lg ${getKindColor(kind)}`}
                    >
                      <button
                        onClick={() => toggleManifest(manifestKey)}
                        className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-opacity-50"
                      >
                        <div className="flex items-center space-x-3">
                          {getKindIcon(kind)}
                          <div>
                            <div className="font-medium">
                              {manifest.metadata.name}
                            </div>
                            {manifest.metadata.namespace && (
                              <div className="text-sm opacity-75">
                                namespace: {manifest.metadata.namespace}
                              </div>
                            )}
                          </div>
                        </div>
                        {expandedManifests.has(manifestKey) ? (
                          <ChevronDownIcon className="w-5 h-5" />
                        ) : (
                          <ChevronRightIcon className="w-5 h-5" />
                        )}
                      </button>

                      {expandedManifests.has(manifestKey) && (
                        <div className="px-4 pb-3 border-t border-current border-opacity-20">
                          <pre className="mt-3 p-3 bg-white rounded text-xs font-mono overflow-x-auto">
                            {formatYaml(manifest)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'lint' && (
        <div className="space-y-4">
          {/* Lint Status */}
          <div className={`rounded-lg p-4 border ${
            dryRun.lint?.passed
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center">
              {dryRun.lint?.passed ? (
                <CheckCircleIcon className="w-6 h-6 text-green-600 mr-3" />
              ) : (
                <XCircleIcon className="w-6 h-6 text-red-600 mr-3" />
              )}
              <div>
                <h3 className={`text-lg font-semibold ${
                  dryRun.lint?.passed ? 'text-green-900' : 'text-red-900'
                }`}>
                  Lint Check {dryRun.lint?.passed ? 'Passed' : 'Failed'}
                </h3>
                <p className={`text-sm ${
                  dryRun.lint?.passed ? 'text-green-700' : 'text-red-700'
                }`}>
                  Chart validation and best practices check
                </p>
              </div>
            </div>
          </div>

          {/* Errors */}
          {dryRun.lint?.errors && dryRun.lint.errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="font-medium text-red-900 mb-3 flex items-center">
                <XCircleIcon className="w-5 h-5 mr-2" />
                Errors ({dryRun.lint.errors.length})
              </h4>
              <ul className="space-y-2">
                {dryRun.lint.errors.map((error, idx) => (
                  <li key={idx} className="text-sm text-red-700 bg-red-100 rounded p-2">
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {dryRun.lint?.warnings && dryRun.lint.warnings.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-medium text-yellow-900 mb-3 flex items-center">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                Warnings ({dryRun.lint.warnings.length})
              </h4>
              <ul className="space-y-2">
                {dryRun.lint.warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-yellow-700 bg-yellow-100 rounded p-2">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Info */}
          {dryRun.lint?.info && dryRun.lint.info.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-3 flex items-center">
                <DocumentTextIcon className="w-5 h-5 mr-2" />
                Information ({dryRun.lint.info.length})
              </h4>
              <ul className="space-y-2">
                {dryRun.lint.info.map((info, idx) => (
                  <li key={idx} className="text-sm text-blue-700 bg-blue-100 rounded p-2">
                    {info}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {activeTab === 'values' && (
        <div>
          <h4 className="text-lg font-medium text-gray-900 mb-4">Values Used</h4>
          <div className="bg-gray-50 rounded-lg p-4 border">
            <pre className="text-sm font-mono overflow-x-auto">
              {formatYaml(dryRun.values_used)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}