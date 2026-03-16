"use client";

import { useCallback, useState } from "react";
import Editor from "@monaco-editor/react";
import { api, ApiError } from "@/lib/api";

type Props = {
  gameId: string;
  initialCode: string;
  version: number;
  readOnly?: boolean;
  onSaved?: (newVersion: number) => void;
};

export default function GameCodeEditor({
  gameId,
  initialCode,
  version,
  readOnly = false,
  onSaved,
}: Props) {
  const [code, setCode] = useState(initialCode);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const isDirty = code !== initialCode;

  const handleSave = useCallback(async () => {
    if (!isDirty || saving) return;
    setSaving(true);
    setMessage(null);

    try {
      const result = await api.games.createVersion(gameId, code);
      setMessage({
        type: "success",
        text: `Saved as v${result.version}. Validation ${result.blueprint_json ? "queued" : "complete"}.`,
      });
      onSaved?.(result.version);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Failed to save.";
      setMessage({ type: "error", text: msg });
    } finally {
      setSaving(false);
    }
  }, [code, isDirty, saving, gameId, onSaved]);

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400 font-mono">
            main.py (v{version})
          </span>
          {isDirty && (
            <span className="text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded px-2 py-0.5">
              Unsaved changes
            </span>
          )}
        </div>
        {!readOnly && (
          <button
            onClick={handleSave}
            disabled={!isDirty || saving}
            className="rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? "Saving..." : "Save as New Version"}
          </button>
        )}
      </div>

      {/* Status message */}
      {message && (
        <div
          className={`rounded-lg px-4 py-2 text-sm ${
            message.type === "success"
              ? "bg-green-500/10 border border-green-500/20 text-green-400"
              : "bg-red-500/10 border border-red-500/20 text-red-400"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Monaco Editor */}
      <div className="rounded-lg border border-gray-800 overflow-hidden">
        <Editor
          height="500px"
          defaultLanguage="python"
          value={code}
          onChange={(value) => setCode(value || "")}
          theme="vs-dark"
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            padding: { top: 12 },
            tabSize: 4,
          }}
        />
      </div>
    </div>
  );
}
