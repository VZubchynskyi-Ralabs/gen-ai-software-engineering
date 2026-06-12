# Codebase Research: Calculator Application Bugs

## Research Conducted By
Bug Researcher Agent

## Date
2026-06-12

## Objective
Identify and document bugs in the Calculator CLI application, including file locations, line numbers, and code snippets.

---

## Bug #1: Division by Zero Not Handled

### Location
**File:** `src/calculator.js`  
**Lines:** 18-26  
**Method:** `divide(a, b)`

### Analysis
The divide method performs division without checking if the denominator is zero. This results in JavaScript returning `Infinity` or `NaN` instead of throwing a meaningful error.

### Code Snippet
```javascript
  /**
   * Divide two numbers
   * @param {number} a - Numerator
   * @param {number} b - Denominator
   * @returns {number} Result of a / b
   * 
   * BUG 1: Missing division by zero check
   */
  divide(a, b) {
    // This should check if b === 0 before dividing
    return a / b;
  }
```

### Impact
- User receives `Infinity` or `NaN` instead of clear error message
- Tests expect error to be thrown but none is raised
- Calculation results are invalid and may propagate through application

### Dependencies
None - isolated to Calculator class

### Related Test
**File:** `tests/calculator.test.js`  
**Line:** 22-25
```javascript
    test('should handle division by zero', () => {
      // This test will fail initially due to BUG 1
      expect(() => calculator.divide(10, 0)).toThrow('Division by zero');
    });
```

**Current Status:** ❌ FAILING

---

## Bug #2: Factorial Doesn't Handle Negative Numbers

### Location
**File:** `src/calculator.js`  
**Lines:** 28-42  
**Method:** `factorial(n)`

### Analysis
The factorial method recursively calculates factorial but doesn't validate that the input is non-negative. For negative inputs, the method will recurse infinitely (n becomes more negative) until stack overflow occurs.

### Code Snippet
```javascript
  /**
   * Calculate factorial of a number
   * @param {number} n - Number to calculate factorial for
   * @returns {number} Factorial of n
   * 
   * BUG 2: Doesn't handle negative numbers properly
   */
  factorial(n) {
    // Missing validation for negative numbers
    // factorial(-5) will cause infinite loop or wrong result
    if (n === 0 || n === 1) {
      return 1;
    }
    return n * this.factorial(n - 1);
  }
```

### Impact
- Application crash due to stack overflow
- User input of negative number causes unhandled exception
- No graceful error handling

### Execution Flow for Negative Input
```
factorial(-5)
  → -5 * factorial(-6)
    → -6 * factorial(-7)
      → -7 * factorial(-8)
        ... infinite recursion → RangeError: Maximum call stack size exceeded
```

### Dependencies
None - isolated recursive method

### Related Test
**File:** `tests/calculator.test.js`  
**Line:** 37-40
```javascript
    test('should handle negative numbers', () => {
      // This test will fail initially due to BUG 2
      expect(() => calculator.factorial(-5)).toThrow('Factorial not defined for negative numbers');
    });
```

**Current Status:** ❌ FAILING

---

## Security Issue #1: Hardcoded Credentials

### Location
**File:** `src/userManager.js`  
**Lines:** 7-10  
**Constructor:** `UserManager`

### Analysis
The UserManager class stores administrative credentials as hardcoded values directly in the constructor. This is a critical security vulnerability as anyone with access to the source code can discover the credentials.

### Code Snippet
```javascript
  constructor() {
    // SECURITY ISSUE 1: Hardcoded credentials
    this.hardcodedPassword = 'admin123';
    this.adminUsername = 'admin';
  }
```

### Impact
- **Severity:** CRITICAL
- Credentials exposed to anyone with source code access
- Cannot be changed without modifying code and redeploying
- Violates security best practices
- OWASP A07:2021 – Identification and Authentication Failures

### Dependencies
Used by: `authenticate(username, password)` method (line 19-32)

---

## Security Issue #2: Insecure Comparison Operator

### Location
**File:** `src/userManager.js`  
**Line:** 25  
**Method:** `authenticate(username, password)`

### Analysis
The authentication method uses `==` (loose equality) instead of `===` (strict equality) for comparing credentials. This allows JavaScript's type coercion, which could lead to security issues.

### Code Snippet
```javascript
  authenticate(username, password) {
    // SECURITY: Using == instead of === allows type coercion attacks
    // SECURITY: Hardcoded credentials
    if (username == this.adminUsername && password == this.hardcodedPassword) {
      return true;
    }
    // ...
  }
```

### Impact
- **Severity:** MEDIUM
- Type coercion could allow unexpected values to pass authentication
- Examples: `"0" == 0` is true, `null == undefined` is true
- Best practice violation even if not immediately exploitable

---

## Security Issue #3: SQL Injection Vulnerability (Simulated)

### Location
**File:** `src/userManager.js`  
**Lines:** 29-30  
**Method:** `authenticate(username, password)`

### Analysis
The method demonstrates SQL injection vulnerability by concatenating user input directly into a SQL query string without sanitization or parameterization.

### Code Snippet
```javascript
    // This simulates a SQL query that would be vulnerable to SQL injection
    const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
    console.log(`[DEBUG] Simulated query: ${query}`);
```

### Impact
- **Severity:** CRITICAL
- Complete database compromise possible
- Attacker could bypass authentication, read/modify data, or drop tables
- OWASP A03:2021 – Injection

### Attack Example
Input: `username = "admin'--"`, `password = "ignored"`

Resulting query:
```sql
SELECT * FROM users WHERE username = 'admin'--' AND password = 'ignored'
```
The `--` comments out the password check, allowing login without valid password.

---

## Security Issue #4: Predictable Token Generation

### Location
**File:** `src/userManager.js`  
**Lines:** 48-52  
**Method:** `generateSessionToken(username)`

### Analysis
Session tokens are generated using only the username and current timestamp, making them predictable and susceptible to brute-force attacks.

### Code Snippet
```javascript
  generateSessionToken(username) {
    // SECURITY: Using timestamp makes tokens predictable
    return `${username}_${Date.now()}`;
  }
```

### Impact
- **Severity:** MEDIUM
- Tokens can be guessed (timestamp is predictable within milliseconds)
- Session hijacking possible
- OWASP A02:2021 – Cryptographic Failures

### Example Token
```
admin_1717891234567
```
An attacker knowing the pattern could generate valid tokens by iterating through recent timestamps.

---

## File Dependencies Map

### src/calculator.js
- **Used by:** `src/index.js` (line 5)
- **Exports:** `{ Calculator }` class
- **Dependencies:** None
- **Bugs:** BUG-001 (divide), BUG-002 (factorial)

### src/userManager.js
- **Used by:** `src/index.js` (line 6)
- **Exports:** `{ UserManager }` class
- **Dependencies:** None
- **Security Issues:** SEC-001, SEC-002, SEC-003, SEC-004

### src/index.js
- **Entry point:** Application main file
- **Dependencies:** 
  - `readline` (Node.js built-in)
  - `chalk` (npm package)
  - `./calculator`
  - `./userManager`
- **Issues:** Uses vulnerable UserManager and buggy Calculator

---

## Test Coverage Analysis

### tests/calculator.test.js
**Lines:** 1-43  
**Test Count:** 7 tests total
- ✅ 5 passing tests (add, multiply, basic factorial)
- ❌ 2 failing tests (division by zero, negative factorial)

### Missing Tests
No tests exist for UserManager security issues. Unit Test Generator should create:
- Tests for authentication method
- Tests for password validation
- Tests for token generation

---

## Recommendations

### For Bug Fixer Agent
1. Add zero-check in `divide()` method before division
2. Add negative number validation in `factorial()` method before recursion
3. Run tests after each fix to verify

### For Security Verifier Agent
1. Identify all four security issues in UserManager
2. Rate hardcoded credentials as CRITICAL
3. Rate SQL injection as CRITICAL
4. Rate type coercion and predictable tokens as MEDIUM

### For Unit Test Generator Agent
1. Generate additional tests for edge cases in Calculator
2. Generate security-focused tests for UserManager
3. Ensure all tests follow FIRST principles
4. Use mocks if needed for UserManager dependencies

---

## References

### Source Files
- `src/calculator.js` - 47 lines - 2 bugs identified
- `src/userManager.js` - 52 lines - 4 security issues identified
- `src/index.js` - 95 lines - Uses vulnerable components
- `tests/calculator.test.js` - 43 lines - 2 failing tests

### External Resources
- OWASP Top 10 2021: https://owasp.org/Top10/
- JavaScript Factorial: https://en.wikipedia.org/wiki/Factorial
- SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection

---

## Conclusion

This research has identified:
- **2 functional bugs** requiring fixes
- **4 security vulnerabilities** requiring remediation
- **2 failing tests** that will pass once bugs are fixed
- **Clear file:line references** for all issues

All claims in this research can be verified by reading the referenced source files at the specified line numbers.

