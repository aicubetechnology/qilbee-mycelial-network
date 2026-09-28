-- Migration: Add 'guardrail' kind to hyphal_memory table
-- Date: 2026-09-28
-- Description: Adds support for storing agent guard-rail/restriction definitions
-- as a memory kind, as a sibling to the existing 'skill' kind. Mirrors
-- 001_add_skill_kind.sql.
--
-- NOTE: Production's actual constraint name was found to be
-- 'hyphal_memory_kind_skill_check' (NOT 'hyphal_memory_kind_check' as
-- 001_add_skill_kind.sql assumed). Because DROP CONSTRAINT IF EXISTS
-- silently no-ops on a name mismatch, running 001-style migrations against
-- a DB with this naming drift leaves the OLD constraint (without the new
-- kind) active alongside the newly-added one - Postgres enforces ALL CHECK
-- constraints simultaneously, so the old one still blocks inserts of the
-- new kind. Discovered via a 500 on POST /memory/v1/hyphal:store against
-- qmn.qilbee.io: "violates check constraint hyphal_memory_kind_skill_check".
-- This migration defensively drops BOTH known historical names before
-- adding the single canonical constraint, so it is safe to run regardless
-- of which name is currently present.

-- Drop old constraint(s), regardless of which historical name is present
ALTER TABLE hyphal_memory 
DROP CONSTRAINT IF EXISTS hyphal_memory_kind_check;

ALTER TABLE hyphal_memory
DROP CONSTRAINT IF EXISTS hyphal_memory_kind_skill_check;

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
