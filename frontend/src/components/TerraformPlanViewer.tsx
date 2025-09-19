import React, { useState } from 'react'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  DocumentTextIcon,
  ClockIcon,
  CubeIcon
} from '@heroicons/react/24/outline'

interface TerraformResource {
  address: string
  type: string
  name: string
  provider: string
  mode: string
  change: {
    actions: string[]
    before?: any
    after?: any
    after_unknown?: any
  }
}

interface TerraformPlan {
  format_version: string
  terraform_version: string
  planned_changes: TerraformResource[]
  configuration: any
  summary: {
    add: number
    change: number
    destroy: number
  }
  status: string
  timestamp: string
  warnings?: string[]
  errors?: string[]
  output_changes?: any
}

interface TerraformPlanViewerProps {
  plan: TerraformPlan
}

export default function TerraformPlanViewer({ plan }: TerraformPlanViewerProps) {
  const [expandedResources, setExpandedResources] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<'summary' | 'changes' | 'output'>('summary')

  const toggleResource = (address: string) => {
    const newExpanded = new Set(expandedResources)
    if (newExpanded.has(address)) {
      newExpanded.delete(address)
    } else {
      newExpanded.add(address)
    }
    setExpandedResources(newExpanded)
  }

  const getActionIcon = (actions: string[]) => {
    if (actions.includes('create')) {
      return <PlusIcon className="w-4 h-4 text-green-600" />
    }
    if (actions.includes('update')) {
      return <PencilIcon className="w-4 h-4 text-yellow-600" />
    }
    if (actions.includes('delete')) {
      return <TrashIcon className="w-4 h-4 text-red-600" />
    }
    return <CubeIcon className="w-4 h-4 text-gray-600" />
  }

  const getActionColor = (actions: string[]) => {
    if (actions.includes('create')) return 'text-green-700 bg-green-50 border-green-200'
    if (actions.includes('update')) return 'text-yellow-700 bg-yellow-50 border-yellow-200'
    if (actions.includes('delete')) return 'text-red-700 bg-red-50 border-red-200'
    return 'text-gray-700 bg-gray-50 border-gray-200'
  }

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'null'
    if (typeof value === 'boolean') return value.toString()
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    return String(value)
  }

  const renderResourceDiff = (resource: TerraformResource) => {
    const { before, after } = resource.change

    if (!before && !after) return null

    return (
      <div className="mt-2 p-3 bg-gray-50 rounded border text-xs">
        <div className="font-mono">
          {Object.entries(after || {}).map(([key, value]) => {
            const beforeValue = before?.[key]
            const isChanged = beforeValue !== value

            return (
              <div key={key} className={`py-1 ${isChanged ? 'bg-yellow-100' : ''}`}>
                <span className="text-gray-600">{key}:</span>
                {isChanged && beforeValue !== undefined && (
                  <div className="ml-4 text-red-600">
                    - {formatValue(beforeValue)}
                  </div>
                )}
                <div className={`ml-4 ${isChanged ? 'text-green-600' : 'text-gray-800'}`}>
                  {isChanged ? '+' : ' '} {formatValue(value)}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {plan.status === 'success' ? (
            <CheckCircleIcon className="w-6 h-6 text-green-500" />
          ) : (
            <ExclamationTriangleIcon className="w-6 h-6 text-red-500" />
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Terraform Plan Results
            </h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <ClockIcon className="w-4 h-4 mr-1" />
                {new Date(plan.timestamp).toLocaleString()}
              </span>
              <span>Terraform v{plan.terraform_version}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Warnings and Errors */}
      {plan.warnings && plan.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500 mr-2" />
            <h4 className="font-medium text-yellow-800">Warnings</h4>
          </div>
          <ul className="text-sm text-yellow-700 space-y-1">
            {plan.warnings.map((warning, idx) => (
              <li key={idx}>• {warning}</li>
            ))}
          </ul>
        </div>
      )}

      {plan.errors && plan.errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
            <h4 className="font-medium text-red-800">Errors</h4>
          </div>
          <ul className="text-sm text-red-700 space-y-1">
            {plan.errors.map((error, idx) => (
              <li key={idx}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'summary', name: 'Summary', icon: DocumentTextIcon },
            { id: 'changes', name: 'Resource Changes', icon: CubeIcon },
            { id: 'output', name: 'Output Changes', icon: ClockIcon }
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
      {activeTab === 'summary' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center">
              <PlusIcon className="w-5 h-5 text-green-600 mr-2" />
              <div>
                <div className="text-2xl font-bold text-green-900">{plan.summary.add}</div>
                <div className="text-sm text-green-700">Resources to Add</div>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div className="flex items-center">
              <PencilIcon className="w-5 h-5 text-yellow-600 mr-2" />
              <div>
                <div className="text-2xl font-bold text-yellow-900">{plan.summary.change}</div>
                <div className="text-sm text-yellow-700">Resources to Change</div>
              </div>
            </div>
          </div>

          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="flex items-center">
              <TrashIcon className="w-5 h-5 text-red-600 mr-2" />
              <div>
                <div className="text-2xl font-bold text-red-900">{plan.summary.destroy}</div>
                <div className="text-sm text-red-700">Resources to Destroy</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'changes' && (
        <div className="space-y-3">
          {plan.planned_changes && plan.planned_changes.length > 0 ? (
            plan.planned_changes.map((resource, idx) => (
              <div
                key={`${resource.address}-${idx}`}
                className={`border rounded-lg ${getActionColor(resource.change.actions)}`}
              >
                <button
                  onClick={() => toggleResource(resource.address)}
                  className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-opacity-50"
                >
                  <div className="flex items-center space-x-3">
                    {getActionIcon(resource.change.actions)}
                    <div>
                      <div className="font-medium">{resource.address}</div>
                      <div className="text-sm opacity-75">
                        {resource.type} • {resource.change.actions.join(', ')}
                      </div>
                    </div>
                  </div>
                  {expandedResources.has(resource.address) ? (
                    <ChevronDownIcon className="w-5 h-5" />
                  ) : (
                    <ChevronRightIcon className="w-5 h-5" />
                  )}
                </button>

                {expandedResources.has(resource.address) && (
                  <div className="px-4 pb-3 border-t border-current border-opacity-20">
                    {renderResourceDiff(resource)}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              No resource changes planned
            </div>
          )}
        </div>
      )}

      {activeTab === 'output' && (
        <div className="space-y-3">
          {plan.output_changes && Object.keys(plan.output_changes).length > 0 ? (
            Object.entries(plan.output_changes).map(([key, change]: [string, any]) => (
              <div key={key} className="border rounded-lg p-4">
                <div className="font-medium text-gray-900 mb-2">{key}</div>
                <div className="bg-gray-50 rounded p-3 font-mono text-sm">
                  {change.before !== undefined && (
                    <div className="text-red-600 mb-1">
                      - {formatValue(change.before)}
                    </div>
                  )}
                  <div className="text-green-600">
                    + {formatValue(change.after)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              No output changes planned
            </div>
          )}
        </div>
      )}
    </div>
  )
}