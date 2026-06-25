# Research Quality Measurement Skill

## Purpose
This skill defines standardized levels and metrics for evaluating the quality of codebase research performed by bug research agents.

## Research Quality Levels

### Level 1: Excellent (90-100%)
**Criteria:**
- All file paths and line numbers are accurate and verified
- All code snippets match the actual source code exactly
- References include precise file:line notation
- Research covers all relevant code paths and dependencies
- Context is comprehensive with proper understanding of code flow
- Zero discrepancies between reported and actual code

**Rating:** ⭐⭐⭐⭐⭐ (5/5 stars)

### Level 2: Good (75-89%)
**Criteria:**
- Most file paths and line numbers are accurate (>90% accuracy)
- Minor discrepancies in code snippets (whitespace, formatting)
- References are mostly complete with occasional missing context
- Research covers main code paths but may miss edge cases
- 1-2 minor discrepancies that don't affect overall understanding

**Rating:** ⭐⭐⭐⭐ (4/5 stars)

### Level 3: Adequate (60-74%)
**Criteria:**
- Some file paths or line numbers are inaccurate (70-90% accuracy)
- Code snippets have noticeable differences from source
- References are incomplete or lack proper context
- Research misses some relevant code paths
- 3-5 discrepancies that partially affect understanding

**Rating:** ⭐⭐⭐ (3/5 stars)

### Level 4: Poor (40-59%)
**Criteria:**
- Many file paths or line numbers are wrong (<70% accuracy)
- Code snippets significantly differ from actual source
- References are vague or incorrect
- Research misses critical code paths
- 6-10 discrepancies that seriously affect understanding

**Rating:** ⭐⭐ (2/5 stars)

### Level 5: Unacceptable (<40%)
**Criteria:**
- Most references are invalid or cannot be verified
- Code snippets are fabricated or heavily modified
- Research is superficial or misleading
- Critical code paths are completely missed
- More than 10 discrepancies or research is unusable

**Rating:** ⭐ (1/5 stars)

## Verification Checklist

When verifying research quality, check the following:

1. **File Reference Accuracy**
   - [ ] All file paths exist in the codebase
   - [ ] Line numbers correspond to the correct code
   - [ ] File:line notation is consistent and precise

2. **Code Snippet Fidelity**
   - [ ] Snippets match source code character-for-character (excluding whitespace normalization)
   - [ ] No fabricated or modified code
   - [ ] Context around snippets is accurate

3. **Completeness**
   - [ ] All relevant files are referenced
   - [ ] Dependencies and imports are traced
   - [ ] Edge cases and error handling are considered

4. **Context Understanding**
   - [ ] Research demonstrates understanding of code flow
   - [ ] Relationships between components are identified
   - [ ] Root causes are properly analyzed

5. **Documentation Quality**
   - [ ] Research is well-organized and readable
   - [ ] Findings are clearly stated
   - [ ] Supporting evidence is provided

## Scoring Formula

```
Quality Score = (
  File Accuracy (40%) +
  Snippet Fidelity (30%) +
  Completeness (20%) +
  Context Understanding (10%)
) × 100
```

## Output Format for Verified Research

```markdown
# Verified Research Report

## Verification Summary
- **Date:** [timestamp]
- **Verifier:** [agent name]
- **Research Quality Level:** [Level 1-5]
- **Quality Score:** [0-100]%
- **Overall Status:** ✅ PASS / ❌ FAIL

## Research Quality Assessment

**Level:** [Level name and rating]
**Score:** [X]%

**Reasoning:**
[Detailed explanation of why this level was assigned]

## Verified Claims
[List of verified claims with references]

## Discrepancies Found
[List of any discrepancies with file:line references]

## References
[All verified file:line references]
```

## Usage by Agents

Agents using this skill should:
1. Read the research document to be verified
2. Check each file:line reference against actual source code
3. Verify code snippets match exactly (excluding minor formatting)
4. Apply the scoring formula to calculate quality score
5. Assign appropriate quality level based on score
6. Generate output using the standard format above
7. Document all discrepancies with specific file:line references

## Examples

### Example 1: Excellent Research (Level 1)
```
File: src/calculator.js:45
Claimed: "The divide method doesn't check for zero"
Actual: Line 45 contains "return a / b;" with no zero check
Status: ✅ Verified (100% match)
```

### Example 2: Poor Research (Level 4)
```
File: src/utils.js:102
Claimed: "The parseInput function validates input"
Actual: File src/utils.js doesn't exist
Status: ❌ Invalid reference
```

## Best Practices

1. **Be Thorough:** Check every single reference, don't skip any
2. **Be Precise:** Line numbers must match exactly
3. **Be Fair:** Minor formatting differences shouldn't heavily penalize
4. **Be Documented:** Record all discrepancies with evidence
5. **Be Constructive:** Suggest how research could be improved

