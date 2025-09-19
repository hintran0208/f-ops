import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  CogIcon,
  CloudIcon,
  BookOpenIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface LayoutProps {
  children: React.ReactNode
}

const navigation = [
  { name: 'Pipeline Agent', href: '/pipeline', icon: RocketLaunchIcon },
  { name: 'Infrastructure Agent', href: '/infrastructure', icon: CloudIcon },
  { name: 'Knowledge Base', href: '/kb', icon: BookOpenIcon },
]

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              {/* Logo */}
              <div className="flex-shrink-0 flex items-center">
                <Link to="/" className="flex items-center">
                  <CogIcon className="h-8 w-8 text-f-ops-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">F-Ops</span>
                </Link>
              </div>

              {/* Navigation Links */}
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href === '/pipeline' && location.pathname === '/')

                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={clsx(
                        'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors duration-200',
                        isActive
                          ? 'border-f-ops-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      )}
                    >
                      <item.icon className="w-4 h-4 mr-2" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            </div>

            {/* Right side */}
            <div className="flex items-center">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Operational</span>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href ||
                (item.href === '/pipeline' && location.pathname === '/')

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    'block pl-3 pr-4 py-2 border-l-4 text-base font-medium transition-colors duration-200',
                    isActive
                      ? 'bg-f-ops-50 border-f-ops-500 text-f-ops-700'
                      : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50 hover:border-gray-300'
                  )}
                >
                  <div className="flex items-center">
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <div>
              F-Ops v0.1.0 — Local-first DevOps Assistant
            </div>
            <div>
              Proposal-only operations • No direct execution
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}