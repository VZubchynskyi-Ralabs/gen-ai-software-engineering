# Bug Context: Calculator Application Issues

## Bug Overview

This document describes the intentional bugs and security issues present in the Calculator CLI application for the 4-agent pipeline to detect and fix.

## Bug ID: BUG-001

### Title
Division by Zero Not Handled

### Description
The Calculator's `divide` method does not check for division by zero, resulting in `Infinity` or `NaN` results instead of proper error handling.

### Location
- **File:** `src/calculator.js`
- **Method:** `divide(a, b)`
- **Lines:** 18-21 (approximate)

### Current Behavior
```javascript
divide(a, b) {
  // This should check if b === 0 before dividing
  return a / b;
}
```

When dividing by zero:
```
calculator.divide(10, 0) => Infinity
calculator.divide(0, 0) => NaN
```

### Expected Behavior
The method should throw a descriptive error when attempting to divide by zero:
```javascript
divide(a, b) {
  if (b === 0) {
    throw new Error('Division by zero');
  }
  return a / b;
}
```

### Impact
- **Severity:** Medium
- **User Impact:** Confusing results, application doesn't fail gracefully
- **Data Impact:** Invalid calculations may propagate through the application

### Steps to Reproduce
1. Run the application: `npm start`
2. Select option 2 (Divide numbers)
3. Enter numerator: 10
4. Enter denominator: 0
5. Observe result: `Infinity`

### Test Case
Current test in `tests/calculator.test.js` expects this behavior to fail but currently doesn't:
```javascript
test('should handle division by zero', () => {
  expect(() => calculator.divide(10, 0)).toThrow('Division by zero');
});
```

### Fix Priority
**High** - This is a fundamental mathematical operation that should have proper error handling.

---

## Bug ID: BUG-002

### Title
Factorial Method Doesn't Handle Negative Numbers

### Description
The Calculator's `factorial` method does not validate that the input is non-negative, causing infinite recursion or incorrect results for negative numbers.

### Location
- **File:** `src/calculator.js`
- **Method:** `factorial(n)`
- **Lines:** 32-42 (approximate)

### Current Behavior
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

When called with negative number:
```
calculator.factorial(-5) => Infinite recursion (stack overflow)
```

### Expected Behavior
The method should validate input and throw an error for negative numbers:
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

### Impact
- **Severity:** High
- **User Impact:** Application crash (stack overflow)
- **System Impact:** Potential denial of service if inputs are not validated

### Steps to Reproduce
1. Run the application: `npm start`
2. Select option 3 (Calculate factorial)
3. Enter a negative number: -5
4. Observe: Stack overflow error

### Test Case
Current test expects proper error handling:
```javascript
test('should handle negative numbers', () => {
  expect(() => calculator.factorial(-5))
    .toThrow('Factorial not defined for negative numbers');
});
```

### Fix Priority
**High** - This causes application crashes and must be fixed before production use.

---

## Security Issue ID: SEC-001

### Title
Hardcoded Admin Credentials

### Description
The UserManager class contains hardcoded administrative credentials directly in the source code, violating security best practices.

### Location
- **File:** `src/userManager.js`
- **Constructor:** Lines 8-10 (approximate)

### Vulnerable Code
```javascript
constructor() {
  // SECURITY ISSUE 1: Hardcoded credentials
  this.hardcodedPassword = 'admin123';
  this.adminUsername = 'admin';
}
```

### Security Impact
- **Severity:** CRITICAL
- **OWASP Category:** A07:2021 – Identification and Authentication Failures
- **Risk:** Anyone with access to source code knows admin credentials

### Attack Scenario
1. Attacker gains access to source code (GitHub, leaked codebase, etc.)
2. Discovers hardcoded credentials: username=`admin`, password=`admin123`
3. Logs into system with admin privileges
4. Full system compromise

### Remediation
1. Remove hardcoded credentials from source code
2. Use environment variables or secure configuration management
3. Implement proper authentication with hashed passwords stored in database
4. Use secure secret management (e.g., AWS Secrets Manager, HashiCorp Vault)

### Additional Context
This is combined with other security issues in the same file (insecure comparison, SQL injection simulation).

---

## Security Issue ID: SEC-002

### Title
Insecure String Comparison (Type Coercion)

### Description
The `authenticate` method uses `==` instead of `===`, allowing type coercion attacks.

### Location
- **File:** `src/userManager.js`
- **Method:** `authenticate(username, password)`
- **Line:** 25 (approximate)

### Vulnerable Code
```javascript
if (username == this.adminUsername && password == this.hardcodedPassword) {
  return true;
}
```

### Security Impact
- **Severity:** MEDIUM
- **OWASP Category:** A04:2021 – Insecure Design
- **Risk:** Type coercion could bypass authentication in certain scenarios

### Attack Scenario
While less critical with hardcoded strings, using `==` can lead to unexpected behavior:
```javascript
"admin" == "admin" // true
"0" == 0 // true (type coercion!)
null == undefined // true (type coercion!)
```

### Remediation
Always use `===` for comparisons in security-sensitive contexts:
```javascript
if (username === this.adminUsername && password === this.hardcodedPassword) {
  return true;
}
```

---

## Security Issue ID: SEC-003

### Title
SQL Injection Vulnerability (Simulated)

### Description
The authenticate method demonstrates SQL injection vulnerability by concatenating user input directly into a SQL query string.

### Location
- **File:** `src/userManager.js`
- **Method:** `authenticate(username, password)`
- **Lines:** 29-30 (approximate)

### Vulnerable Code
```javascript
// This simulates a SQL query that would be vulnerable to SQL injection
const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
console.log(`[DEBUG] Simulated query: ${query}`);
```

### Security Impact
- **Severity:** CRITICAL
- **OWASP Category:** A03:2021 – Injection
- **Risk:** Complete database compromise if this were connected to a real database

### Attack Scenario
Input: `username = "admin'--"`, `password = "anything"`

Resulting query:
```sql
SELECT * FROM users WHERE username = 'admin'--' AND password = 'anything'
```

The `--` comments out the rest of the query, bypassing password check.

### Remediation
1. Use parameterized queries or prepared statements
2. Never concatenate user input into SQL queries
3. Use an ORM with built-in SQL injection protection
4. Implement input validation and sanitization

```javascript
// Safe approach with parameterized query
const query = 'SELECT * FROM users WHERE username = ? AND password = ?';
db.execute(query, [username, hashedPassword]);
```

---

## Security Issue ID: SEC-004

### Title
Predictable Session Token Generation

### Description
The `generateSessionToken` method creates predictable tokens using timestamp, which can be guessed or brute-forced.

### Location
- **File:** `src/userManager.js`
- **Method:** `generateSessionToken(username)`

### Vulnerable Code
```javascript
generateSessionToken(username) {
  // SECURITY: Using timestamp makes tokens predictable
  return `${username}_${Date.now()}`;
}
```

### Security Impact
- **Severity:** MEDIUM
- **OWASP Category:** A02:2021 – Cryptographic Failures
- **Risk:** Session hijacking, unauthorized access

### Attack Scenario
1. Attacker knows tokens follow pattern: `username_timestamp`
2. Attacker can guess timestamp (within a few milliseconds)
3. Attacker generates potential tokens and attempts session hijacking

### Remediation
Use cryptographically secure random token generation:
```javascript
const crypto = require('crypto');

generateSessionToken(username) {
  return crypto.randomBytes(32).toString('hex');
}
```

---

## Test Environment

### Prerequisites
- Node.js 14+ installed
- npm installed

### Setup
```bash
cd homework-4
npm install
```

### Running the Application
```bash
npm start
```

### Running Tests
```bash
npm test
```

### Expected Test Results (Before Fixes)
```
FAIL tests/calculator.test.js
  Calculator
    divide
      ✗ should handle division by zero
    factorial
      ✗ should handle negative numbers

Tests: 2 failed, 5 passed, 7 total
```

---

## Pipeline Execution Context

This bug context will be used by the 4-agent pipeline:

1. **Bug Research Verifier** - Verifies the research about these bugs
2. **Bug Fixer** - Applies fixes to BUG-001 and BUG-002
3. **Security Verifier** - Identifies SEC-001 through SEC-004
4. **Unit Test Generator** - Creates tests for the fixed methods

## Additional Notes

- All bugs are intentional for educational purposes
- Bugs represent common real-world issues
- Security issues demonstrate OWASP Top 10 vulnerabilities
- Application is simplified but demonstrates realistic problems

