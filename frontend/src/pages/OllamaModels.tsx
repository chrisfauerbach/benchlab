import { useState, useEffect, useCallback } from 'react';
import { Trash2, Download, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { useOllamaModels, usePullModel, useDeleteModel } from '@/hooks/use-ollama';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/utils';

const POPULAR_MODELS = [
  { name: 'llama3.2:3b', desc: 'Meta Llama 3.2 3B', size: '2.0 GB' },
  { name: 'llama3.2:1b', desc: 'Meta Llama 3.2 1B', size: '1.3 GB' },
  { name: 'llama3.1:8b', desc: 'Meta Llama 3.1 8B', size: '4.7 GB' },
  { name: 'mistral:7b', desc: 'Mistral 7B', size: '4.1 GB' },
  { name: 'gemma2:9b', desc: 'Google Gemma 2 9B', size: '5.4 GB' },
  { name: 'gemma2:2b', desc: 'Google Gemma 2 2B', size: '1.6 GB' },
  { name: 'phi3:mini', desc: 'Microsoft Phi-3 Mini', size: '2.3 GB' },
  { name: 'codellama:7b', desc: 'Code Llama 7B', size: '3.8 GB' },
  { name: 'qwen2.5:7b', desc: 'Qwen 2.5 7B', size: '4.7 GB' },
  { name: 'qwen2.5:3b', desc: 'Qwen 2.5 3B', size: '1.9 GB' },
  { name: 'deepseek-r1:8b', desc: 'DeepSeek R1 8B', size: '4.9 GB' },
  { name: 'deepseek-r1:1.5b', desc: 'DeepSeek R1 1.5B', size: '1.1 GB' },
];

function formatBytes(bytes: number): string {
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

type PullState = 'idle' | 'pending' | 'pulling' | 'done' | 'error';

function PullButton({ name, installedNames }: { name: string; installedNames: Set<string> }) {
  const pull = usePullModel();
  const [state, setState] = useState<PullState>(
    installedNames.has(name) ? 'done' : 'idle',
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (installedNames.has(name) && state === 'idle') {
      setState('done');
    }
  }, [installedNames, name, state]);

  const pollStatus = useCallback(async (modelName: string) => {
    const poll = async () => {
      try {
        const res = await api.pullModelStatus(modelName);
        if (res.status === 'done') {
          setState('done');
          return;
        }
        if (res.status === 'error') {
          setState('error');
          setError(res.error ?? 'Unknown error');
          return;
        }
        setTimeout(poll, 2000);
      } catch {
        setTimeout(poll, 3000);
      }
    };
    poll();
  }, []);

  const handlePull = async () => {
    setState('pending');
    setError(null);
    try {
      await pull.mutateAsync(name);
      setState('pulling');
      pollStatus(name);
    } catch (e: unknown) {
      setState('error');
      setError(e instanceof Error ? e.message : 'Failed to start pull');
    }
  };

  if (state === 'done') {
    return (
      <span className="inline-flex items-center gap-1 text-green-600 text-sm">
        <CheckCircle className="h-4 w-4" /> Installed
      </span>
    );
  }
  if (state === 'pulling' || state === 'pending') {
    return (
      <span className="inline-flex items-center gap-1 text-blue-600 text-sm">
        <Loader2 className="h-4 w-4 animate-spin" /> Pulling...
      </span>
    );
  }
  if (state === 'error') {
    return (
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center gap-1 text-red-600 text-xs">
          <AlertCircle className="h-3 w-3" /> {error}
        </span>
        <button onClick={handlePull} className="text-xs text-blue-600 hover:underline">
          Retry
        </button>
      </div>
    );
  }
  return (
    <button
      onClick={handlePull}
      className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90 transition-colors"
    >
      <Download className="h-3.5 w-3.5" /> Pull
    </button>
  );
}

export function OllamaModels() {
  const { data, isLoading } = useOllamaModels();
  const deleteModel = useDeleteModel();
  const [customModel, setCustomModel] = useState('');

  const models = data?.models ?? [];
  const installedNames = new Set(models.map((m) => m.name));

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete model "${name}"?`)) return;
    await deleteModel.mutateAsync(name);
  };

  const handleCustomPull = () => {
    if (!customModel.trim()) return;
    // The PullButton handles pull logic; we render it inline
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Ollama Models</h1>

      {/* Installed Models */}
      <Card>
        <CardHeader>
          <CardTitle>Installed Models</CardTitle>
        </CardHeader>
        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground py-4">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading models...
          </div>
        ) : models.length === 0 ? (
          <p className="text-muted-foreground text-sm">No models installed. Pull one below to get started.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Model</th>
                  <th className="pb-2 font-medium">Size</th>
                  <th className="pb-2 font-medium">Modified</th>
                  <th className="pb-2 font-medium w-10"></th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.digest} className="border-b border-border last:border-0">
                    <td className="py-2.5 font-mono text-sm">
                      {m.name}
                      {m.details?.parameter_size && (
                        <Badge variant="secondary" className="ml-2">{m.details.parameter_size}</Badge>
                      )}
                    </td>
                    <td className="py-2.5">{formatBytes(m.size)}</td>
                    <td className="py-2.5 text-muted-foreground">{formatDate(m.modified_at)}</td>
                    <td className="py-2.5">
                      <button
                        onClick={() => handleDelete(m.name)}
                        disabled={deleteModel.isPending}
                        className="text-muted-foreground hover:text-destructive transition-colors disabled:opacity-50"
                        title="Delete model"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Pull New Model */}
      <Card>
        <CardHeader>
          <CardTitle>Pull New Model</CardTitle>
        </CardHeader>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {POPULAR_MODELS.map((pm) => (
            <div
              key={pm.name}
              className="flex items-center justify-between rounded-md border border-border p-3"
            >
              <div className="min-w-0">
                <p className="font-mono text-sm truncate">{pm.name}</p>
                <p className="text-xs text-muted-foreground">{pm.desc} &middot; {pm.size}</p>
              </div>
              <div className="ml-3 shrink-0">
                <PullButton name={pm.name} installedNames={installedNames} />
              </div>
            </div>
          ))}
        </div>

        {/* Custom model input */}
        <div className="mt-4 flex gap-2">
          <input
            type="text"
            placeholder="Custom model tag, e.g. llama3.2:latest"
            value={customModel}
            onChange={(e) => setCustomModel(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCustomPull()}
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
          {customModel.trim() && (
            <PullButton name={customModel.trim()} installedNames={installedNames} />
          )}
        </div>
      </Card>

      {data?.error && (
        <Card className="border-destructive">
          <p className="text-destructive text-sm">Ollama connection error: {data.error}</p>
        </Card>
      )}
    </div>
  );
}
