import React, { useMemo, useState } from 'react';
import { ChevronRight, Copy, Download, FileJson, Search } from 'lucide-react';

interface JsonInspectorProps {
  title: string;
  data: unknown;
  filename: string;
}

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const JsonNode: React.FC<{ label: string; value: unknown; depth?: number; query: string }> = ({
  label,
  value,
  depth = 0,
  query
}) => {
  const [open, setOpen] = useState(depth < 2);
  const searchable = `${label} ${typeof value === 'string' ? value : ''}`.toLowerCase();
  const isMatch = query.length > 0 && searchable.includes(query.toLowerCase());
  const isBranch = Array.isArray(value) || isObject(value);
  const entries = Array.isArray(value)
    ? value.map((item, index) => [String(index), item] as const)
    : isObject(value)
      ? Object.entries(value)
      : [];

  return (
    <div style={{ marginLeft: depth === 0 ? 0 : 14 }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        minHeight: '24px',
        color: isMatch ? '#FFFFFF' : '#D4D4D4',
        backgroundColor: isMatch ? 'rgba(0, 112, 243, 0.18)' : 'transparent',
        borderRadius: '4px',
        padding: '2px 4px'
      }}>
        {isBranch ? (
          <button
            onClick={() => setOpen(!open)}
            style={{ background: 'none', border: 'none', color: '#888888', cursor: 'pointer', padding: 0, display: 'flex' }}
            aria-label={open ? 'Collapse JSON node' : 'Expand JSON node'}
          >
            <ChevronRight size={14} style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)' }} />
          </button>
        ) : (
          <span style={{ width: 14 }} />
        )}
        <span style={{ color: '#0070F3', fontWeight: 700 }}>{label}</span>
        <span style={{ color: '#666666' }}>{isBranch ? Array.isArray(value) ? `[${value.length}]` : '{...}' : ':'}</span>
        {!isBranch && (
          <span style={{ color: typeof value === 'number' ? '#F59E0B' : typeof value === 'boolean' ? '#10B981' : '#D4D4D4' }}>
            {value === null ? 'null' : JSON.stringify(value)}
          </span>
        )}
      </div>
      {isBranch && open && (
        <div>
          {entries.length === 0 ? (
            <div style={{ marginLeft: 20, color: '#666666' }}>{Array.isArray(value) ? '[]' : '{}'}</div>
          ) : (
            entries.map(([childLabel, childValue]) => (
              <JsonNode key={`${label}-${childLabel}`} label={childLabel} value={childValue} depth={depth + 1} query={query} />
            ))
          )}
        </div>
      )}
    </div>
  );
};

export const JsonInspector: React.FC<JsonInspectorProps> = ({ title, data, filename }) => {
  const [mode, setMode] = useState<'tree' | 'raw'>('tree');
  const [query, setQuery] = useState('');
  const [copied, setCopied] = useState(false);
  const jsonText = useMemo(() => JSON.stringify(data, null, 2), [data]);

  const copyJson = async () => {
    await navigator.clipboard.writeText(jsonText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  };

  const downloadJson = () => {
    const blob = new Blob([jsonText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{
      backgroundColor: '#121212',
      border: '1px solid #1E1E1E',
      borderRadius: '8px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      minHeight: 0
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        padding: '12px 14px',
        borderBottom: '1px solid #1E1E1E',
        backgroundColor: '#161616'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileJson size={16} color="#0070F3" />
          <strong style={{ fontSize: '13px' }}>{title}</strong>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: '#666666' }} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search JSON"
              style={{
                backgroundColor: '#0A0A0A',
                border: '1px solid #1E1E1E',
                borderRadius: '6px',
                color: '#FFFFFF',
                padding: '7px 8px 7px 28px',
                fontSize: '12px',
                width: 170,
                outline: 'none'
              }}
            />
          </div>
          <button onClick={() => setMode(mode === 'tree' ? 'raw' : 'tree')} style={toolbarButtonStyle}>
            {mode === 'tree' ? 'Raw' : 'Tree'}
          </button>
          <button onClick={copyJson} style={toolbarButtonStyle} title="Copy JSON">
            <Copy size={14} /> {copied ? 'Copied' : 'Copy'}
          </button>
          <button onClick={downloadJson} style={toolbarButtonStyle} title="Download JSON">
            <Download size={14} /> Download
          </button>
        </div>
      </div>
      <div style={{
        backgroundColor: '#0A0A0A',
        padding: '14px',
        overflow: 'auto',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        lineHeight: 1.6,
        flexGrow: 1,
        maxHeight: 560
      }}>
        {mode === 'tree' ? (
          <JsonNode label="contract" value={data} query={query} />
        ) : (
          <pre style={{ margin: 0, color: '#D4D4D4', whiteSpace: 'pre-wrap' }}>{jsonText}</pre>
        )}
      </div>
    </div>
  );
};

const toolbarButtonStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '6px',
  backgroundColor: '#0A0A0A',
  border: '1px solid #1E1E1E',
  color: '#FFFFFF',
  borderRadius: '6px',
  padding: '7px 9px',
  cursor: 'pointer',
  fontSize: '12px',
  fontFamily: 'inherit'
};
