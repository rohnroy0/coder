import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play, RotateCcw, Loader2, Code2, ClipboardX } from 'lucide-react';

const STARTER_TEMPLATES = {
  python: `# Write your Python solution below
import sys

def main():
    # Read input from standard input
    # Example: lines = sys.stdin.read().split()
    pass

if __name__ == "__main__":
    main()
`,
  c: `#include <stdio.h>

int main(void) {
    // Read input from stdin and print your answer to stdout
    return 0;
}
`,
  cpp: `#include <iostream>
using namespace std;

int main() {
    // Read input from stdin and print your answer to stdout
    return 0;
}
`,
};

const LANGUAGE_META = {
  python: { monacoLanguage: 'python', filename: 'solution.py', label: 'Python 3' },
  c: { monacoLanguage: 'c', filename: 'solution.c', label: 'C' },
  cpp: { monacoLanguage: 'cpp', filename: 'solution.cpp', label: 'C++' },
};

export const CodeEditor = ({
  code,
  onChange,
  onSubmit,
  onRun,
  loading = false,
  running = false,
  language = 'python',
}) => {
  const meta = LANGUAGE_META[language] || LANGUAGE_META.python;
  const template = STARTER_TEMPLATES[language] || STARTER_TEMPLATES.python;

  const [pasteBlockedFlash, setPasteBlockedFlash] = useState(false);

  const handleReset = () => {
    if (window.confirm('Reset editor to default template?')) {
      onChange(template);
    }
  };

  const flashPasteBlocked = () => {
    setPasteBlockedFlash(true);
    setTimeout(() => setPasteBlockedFlash(false), 2000);
  };

  const handleEditorMount = (editor, monaco) => {
    // Pasting into the code editor is always disabled (anti-cheating). The
    // Ctrl+V command intercepts the keystroke before Monaco's own handling
    // runs - necessary because Monaco doesn't bind Ctrl+V itself in the
    // browser, deferring to native paste instead. The native "paste" event
    // listener is a fallback for triggers that don't go through this
    // keybinding at all (browser Edit menu, right-click "Paste", middle-click
    // paste).
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyV, () => {
      flashPasteBlocked();
    });

    const domNode = editor.getDomNode();
    domNode?.addEventListener(
      'paste',
      (e) => {
        e.preventDefault();
        e.stopPropagation();
        flashPasteBlocked();
      },
      true
    );
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 rounded-xl overflow-hidden border border-slate-800 shadow-md">
      {/* Editor Header Bar */}
      <div className="bg-slate-950 px-4 py-3 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center space-x-2 text-slate-300 text-xs font-mono font-medium">
          <Code2 className="w-4 h-4 text-indigo-400" />
          <span>{meta.filename}</span>
          <span className="bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full text-[10px]">{meta.label}</span>
          <span
            className="flex items-center space-x-1 bg-rose-950/60 text-rose-300 border border-rose-800/60 px-2 py-0.5 rounded-full text-[10px] font-semibold"
            title="Pasting into the code editor is disabled"
          >
            <ClipboardX className="w-3 h-3" />
            <span>Paste Disabled</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleReset}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors flex items-center space-x-1 text-xs"
            title="Reset to starter template"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>

          <button
            onClick={onRun}
            disabled={loading || running}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 rounded-lg transition-colors shadow-sm border border-slate-700"
            title="Run your code against the sample test cases"
          >
            {running ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" />
                <span>Run</span>
              </>
            )}
          </button>

          <button
            onClick={onSubmit}
            disabled={loading || running}
            className="flex items-center space-x-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg transition-colors shadow-sm"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Evaluating...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Submit Solution</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1 min-h-0 relative">
        {pasteBlockedFlash && (
          <div className="absolute top-2 right-2 z-10 flex items-center space-x-1.5 bg-rose-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-lg">
            <ClipboardX className="w-3.5 h-3.5" />
            <span>Pasting is disabled</span>
          </div>
        )}
        <Editor
          height="100%"
          defaultLanguage={meta.monacoLanguage}
          language={meta.monacoLanguage}
          theme="vs-dark"
          value={code || template}
          onChange={(val) => onChange(val || '')}
          onMount={handleEditorMount}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            padding: { top: 12, bottom: 12 },
            lineNumbersMinChars: 3,
          }}
        />
      </div>
    </div>
  );
};

export default CodeEditor;
