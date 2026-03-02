const BASE = '/api';

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export interface BatchSummary {
  batch_id: string;
  timestamp: string;
  status: string;
  total_prompts: number;
  total_models: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  batch_duration_seconds: number | null;
  model_rankings: ModelRanking[];
}

export interface ModelRanking {
  model_name: string;
  display_name: string;
  composite_score: number | null;
  weighted_composite_score: number | null;
  total_executions: number;
  successful_executions: number;
  avg_output_tokens_per_sec: number | null;
  avg_total_generation_ms: number | null;
}

export interface ResultDoc {
  result_id: string;
  batch_id: string;
  timestamp: string;
  prompt: {
    id: string;
    name: string;
    category: string;
    input_text: string;
    difficulty: string;
    tags: string[];
  };
  model: { name: string; display_name: string };
  output: string;
  success: boolean;
  error?: string;
  metrics: {
    ttft_ms: number | null;
    total_generation_ms: number | null;
    output_tokens_per_sec: number | null;
    input_tokens: number | null;
    output_tokens: number | null;
  };
  evaluation_summary?: {
    composite_score: number | null;
    weighted_composite_score: number | null;
    mean_scores: Record<string, number>;
    evaluator_count: number;
  };
}

export interface LeaderboardEntry {
  model: string;
  avg_score: number | null;
  avg_ttft_ms: number | null;
  avg_tokens_per_sec: number | null;
}

export interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
  digest: string;
  details?: {
    format: string;
    family: string;
    parameter_size: string;
    quantization_level: string;
  };
}

export const api = {
  health: () => fetchJSON<{ status: string; version: string; elasticsearch: string; ollama: string }>('/health'),

  listBatches: (limit = 50) =>
    fetchJSON<{ batches: BatchSummary[]; total: number }>(`/batches?limit=${limit}`),

  getBatch: (id: string) => fetchJSON<BatchSummary>(`/batches/${id}`),

  getBatchResults: (id: string, model?: string) => {
    const params = new URLSearchParams();
    if (model) params.set('model', model);
    return fetchJSON<{ results: ResultDoc[]; total: number }>(`/batches/${id}/results?${params}`);
  },

  compareBatchModels: (id: string) =>
    fetchJSON<{ batch_id: string; models: Record<string, unknown> }>(`/batches/${id}/compare`),

  deleteBatch: (id: string) => fetchJSON<{ deleted: number }>(`/batches/${id}`, { method: 'DELETE' }),

  listModels: () => fetchJSON<{ models: string[] }>('/models'),
  getModelStats: (model?: string) => {
    const params = model ? `?model=${model}` : '';
    return fetchJSON<{ stats: unknown }>(`/models/stats${params}`);
  },

  getLeaderboard: (dimension?: string) => {
    const params = dimension ? `?dimension=${dimension}` : '';
    return fetchJSON<{ rankings: LeaderboardEntry[]; dimension: string | null }>(`/metrics/leaderboard${params}`);
  },

  getDistribution: (field: string, batchId?: string) => {
    const params = new URLSearchParams({ field });
    if (batchId) params.set('batch_id', batchId);
    return fetchJSON<{ field: string; data: unknown }>(`/metrics/distribution?${params}`);
  },

  listPrompts: (category?: string) => {
    const params = category ? `?category=${category}` : '';
    return fetchJSON<{ prompts: Array<Record<string, unknown>>; categories: string[] }>(`/prompts${params}`);
  },

  getPromptResults: (promptId: string) =>
    fetchJSON<{ results: ResultDoc[]; total: number }>(`/prompts/${promptId}/results`),

  startRun: (body: { prompts_dir?: string; batch_id?: string }) =>
    fetchJSON<{ batch_id: string; status: string }>('/runs', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getRunStatus: (batchId: string) =>
    fetchJSON<{ batch_id: string; status: string }>(`/runs/${batchId}`),

  listOllamaModels: () =>
    fetchJSON<{ models: OllamaModel[]; error?: string }>('/models/available'),

  pullModel: (name: string) =>
    fetchJSON<{ status: string; name: string }>('/models/pull', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),

  pullModelStatus: (name: string) =>
    fetchJSON<{ status: string; error?: string }>(`/models/pull/${encodeURIComponent(name)}/status`),

  deleteModel: (name: string) =>
    fetchJSON<{ status: string; name: string }>(`/models/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    }),
};
