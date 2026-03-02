import { Link } from 'react-router-dom';
import { useBatches } from '@/hooks/use-batches';
import { useLeaderboard } from '@/hooks/use-metrics';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { StatCard } from '@/components/StatCard';
import { Badge } from '@/components/Badge';
import { formatDuration, formatDate, formatNumber } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function Dashboard() {
  const { data: batchData, isLoading: loadingBatches } = useBatches(10);
  const { data: leaderboardData } = useLeaderboard();

  const batches = batchData?.batches ?? [];
  const totalExecutions = batches.reduce((s, b) => s + b.total_executions, 0);
  const totalSuccessful = batches.reduce((s, b) => s + b.successful_executions, 0);

  const chartData = (leaderboardData?.rankings ?? []).map((r) => ({
    model: r.model.split(':')[0],
    score: r.avg_score ?? 0,
    speed: r.avg_tokens_per_sec ?? 0,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Batches" value={batches.length} />
        <StatCard title="Total Runs" value={totalExecutions} />
        <StatCard title="Success Rate" value={totalExecutions ? `${((totalSuccessful / totalExecutions) * 100).toFixed(0)}%` : 'n/a'} />
        <StatCard title="Models Tested" value={new Set(batches.flatMap((b) => b.model_rankings.map((r) => r.model_name))).size} />
      </div>

      {chartData.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Model Scores</CardTitle></CardHeader>
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
        <CardHeader><CardTitle>Recent Batches</CardTitle></CardHeader>
        {loadingBatches ? (
          <p className="text-muted-foreground">Loading...</p>
        ) : batches.length === 0 ? (
          <p className="text-muted-foreground">No batches yet. Run <code>benchlab run</code> to get started.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 pr-4">Batch ID</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Models</th>
                  <th className="pb-2 pr-4">Prompts</th>
                  <th className="pb-2 pr-4">Success</th>
                  <th className="pb-2 pr-4">Duration</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((b) => (
                  <tr key={b.batch_id} className="border-b border-border/50 hover:bg-accent/50">
                    <td className="py-2 pr-4">
                      <Link to={`/batches/${b.batch_id}`} className="text-primary hover:underline font-mono text-xs">
                        {b.batch_id}
                      </Link>
                    </td>
                    <td className="py-2 pr-4">
                      <Badge variant={b.status === 'completed' ? 'success' : 'warning'}>{b.status}</Badge>
                    </td>
                    <td className="py-2 pr-4">{b.total_models}</td>
                    <td className="py-2 pr-4">{b.total_prompts}</td>
                    <td className="py-2 pr-4">{b.successful_executions}/{b.total_executions}</td>
                    <td className="py-2 pr-4">{formatDuration(b.batch_duration_seconds)}</td>
                    <td className="py-2 text-muted-foreground">{formatDate(b.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {(leaderboardData?.rankings ?? []).length > 0 && (
        <Card>
          <CardHeader><CardTitle>Top Models</CardTitle></CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 pr-4">#</th>
                  <th className="pb-2 pr-4">Model</th>
                  <th className="pb-2 pr-4">Avg Score</th>
                  <th className="pb-2 pr-4">Avg TTFT</th>
                  <th className="pb-2">Tokens/sec</th>
                </tr>
              </thead>
              <tbody>
                {(leaderboardData?.rankings ?? []).map((r, i) => (
                  <tr key={r.model} className="border-b border-border/50">
                    <td className="py-2 pr-4 font-medium">{i + 1}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{r.model}</td>
                    <td className="py-2 pr-4">{formatNumber(r.avg_score)}</td>
                    <td className="py-2 pr-4">{formatNumber(r.avg_ttft_ms, 0)}ms</td>
                    <td className="py-2">{formatNumber(r.avg_tokens_per_sec)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
