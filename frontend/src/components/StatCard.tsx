import { Card } from './Card';

export function StatCard({ title, value, subtitle }: { title: string; value: string | number; subtitle?: string }) {
  return (
    <Card className="flex flex-col">
      <span className="text-sm text-muted-foreground">{title}</span>
      <span className="text-2xl font-bold mt-1">{value}</span>
      {subtitle && <span className="text-xs text-muted-foreground mt-1">{subtitle}</span>}
    </Card>
  );
}
