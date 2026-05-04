# Token Usage Implementation Spec

## Purpose

This document defines the implementation plan for token usage capture in Prompt Transformer.

The goal is to support Herman admin reporting on token consumption while clearly separating:

- transformer-owned administrative token usage
  - coaching-related internal LLM work
  - scoring-related internal LLM work
  - other future transformer-owned evaluator or policy calls
- end-user response token usage
  - the downstream LLM call that produces the final answer shown to the user

The design should minimize database schema impact and should build on the request and conversation data Prompt Transformer already stores.

## Core rule

Prompt Transformer must treat token usage as analytics, not as business logic.

That means:

- token usage should be captured consistently across all LLM connectors
- token reporting should not change prompt enforcement behavior
- token reporting should not change prompt scoring behavior
- token usage should be attributable by category so Herman admin can measure cost separately for:
  - internal transformer work
  - final user-facing completion work

## Goals

- capture normalized token usage from every LLM connector
- separate `admin` token usage from `final_response` token usage
- preserve per-turn reporting because token spend happens per request, not only per conversation
- minimize schema changes
- let Herman admin report token usage by:
  - user
  - conversation
  - request
  - provider
  - model
  - task type
  - result type
- support future prompt-efficiency analysis
  - for example whether better prompts reduce downstream token consumption

## Non-goals

- changing prompt transformation behavior based on token usage
- billing or chargeback logic
- exact cost calculation in v1
- backfilling historical token usage for old requests
- introducing a separate high-volume event table in v1

## Product use case

Herman admin should be able to answer questions like:

- how many tokens are being spent on internal transformer evaluation versus final responses?
- are users who improve their prompts generating lower final-response token consumption?
- which tenants, users, or task types create the most transformer-side overhead?
- are coaching and scoring features creating acceptable administrative token cost?

To support this, token usage must be stored with the existing prompt transform request record, which is already the natural per-turn analytics unit.

## Current state

### Existing request persistence

Prompt Transformer already stores one row per request in `prompt_transform_requests`.

Current request logging includes:

- `session_id`
- `conversation_id`
- `user_id_hash`
- `raw_prompt`
- `transformed_prompt`
- `task_type`
- `result_type`
- `target_provider`
- `target_model`
- `conversation_json`
- `findings_json`
- `metadata_json`

This makes `prompt_transform_requests` the best place to attach token usage without introducing a second analytics entity in v1.

### Existing connector behavior

The LLM adapter layer already extracts provider `usage` payloads into `TransformerLlmResponse`.

Current adapters:

- `openai`
- `azure_openai`
- `anthropic`
- `xai`

These payloads are provider-specific and are not yet normalized into one reporting shape.

### Existing transformer-owned LLM usage

Today, Prompt Transformer makes internal LLM calls for structure evaluation in the scoring and enforcement path.

Current direct internal call site:

- `StructureEvaluationService`

This internal call should count as `admin` usage because it supports coaching and scoring behavior, not the final user-facing answer.

### Current gap

Prompt Transformer does not execute the final downstream completion that generates the user-visible answer.

That means:

- transformer-owned `admin` usage can be captured directly inside Prompt Transformer
- `final_response` usage must be reported back to Prompt Transformer by the Herman caller after the final LLM call completes

This ownership split is fundamental and should be explicit in the API contract.

## Ownership split

### Prompt Transformer responsibilities

- normalize usage payloads returned by every connector
- capture token usage for transformer-owned internal LLM calls
- persist request-level token usage analytics
- expose enough request identity for downstream systems to attach final-response usage later
- provide read-friendly persisted data for Herman admin reporting

### Herman caller responsibilities

- execute the final downstream answer-generation call
- capture the final model's token usage from the real completion response
- report that usage back to Prompt Transformer using the transformer request identity
- avoid double-submitting final usage for the same request unless explicitly updating

## Reporting unit

The primary token-usage reporting unit should be the prompt transform request row.

Reasoning:

- transformer token work is triggered per request
- final-response token work is also tied to one transformed request
- Herman admin needs turn-level attribution before any conversation rollups
- request-level storage preserves flexibility for future rollups without adding schema now

Conversation-level and user-level reporting should be derived from request-level data.

## Token usage categories

Prompt Transformer should classify usage into two top-level categories.

### `admin`

`admin` usage is transformer-owned internal LLM consumption.

This includes:

- structure evaluation for coaching
- semantic scoring support
- future internal coaching generation calls
- future internal evaluator or policy LLM calls

This usage is administrative because it exists to improve, judge, or govern prompting behavior.

It is not the final end-user answer.

### `final_response`

`final_response` usage is the downstream answer-generation call made after Prompt Transformer returns a transformed prompt.

This is the token usage Herman admin ultimately wants to compare against prompt quality improvements.

## Token usage purposes

Within each category, Prompt Transformer should preserve finer-grained purpose labels.

Recommended v1 purposes:

- `structure_evaluator`
- `final_response`

Future-compatible purposes:

- `coaching_generator`
- `score_explainer`
- `policy_evaluator`
- `compliance_evaluator`

Purpose labels should be stored as plain strings so the system can grow without additional migrations.

## Canonical normalized token shape

All providers should be normalized into one internal shape before persistence.

Recommended normalized fields:

- `input_tokens`
- `output_tokens`
- `total_tokens`
- `reasoning_tokens`
  - optional
- `cache_read_tokens`
  - optional
- `cache_write_tokens`
  - optional
- `raw_usage`
  - optional provider payload for debugging only

Recommended normalized usage object:

```json
{
  "input_tokens": 120,
  "output_tokens": 45,
  "total_tokens": 165,
  "reasoning_tokens": null,
  "cache_read_tokens": null,
  "cache_write_tokens": null,
  "raw_usage": {
    "prompt_tokens": 120,
    "completion_tokens": 45,
    "total_tokens": 165
  }
}
```

### Normalization rules

The normalizer should map provider-specific keys into the canonical fields.

Examples:

- OpenAI-style:
  - `prompt_tokens` -> `input_tokens`
  - `completion_tokens` -> `output_tokens`
  - `total_tokens` -> `total_tokens`
- Anthropic-style:
  - `input_tokens` -> `input_tokens`
  - `output_tokens` -> `output_tokens`
  - derive `total_tokens` when absent

Recommended rule:

- if `total_tokens` is missing but `input_tokens` and `output_tokens` exist, compute `total_tokens = input_tokens + output_tokens`

If provider usage is absent entirely:

- normalized usage should be `null`
- request persistence should still succeed

## Persistence model

### Recommendation

Add one nullable JSON column to `prompt_transform_requests`:

- `token_usage_json`

This is the preferred v1 design because it:

- minimizes schema impact
- preserves flexibility for category and provider details
- avoids creating a new request-event table
- keeps token usage colocated with the existing request analytics row

### Recommended stored shape

```json
{
  "admin": {
    "input_tokens": 120,
    "output_tokens": 45,
    "total_tokens": 165,
    "calls": 1,
    "by_purpose": {
      "structure_evaluator": {
        "input_tokens": 120,
        "output_tokens": 45,
        "total_tokens": 165,
        "calls": 1
      }
    }
  },
  "final_response": {
    "input_tokens": 820,
    "output_tokens": 260,
    "total_tokens": 1080,
    "calls": 1
  },
  "providers": [
    {
      "category": "admin",
      "purpose": "structure_evaluator",
      "provider": "openai",
      "model": "gpt-4.1-mini",
      "input_tokens": 120,
      "output_tokens": 45,
      "total_tokens": 165
    },
    {
      "category": "final_response",
      "purpose": "final_response",
      "provider": "openai",
      "model": "gpt-4.1",
      "input_tokens": 820,
      "output_tokens": 260,
      "total_tokens": 1080
    }
  ]
}
```

### Why JSON instead of multiple scalar columns

Using JSON avoids adding many nullable columns such as:

- `admin_input_tokens`
- `admin_output_tokens`
- `admin_total_tokens`
- `final_input_tokens`
- `final_output_tokens`
- `final_total_tokens`

That scalar approach is more rigid and grows poorly as transformer-owned purposes expand.

JSON is the better fit because the reporting need is new dimensional analytics, not strict transactional logic.

## Request identity contract

To attach final-response usage to the correct request row, Prompt Transformer should return a stable request identifier from `transform_prompt`.

Recommended response addition:

- `metadata.request_log_id`

Alternative naming:

- `metadata.transform_request_id`

The important requirement is that the returned identifier maps directly to the `prompt_transform_requests` row.

This identifier should be treated as internal analytics identity, not user-facing conversation state.

## API changes

### 1. `POST /api/transform_prompt`

No token usage payload needs to be supplied by the caller on this request.

Prompt Transformer should:

- create the request row
- capture any transformer-owned `admin` usage that occurs during processing
- return the persisted request identity in the response metadata

Recommended response metadata additions:

- `request_log_id`
- optional `token_usage`
  - only if useful for debugging

### 2. New endpoint: `POST /api/request_usage/final_response`

Prompt Transformer should add a new authenticated write-back endpoint so Herman can report final-response token usage after the real completion finishes.

Recommended request body:

```json
{
  "request_log_id": 12345,
  "provider": "openai",
  "model": "gpt-4.1",
  "usage": {
    "input_tokens": 820,
    "output_tokens": 260,
    "total_tokens": 1080,
    "raw_usage": {
      "prompt_tokens": 820,
      "completion_tokens": 260,
      "total_tokens": 1080
    }
  }
}
```

Recommended behavior:

- locate the existing `prompt_transform_requests` row by `request_log_id`
- merge the supplied usage into `token_usage_json.final_response`
- append or upsert the matching provider-model record in `token_usage_json.providers`
- remain idempotent when the same request submits the same final usage again

Recommended response:

```json
{
  "request_log_id": 12345,
  "status": "updated"
}
```

### Why a separate endpoint is preferred

A follow-up write endpoint is better than expanding `transform_prompt` because:

- final-response usage does not exist yet at transform time
- the final response may fail, retry, or use a fallback model
- the Herman caller is the real source of truth for final completion usage

## Internal service changes

### LLM types

Add a normalized usage model to the LLM response contract.

Recommended addition to `TransformerLlmResponse`:

- `normalized_usage`

This should be a structured object rather than a generic dict so downstream services do not need provider-specific parsing.

### Token usage normalization service

Add a dedicated service, for example:

- `app/services/token_usage.py`

Recommended responsibilities:

- normalize provider-specific usage payloads
- build per-call attribution records
- merge multiple usage entries into one persisted `token_usage_json` shape

Recommended helpers:

- `normalize_usage(provider, usage_payload)`
- `build_usage_entry(category, purpose, provider, model, normalized_usage)`
- `merge_usage(existing_token_usage_json, new_entry)`

### Connector layer

Every connector should continue returning raw provider usage, but the gateway or adapter layer should also populate normalized usage.

Recommended rule:

- normalize usage as close to the connector response as practical
- avoid pushing provider-specific logic into business services like scoring or enforcement

### Structure evaluation path

`StructureEvaluationService` should return both:

- evaluator payload
- normalized token usage metadata for the internal LLM call

That usage should be tagged as:

- `category = "admin"`
- `purpose = "structure_evaluator"`

The usage should then be threaded through:

- `PromptRequirementService`
- `TransformerEngine`
- `RequestLogger`

### Request logger

`RequestLogger.log()` should persist `token_usage_json` along with the rest of the request payload.

If no internal usage occurred and no final-response usage has been reported yet:

- `token_usage_json` may be `null`
- or may contain only the `admin` block if evaluator usage occurred

## Database migration

### Required schema change

Add one nullable JSON column:

- `prompt_transform_requests.token_usage_json`

Recommended Alembic change:

- add the column as nullable
- do not backfill existing rows
- do not add a JSON default unless required by the target database conventions

### No v1 changes to `conversation_prompt_scores`

Do not add token usage fields to `conversation_prompt_scores` in v1.

Reasoning:

- that table is a conversation rollup for scoring
- token usage happens per request
- conflating token spend with conversation score rollups would complicate both models

If conversation-level token rollups are needed later, compute them from `prompt_transform_requests`.

## Reporting model for Herman admin

Herman admin reporting should read token usage from `prompt_transform_requests`.

Recommended initial reporting dimensions:

- `user_id_hash`
- `conversation_id`
- `session_id`
- `task_type`
- `result_type`
- `target_provider`
- `target_model`
- request `created_at`

Recommended derived measures:

- total admin input tokens
- total admin output tokens
- total admin tokens
- total final-response input tokens
- total final-response output tokens
- total final-response tokens
- average final-response tokens per request
- average admin tokens per request
- admin-to-final token ratio
- token totals by task type
- token totals by model

Recommended future analysis:

- compare `final_response.total_tokens` before and after prompt quality improvements
- compare score improvement against token reduction
- detect whether coaching overhead is producing enough downstream savings

## Suggested query strategy

In v1, use JSON extraction queries directly against `prompt_transform_requests`.

Do not add a dedicated rollup table yet.

If reporting volume later justifies optimization, future options include:

- a database view
- a materialized view
- a periodic analytics export

## Error handling

### Missing usage from provider

If a provider response omits token usage:

- do not fail the request
- persist `null` usage for that call
- allow reporting to treat the row as unknown rather than zero

### Final-response write-back not received

If Herman never reports final-response usage:

- the request row should still remain valid
- `token_usage_json.final_response` should remain absent or `null`

This is preferable to inventing zero values that imply known consumption.

### Duplicate write-back

The final-response write endpoint should be idempotent for the same request.

Recommended behavior:

- if the existing payload matches the new payload, return success without duplicating counts
- if the caller intentionally wants to replace usage after a retry or corrected measurement, update the stored payload in place

## Security and privacy

Token usage storage should not include prompt text beyond what is already persisted elsewhere in the request log.

Recommended rule:

- keep raw provider usage payloads only when they do not contain sensitive generated text
- never store response bodies inside `token_usage_json`

This feature is analytics-only and should not expand sensitive data retention beyond token metadata.

## Testing plan

### Unit tests

Add tests for:

- OpenAI usage normalization
- Azure OpenAI usage normalization
- Anthropic usage normalization
- xAI usage normalization
- absent usage payloads
- merge logic for multiple admin entries
- merge logic for final-response write-back

### Integration tests

Add tests for:

- structure evaluator usage persisting into `token_usage_json.admin`
- transform responses returning `request_log_id`
- final-response write-back updating the correct request row
- repeated write-back remaining idempotent
- reporting-safe behavior when usage is missing

### Example cases

Case 1:

- evaluator call succeeds with usage payload
- expect `admin.by_purpose.structure_evaluator.total_tokens > 0`

Case 2:

- transform request runs with evaluator disabled
- expect no `admin` usage entry

Case 3:

- Herman reports final-response usage for the returned `request_log_id`
- expect `final_response.total_tokens` to be populated on the same request row

Case 4:

- same final-response payload is submitted twice
- expect no double-counting

Case 5:

- provider returns no usage block
- expect successful request with `null` normalized usage

## Rollout plan

### Phase 1

- add normalized usage model
- add `token_usage_json` column
- capture transformer-owned `admin` usage
- return request row identity from `transform_prompt`

### Phase 2

- add final-response write-back endpoint
- update Herman caller to report downstream completion usage

### Phase 3

- add Herman admin queries or read APIs for token reporting
- validate whether better prompting correlates with lower downstream token spend

## Open decisions

These should be finalized before implementation:

1. Should the response field be named `request_log_id` or `transform_request_id`?
2. Should raw provider usage always be stored, or only normalized fields?
3. If Herman retries a final completion with a different model, should the write-back endpoint replace or version the stored `final_response` entry?
4. Do we want a compact read endpoint for request-level token usage, or is database-side admin reporting sufficient in v1?

## Recommendation

Implement token usage as request-level analytics stored on `prompt_transform_requests` in a single `token_usage_json` column.

Capture transformer-owned internal LLM usage directly as `admin` usage.

Require Herman to write back final downstream completion usage as `final_response` usage using a returned transformer request identifier.

This provides clear category separation, minimal schema impact, and a solid base for future Herman admin reporting on prompt efficiency.
