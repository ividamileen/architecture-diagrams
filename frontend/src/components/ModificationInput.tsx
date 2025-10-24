import React, { useState } from 'react';
import { Wand2, Loader2 } from 'lucide-react';

interface ModificationInputProps {
  onSubmit: (request: string) => void;
  loading?: boolean;
}

export function ModificationInput({ onSubmit, loading = false }: ModificationInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim() || loading) return;
    onSubmit(input.trim());
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      <div className="flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Request diagram modifications (e.g., 'Add Redis cache between API and database')"
          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          disabled={loading}
        />
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || loading}
          className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {loading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              <Wand2 className="w-5 h-5" />
              <span>Modify</span>
            </>
          )}
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Describe how you want to modify the diagram using natural language
      </p>
    </div>
  );
}
