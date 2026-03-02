import { cn } from '@/lib/utils';

export function ScoreBar({ score, max = 10, label }: { score: number | null; max?: number; label?: string }) {
  if (score == null) return <span className="text-muted-foreground text-sm">n/a</span>;
  const pct = (score / max) * 100;
  const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      {label && <span className="text-xs text-muted-foreground w-20 truncate">{label}</span>}
      <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full transition-all', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium w-8 text-right">{score.toFixed(1)}</span>
    </div>
  );
}
