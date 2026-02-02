# Dashboard App Backend Performance Testing

This directory contains comprehensive performance testing tools for the Dashboard-App backend, designed to measure and optimize query performance before and after index creation.

## Files

### Main Performance Testing Script
- **`test_query_performance.py`** - Comprehensive performance testing suite with mock data generation

### Quick Testing Tools
- **`quick_performance_test.py`** - Fast performance demonstration using real database

## Features

### Comprehensive Testing (`test_query_performance.py`)

The main performance testing script provides:

#### Mock Data Generation
- 1,000 heuristics records
- 2,000 learnings records  
- 5,000 workflow runs
- 10,000 metrics records
- 500 workflow definitions

#### Performance Metrics Measured
- **Query execution time** (milliseconds)
- **Memory usage** (peak MB)
- **Data transfer size** (KB)
- **Rows and columns returned**

#### Test Coverage
1. **Stats Endpoint** (`/api/v1/stats`)
   - Consolidated count queries
   - Aggregate functions

2. **Learning Velocity** (`/api/v1/learning-velocity`)
   - Date-based grouping
   - Time-based filtering

3. **Heuristics Endpoint** (`/api/v1/heuristics`)
   - Optimized vs unoptimized queries
   - Pagination performance

4. **Learnings Endpoint** (`/api/v1/knowledge/learnings`)
   - Specific column selection vs SELECT *
   - Pagination with OFFSET

5. **Workflows List** (`/api/v1/workflows/list`)
   - ORDER BY optimization
   - Large dataset pagination

#### Index Performance Testing
Tests performance before and after creating these indexes:
- `idx_heuristics_confidence` - For confidence ordering
- `idx_heuristics_domain` - For domain filtering
- `idx_heuristics_created` - For date-based queries
- `idx_learnings_type` - For type filtering
- `idx_learnings_domain` - For domain filtering
- `idx_learnings_created` - For date ordering
- `idx_workflow_runs_status` - For status filtering
- `idx_workflow_runs_created` - For date ordering
- `idx_metrics_type` - For type filtering
- `idx_metrics_timestamp` - For time-series queries
- `idx_workflows_created` - For date ordering

## Usage

### Run Comprehensive Performance Test
```bash
# Basic test with auto-cleanup
python test_query_performance.py

# Keep test database for inspection
python test_query_performance.py --no-cleanup

# Custom output file
python test_query_performance.py --output my_report.json

# Custom database path
python test_query_performance.py --db-path /path/to/database.db
```

### Run Quick Performance Test
```bash
python quick_performance_test.py
```

## Report Output

### JSON Report Structure
```json
{
  "timestamp": "2026-02-02T18:19:10.829842",
  "test_results": [...],
  "mock_data_stats": {
    "heuristics": 1000,
    "learnings": 2000,
    "workflow_runs": 5000,
    "metrics": 10000,
    "workflows": 500
  },
  "indexes_created": [...],
  "recommendations": [...],
  "summary": {
    "total_tests": 5,
    "avg_time_before": 0.63,
    "avg_time_after": 0.51,
    "overall_improvement": 18.0,
    "data_reduction_optimized": 0.2
  }
}
```

### Console Summary
The script prints a human-readable summary including:
- Mock data generated
- Performance metrics before/after indexes
- Percentage improvements
- Recommendations for optimization

## Performance Optimizations Tested

### 1. Column Selection Optimization
- **Before**: `SELECT * FROM table`
- **After**: `SELECT id, name, created_at FROM table`
- **Benefit**: Reduced data transfer, improved query speed

### 2. Index Creation
- Tests performance with and without strategic indexes
- Measures improvement in filtering, sorting, and joining

### 3. Pagination Optimization
- Tests `LIMIT` and `OFFSET` performance
- Ensures scalability with large datasets

### 4. Query Structure
- Compares different query approaches
- Identifies optimal patterns for common operations

## Sample Results

### Performance Improvements Demonstrated
- **Learning Velocity**: 59.7% improvement with indexes
- **Heuristics Endpoint**: 24.3% improvement with indexes
- **Learnings Endpoint**: 27.2% improvement with indexes
- **Workflows List**: 30.5% improvement with indexes

### Data Transfer Optimization
- Column selection can reduce data transfer by up to 40%
- Memory usage improvements proportional to data reduction

## Recommendations Generated

The testing tool automatically generates recommendations such as:

1. **Query Optimization**
   - Use specific columns instead of SELECT *
   - Implement proper pagination
   - Add covering indexes for frequent queries

2. **Index Strategy**
   - Create indexes on frequently filtered columns
   - Consider composite indexes for complex queries
   - Monitor index effectiveness

3. **Performance Monitoring**
   - Regular query execution plan analysis
   - Monitor slow query logs
   - Track performance trends over time

## Integration with Development Workflow

### Before Production Deployments
```bash
# Run full performance test suite
python test_query_performance.py --output pre_deployment_perf.json
```

### During Development
```bash
# Quick performance check
python quick_performance_test.py
```

### Performance Regression Testing
Compare reports over time to detect performance regressions:
```bash
# Compare with baseline
diff performance_report_baseline.json performance_report_latest.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure script is run from the backend directory
2. **Permission Errors**: Check write permissions for report output
3. **Database Locks**: Close other connections before testing

### Debug Mode
For detailed error information:
```bash
python test_query_performance.py --no-cleanup
# Then inspect test database manually
sqlite3 /path/to/test_performance.db
```

## Dependencies

- `psutil` - For memory usage monitoring
- `tracemalloc` - Built-in Python memory tracer
- `sqlite3` - Built-in Python database interface

Install additional dependency if needed:
```bash
pip install psutil
```

## Best Practices

1. **Regular Testing**: Run performance tests regularly to catch regressions
2. **Baseline Establishment**: Create performance baselines for comparison
3. **Continuous Monitoring**: Use quick tests during development
4. **Report Analysis**: Review detailed JSON reports for optimization opportunities
5. **Index Maintenance**: Regularly review and update index strategy

## Future Enhancements

Potential improvements to the testing suite:

1. **Concurrent Load Testing**: Test performance under concurrent load
2. **Database Size Scaling**: Test with larger datasets (10K, 100K, 1M records)
3. **Query Plan Analysis**: Include EXPLAIN QUERY PLAN in test results
4. **Regression Detection**: Automatic comparison with previous test results
5. **CI/CD Integration**: Automated performance testing in deployment pipelines