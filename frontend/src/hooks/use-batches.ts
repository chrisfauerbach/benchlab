import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useBatches(limit = 50) {
  return useQuery({
    queryKey: ['batches', limit],
    queryFn: () => api.listBatches(limit),
  });
}

export function useBatch(id: string) {
  return useQuery({
    queryKey: ['batch', id],
    queryFn: () => api.getBatch(id),
    enabled: !!id,
  });
}

export function useBatchResults(id: string, model?: string) {
  return useQuery({
    queryKey: ['batchResults', id, model],
    queryFn: () => api.getBatchResults(id, model),
    enabled: !!id,
  });
}

export function useBatchComparison(id: string) {
  return useQuery({
    queryKey: ['batchComparison', id],
    queryFn: () => api.compareBatchModels(id),
    enabled: !!id,
  });
}
