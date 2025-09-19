import React, { useRef, useEffect } from 'react'
import Editor, { OnMount } from '@monaco-editor/react'
import * as monaco from 'monaco-editor'

interface CodeEditorProps {
  value: string
  onChange: (value: string) => void
  language?: string
  height?: string | number
  readOnly?: boolean
  theme?: string
}

export default function CodeEditor({
  value,
  onChange,
  language = 'yaml',
  height = 300,
  readOnly = false,
  theme = 'vs-dark'
}: CodeEditorProps) {
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor

    // Configure YAML language support
    monaco.languages.registerDocumentFormattingEditProvider('yaml', {
      provideDocumentFormattingEdits: () => {
        return []
      }
    })

    // Configure editor options
    editor.updateOptions({
      fontSize: 12,
      fontFamily: 'JetBrains Mono, Monaco, Consolas, monospace',
      lineNumbers: 'on',
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      wordWrap: 'on',
      tabSize: 2,
      insertSpaces: true,
      automaticLayout: true,
      contextmenu: true,
      selectOnLineNumbers: true,
      roundedSelection: false,
      readOnly: readOnly,
      cursorStyle: 'line',
      smoothScrolling: true,
      mouseWheelZoom: true,
      folding: true,
      foldingStrategy: 'indentation',
      showFoldingControls: 'always',
      bracketPairColorization: {
        enabled: true
      }
    })

    // Auto-save on content change
    editor.onDidChangeModelContent(() => {
      const content = editor.getValue()
      onChange(content)

      // Auto-save to localStorage
      const storageKey = `fops_editor_${Date.now()}`
      localStorage.setItem('fops_current_edit', JSON.stringify({
        content,
        timestamp: Date.now(),
        language
      }))
    })
  }

  useEffect(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem('fops_current_edit')
    if (saved && !value) {
      try {
        const { content } = JSON.parse(saved)
        if (content && editorRef.current) {
          editorRef.current.setValue(content)
        }
      } catch (e) {
        console.warn('Failed to load saved content:', e)
      }
    }
  }, [])

  const getLanguageFromFilename = (filename: string): string => {
    if (filename.endsWith('.yml') || filename.endsWith('.yaml')) return 'yaml'
    if (filename.endsWith('.json')) return 'json'
    if (filename.endsWith('.js') || filename.endsWith('.ts')) return 'typescript'
    if (filename.endsWith('.dockerfile') || filename.toLowerCase().includes('dockerfile')) return 'dockerfile'
    if (filename.endsWith('.sh')) return 'shell'
    if (filename.endsWith('.md')) return 'markdown'
    return 'yaml' // Default to YAML for CI/CD files
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <Editor
        height={height}
        defaultLanguage={language}
        language={language}
        value={value}
        theme={theme}
        onMount={handleEditorDidMount}
        options={{
          selectOnLineNumbers: true,
          automaticLayout: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          fontSize: 12,
          fontFamily: 'JetBrains Mono, Monaco, Consolas, monospace',
          lineNumbers: 'on',
          readOnly: readOnly
        }}
      />
    </div>
  )
}