import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  BookOpenIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  LinkIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  CloudArrowUpIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { kbApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

interface ConnectFormData {
  uri: string
  type: string
  description?: string
}

interface SearchFormData {
  query: string
  limit: number
}

interface ConnectResult {
  success: boolean
  message: string
  documents_indexed?: number
  chunks_created?: number
  processing_time?: number
}

interface SearchResult {
  results: Array<{
    content: string
    source: string
    score: number
    metadata: Record<string, any>
  }>
  total: number
  query: string
  processing_time: number
}

export default function KBConnectModule() {
  const [connectResult, setConnectResult] = useState<ConnectResult | null>(null)
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null)
  const [activeTab, setActiveTab] = useState<'connect' | 'search'>('connect')

  const { register: registerConnect, handleSubmit: handleConnectSubmit, formState: { errors: connectErrors } } = useForm<ConnectFormData>({
    defaultValues: {
      uri: '',
      type: 'auto-detect',
      description: ''
    }
  })

  const { register: registerSearch, handleSubmit: handleSearchSubmit, formState: { errors: searchErrors } } = useForm<SearchFormData>({
    defaultValues: {
      query: '',
      limit: 10
    }
  })

  // Connect mutation
  const connectMutation = useMutation({
    mutationFn: (data: ConnectFormData) => kbApi.connect(data.uri),
    onSuccess: (response) => {
      setConnectResult(response)
    }
  })

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: (data: SearchFormData) => kbApi.search(data.query),
    onSuccess: (response) => {
      setSearchResult(response)
    }
  })

  const onConnectSubmit = (data: ConnectFormData) => {
    connectMutation.mutate(data)
  }

  const onSearchSubmit = (data: SearchFormData) => {
    searchMutation.mutate(data)
  }

  return (
    <div className="px-4 sm:px-0">
      <div className="mb-8">
        <div className="flex items-center">
          <BookOpenIcon className="h-8 w-8 text-f-ops-600 mr-3" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
            <p className="mt-2 text-gray-600">
              Connect external knowledge sources and search indexed content
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'connect', name: 'Connect Sources', icon: LinkIcon },
            { id: 'search', name: 'Search Knowledge', icon: MagnifyingGlassIcon }
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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Panel */}
        <div className="lg:col-span-4">
          {activeTab === 'connect' && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Connect Knowledge Source
              </h2>

              <form onSubmit={handleConnectSubmit(onConnectSubmit)} className="space-y-4">
                {/* URI Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source URI
                  </label>
                  <input
                    type="url"
                    {...registerConnect('uri', {
                      required: 'URI is required',
                      pattern: {
                        value: /^https?:\/\/.+/,
                        message: 'Please enter a valid URL'
                      }
                    })}
                    className="form-input"
                    placeholder="https://docs.example.com or https://github.com/user/repo"
                  />
                  {connectErrors.uri && (
                    <p className="mt-1 text-sm text-red-600">{connectErrors.uri.message}</p>
                  )}
                </div>

                {/* Source Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source Type
                  </label>
                  <select
                    {...registerConnect('type')}
                    className="form-select"
                  >
                    <option value="auto-detect">Auto-detect</option>
                    <option value="documentation">Documentation Site</option>
                    <option value="github">GitHub Repository</option>
                    <option value="confluence">Confluence Space</option>
                    <option value="notion">Notion Pages</option>
                    <option value="wiki">Wiki</option>
                    <option value="blog">Blog/News</option>
                  </select>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    {...registerConnect('description')}
                    className="form-input"
                    rows={3}
                    placeholder="Brief description of this knowledge source..."
                  />
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={connectMutation.isPending}
                  className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {connectMutation.isPending ? (
                    <div className="flex items-center justify-center">
                      <LoadingSpinner className="w-4 h-4 mr-2" />
                      Connecting & Indexing...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center">
                      <CloudArrowUpIcon className="w-4 h-4 mr-2" />
                      Connect & Index
                    </div>
                  )}
                </button>
              </form>

              {/* Connection Tips */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-2">Supported Sources</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• GitHub repositories (README, docs, wikis)</li>
                  <li>• Documentation sites (GitBook, Notion, etc.)</li>
                  <li>• Confluence spaces</li>
                  <li>• Wiki pages and blogs</li>
                  <li>• Any publicly accessible web content</li>
                </ul>
              </div>
            </div>
          )}

          {activeTab === 'search' && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Search Knowledge Base
              </h2>

              <form onSubmit={handleSearchSubmit(onSearchSubmit)} className="space-y-4">
                {/* Search Query */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Query
                  </label>
                  <textarea
                    {...registerSearch('query', {
                      required: 'Search query is required',
                      minLength: {
                        value: 3,
                        message: 'Query must be at least 3 characters'
                      }
                    })}
                    className="form-input"
                    rows={3}
                    placeholder="How to configure CI/CD for Node.js applications?"
                  />
                  {searchErrors.query && (
                    <p className="mt-1 text-sm text-red-600">{searchErrors.query.message}</p>
                  )}
                </div>

                {/* Result Limit */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Results
                  </label>
                  <select
                    {...registerSearch('limit')}
                    className="form-select"
                  >
                    <option value={5}>5 results</option>
                    <option value={10}>10 results</option>
                    <option value={20}>20 results</option>
                    <option value={50}>50 results</option>
                  </select>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={searchMutation.isPending}
                  className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {searchMutation.isPending ? (
                    <div className="flex items-center justify-center">
                      <LoadingSpinner className="w-4 h-4 mr-2" />
                      Searching...
                    </div>
                  ) : (
                    <div className="flex items-center justify-center">
                      <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
                      Search Knowledge Base
                    </div>
                  )}
                </button>
              </form>

              {/* Search Tips */}
              <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
                <h4 className="font-medium text-green-900 mb-2">Search Tips</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Use specific technical terms and concepts</li>
                  <li>• Ask complete questions for better results</li>
                  <li>• Include context about your use case</li>
                  <li>• Try different phrasings if needed</li>
                </ul>
              </div>
            </div>
          )}
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8">
          {activeTab === 'connect' && connectResult && (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Connection Results
                </h2>
                <div className="flex items-center space-x-2">
                  {connectResult.success ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircleIcon className="w-5 h-5 text-red-500" />
                  )}
                  <span className={`text-sm font-medium ${
                    connectResult.success ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {connectResult.success ? 'Success' : 'Failed'}
                  </span>
                </div>
              </div>

              <p className="text-gray-600 mb-6">{connectResult.message}</p>

              {connectResult.success && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-900">
                      {connectResult.documents_indexed || 0}
                    </div>
                    <div className="text-sm text-blue-700">Documents Indexed</div>
                  </div>

                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-900">
                      {connectResult.chunks_created || 0}
                    </div>
                    <div className="text-sm text-green-700">Content Chunks</div>
                  </div>

                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-900">
                      {connectResult.processing_time || 0}s
                    </div>
                    <div className="text-sm text-purple-700">Processing Time</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'search' && searchResult && (
            <div className="space-y-6">
              {/* Search Summary */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Search Results
                  </h2>
                  <div className="text-sm text-gray-500">
                    {searchResult.total} results in {searchResult.processing_time}ms
                  </div>
                </div>
                <p className="text-gray-600">
                  Results for: <span className="font-medium">"{searchResult.query}"</span>
                </p>
              </div>

              {/* Search Results */}
              <div className="space-y-4">
                {searchResult.results.map((result, idx) => (
                  <div key={idx} className="card p-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <DocumentTextIcon className="w-5 h-5 text-gray-400" />
                        <div className="font-medium text-gray-900">
                          {result.source}
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        Score: {(result.score * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div className="text-gray-700 mb-3">
                      {result.content}
                    </div>

                    {result.metadata && Object.keys(result.metadata).length > 0 && (
                      <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
                        <div className="font-medium text-gray-900 mb-2">Metadata</div>
                        <div className="space-y-1">
                          {Object.entries(result.metadata).map(([key, value]) => (
                            <div key={key} className="text-gray-600">
                              <span className="font-medium">{key}:</span> {String(value)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!connectResult && activeTab === 'connect' && (
            <div className="card p-12 text-center">
              <CloudArrowUpIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Ready to Connect Knowledge Sources
              </h3>
              <p className="text-gray-500">
                Enter a URL to crawl and index external knowledge sources into your knowledge base.
              </p>
            </div>
          )}

          {!searchResult && activeTab === 'search' && (
            <div className="card p-12 text-center">
              <MagnifyingGlassIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Ready to Search Knowledge Base
              </h3>
              <p className="text-gray-500">
                Enter your search query to find relevant information from indexed knowledge sources.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}