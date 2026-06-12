# Implementation Plan: Fix Calculator Bugs

## Plan Created By
Bug Planner Agent

## Date
2026-06-12

## Objective
Fix two functional bugs in the Calculator class based on verified research findings.

---

## Summary

This plan addresses two critical bugs in `src/calculator.js`:
1. **BUG-001:** Division by zero not handled
2. **BUG-002:** Factorial doesn't validate negative numbers

Both fixes involve adding validation before performing the mathematical operation and throwing descriptive errors when invalid input is detected.

---

## Changes Required

### Change 1: Fix Division by Zero

**File:** `src/calculator.js`  
**Method:** `divide(a, b)`  
**Lines:** 23-25 (approximate)

**Before:**
```javascript
  divide(a, b) {
    // This should check if b === 0 before dividing
    return a / b;
  }
```

**After:**
```javascript
  divide(a, b) {
    if (b === 0) {
      throw new Error('Division by zero');
    }
    return a / b;
  }
```

**Rationale:**
- Prevents returning `Infinity` or `NaN`
- Provides clear error message to users
- Makes the error catchable and handleable
- Aligns with test expectations

**Test Impact:**
- Test `should handle division by zero` will now PASS
- Existing passing tests remain unaffected

---

### Change 2: Fix Factorial for Negative Numbers

**File:** `src/calculator.js`  
**Method:** `factorial(n)`  
**Lines:** 34-39 (approximate)

**Before:**
```javascript
  factorial(n) {
    // Missing validation for negative numbers
    // factorial(-5) will cause infinite loop or wrong result
    if (n === 0 || n === 1) {
      return 1;
    }
    return n * this.factorial(n - 1);
  }
```

**After:**
```javascript
  factorial(n) {
    if (n < 0) {
      throw new Error('Factorial not defined for negative numbers');
    }
    if (n === 0 || n === 1) {
      return 1;
    }
    return n * this.factorial(n - 1);
  }
```

**Rationale:**
- Prevents infinite recursion and stack overflow
- Mathematically correct (factorial is undefined for negative integers)
- Provides clear error message
- Aligns with test expectations

**Test Impact:**
- Test `should handle negative numbers` will now PASS
- Existing positive number factorial tests remain unaffected

---

## Testing Strategy

### Test Command
```bash
npm test
```

### Expected Test Results After Fixes

**Before Fixes:**
```
FAIL tests/calculator.test.js
  Calculator
    divide
      ✗ should handle division by zero (8ms)
    factorial
      ✗ should handle negative numbers (7ms)

Tests: 2 failed, 5 passed, 7 total
```

**After Fixes:**
```
PASS tests/calculator.test.js
  Calculator
    add
      ✓ should add two positive numbers (2ms)
      ✓ should add negative numbers (1ms)
    divide
      ✓ should divide two numbers (1ms)
      ✓ should handle division by zero (1ms)
    factorial
      ✓ should calculate factorial of positive number (1ms)
      ✓ should return 1 for factorial of 0 (1ms)
      ✓ should handle negative numbers (1ms)
    multiply
      ✓ should multiply two numbers (1ms)

Tests: 8 passed, 8 total
```

### Test-Driven Development Approach
1. Run tests before making changes (confirm 2 failures)
2. Apply Fix #1 (division by zero)
3. Run tests (confirm 1 failure resolved)
4. Apply Fix #2 (factorial negative numbers)
5. Run tests (confirm all tests pass)

---

## Implementation Order

1. **First:** Fix `divide` method
   - Simpler fix (single condition check)
   - Lower risk of introducing new bugs
   
2. **Second:** Fix `factorial` method
   - Slightly more complex (recursive function)
   - Must ensure validation comes before recursion

---

## Dependencies

### Code Dependencies
None - both methods are self-contained with no external dependencies

### Package Dependencies
No new packages required - fixes use native JavaScript

---

## Rollback Plan

If tests fail after implementing fixes:

```bash
# Restore original file
git checkout src/calculator.js

# Re-run tests to confirm 2 failures
npm test
```

---

## Manual Verification Steps

After automated tests pass, manually verify:

### Manual Test 1: Division by Zero
```bash
npm start
# Select: 2 (Divide numbers)
# Enter numerator: 10
# Enter denominator: 0
# Expected: Error message displayed (not "Infinity")
```

### Manual Test 2: Negative Factorial
```bash
npm start
# Select: 3 (Calculate factorial)
# Enter number: -5
# Expected: Error message displayed (not stack overflow)
```

### Manual Test 3: Normal Operations Still Work
```bash
npm start
# Select: 2 (Divide numbers)
# Enter numerator: 10
# Enter denominator: 2
# Expected: Result: 5

# Select: 3 (Calculate factorial)
# Enter number: 5
# Expected: Result: 120
```

---

## Risk Assessment

### Low Risk Changes
Both changes are minimal code additions:
- Adding validation before existing logic
- Not modifying core algorithm logic
- Throwing standard JavaScript errors

### Potential Issues
- **None expected** - changes are defensive and additive
- Error handling is standard JavaScript pattern
- Tests are comprehensive and should catch any issues

---

## Code Quality Considerations

### Error Message Consistency
- Use descriptive, user-friendly error messages
- "Division by zero" - clear and standard
- "Factorial not defined for negative numbers" - mathematical accuracy

### Performance Impact
- Negligible - single condition check per method call
- O(1) additional complexity

### Maintainability
- Code becomes more robust and self-documenting
- Error cases are explicitly handled
- Future developers can see validation logic clearly

---

## Documentation Updates

No documentation updates required - JSDoc comments already mention the bugs and these fixes address them.

---

## Review Checklist

Before implementation:
- [x] Verified research findings are accurate
- [x] Identified exact locations for changes
- [x] Defined before/after code clearly
- [x] Specified test command
- [x] Documented expected test outcomes
- [x] Created manual verification steps
- [x] Assessed risks

After implementation (for Bug Fixer):
- [ ] Applied change #1
- [ ] Ran tests after change #1
- [ ] Applied change #2
- [ ] Ran tests after change #2
- [ ] All automated tests pass
- [ ] Performed manual verification
- [ ] Created fix-summary.md

---

## References

- **Verified Research:** `research/verified-research.md`
- **Bug Context:** `bug-context.md`
- **Source File:** `src/calculator.js`
- **Test File:** `tests/calculator.test.js`

---

## Conclusion

This implementation plan provides clear, actionable steps to fix both bugs in the Calculator class. The changes are minimal, low-risk, and well-tested. Once implemented, all existing tests should pass, and the application will handle edge cases gracefully.

**Estimated Implementation Time:** 5 minutes  
**Estimated Testing Time:** 2 minutes  
**Total Effort:** 7 minutes

