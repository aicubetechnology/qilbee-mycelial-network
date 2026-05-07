-- Migration: Add 'skill' kind to hyphal_memory table
-- Date: 2024-01-30
-- Description: Adds support for storing agent skills as a memory kind

-- Drop the old constraint
ALTER TABLE hyphal_memory 
DROP CONSTRAINT IF EXISTS hyphal_memory_kind_check;

-- Add the new constraint with 'skill' included
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
    'skill'
));

-- Add comment explaining the skill kind
COMMENT ON COLUMN hyphal_memory.kind IS 
'Memory kind: insight, snippet, tool_hint, plan, outcome, result, task, context, memory, agent_result, skill. 
The skill kind stores agent skill definitions with their schemas, capabilities, and execution metadata.';
