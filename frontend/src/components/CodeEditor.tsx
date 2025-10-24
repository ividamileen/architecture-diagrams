import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Save, Loader2 } from 'lucide-react';

interface CodeEditorProps {
  code: string;
  language: string;
  onSave: (code: string) => void;
  loading?: boolean;
}

export function CodeEditor({ code, language, onSave, loading = false }: CodeEditorProps) {
  const [editorValue, setEditorValue] = useState(code);
  const [hasChanges, setHasChanges] = useState(false);

  const handleEditorChange = (value: string | undefined) => {
    setEditorValue(value || '');
    setHasChanges(value !== code);
  };

  const handleSave = () => {
    onSave(editorValue);
    setHasChanges(false);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-2 border-b border-gray-200 bg-gray-50">
        <span className="text-sm text-gray-600">
          {hasChanges && <span className="text-orange-500 mr-2">● Unsaved changes</span>}
        </span>
        <button
          onClick={handleSave}
          disabled={!hasChanges || loading}
          className="px-4 py-1.5 text-sm bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Saving...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Save</span>
            </>
          )}
        </button>
      </div>
      <div className="flex-1">
        <Editor
          height="100%"
          language={language}
          value={editorValue}
          onChange={handleEditorChange}
          theme="vs-light"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}
