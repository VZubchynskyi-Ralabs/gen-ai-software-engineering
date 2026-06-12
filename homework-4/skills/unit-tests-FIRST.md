# Unit Tests FIRST Principles Skill

## Purpose
This skill defines the FIRST principles for writing high-quality unit tests. Unit test generator agents must follow these principles when creating tests.

## The FIRST Principles

### F - Fast ⚡
**Definition:** Tests should run quickly (milliseconds to seconds, not minutes)

**Why it matters:**
- Fast tests encourage frequent execution
- Developers get immediate feedback
- CI/CD pipelines complete faster
- Test-driven development (TDD) is practical

**Best Practices:**
- Avoid I/O operations (file system, network, database)
- Use mocks/stubs for external dependencies
- Keep test data minimal
- Avoid Thread.sleep() or artificial delays
- Target: <100ms per test, <10s for entire suite

**Example - Fast test:**
```javascript
test('should calculate sum of two numbers', () => {
  const calculator = new Calculator();
  expect(calculator.add(2, 3)).toBe(5);
  // Runs in <1ms
});
```

**Example - Slow test (avoid):**
```javascript
test('should fetch user from database', async () => {
  const db = await connectToDatabase(); // ❌ Real DB connection
  const user = await db.users.findById(1);
  expect(user.name).toBe('John');
  // Takes 500ms+ per test
});
```

---

### I - Independent 🔀
**Definition:** Tests should not depend on each other or shared state

**Why it matters:**
- Tests can run in any order
- Parallel execution is possible
- Failures are isolated and easy to debug
- No cascading failures

**Best Practices:**
- Each test sets up its own data
- Use `beforeEach()` for fresh state
- Avoid global variables or shared state
- Don't rely on test execution order
- Clean up after each test

**Example - Independent test:**
```javascript
describe('Calculator', () => {
  let calculator;
  
  beforeEach(() => {
    calculator = new Calculator(); // Fresh instance each test
  });
  
  test('test 1', () => {
    expect(calculator.add(1, 1)).toBe(2);
  });
  
  test('test 2', () => {
    expect(calculator.add(2, 2)).toBe(4);
  });
  // Tests can run in any order
});
```

**Example - Dependent test (avoid):**
```javascript
let sharedResult; // ❌ Shared state

test('test 1', () => {
  sharedResult = calculator.add(1, 1);
  expect(sharedResult).toBe(2);
});

test('test 2', () => {
  expect(sharedResult).toBe(2); // ❌ Depends on test 1
});
```

---

### R - Repeatable 🔁
**Definition:** Tests should produce the same result every time they run

**Why it matters:**
- Reliable test results build confidence
- No flaky tests that randomly fail
- Debugging is easier
- CI/CD results are trustworthy

**Best Practices:**
- Avoid randomness (use fixed seeds if needed)
- Don't depend on current date/time (mock it)
- Eliminate external dependencies
- Control all inputs
- Ensure deterministic behavior

**Example - Repeatable test:**
```javascript
test('should format date correctly', () => {
  const fixedDate = new Date('2024-01-15');
  const formatted = formatDate(fixedDate);
  expect(formatted).toBe('2024-01-15');
  // Always produces same result
});
```

**Example - Non-repeatable test (avoid):**
```javascript
test('should format current date', () => {
  const formatted = formatDate(new Date()); // ❌ Uses current date
  expect(formatted).toBe('2024-01-15');
  // Will fail tomorrow!
});
```

---

### S - Self-Validating ✅
**Definition:** Tests should have clear pass/fail results without manual inspection

**Why it matters:**
- No human interpretation needed
- Automated CI/CD integration
- Clear success/failure signals
- No ambiguity

**Best Practices:**
- Use assertions (expect, assert)
- Don't use console.log for validation
- Don't require manual output inspection
- Binary outcome: pass or fail
- Clear error messages

**Example - Self-validating test:**
```javascript
test('should divide two numbers', () => {
  const result = calculator.divide(10, 2);
  expect(result).toBe(5); // ✅ Clear assertion
});
```

**Example - Not self-validating (avoid):**
```javascript
test('should divide two numbers', () => {
  const result = calculator.divide(10, 2);
  console.log('Result:', result); // ❌ Requires manual checking
  // No assertion - did it pass or fail?
});
```

---

### T - Timely ⏰
**Definition:** Tests should be written at the right time (ideally before or with the code)

**Why it matters:**
- TDD improves design
- Tests guide implementation
- Better code coverage
- Catches bugs early

**Best Practices:**
- Write tests before or during development (TDD/BDD)
- Don't wait until the end of the project
- Test while requirements are fresh
- Update tests when code changes
- New features should include tests

**Timing Approaches:**
1. **Test-First (TDD):** Write test → Watch it fail → Write code → Test passes
2. **Test-During:** Write code and tests in parallel
3. **Test-After (avoid):** Write all code first, then write tests

**Example - Timely (TDD approach):**
```javascript
// Step 1: Write failing test
test('should validate negative numbers in factorial', () => {
  expect(() => calculator.factorial(-5))
    .toThrow('Factorial not defined for negative numbers');
});
// Test fails (feature doesn't exist yet)

// Step 2: Implement feature
factorial(n) {
  if (n < 0) throw new Error('Factorial not defined for negative numbers');
  // ... rest of implementation
}
// Now test passes
```

---

## FIRST Checklist for Test Generation

When generating unit tests, verify each test meets ALL FIRST criteria:

- [ ] **Fast:** Test runs in <100ms without I/O operations
- [ ] **Independent:** Test doesn't depend on other tests or shared state
- [ ] **Repeatable:** Test produces same result every time
- [ ] **Self-Validating:** Test has clear assertions and pass/fail outcome
- [ ] **Timely:** Test is written for current/changed code (applicable for generation)

## Test Structure Template

```javascript
describe('[Component/Class Name]', () => {
  // Setup - runs before each test (Independent)
  let instanceUnderTest;
  
  beforeEach(() => {
    instanceUnderTest = new ComponentUnderTest();
  });
  
  describe('[method name]', () => {
    test('should [expected behavior] when [condition]', () => {
      // Arrange - Set up test data (Fast, Repeatable)
      const input = fixedTestValue;
      
      // Act - Execute the code under test
      const result = instanceUnderTest.method(input);
      
      // Assert - Verify the outcome (Self-Validating)
      expect(result).toBe(expectedValue);
    });
  });
});
```

## Common FIRST Violations to Avoid

❌ **Not Fast:** Using setTimeout, real database, actual API calls
❌ **Not Independent:** Tests modifying global state, test order matters
❌ **Not Repeatable:** Using Math.random(), new Date(), external services
❌ **Not Self-Validating:** Only logging output, manual verification needed
❌ **Not Timely:** Tests written months after code, outdated test suite

## Quality Metrics

A FIRST-compliant test suite should have:
- **95%+** of tests run in <100ms
- **100%** of tests can run in any order
- **100%** of tests are deterministic (no flaky tests)
- **100%** of tests have assertions
- **Tests written within same sprint/iteration as code**

## Usage by Unit Test Generator Agent

The agent should:
1. Analyze changed code to determine what needs testing
2. Generate tests that satisfy ALL five FIRST principles
3. Use mocks/stubs for external dependencies (Fast + Repeatable)
4. Create fresh instances in beforeEach (Independent)
5. Use fixed test data (Repeatable)
6. Include clear expect() assertions (Self-Validating)
7. Focus on currently changed code (Timely)
8. Run generated tests to verify they pass
9. Document FIRST compliance in test-report.md

## Example: Full FIRST-Compliant Test Suite

```javascript
const { Calculator } = require('../src/calculator');

describe('Calculator', () => {
  let calculator;

  // I: Independent - fresh instance for each test
  beforeEach(() => {
    calculator = new Calculator();
  });

  describe('add', () => {
    // F: Fast - no I/O, runs in milliseconds
    // I: Independent - doesn't affect other tests
    // R: Repeatable - same inputs, same outputs
    // S: Self-Validating - clear assertion
    // T: Timely - testing current implementation
    test('should add two positive numbers', () => {
      expect(calculator.add(2, 3)).toBe(5);
    });

    test('should handle negative numbers', () => {
      expect(calculator.add(-2, 3)).toBe(1);
    });
  });

  describe('divide', () => {
    test('should divide two numbers', () => {
      expect(calculator.divide(10, 2)).toBe(5);
    });

    test('should throw error for division by zero', () => {
      expect(() => calculator.divide(10, 0))
        .toThrow('Division by zero');
    });
  });
});
```

This test suite is:
- ⚡ **Fast:** All tests run in <10ms total
- 🔀 **Independent:** Tests can run in any order, no shared state
- 🔁 **Repeatable:** Always produces same results
- ✅ **Self-Validating:** Clear pass/fail with assertions
- ⏰ **Timely:** Tests the current Calculator implementation

