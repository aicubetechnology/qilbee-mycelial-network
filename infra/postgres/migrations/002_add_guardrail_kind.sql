-- Migration: Add 'guardrail' kind to hyphal_memory table
-- Date: 2026-09-28
-- Description: Adds support for storing agent guard-rail/restriction definitions
-- as a memory kind, as a sibling to the existing 'skill' kind. Mirrors
-- 001_add_skill_kind.sql.

-- Drop the old constraint
ALTER TABLE hyphal_memory 
DROP CONSTRAINT IF EXISTS hyphal_memory_kind_check;

-- Add the new constraint with 'guardrail' included
ALTER TABLE hyphal_memory 
ADD CONSTRAINT hyphal_memory_kind_check 
CHECK (kind IN (
    'insight', 
    'snippet', 
    'tool_hint', 
    'plan', 
    'outcome', 
    'result', 
    'task', 
    'context', 
    'memory', 
    'agent_result', 
    'skill',
    'guardrail'
));

-- Add comment explaining the guardrail kind
COMMENT ON COLUMN hyphal_memory.kind IS 
'Memory kind: insight, snippet, tool_hint, plan, outcome, result, task, context, memory, agent_result, skill, guardrail. 
The skill kind stores agent skill definitions with their schemas, capabilities, and execution metadata.
The guardrail kind stores agent guard-rail/restriction definitions (e.g. compliance rules, forbidden actions, operational constraints) surfaced proactively via kind=''guardrail'' hyphal_search(), mirroring the skill kind pattern.';
