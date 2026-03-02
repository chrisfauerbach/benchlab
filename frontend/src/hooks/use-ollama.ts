import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useOllamaModels() {
  return useQuery({
    queryKey: ['ollamaModels'],
    queryFn: () => api.listOllamaModels(),
    refetchInterval: 15_000,
  });
}

export function usePullModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.pullModel(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ollamaModels'] });
    },
  });
}

export function useDeleteModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.deleteModel(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ollamaModels'] });
    },
  });
}
