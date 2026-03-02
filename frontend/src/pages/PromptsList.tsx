import { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePrompts } from '@/hooks/use-metrics';
import { Card } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { formatNumber } from '@/lib/utils';

export function PromptsList() {
  const [category, setCategory] = useState<string | undefined>();
  const { data, isLoading } = usePrompts(category);

  const prompts = data?.prompts ?? [];
  const categories = data?.categories ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Prompts</h1>
        <select
          className="border border-border rounded-md px-3 py-1.5 text-sm bg-card"
          value={category ?? ''}
          onChange={(e) => setCategory(e.target.value || undefined)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : prompts.length === 0 ? (
        <Card><p className="text-muted-foreground p-4">No prompts found.</p></Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-2 pr-4">Name</th>
                  <th className="pb-2 pr-4">Category</th>
                  <th className="pb-2 pr-4">Difficulty</th>
                  <th className="pb-2 pr-4">Runs</th>
                  <th className="pb-2 pr-4">Avg Score</th>
                  <th className="pb-2">Tags</th>
                </tr>
              </thead>
              <tbody>
                {prompts.map((p: any) => (
                  <tr key={p.id} className="border-b border-border/50 hover:bg-accent/50">
                    <td className="py-2 pr-4">
                      <Link to={`/prompts/${p.id}`} className="text-primary hover:underline">
                        {p.name}
                      </Link>
                    </td>
                    <td className="py-2 pr-4"><Badge variant="secondary">{p.category}</Badge></td>
                    <td className="py-2 pr-4">{p.difficulty}</td>
                    <td className="py-2 pr-4">{p.result_count ?? 0}</td>
                    <td className="py-2 pr-4">{formatNumber(p.avg_composite_score)}</td>
                    <td className="py-2">
                      <div className="flex gap-1 flex-wrap">
                        {(p.tags ?? []).map((t: string) => (
                          <Badge key={t} variant="secondary">{t}</Badge>
                        ))}
                      </div>
                    </td>
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
