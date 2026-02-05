# Heuristic: Database Recovery Process

## Rule
When the Emergent Learning Framework shows database synchronization issues:
1. Run the bootstrap recovery script (`/home/bamer/.opencode/emergent-learning/scripts/bootstrap-recovery.sh --auto`)
2. Verify database integrity after recovery
3. Check file-system/database synchronization status
4. Address any remaining inconsistencies manually

## Explanation
The bootstrap recovery script can resolve many common database issues by:
- Creating backups before making changes
- Fixing directory structure problems
- Optimizing database performance
- Cleaning temporary files
- Verifying database integrity

## Context
During system diagnostics, we found that the database had synchronization issues between file system records and database entries. Running the bootstrap recovery script successfully restored database functionality.

## Confidence
0.8

## Validation
This approach was validated during the diagnostic process and successfully restored system functionality.

## Domain
meta-learning

## Tags
database, recovery, synchronization, maintenance