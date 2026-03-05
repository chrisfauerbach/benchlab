import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, type RunStatus } from '@/lib/api';

export type { RunStatus };

export function useStartRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { prompts_dir?: string; batch_id?: string; target_models?: string[]; evaluation_enabled?: boolean }) =>
      api.startRun(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
    },
  });
}

export function useRunStatus(batchId: string | null) {
  return useQuery({
    queryKey: ['runStatus', batchId],
    queryFn: () => api.getRunStatus(batchId!),
    enabled: !!batchId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'starting' || status === 'running' || status === 'cancelling') {
        return 3000;
      }
      return false;
    },
  });
}

export function useActiveRuns() {
  return useQuery({
    queryKey: ['activeRuns'],
    queryFn: () => api.listActiveRuns(),
    refetchInterval: 3000,
  });
}

export function useCancelRun() {
  return useMutation({
    mutationFn: (batchId: string) => api.cancelRun(batchId),
  });
}
