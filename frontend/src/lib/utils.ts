import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return 'n/a';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s.toFixed(0)}s`;
}

export function formatNumber(n: number | null | undefined, decimals = 1): string {
  if (n == null) return 'n/a';
  return n.toFixed(decimals);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}
