-- Clean up bad domain data in heuristics table
-- Domains that are clearly parsing artifacts

DELETE FROM heuristics WHERE domain IN (
    'recommendation:',
    'provide',
    'status',
    'severitybased',
    'recommended'
);

-- Verify cleanup
SELECT 'Remaining heuristics with unusual domains (should be 0 or minimal):';
SELECT domain, COUNT(*) as count FROM heuristics
WHERE domain NOT IN (
    'core-principles', 'golden', 'infrastructure', 'test', 'performance', 'security',
    'system-patterns', 'testing', 'workflow', 'react', 'architecture', 'system-quality',
    'test-domain', 'api', 'autonomousoperations', 'database-performance', 'debugging',
    'development', 'escalation', 'frontend', 'general', 'monitoring', 'parallel',
    'project-management', 'system-migration', 'system', 'system-diagnostics',
    'securitysafety', 'elf-compliance', 'learnedarchitecture', 'learnedgeneral',
    'functionaltest'
)
GROUP BY domain
ORDER BY count DESC;

-- Show cleanup was successful
SELECT 'Heuristics count after cleanup:', COUNT(*) FROM heuristics;
