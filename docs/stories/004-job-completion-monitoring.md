# Job Completion, Monitoring & Testing

## Overview
Implement job completion tracking, failure handling with retry logic, comprehensive monitoring capabilities, and integration testing of the complete ETL pipeline. This ensures production readiness, observability, and the ability to recover from failures.

## Dependencies
- Depends on: 003-data-transformation-loading (all core components must exist)
- Blocks: None (final story, enables production deployment)

## Acceptance Criteria
- [ ] Upon successful warehouse loading, job status is updated to 'completed'
- [ ] Completion timestamp is recorded in the job record
- [ ] Job status is updated to 'failed' when any processing step fails
- [ ] Error message and exception details are captured and stored in job record
- [ ] `retry_count` is incremented on failure
- [ ] Failed jobs can be retried by resetting status to 'pending' (manual intervention)
- [ ] Retry limit is enforced (default max 3 attempts via RETRY_MAX_ATTEMPTS)
- [ ] Worker only processes jobs with status='pending' (skips 'processing', 'completed', 'failed')
- [ ] Monitoring capabilities include:
  - Query jobs table to see status of each job (pending, processing, completed, failed)
  - Review failed jobs with error_message and retry_count fields
  - Identify temporary vs. permanent failures
- [ ] Complete pipeline integration testing:
  - CSV input → jobs created → jobs processed → warehouse loaded → job completed
  - Error scenarios: API failures, database failures, data validation failures
  - Retry scenarios: Temporary API failures recovered on retry
- [ ] Comprehensive documentation:
  - Troubleshooting guide for common failure modes
  - Database monitoring queries
  - Retry procedures for failed jobs
- [ ] Sample flow demonstration (sandbox/sample_run.py):
  - Creates test CSV data
  - Runs full publisher → worker → warehouse flow
  - Displays results and job status
- [ ] All components work together end-to-end:
  - Publisher successfully creates jobs
  - Worker processes all pending jobs
  - Extractors fetch data from APIs (or test doubles)
  - Transformer cleans and merges data
  - Loader inserts into warehouse
  - Jobs table reflects success or failure
  - Can re-run worker safely without duplicate processing

## Technical Details

### Files to Create/Modify
- `worker.py` (update: add completion/failure handling)
- `sandbox/sample_run.py` (create new: demonstration flow)
- `README.md` (update: add troubleshooting section)
- `docs/troubleshooting.md` (create new: detailed debugging guide)

### Database Changes
- Ensure jobs table schema supports:
  - status: 'pending', 'processing', 'completed', 'failed'
  - completed_at: timestamp (nullable)
  - error_message: text field for failure details
  - retry_count: integer tracking attempts
- Add indexes for efficient queries by status and completion date

### Retry Logic Implementation
- After failure, increment retry_count
- Check against RETRY_MAX_ATTEMPTS config (default: 3)
- Only retry if within limit (otherwise mark as 'failed' permanently)
- Can be re-triggered manually by resetting status to 'pending'

### Monitoring Queries (documented)
```sql
-- Check job status overview
SELECT status, COUNT(*) as count FROM jobs GROUP BY status;

-- Find failed jobs needing investigation
SELECT job_id, title, error_message, retry_count FROM jobs 
WHERE status = 'failed' ORDER BY created_at DESC;

-- Monitor processing in progress
SELECT job_id, title, updated_at FROM jobs WHERE status = 'processing';

-- Success rate
SELECT 
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
  COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
FROM jobs;
```

### Configuration
- `RETRY_MAX_ATTEMPTS`: Maximum retry attempts per job (default: 3)
- `BATCH_SIZE`: Jobs per worker run (from story 002)
- All settings in `config.py`

### Environment Variables
- `RETRY_MAX_ATTEMPTS` (default: 3)
- `LOG_LEVEL` (default: INFO) - used for comprehensive logging

## Implementation Notes
- The sample_run.py should use test doubles or mock API responses to avoid dependency on external APIs
- Retry logic must be idempotent (safe to retry multiple times)
- Job completion should be atomic (either fully complete or marked failed, never partial)
- Error messages should be specific enough to aid debugging (include original exception details)
- Consider implementing a "dead letter queue" concept for jobs that exceed retry limits
- Documentation should help ops teams understand failure modes and recovery procedures

## Testing Requirements
- **Unit tests**:
  - Retry count logic and max attempt enforcement
  - Job status transitions
  - Error message capture and storage
  - Monitoring query correctness
- **Integration tests**:
  - Complete end-to-end CSV → warehouse flow
  - Failure and recovery scenarios:
    - API failure → automatic retry success
    - Database connection loss → proper error capture
    - Data validation failure → job marked failed
    - Manual retry after failure
  - Multiple job processing (batch size handling)
  - Idempotency (same job can be retried safely)
  - Concurrent worker instances don't process same job twice
- **Performance tests**:
  - Batch processing with large job counts (100+)
  - Database query performance with many completed jobs
- **Regression tests**:
  - Sample flow completes successfully
  - Monitoring queries return expected results

## Estimated Effort
**Medium: 4-8 hours**

---

## Implementation Steps

1. Update worker.py with job completion/failure handling
2. Implement retry count increment and max attempt checks
3. Build sample_run.py demonstration flow
4. Create comprehensive troubleshooting documentation
5. Write integration tests covering all phases
6. Test failure scenarios and recovery procedures
7. Document monitoring queries and procedures
8. Performance test with large batch sizes
9. Verify end-to-end pipeline with actual data
10. Create runbooks for common operational scenarios

## Production Readiness Checklist
- [ ] All 4 stories implemented and tested
- [ ] No production bugs in sample_run.py flow
- [ ] Error handling covers all failure modes
- [ ] Monitoring capabilities documented
- [ ] Troubleshooting guide complete
- [ ] Retry logic validated
- [ ] Team trained on monitoring and recovery procedures

