"""Elasticsearch index mapping definition for benchlab-results."""

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "doc_type": {"type": "keyword"},
            "batch_id": {"type": "keyword"},
            "result_id": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "repetition": {"type": "integer"},
            "status": {"type": "keyword"},

            # Prompt info
            "prompt": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "category": {"type": "keyword"},
                    "input_text": {"type": "text"},
                    "system_prompt": {"type": "text"},
                    "expected_output": {"type": "text"},
                    "tags": {"type": "keyword"},
                    "difficulty": {"type": "keyword"},
                }
            },

            # Model info
            "model": {
                "properties": {
                    "name": {"type": "keyword"},
                    "display_name": {"type": "keyword"},
                    "parameters": {"type": "object", "enabled": False},
                }
            },

            # Output
            "output": {"type": "text"},
            "error": {"type": "text"},
            "success": {"type": "boolean"},

            # Execution metrics
            "metrics": {
                "properties": {
                    "ttft_ms": {"type": "float"},
                    "total_generation_ms": {"type": "float"},
                    "model_load_ms": {"type": "float"},
                    "prompt_eval_ms": {"type": "float"},
                    "eval_ms": {"type": "float"},
                    "output_tokens_per_sec": {"type": "float"},
                    "prompt_tokens_per_sec": {"type": "float"},
                    "input_tokens": {"type": "integer"},
                    "output_tokens": {"type": "integer"},
                    "total_tokens": {"type": "integer"},
                    "char_count": {"type": "integer"},
                    "word_count": {"type": "integer"},
                    "sentence_count": {"type": "integer"},
                }
            },

            # Evaluations (nested for per-evaluator queries)
            "evaluations": {
                "type": "nested",
                "properties": {
                    "evaluator_model": {"type": "keyword"},
                    "scores": {"type": "object", "enabled": False},
                    "custom_scores": {"type": "object", "enabled": False},
                    "reasoning": {"type": "text"},
                    "eval_metrics": {
                        "properties": {
                            "total_generation_ms": {"type": "float"},
                            "output_tokens_per_sec": {"type": "float"},
                            "input_tokens": {"type": "integer"},
                            "output_tokens": {"type": "integer"},
                        }
                    },
                }
            },

            # Evaluation summary
            "evaluation_summary": {
                "properties": {
                    "mean_scores": {"type": "object", "enabled": False},
                    "median_scores": {"type": "object", "enabled": False},
                    "std_scores": {"type": "object", "enabled": False},
                    "composite_score": {"type": "float"},
                    "weighted_composite_score": {"type": "float"},
                    "krippendorff_alpha": {"type": "object", "enabled": False},
                    "score_ranges": {"type": "object", "enabled": False},
                    "evaluator_count": {"type": "integer"},
                }
            },

            # Batch summary fields
            "total_prompts": {"type": "integer"},
            "total_models": {"type": "integer"},
            "total_executions": {"type": "integer"},
            "successful_executions": {"type": "integer"},
            "failed_executions": {"type": "integer"},
            "batch_duration_seconds": {"type": "float"},
            "model_rankings": {
                "type": "nested",
                "properties": {
                    "model_name": {"type": "keyword"},
                    "display_name": {"type": "keyword"},
                    "composite_score": {"type": "float"},
                    "weighted_composite_score": {"type": "float"},
                    "mean_scores": {"type": "object", "enabled": False},
                    "total_executions": {"type": "integer"},
                    "successful_executions": {"type": "integer"},
                    "avg_output_tokens_per_sec": {"type": "float"},
                    "avg_total_generation_ms": {"type": "float"},
                }
            },
            "config_snapshot": {"type": "object", "enabled": False},
            "prompt_categories": {"type": "keyword"},
            "tags_used": {"type": "keyword"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
}
