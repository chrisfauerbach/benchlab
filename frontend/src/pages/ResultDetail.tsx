import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { ScoreBar } from '@/components/ScoreBar';
import { formatNumber, formatDate } from '@/lib/utils';
import type { ResultDoc } from '@/lib/api';

export function ResultDetail() {
  const { id } = useParams<{ id: string }>();
  // We fetch all batch results and find the one — or could add a dedicated endpoint
  // For now, search through batch results by parsing the result_id
  const batchId = id?.split('-')[0] ?? '';

  const { data, isLoading } = useQuery({
    queryKey: ['result', id],
    queryFn: async () => {
      const res = await fetch(`/api/batches/${batchId}/results`);
      const data = await res.json();
      return (data.results as ResultDoc[]).find((r) => r.result_id === id);
    },
    enabled: !!id,
  });

  if (isLoading) return <p className="text-muted-foreground">Loading...</p>;
  if (!data) return <p className="text-destructive">Result not found.</p>;

  const r = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to={`/batches/${r.batch_id}`} className="text-muted-foreground hover:text-foreground text-sm">&larr; Back to batch</Link>
        <h1 className="text-2xl font-bold">Result Detail</h1>
        <Badge variant={r.success ? 'success' : 'destructive'}>{r.success ? 'Success' : 'Failed'}</Badge>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>Prompt</CardTitle></CardHeader>
          <div className="space-y-2 text-sm">
            <div><span className="text-muted-foreground">Name:</span> {r.prompt.name}</div>
            <div><span className="text-muted-foreground">Category:</span> <Badge variant="secondary">{r.prompt.category}</Badge></div>
            <div><span className="text-muted-foreground">Difficulty:</span> {r.prompt.difficulty}</div>
          </div>
          <pre className="whitespace-pre-wrap text-sm bg-accent/30 p-3 rounded-md mt-3">{r.prompt.input_text}</pre>
        </Card>

        <Card>
          <CardHeader><CardTitle>Metrics</CardTitle></CardHeader>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">Model:</span> {r.model.display_name}</div>
            <div><span className="text-muted-foreground">Batch:</span> <span className="font-mono text-xs">{r.batch_id}</span></div>
            <div><span className="text-muted-foreground">TTFT:</span> {formatNumber(r.metrics.ttft_ms, 0)}ms</div>
            <div><span className="text-muted-foreground">Gen Time:</span> {formatNumber(r.metrics.total_generation_ms, 0)}ms</div>
            <div><span className="text-muted-foreground">Tokens/sec:</span> {formatNumber(r.metrics.output_tokens_per_sec)}</div>
            <div><span className="text-muted-foreground">Input Tokens:</span> {r.metrics.input_tokens ?? 'n/a'}</div>
            <div><span className="text-muted-foreground">Output Tokens:</span> {r.metrics.output_tokens ?? 'n/a'}</div>
            <div><span className="text-muted-foreground">Timestamp:</span> {formatDate(r.timestamp)}</div>
          </div>
        </Card>
      </div>

      {r.evaluation_summary && (
        <Card>
          <CardHeader>
            <CardTitle>
              Evaluation Scores
              <span className="text-sm font-normal text-muted-foreground ml-2">
                ({r.evaluation_summary.evaluator_count} evaluator{r.evaluation_summary.evaluator_count > 1 ? 's' : ''})
              </span>
            </CardTitle>
          </CardHeader>
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(r.evaluation_summary.mean_scores).map(([dim, score]) => (
              <ScoreBar key={dim} score={score} label={dim} />
            ))}
          </div>
          <div className="mt-4 flex gap-6 text-sm">
            <div>
              <span className="text-muted-foreground">Composite: </span>
              <span className="font-bold">{formatNumber(r.evaluation_summary.composite_score)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Weighted: </span>
              <span className="font-bold">{formatNumber(r.evaluation_summary.weighted_composite_score)}</span>
            </div>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Output</CardTitle></CardHeader>
        <pre className="whitespace-pre-wrap text-sm bg-accent/20 p-4 rounded-md max-h-96 overflow-auto">
          {r.output || r.error || 'No output'}
        </pre>
      </Card>
    </div>
  );
}
