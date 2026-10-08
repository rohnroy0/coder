import React, { useState, useRef, useEffect } from 'react';
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
  disablePaste = false,
}) => {
  const meta = LANGUAGE_META[language] || LANGUAGE_META.python;
  const template = STARTER_TEMPLATES[language] || STARTER_TEMPLATES.python;

  const [pasteBlockedFlash, setPasteBlockedFlash] = useState(false);
  // The paste listener is attached once at editor mount, but `disablePaste` can
  // flip after that (it loads async) - a ref keeps the listener reading the
  // current value instead of closing over whatever it was at mount time.
  const disablePasteRef = useRef(disablePaste);
  useEffect(() => {
    disablePasteRef.current = disablePaste;
  }, [disablePaste]);

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
    // Primary: Monaco/VS Code's editor core often handles Ctrl+V by reading the
    // clipboard directly via the async Clipboard API in response to the
    // keydown - it does NOT always go through a native browser "paste" DOM
    // event, so a plain event listener alone can't reliably catch it. Binding
    // our own command to the same keystroke on this editor instance overrides
    // Monaco's built-in paste action entirely.
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyV, () => {
      if (disablePasteRef.current) {
        flashPasteBlocked();
        return;
      }
      editor.trigger('keyboard', 'editor.action.clipboardPasteAction', null);
    });

    // Fallback: still block the native browser paste event too, in case it's
    // triggered some other way (browser Edit menu, middle-click paste, etc.)
    const domNode = editor.getDomNode();
    domNode?.addEventListener(
      'paste',
      (e) => {
        if (disablePasteRef.current) {
          e.preventDefault();
          e.stopPropagation();
          flashPasteBlocked();
        }
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
          {disablePaste && (
            <span
              className="flex items-center space-x-1 bg-rose-950/60 text-rose-300 border border-rose-800/60 px-2 py-0.5 rounded-full text-[10px] font-semibold"
              title="Your teacher has disabled pasting into this editor for this classroom"
            >
              <ClipboardX className="w-3 h-3" />
              <span>Paste Disabled</span>
            </span>
          )}
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
      <div className="flex-1 min-h-[300px] relative">
        {pasteBlockedFlash && (
          <div className="absolute top-2 right-2 z-10 flex items-center space-x-1.5 bg-rose-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-lg">
            <ClipboardX className="w-3.5 h-3.5" />
            <span>Pasting is disabled for this classroom</span>
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
