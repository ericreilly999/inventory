# Fix CI/CD Pipeline Failures - Design Document

## Architecture Overview

This design addresses systematic fixes to the CI/CD pipeline failures across four main areas:
1. Infrastructure validation (Terraform)
2. Code quality (Flake8 linting)
3. Test coverage
4. Test reliability

## Design Decisions

### 1. Terraform RDS Module Fix

**Problem:** Random password resource creates marked values that crash when used in conditionals.

**Solution:** Restructure to avoid conditional evaluation of marked values.

```hcl
# Current (broken):
locals {
  db_password = var.db_password != null ? var.db_password : (
    length(random_password.db_password) > 0 ? nonsensitive(random_password.db_password[0].result) : ""
  )
}

# Fixed approach:
resource "random_password" "db_password" {
  count   = var.db_password == null ? 1 : 0
  length  = 16
  special = true
}

locals {
  # Separate the marked value extraction from conditional logic
  db_password = var.db_password != null ? var.db_password : try(nonsensitive(random_password.db_password[0].result), "")
}
```

**Rationale:** Using `try()` function avoids conditional evaluation of the marked value directly.

### 2. Flake8 Linting Strategy

**Approach:** Automated fixes where possible, manual review for complex cases.

**Tools:**
- `autopep8` for automatic E501 fixes
- `autoflake` for F841 (unused variables)
- Manual fixes for E712, E741, E402, F541, E203

**Line Length Strategy:**
- Break long lines at logical points (operators, commas)
- Use parentheses for implicit line continuation
- Maintain readability over strict adherence

### 3. Test Coverage Strategy

**Current Coverage:** 21%  
**Target Coverage:** 80%

**Approach:**
1. **Phase 1:** Add integration tests for 0% coverage routers
2. **Phase 2:** Add unit tests for business logic
3. **Phase 3:** Add edge case tests

**Priority Areas:**
- Service routers (highest impact)
- Dependencies modules
- Shared utilities

**Test Types:**
- Integration tests: API endpoint testing
- Unit tests: Business logic, validation
- Property-based tests: Already exist, maintain

### 4. Test Isolation Fix

**Problem:** Tests sharing database state causing unique constraint violations.

**Root Cause Analysis:**
- `test_db_session` fixture not properly isolated
- Tables not being cleaned between tests
- Module-level table creation causing state persistence

**Solution:**

```python
# conftest.py
@pytest.fixture(scope="function")
def test_db_session():
    """Provide a transactional database session for tests."""
    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
```

**Key Changes:**
- Function scope (not module scope)
- Explicit table drop after each test
- Engine disposal to prevent connection leaks

### 5. Datetime Handling

**Problem:** Timezone-naive vs timezone-aware datetime comparisons.

**Solution:** Ensure all datetime objects are timezone-aware.

```python
from datetime import datetime, timezone

# Always use timezone-aware datetimes
moved_at = datetime.now(timezone.utc)

# In tests, compare with timezone-aware datetimes
assert move.moved_at == expected_time  # Both must be timezone-aware
```

## Implementation Plan

### Phase 1: Infrastructure (Priority: Critical)
1. Fix Terraform RDS module
2. Validate terraform in all environments
3. Test deployment pipeline

### Phase 2: Code Quality (Priority: High)
1. Run autopep8 for line length fixes
2. Fix boolean comparisons (E712)
3. Remove unused variables (F841)
4. Fix remaining linting issues
5. Run black and isort for final formatting

### Phase 3: Test Reliability (Priority: High)
1. Fix database isolation in conftest.py
2. Fix timezone-aware datetime issues
3. Fix authentication edge cases
4. Fix API contract tests
5. Fix inter-service communication tests
6. Verify all tests pass

### Phase 4: Test Coverage (Priority: Medium)
1. Add integration tests for service routers
2. Add unit tests for dependencies
3. Add tests for shared utilities
4. Verify 80% coverage threshold

### Phase 5: Cleanup (Priority: Low)
1. Remove temporary files
2. Update documentation
3. Final CI/CD verification

## Testing Strategy

### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Focus on business logic

### Integration Tests
- Test API endpoints end-to-end
- Use test database
- Verify request/response contracts

### Property-Based Tests
- Already exist, maintain them
- Ensure they pass with new changes

## Rollout Strategy

1. **Create feature branch:** `fix/cicd-pipeline`
2. **Implement fixes in order:** Infrastructure → Quality → Tests → Coverage
3. **Commit after each phase:** Allows incremental progress tracking
4. **Push and verify:** Check GitHub Actions after each push
5. **Iterate:** Fix any new issues that arise
6. **Merge:** Once all checks pass

## Monitoring and Validation

### Success Metrics
- GitHub Actions: All workflows green
- Flake8: 0 violations
- Test Coverage: ≥80%
- Test Results: 0 failures
- Terraform: Validation passes

### Validation Steps
1. Run flake8 locally before push
2. Run pytest with coverage locally
3. Run terraform validate locally
4. Push and wait for GitHub Actions
5. Review logs for any failures
6. Iterate until all pass

## Risk Mitigation

### Risks
1. **Breaking changes:** Linting fixes might break functionality
2. **Test flakiness:** Database isolation might not be perfect
3. **Coverage gaps:** Hard to reach 80% without extensive tests
4. **Time constraints:** Large scope of work

### Mitigation
1. **Incremental changes:** Small commits, easy to revert
2. **Thorough testing:** Run tests locally before push
3. **Pragmatic coverage:** Focus on high-value tests
4. **Automated tools:** Use autopep8, autoflake where possible

## Dependencies

### External
- GitHub Actions runners
- Terraform validation
- Python 3.11 environment

### Internal
- Test fixtures in conftest.py
- Shared models and utilities
- Service routers and dependencies

## Future Improvements

1. **Pre-commit hooks:** Enforce linting before commit
2. **Coverage ratcheting:** Prevent coverage from decreasing
3. **Automated formatting:** CI job to auto-format code
4. **Test parallelization:** Speed up test execution
5. **Terraform modules:** Better organization and reusability
