import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Loader2, CheckCircle, XCircle, Square } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { StatCard } from '@/components/StatCard';
import { useOllamaModels } from '@/hooks/use-ollama';
import { useStartRun, useRunStatus, useActiveRuns, useCancelRun, type RunStatus } from '@/hooks/use-runs';
import { formatDuration } from '@/lib/utils';

type Phase = 'configure' | 'running' | 'completed' | 'failed';

function useElapsedTime(startedAt: string | null): number {
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!startedAt) {
      setElapsed(0);
      return;
    }
    const start = new Date(startedAt).getTime();
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    intervalRef.current = setInterval(tick, 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [startedAt]);

  return elapsed;
}

function ActiveRunRow({ run, onCancel }: { run: RunStatus; onCancel: (id: string) => void }) {
  const elapsed = useElapsedTime(run.started_at ?? null);
  const progress = run.total_tasks ? Math.round(((run.completed_tasks ?? 0) / run.total_tasks) * 100) : 0;

  return (
    <div className="flex items-center gap-4 rounded-md border border-border p-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-mono text-sm truncate">{run.batch_id}</span>
          <Badge variant={run.status === 'running' ? 'default' : 'secondary'}>
            {run.status}
          </Badge>
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>{formatDuration(elapsed)}</span>
          {run.current_model && <span className="font-mono">{run.current_model}</span>}
          {run.total_tasks != null && (
            <span>{run.completed_tasks ?? 0}/{run.total_tasks}</span>
          )}
        </div>
      </div>
      {run.total_tasks != null && (
        <div className="w-24 h-2 rounded-full bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      {run.status === 'running' && (
        <button
          onClick={() => onCancel(run.batch_id)}
          className="text-red-600 hover:text-red-700 p-1"
          title="Cancel run"
        >
          <Square className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}

export function StartRun() {
  const navigate = useNavigate();
  const { data: ollamaData, isLoading: modelsLoading } = useOllamaModels();
  const startRun = useStartRun();
  const cancelRun = useCancelRun();
  const { data: activeRunsData } = useActiveRuns();

  const [phase, setPhase] = useState<Phase>('configure');
  const [selectedModels, setSelectedModels] = useState<Set<string>>(new Set());
  const [evaluationEnabled, setEvaluationEnabled] = useState(true);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data: runStatus } = useRunStatus(phase === 'running' ? batchId : null);

  const elapsed = useElapsedTime(
    phase === 'running' && runStatus?.started_at ? runStatus.started_at : null
  );

  const models = ollamaData?.models ?? [];
  const activeRuns = activeRunsData?.runs ?? [];

  // Filter out current batch from active runs list
  const otherActiveRuns = activeRuns.filter((r) => r.batch_id !== batchId);

  // Transition to completed/failed when polling detects terminal status
  if (phase === 'running' && runStatus) {
    if (runStatus.status === 'completed') {
      setPhase('completed');
    } else if (runStatus.status === 'failed') {
      setErrorMessage(runStatus.error ?? 'Run failed');
      setPhase('failed');
    }
  }

  const toggleModel = (name: string) => {
    setSelectedModels((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const selectAll = () => setSelectedModels(new Set(models.map((m) => m.name)));
  const clearAll = () => setSelectedModels(new Set());

  const handleStart = async () => {
    try {
      const result = await startRun.mutateAsync({
        target_models: Array.from(selectedModels),
        evaluation_enabled: evaluationEnabled,
      });
      setBatchId(result.batch_id);
      setPhase('running');
    } catch (e: unknown) {
      setErrorMessage(e instanceof Error ? e.message : 'Failed to start run');
      setPhase('failed');
    }
  };

  const handleCancel = async (id?: string) => {
    const targetId = id ?? batchId;
    if (targetId) {
      try {
        await cancelRun.mutateAsync(targetId);
      } catch {
        // ignore cancel errors
      }
    }
  };

  const handleReset = () => {
    setPhase('configure');
    setBatchId(null);
    setErrorMessage(null);
  };

  if (phase === 'completed') {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Start Run</h1>
        <Card className="flex flex-col items-center py-12 text-center">
          <CheckCircle className="h-12 w-12 text-green-600 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Run Completed</h2>
          <p className="text-muted-foreground mb-6">
            Batch <span className="font-mono">{batchId}</span> finished successfully.
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => navigate(`/batches/${batchId}`)}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              View Results
            </button>
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
            >
              Start Another Run
            </button>
          </div>
        </Card>
      </div>
    );
  }

  if (phase === 'failed') {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Start Run</h1>
        <Card className="flex flex-col items-center py-12 text-center">
          <XCircle className="h-12 w-12 text-red-500 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Run Failed</h2>
          <p className="text-muted-foreground mb-6 max-w-md">
            {errorMessage ?? 'An unknown error occurred.'}
          </p>
          <button
            onClick={handleReset}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
        </Card>
      </div>
    );
  }

  if (phase === 'running') {
    const completed = runStatus?.completed_tasks ?? 0;
    const total = runStatus?.total_tasks ?? 0;
    const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
    const targetModels = runStatus?.target_models ?? Array.from(selectedModels);
    const currentModel = runStatus?.current_model ?? null;

    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Start Run</h1>

        <Card className="space-y-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 text-primary animate-spin" />
              <CardTitle>Running Benchmark</CardTitle>
              <Badge variant={runStatus?.status === 'running' ? 'default' : 'secondary'}>
                {runStatus?.status ?? 'starting'}
              </Badge>
            </div>
          </CardHeader>

          {/* Stats row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatCard title="Elapsed Time" value={formatDuration(elapsed)} />
            <StatCard title="Progress" value={`${completed}/${total}`} subtitle={total > 0 ? `${progress}%` : undefined} />
            <StatCard title="Current Model" value={currentModel ?? 'Waiting...'} />
            <StatCard title="Batch ID" value={batchId ?? '—'} />
          </div>

          {/* Progress bar */}
          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Target models */}
          {targetModels.length > 0 && (
            <div>
              <p className="text-sm text-muted-foreground mb-2">Target Models</p>
              <div className="flex flex-wrap gap-2">
                {targetModels.map((m) => (
                  <Badge key={m} variant={m === currentModel ? 'default' : 'secondary'}>
                    {m}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Cancel button */}
          <div className="flex justify-center pt-2">
            <button
              onClick={() => handleCancel()}
              disabled={cancelRun.isPending}
              className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
            >
              <Square className="h-3.5 w-3.5" />
              {cancelRun.isPending ? 'Cancelling...' : 'Cancel Run'}
            </button>
          </div>
        </Card>

        {/* Other active runs */}
        {otherActiveRuns.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Other Active Runs</CardTitle>
            </CardHeader>
            <div className="space-y-2">
              {otherActiveRuns.map((run) => (
                <ActiveRunRow key={run.batch_id} run={run} onCancel={handleCancel} />
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  }

  // Configure phase
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Start Run</h1>

      {/* Model Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Select Models</CardTitle>
            <div className="flex gap-2">
              <button
                onClick={selectAll}
                className="text-xs text-primary hover:underline"
              >
                Select All
              </button>
              <span className="text-xs text-muted-foreground">|</span>
              <button
                onClick={clearAll}
                className="text-xs text-muted-foreground hover:underline"
              >
                Clear
              </button>
            </div>
          </div>
        </CardHeader>
        {modelsLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground py-4">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading models...
          </div>
        ) : models.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No models installed. Go to the{' '}
            <button onClick={() => navigate('/ollama')} className="text-primary hover:underline">
              Ollama page
            </button>{' '}
            to pull models first.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {models.map((m) => (
              <label
                key={m.name}
                className="flex items-center gap-3 rounded-md border border-border p-3 cursor-pointer hover:bg-accent transition-colors has-[:checked]:border-primary has-[:checked]:bg-primary/5"
              >
                <input
                  type="checkbox"
                  checked={selectedModels.has(m.name)}
                  onChange={() => toggleModel(m.name)}
                  className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                />
                <div className="min-w-0">
                  <p className="font-mono text-sm truncate">{m.name}</p>
                  {m.details?.parameter_size && (
                    <p className="text-xs text-muted-foreground">{m.details.parameter_size}</p>
                  )}
                </div>
              </label>
            ))}
          </div>
        )}
      </Card>

      {/* Options */}
      <Card>
        <CardHeader>
          <CardTitle>Options</CardTitle>
        </CardHeader>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={evaluationEnabled}
            onChange={(e) => setEvaluationEnabled(e.target.checked)}
            className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
          />
          <div>
            <p className="text-sm font-medium">Enable LLM-as-Judge Evaluation</p>
            <p className="text-xs text-muted-foreground">Run quality evaluation on model outputs after benchmark completes</p>
          </div>
        </label>
      </Card>

      {/* Start Button */}
      <button
        onClick={handleStart}
        disabled={selectedModels.size === 0 || startRun.isPending}
        className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {startRun.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Play className="h-4 w-4" />
        )}
        {startRun.isPending ? 'Starting...' : 'Start Benchmark Run'}
      </button>

      {/* Active runs section */}
      {activeRuns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Runs</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {activeRuns.map((run) => (
              <ActiveRunRow key={run.batch_id} run={run} onCancel={handleCancel} />
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
