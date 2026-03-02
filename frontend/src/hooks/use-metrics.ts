import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useLeaderboard(dimension?: string) {
  return useQuery({
    queryKey: ['leaderboard', dimension],
    queryFn: () => api.getLeaderboard(dimension),
  });
}

export function useDistribution(field: string, batchId?: string) {
  return useQuery({
    queryKey: ['distribution', field, batchId],
    queryFn: () => api.getDistribution(field, batchId),
    enabled: !!field,
  });
}

export function usePrompts(category?: string) {
  return useQuery({
    queryKey: ['prompts', category],
    queryFn: () => api.listPrompts(category),
  });
}

export function usePromptResults(promptId: string) {
  return useQuery({
    queryKey: ['promptResults', promptId],
    queryFn: () => api.getPromptResults(promptId),
    enabled: !!promptId,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
    refetchInterval: 30000,
  });
}
