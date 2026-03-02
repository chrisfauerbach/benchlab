import { useModelStats } from '@/hooks/use-models';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { formatNumber } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export function ModelComparison() {
  const { data, isLoading } = useModelStats();

  const buckets: Array<{
    key: string;
    doc_count: number;
    avg_ttft: { value: number | null };
    avg_generation: { value: number | null };
    avg_tokens_per_sec: { value: number | null };
    avg_composite: { value: number | null };
  }> = (data?.stats as any)?.buckets ?? [];

  const chartData = buckets.map((b) => ({
    model: b.key.split(':')[0],
    score: b.avg_composite?.value ?? 0,
    ttft: b.avg_ttft?.value ?? 0,
    speed: b.avg_tokens_per_sec?.value ?? 0,
    runs: b.doc_count,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Models</h1>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : buckets.length === 0 ? (
        <Card><p className="text-muted-foreground p-4">No model data yet.</p></Card>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Speed (tokens/sec)</CardTitle></CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <XAxis dataKey="model" fontSize={12} />
                    <YAxis fontSize={12} />
                    <Tooltip />
                    <Bar dataKey="speed" name="Tokens/sec" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card>
              <CardHeader><CardTitle>Quality vs Speed</CardTitle></CardHeader>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <XAxis dataKey="model" fontSize={12} />
                    <YAxis yAxisId="left" domain={[0, 10]} fontSize={12} />
                    <YAxis yAxisId="right" orientation="right" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    <Bar yAxisId="left" dataKey="score" name="Score" fill="hsl(221.2, 83.2%, 53.3%)" radius={[4, 4, 0, 0]} />
                    <Bar yAxisId="right" dataKey="speed" name="Tokens/s" fill="hsl(142, 71%, 45%)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <Card>
            <CardHeader><CardTitle>Model Statistics</CardTitle></CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Model</th>
                    <th className="pb-2 pr-4">Runs</th>
                    <th className="pb-2 pr-4">Avg Score</th>
                    <th className="pb-2 pr-4">Avg TTFT</th>
                    <th className="pb-2 pr-4">Avg Gen Time</th>
                    <th className="pb-2">Tokens/sec</th>
                  </tr>
                </thead>
                <tbody>
                  {buckets.map((b) => (
                    <tr key={b.key} className="border-b border-border/50">
                      <td className="py-2 pr-4 font-mono text-xs">{b.key}</td>
                      <td className="py-2 pr-4">{b.doc_count}</td>
                      <td className="py-2 pr-4">{formatNumber(b.avg_composite?.value)}</td>
                      <td className="py-2 pr-4">{formatNumber(b.avg_ttft?.value, 0)}ms</td>
                      <td className="py-2 pr-4">{formatNumber(b.avg_generation?.value, 0)}ms</td>
                      <td className="py-2">{formatNumber(b.avg_tokens_per_sec?.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
