import { useParams, Link } from 'react-router-dom';
import { usePromptResults } from '@/hooks/use-metrics';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { ScoreBar } from '@/components/ScoreBar';
import { formatNumber } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function PromptDetail() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = usePromptResults(id!);

  const results = data?.results ?? [];
  const prompt = results[0]?.prompt;

  // Group by model for comparison
  const byModel: Record<string, typeof results> = {};
  for (const r of results) {
    const key = r.model.name;
    if (!byModel[key]) byModel[key] = [];
    byModel[key].push(r);
  }

  const chartData = Object.entries(byModel).map(([model, rs]) => {
    const scores = rs
      .map((r) => r.evaluation_summary?.composite_score)
      .filter((s): s is number => s != null);
    return {
      model: model.split(':')[0],
      score: scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0,
      runs: rs.length,
    };
  });

  if (isLoading) return <p className="text-muted-foreground">Loading...</p>;
  if (!prompt) return <p className="text-destructive">Prompt not found.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/" className="text-muted-foreground hover:text-foreground text-sm">&larr; Back</Link>
        <h1 className="text-2xl font-bold">{prompt.name}</h1>
        <Badge variant="secondary">{prompt.category}</Badge>
        <Badge variant="secondary">{prompt.difficulty}</Badge>
      </div>

      <Card>
        <CardHeader><CardTitle>Prompt</CardTitle></CardHeader>
        <pre className="whitespace-pre-wrap text-sm bg-accent/30 p-4 rounded-md">{prompt.input_text}</pre>
        {prompt.tags.length > 0 && (
          <div className="flex gap-1 mt-3">
            {prompt.tags.map((t) => (
              <Badge key={t} variant="secondary">{t}</Badge>
            ))}
          </div>
        )}
      </Card>

      {chartData.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Model Scores for this Prompt</CardTitle></CardHeader>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="model" fontSize={12} />
                <YAxis domain={[0, 10]} fontSize={12} />
                <Tooltip />
                <Bar dataKey="score" fill="hsl(221.2, 83.2%, 53.3%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Results ({results.length})</CardTitle></CardHeader>
        <div className="space-y-4">
          {results.map((r) => (
            <div key={r.result_id} className="border border-border rounded-md p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm">{r.model.display_name}</span>
                  <Badge variant={r.success ? 'success' : 'destructive'}>
                    {r.success ? 'OK' : 'Error'}
                  </Badge>
                </div>
                <div className="text-sm text-muted-foreground">
                  {formatNumber(r.metrics.output_tokens_per_sec)} tok/s | {formatNumber(r.metrics.ttft_ms, 0)}ms TTFT
                </div>
              </div>
              {r.evaluation_summary && (
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {Object.entries(r.evaluation_summary.mean_scores).map(([dim, score]) => (
                    <ScoreBar key={dim} score={score} label={dim} />
                  ))}
                </div>
              )}
              <pre className="whitespace-pre-wrap text-xs bg-accent/20 p-3 rounded max-h-48 overflow-auto">
                {r.output || r.error}
              </pre>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
