import React, { useState, useEffect } from 'react';
import { Download, Edit2, Loader2, RefreshCw, Code, FileText } from 'lucide-react';
import { diagramsApi } from '../services/api';
import type { Diagram } from '../types';
import { CodeEditor } from './CodeEditor';
import { ModificationInput } from './ModificationInput';

interface DiagramViewerProps {
  conversationId: number;
  currentDiagram: Diagram | null;
  onDiagramUpdated: (diagram: Diagram) => void;
}

export function DiagramViewer({
  conversationId,
  currentDiagram,
  onDiagramUpdated,
}: DiagramViewerProps) {
  const [activeTab, setActiveTab] = useState<'plantuml' | 'drawio'>('plantuml');
  const [viewMode, setViewMode] = useState<'preview' | 'code'>('preview');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const diagram = await diagramsApi.generate({
        conversation_id: conversationId,
        force_regenerate: true,
      });
      onDiagramUpdated(diagram);
    } catch (error) {
      console.error('Error generating diagram:', error);
    } finally {
      setGenerating(false);
    }
  };

  const handleCodeUpdate = async (code: string) => {
    if (!currentDiagram) return;

    setLoading(true);
    try {
      const updated = await diagramsApi.updateCode(
        currentDiagram.id,
        activeTab === 'plantuml' ? code : undefined,
        activeTab === 'drawio' ? code : undefined
      );
      onDiagramUpdated(updated);
    } catch (error) {
      console.error('Error updating code:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleModification = async (request: string) => {
    if (!currentDiagram) return;

    setLoading(true);
    try {
      const result = await diagramsApi.modify({
        diagram_id: currentDiagram.id,
        request,
        user_id: 'user-1',
      });

      if (result.success && result.new_diagram) {
        onDiagramUpdated(result.new_diagram);
      } else {
        console.error('Modification failed:', result.error_message);
      }
    } catch (error) {
      console.error('Error modifying diagram:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format: 'png' | 'plantuml' | 'drawio') => {
    if (!currentDiagram) return;

    if (format === 'png') {
      window.open(diagramsApi.getPng(currentDiagram.id), '_blank');
    } else if (format === 'plantuml') {
      const code = currentDiagram.plantuml_code || '';
      const blob = new Blob([code], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `diagram_${currentDiagram.id}.puml`;
      a.click();
    } else if (format === 'drawio') {
      const xml = currentDiagram.drawio_xml || '';
      const blob = new Blob([xml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `diagram_${currentDiagram.id}.drawio`;
      a.click();
    }
  };

  if (!currentDiagram && !generating) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <FileText className="w-16 h-16 text-gray-400 mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">No Diagram Yet</h3>
        <p className="text-gray-500 mb-6">
          Start a technical conversation or generate a diagram manually
        </p>
        <button
          onClick={handleGenerate}
          className="px-6 py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center space-x-2"
        >
          <RefreshCw className="w-5 h-5" />
          <span>Generate Diagram</span>
        </button>
      </div>
    );
  }

  if (generating) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Loader2 className="w-12 h-12 text-primary-500 animate-spin mb-4" />
        <p className="text-gray-600">Generating diagram...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Diagram v{currentDiagram?.version}
            </h3>
            <p className="text-sm text-gray-500">
              {currentDiagram?.components_count} components, {currentDiagram?.relationships_count}{' '}
              relationships
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center space-x-2"
            >
              <RefreshCw className={generating ? 'w-4 h-4 animate-spin' : 'w-4 h-4'} />
              <span>Regenerate</span>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('plantuml')}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'plantuml'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            PlantUML
          </button>
          <button
            onClick={() => setActiveTab('drawio')}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'drawio'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Draw.io
          </button>
        </div>

        {/* View mode toggle */}
        <div className="flex space-x-2 mt-4">
          <button
            onClick={() => setViewMode('preview')}
            className={`px-3 py-1.5 text-sm rounded-md ${
              viewMode === 'preview'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Preview
          </button>
          <button
            onClick={() => setViewMode('code')}
            className={`px-3 py-1.5 text-sm rounded-md flex items-center space-x-1 ${
              viewMode === 'code'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Code className="w-4 h-4" />
            <span>Code</span>
          </button>
        </div>

        {/* Download buttons */}
        <div className="flex space-x-2 mt-4">
          <button
            onClick={() => handleDownload('png')}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 flex items-center space-x-1"
          >
            <Download className="w-4 h-4" />
            <span>PNG</span>
          </button>
          <button
            onClick={() => handleDownload(activeTab)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 flex items-center space-x-1"
          >
            <Download className="w-4 h-4" />
            <span>{activeTab === 'plantuml' ? 'PlantUML' : 'Draw.io'}</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'preview' ? (
          <div className="h-full overflow-auto p-4 bg-gray-50">
            {currentDiagram?.png_url ? (
              <img
                src={currentDiagram.png_url}
                alt="Architecture Diagram"
                className="max-w-full h-auto mx-auto shadow-lg rounded-lg"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">No preview available</p>
              </div>
            )}
          </div>
        ) : (
          <CodeEditor
            code={
              activeTab === 'plantuml'
                ? currentDiagram?.plantuml_code || ''
                : currentDiagram?.drawio_xml || ''
            }
            language={activeTab === 'plantuml' ? 'plaintext' : 'xml'}
            onSave={handleCodeUpdate}
            loading={loading}
          />
        )}
      </div>

      {/* Modification Input */}
      <ModificationInput onSubmit={handleModification} loading={loading} />
    </div>
  );
}
