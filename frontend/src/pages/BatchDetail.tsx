import { useParams, Link } from 'react-router-dom';
import { useBatch, useBatchResults } from '@/hooks/use-batches';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { StatCard } from '@/components/StatCard';
import { Badge } from '@/components/Badge';
import { ScoreBar } from '@/components/ScoreBar';
import { formatDuration, formatNumber, formatDate } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function BatchDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: batch, isLoading } = useBatch(id!);
  const { data: resultsData } = useBatchResults(id!);
  if (isLoading) return <p className="text-muted-foreground">Loading...</p>;
  if (!batch) return <p className="text-destructive">Batch not found.</p>;

  const results = resultsData?.results ?? [];

  const chartData = batch.model_rankings.map((r) => ({
    model: r.display_name,
    score: r.composite_score ?? 0,
    speed: r.avg_output_tokens_per_sec ?? 0,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/" className="text-muted-foreground hover:text-foreground text-sm">&larr; Back</Link>
        <h1 className="text-2xl font-bold">Batch: <span className="font-mono">{batch.batch_id}</span></h1>
        <Badge variant={batch.status === 'completed' ? 'success' : 'warning'}>{batch.status}</Badge>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <StatCard title="Models" value={batch.total_models} />
        <StatCard title="Prompts" value={batch.total_prompts} />
        <StatCard title="Executions" value={`${batch.successful_executions}/${batch.total_executions}`} />
        <StatCard title="Duration" value={formatDuration(batch.batch_duration_seconds)} />
        <StatCard title="Timestamp" value={formatDate(batch.timestamp).split(',')[0]} />
      </div>

      {chartData.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Model Comparison</CardTitle></CardHeader>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="model" fontSize={12} />
                <YAxis domain={[0, 10]} fontSize={12} />
                <Tooltip />
                <Bar dataKey="score" name="Composite Score" fill="hsl(221.2, 83.2%, 53.3%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Model Rankings</CardTitle></CardHeader>
        <div className="space-y-3">
          {batch.model_rankings.map((r, i) => (
            <div key={r.model_name} className="flex items-center gap-4 p-3 rounded-md bg-accent/30">
              <span className="text-lg font-bold w-8">{i + 1}</span>
              <div className="flex-1">
                <div className="font-medium">{r.display_name}</div>
                <div className="text-xs text-muted-foreground font-mono">{r.model_name}</div>
              </div>
              <div className="w-40">
                <ScoreBar score={r.composite_score} label="Score" />
              </div>
              <div className="text-sm text-right w-28">
                <div>{formatNumber(r.avg_output_tokens_per_sec)} tok/s</div>
                <div className="text-muted-foreground text-xs">{formatNumber(r.avg_total_generation_ms, 0)}ms gen</div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader><CardTitle>Results ({results.length})</CardTitle></CardHeader>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="pb-2 pr-4">Prompt</th>
                <th className="pb-2 pr-4">Model</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Score</th>
                <th className="pb-2 pr-4">Tokens/s</th>
                <th className="pb-2 pr-4">TTFT</th>
                <th className="pb-2">Output</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.result_id} className="border-b border-border/50 hover:bg-accent/50">
                  <td className="py-2 pr-4">
                    <Link to={`/prompts/${r.prompt.id}`} className="text-primary hover:underline">
                      {r.prompt.name}
                    </Link>
                    <div className="text-xs text-muted-foreground">{r.prompt.category}</div>
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs">{r.model.display_name}</td>
                  <td className="py-2 pr-4">
                    <Badge variant={r.success ? 'success' : 'destructive'}>
                      {r.success ? 'OK' : 'Error'}
                    </Badge>
                  </td>
                  <td className="py-2 pr-4">{formatNumber(r.evaluation_summary?.composite_score)}</td>
                  <td className="py-2 pr-4">{formatNumber(r.metrics.output_tokens_per_sec)}</td>
                  <td className="py-2 pr-4">{formatNumber(r.metrics.ttft_ms, 0)}ms</td>
                  <td className="py-2 max-w-xs truncate text-muted-foreground text-xs">
                    <Link to={`/results/${r.result_id}`} className="hover:text-foreground">
                      {r.output.slice(0, 80)}...
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
