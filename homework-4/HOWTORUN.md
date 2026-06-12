# How to Run: 4-Agent Pipeline

This guide provides step-by-step instructions for running the 4-agent bug-fixing pipeline.

---

## 📋 Prerequisites

### Required Software
- **Node.js** 14 or higher
- **npm** 6 or higher
- **Git** (optional, for version control)

### Verify Installation
```bash
node --version   # Should show v14.x.x or higher
npm --version    # Should show 6.x.x or higher
```

---

## 🚀 Installation

### Step 1: Navigate to Project Directory
```bash
cd /path/to/homework-4
```

### Step 2: Install Dependencies
```bash
npm install
```

**Expected output:**
```
added 500+ packages in 10s
```

**Dependencies installed:**
- `chalk@4.1.2` - Terminal colors (for the sample app)
- `jest@29.7.0` - Testing framework
- Other transitive dependencies

---

## 🧪 Initial State Verification

Before running the pipeline, verify the application is in its initial buggy state.

### Test the Buggy Application

#### Run Tests (should see 2 failures)
```bash
npm test
```

**Expected output:**
```
FAIL tests/calculator.test.js
  Calculator
    divide
      ✗ should handle division by zero (8ms)
    factorial
      ✗ should handle negative numbers (7ms)

Tests: 2 failed, 5 passed, 7 total
```

✅ **Correct!** Two tests are failing (division by zero and negative factorial).

#### Test the CLI Application
```bash
npm start
```

**Test division by zero:**
1. Select option: `2` (Divide numbers)
2. Enter numerator: `10`
3. Enter denominator: `0`
4. **Bug:** Result shows `Infinity` instead of error message

**Test negative factorial:**
1. Select option: `3` (Calculate factorial)
2. Enter number: `-5`
3. **Bug:** Application crashes with "Maximum call stack size exceeded"

Press `Ctrl+C` to exit.

---

## 🤖 Run the 4-Agent Pipeline

### Single Command Execution

This is the **main deliverable** - the entire pipeline runs with one command:

```bash
npm run pipeline
```

### What Happens

The pipeline executes 4 agents in sequence:

```
================================================================================
                          4-AGENT BUG FIXING PIPELINE
================================================================================

Pipeline Configuration:
Context Directory: context/bugs/CALC-001
Total Agents: 4

ℹ Verifying prerequisites...
✓ All required directories exist
✓ All required files exist
ℹ Prerequisites verified!

[Step 1/4] Bug Research Verifier
────────────────────────────────────────────────────────────────────────────────
ℹ Model: gpt-4
ℹ Agent File: agents/research-verifier.agent.md
✓ Input verified: context/bugs/CALC-001/research/codebase-research.md
ℹ Loading skills:
✓   - skills/research-quality-measurement.md
ℹ Verifying research quality...
✓ Research verification complete - Quality Level 1 (Excellent)
✓ Agent completed successfully
✓ Output written to: context/bugs/CALC-001/research/verified-research.md

[Step 2/4] Bug Fixer
────────────────────────────────────────────────────────────────────────────────
ℹ Model: gpt-3.5-turbo
ℹ Agent File: agents/bug-fixer.agent.md
✓ Input verified: context/bugs/CALC-001/implementation-plan.md
ℹ Applying bug fixes from implementation plan...
ℹ Applying Fix #1: Division by zero check...
✓ Fix #1 applied
ℹ Applying Fix #2: Factorial negative number validation...
✓ Fix #2 applied
ℹ Running tests...
✓ All tests passed!
✓ Agent completed successfully
✓ Output written to: context/bugs/CALC-001/fix-summary.md

[Step 3/4] Security Verifier
────────────────────────────────────────────────────────────────────────────────
ℹ Model: gpt-4
ℹ Agent File: agents/security-verifier.agent.md
✓ Input verified: context/bugs/CALC-001/fix-summary.md
ℹ Scanning for security vulnerabilities...
ℹ Analyzing modified and existing files...
⚠ Found 4 security issues in src/userManager.js
✓ Agent completed successfully
✓ Output written to: context/bugs/CALC-001/security-report.md
⚠ Security scan complete - 2 CRITICAL issues found

[Step 4/4] Unit Test Generator
────────────────────────────────────────────────────────────────────────────────
ℹ Model: gpt-3.5-turbo
ℹ Agent File: agents/unit-test-generator.agent.md
✓ Input verified: context/bugs/CALC-001/fix-summary.md
ℹ Loading skills:
✓   - skills/unit-tests-FIRST.md
ℹ Generating unit tests following FIRST principles...
✓ Generated additional test file: tests/calculator.generated.test.js
ℹ Running all tests including generated tests...
✓ All tests passed including generated tests!
✓ Agent completed successfully
✓ Output written to: context/bugs/CALC-001/test-report.md

================================================================================
                              PIPELINE COMPLETE
================================================================================

✓ All 4/4 agents completed successfully!

Generated Outputs:
  ✓ context/bugs/CALC-001/research/verified-research.md
  ✓ context/bugs/CALC-001/fix-summary.md
  ✓ context/bugs/CALC-001/security-report.md
  ✓ context/bugs/CALC-001/test-report.md

Summary:
✓ Research verified (Quality Level 1 - Excellent, 98%)
✓ Bug fixes applied (2/2 fixes successful, all tests passing)
⚠ Security scan complete (2 CRITICAL, 2 MEDIUM issues found)
✓ Unit tests generated (22 new tests, all FIRST-compliant)

Next Steps:
  1. Review security-report.md and address CRITICAL issues
  2. Review test-report.md for test coverage details
  3. Run npm test to verify all tests pass
  4. Run npm start to test the fixed application

Pipeline execution completed successfully!
```

**Execution Time:** ~5-10 seconds

---

## 📊 Verify Pipeline Results

### Step 1: Check Generated Outputs

All agent outputs are in `context/bugs/CALC-001/`:

```bash
ls -la context/bugs/CALC-001/
```

**Expected files:**
```
bug-context.md              # Initial bug descriptions
implementation-plan.md      # Fix plan (input for Bug Fixer)
fix-summary.md             # ✓ Output: Bug Fixer
security-report.md         # ✓ Output: Security Verifier
test-report.md             # ✓ Output: Unit Test Generator
research/
  codebase-research.md     # Initial research (input for Verifier)
  verified-research.md     # ✓ Output: Research Verifier
```

### Step 2: Review Each Output

#### Research Verification Result
```bash
cat context/bugs/CALC-001/research/verified-research.md
```

**Key sections to review:**
- **Verification Summary:** Quality Level, Score, Status
- **Verified Claims:** Each research claim with verification status
- **Discrepancies Found:** Any issues with the research

**Expected:** Level 1 (Excellent), 98% score, 0 discrepancies

---

#### Bug Fix Summary
```bash
cat context/bugs/CALC-001/fix-summary.md
```

**Key sections to review:**
- **Overview:** Overall status, changes applied, tests status
- **Changes Made:** Before/after code for each fix
- **Overall Test Results:** Full test output

**Expected:** ✅ SUCCESS, 2/2 changes applied, all tests passing

---

#### Security Report
```bash
cat context/bugs/CALC-001/security-report.md
```

**Key sections to review:**
- **Executive Summary:** Total findings by severity
- **Security Findings:** Each vulnerability with remediation
- **Overall Risk Level:** CRITICAL/HIGH/MEDIUM/LOW

**Expected:** 2 CRITICAL, 2 MEDIUM, Overall Risk: CRITICAL

---

#### Test Generation Report
```bash
cat context/bugs/CALC-001/test-report.md
```

**Key sections to review:**
- **FIRST Principles Compliance:** Verification of each principle
- **Generated Test Files:** List of new tests
- **Test Execution Results:** All tests passing

**Expected:** ✅ All FIRST principles met, 22 new tests, all passing

---

### Step 3: Run Tests

Verify all tests now pass:

```bash
npm test
```

**Expected output:**
```
PASS tests/calculator.test.js
PASS tests/calculator.generated.test.js

Tests: 30 passed, 30 total
```

✅ **Success!** All tests pass including the 22 newly generated tests.

---

### Step 4: Test the Fixed Application

Run the CLI application to verify fixes:

```bash
npm start
```

#### Test Fixed Division by Zero
1. Select option: `2` (Divide numbers)
2. Enter numerator: `10`
3. Enter denominator: `0`
4. **Fixed:** Should see error handling (application doesn't show Infinity)

#### Test Fixed Factorial
1. Select option: `3` (Calculate factorial)
2. Enter number: `-5`
3. **Fixed:** Should see error handling (no stack overflow)

#### Test Normal Operations Still Work
1. **Division:** 10 ÷ 2 = 5 ✓
2. **Factorial:** 5! = 120 ✓
3. **Addition:** 2 + 3 = 5 ✓

Press `Ctrl+C` to exit.

---

## 📁 Understanding the Outputs

### Verified Research (`verified-research.md`)
- **Purpose:** Confirms all research claims are accurate
- **Quality Level:** Rates research quality (1-5 scale)
- **Use Case:** Ensures Bug Fixer works from verified information

### Fix Summary (`fix-summary.md`)
- **Purpose:** Documents exactly what was changed and why
- **Test Results:** Shows before/after test execution
- **Use Case:** Audit trail for all code modifications

### Security Report (`security-report.md`)
- **Purpose:** Identifies security vulnerabilities
- **Severity Ratings:** CRITICAL, HIGH, MEDIUM, LOW
- **Use Case:** Security review before production deployment

### Test Report (`test-report.md`)
- **Purpose:** Documents generated tests and FIRST compliance
- **Coverage:** Shows test coverage metrics
- **Use Case:** Ensures comprehensive test suite

---

## 🎯 Manual Verification Steps

### Verify Repository Structure
```bash
tree -L 3 -I 'node_modules'
```

Expected structure matches the layout in README.md.

### Verify Agent Files
```bash
ls -la agents/
```

Should show 4 agent files:
- `research-verifier.agent.md`
- `bug-fixer.agent.md`
- `security-verifier.agent.md`
- `unit-test-generator.agent.md`

### Verify Skill Files
```bash
ls -la skills/
```

Should show 2 skill files:
- `research-quality-measurement.md`
- `unit-tests-FIRST.md`

### Verify Source Code Changes
```bash
git diff src/calculator.js
```

Should show:
- Added `if (b === 0)` check in `divide()` method
- Added `if (n < 0)` check in `factorial()` method

---

## 🔍 Troubleshooting

### Issue: `npm install` fails

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Issue: Tests fail after pipeline

**Cause:** Pipeline may not have run successfully

**Solution:**
```bash
# Check if fixes were applied
cat src/calculator.js | grep "if (b === 0)"

# If not found, run pipeline again
npm run pipeline
```

### Issue: Pipeline script not executable

**Solution:**
```bash
# The script is run via npm, but if you need to run directly:
chmod +x pipeline-runner.js
node pipeline-runner.js
```

### Issue: Application crashes on start

**Solution:**
```bash
# Verify chalk is installed
npm list chalk

# If not found:
npm install chalk@4.1.2
```

---

## 📸 Screenshots (for Submission)

Take screenshots of:

1. **Pipeline Execution**
   ```bash
   npm run pipeline
   ```
   Screenshot showing all 4 agents completing successfully

2. **Test Results**
   ```bash
   npm test
   ```
   Screenshot showing all 30 tests passing

3. **Security Report** (first page)
   ```bash
   cat context/bugs/CALC-001/security-report.md | head -50
   ```
   Screenshot showing CRITICAL findings

4. **Fixed Application** (division by zero)
   ```bash
   npm start
   # Select division by zero scenario
   ```
   Screenshot showing proper error handling

Save screenshots to `docs/screenshots/` directory.

---

## 🎓 Understanding Model Selection

Each agent specifies its model in the frontmatter:

```yaml
model: gpt-4
modelJustification: >
  Reasoning explanation...
```

**GPT-4 Agents:**
- **Research Verifier:** Needs deep code understanding
- **Security Verifier:** Needs to detect subtle vulnerabilities

**GPT-3.5-turbo Agents:**
- **Bug Fixer:** Follows explicit plan, straightforward execution
- **Unit Test Generator:** Pattern-based test creation

---

## ✅ Success Criteria

You've successfully completed the homework if:

- [x] `npm run pipeline` completes without errors
- [x] All 4 agent outputs are generated
- [x] `npm test` shows 30/30 tests passing
- [x] Fixed application handles edge cases correctly
- [x] Security report identifies all 4 vulnerabilities
- [x] Test report shows FIRST compliance
- [x] Research verification shows Level 1 quality

---

## 📞 Next Steps

After verifying the pipeline works:

1. **Review all agent outputs** thoroughly
2. **Take screenshots** for submission
3. **Read agent definitions** to understand their logic
4. **Review skills** to see how agents use them
5. **Examine pipeline-runner.js** to see orchestration
6. **Consider improvements** for future iterations

---

## 🎉 Congratulations!

You've successfully run the 4-agent pipeline and demonstrated:
- Multi-agent coordination
- Skill-based agent design
- Appropriate model selection
- Comprehensive documentation
- Quality assurance workflow

**Ready to submit?** Make sure you have all deliverables listed in README.md.

---

**Questions?** Review the [README.md](./README.md) or agent files in `agents/` directory.

