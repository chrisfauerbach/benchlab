import { useState } from 'react';
import { useLeaderboard } from '@/hooks/use-metrics';
import { Card, CardHeader, CardTitle } from '@/components/Card';
import { ScoreBar } from '@/components/ScoreBar';
import { formatNumber } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const DIMENSIONS = ['coherence', 'accuracy', 'relevance', 'completeness', 'conciseness', 'helpfulness'];

export function Leaderboard() {
  const [dimension, setDimension] = useState<string | undefined>();
  const { data, isLoading } = useLeaderboard(dimension);

  const rankings = data?.rankings ?? [];

  const chartData = rankings.map((r) => ({
    model: r.model.split(':')[0],
    score: r.avg_score ?? 0,
    speed: r.avg_tokens_per_sec ?? 0,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Leaderboard</h1>
        <select
          className="border border-border rounded-md px-3 py-1.5 text-sm bg-card"
          value={dimension ?? ''}
          onChange={(e) => setDimension(e.target.value || undefined)}
        >
          <option value="">Composite Score</option>
          {DIMENSIONS.map((d) => (
            <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : rankings.length === 0 ? (
        <Card><p className="text-muted-foreground p-4">No evaluation data yet.</p></Card>
      ) : (
        <>
          <Card>
            <CardHeader><CardTitle>{dimension ? `${dimension} Scores` : 'Composite Scores'}</CardTitle></CardHeader>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical">
                  <XAxis type="number" domain={[0, 10]} fontSize={12} />
                  <YAxis type="category" dataKey="model" width={100} fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="score" fill="hsl(221.2, 83.2%, 53.3%)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card>
            <CardHeader><CardTitle>Rankings</CardTitle></CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="pb-2 pr-4">#</th>
                    <th className="pb-2 pr-4">Model</th>
                    <th className="pb-2 pr-4">Score</th>
                    <th className="pb-2 pr-4">Avg TTFT</th>
                    <th className="pb-2">Tokens/sec</th>
                  </tr>
                </thead>
                <tbody>
                  {rankings.map((r, i) => (
                    <tr key={r.model} className="border-b border-border/50">
                      <td className="py-3 pr-4 font-bold text-lg">{i + 1}</td>
                      <td className="py-3 pr-4">
                        <span className="font-mono">{r.model}</span>
                      </td>
                      <td className="py-3 pr-4 w-48">
                        <ScoreBar score={r.avg_score} />
                      </td>
                      <td className="py-3 pr-4">{formatNumber(r.avg_ttft_ms, 0)}ms</td>
                      <td className="py-3">{formatNumber(r.avg_tokens_per_sec)}</td>
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
