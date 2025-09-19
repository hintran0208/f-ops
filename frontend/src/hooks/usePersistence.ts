import { useState, useEffect, useCallback } from 'react'

interface PersistenceData {
  result: any
  uploadedFiles: any[]
  editingFile: string | null
  editedContent: string
  formData: any
  timestamp: number
}

const STORAGE_KEY = 'fops_pipeline_state'
const AUTO_SAVE_INTERVAL = 5000 // 5 seconds

export function usePersistence() {
  const [isRestored, setIsRestored] = useState(false)

  const saveState = useCallback((data: Partial<PersistenceData>) => {
    try {
      const existing = localStorage.getItem(STORAGE_KEY)
      const current = existing ? JSON.parse(existing) : {}

      const updated = {
        ...current,
        ...data,
        timestamp: Date.now()
      }

      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    } catch (error) {
      console.warn('Failed to save state:', error)
    }
  }, [])

  const loadState = useCallback((): PersistenceData | null => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (!saved) return null

      const data = JSON.parse(saved)

      // Only restore if saved within last 24 hours
      const dayAgo = Date.now() - (24 * 60 * 60 * 1000)
      if (data.timestamp < dayAgo) {
        localStorage.removeItem(STORAGE_KEY)
        return null
      }

      return data
    } catch (error) {
      console.warn('Failed to load state:', error)
      return null
    }
  }, [])

  const clearState = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem('fops_current_edit')
  }, [])

  const autoSave = useCallback((data: Partial<PersistenceData>) => {
    // Debounced auto-save
    const timeoutId = setTimeout(() => {
      saveState(data)
    }, 1000)

    return () => clearTimeout(timeoutId)
  }, [saveState])

  // Save file content to specific key for recovery
  const saveFileContent = useCallback((filePath: string, content: string) => {
    try {
      const key = `fops_file_${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`
      localStorage.setItem(key, JSON.stringify({
        filePath,
        content,
        timestamp: Date.now()
      }))
    } catch (error) {
      console.warn('Failed to save file content:', error)
    }
  }, [])

  const loadFileContent = useCallback((filePath: string): string | null => {
    try {
      const key = `fops_file_${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`
      const saved = localStorage.getItem(key)
      if (!saved) return null

      const data = JSON.parse(saved)

      // Only restore if saved within last hour
      const hourAgo = Date.now() - (60 * 60 * 1000)
      if (data.timestamp < hourAgo) {
        localStorage.removeItem(key)
        return null
      }

      return data.content
    } catch (error) {
      console.warn('Failed to load file content:', error)
      return null
    }
  }, [])

  const clearFileContent = useCallback((filePath: string) => {
    const key = `fops_file_${filePath.replace(/[^a-zA-Z0-9]/g, '_')}`
    localStorage.removeItem(key)
  }, [])

  return {
    saveState,
    loadState,
    clearState,
    autoSave,
    saveFileContent,
    loadFileContent,
    clearFileContent,
    isRestored
  }
}