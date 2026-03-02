import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: () => api.listModels(),
  });
}

export function useModelStats(model?: string) {
  return useQuery({
    queryKey: ['modelStats', model],
    queryFn: () => api.getModelStats(model),
  });
}
