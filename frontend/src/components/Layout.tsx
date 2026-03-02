import { Link, useLocation } from 'react-router-dom';
import { BarChart3, FlaskConical, HardDrive, LayoutDashboard, ListOrdered, MessageSquare } from 'lucide-react';
import { useHealth } from '@/hooks/use-metrics';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/leaderboard', label: 'Leaderboard', icon: ListOrdered },
  { to: '/models', label: 'Models', icon: FlaskConical },
  { to: '/prompts', label: 'Prompts', icon: MessageSquare },
  { to: '/ollama', label: 'Ollama', icon: HardDrive },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const { data: health } = useHealth();

  return (
    <div className="flex h-screen">
      <aside className="w-56 border-r border-border bg-card flex flex-col">
        <div className="p-4 border-b border-border">
          <Link to="/" className="flex items-center gap-2 text-lg font-bold text-primary no-underline">
            <BarChart3 className="h-6 w-6" />
            BenchLab
          </Link>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = location.pathname === item.to ||
              (item.to !== '/' && location.pathname.startsWith(item.to));
            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-md text-sm no-underline transition-colors',
                  active
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-border text-xs text-muted-foreground space-y-1">
          <div className="flex justify-between">
            <span>ES</span>
            <span className={health?.elasticsearch === 'connected' ? 'text-green-600' : 'text-red-500'}>
              {health?.elasticsearch ?? '...'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Ollama</span>
            <span className={health?.ollama === 'connected' ? 'text-green-600' : 'text-red-500'}>
              {health?.ollama ?? '...'}
            </span>
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  );
}
