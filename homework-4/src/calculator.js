/**
 * Calculator class with basic mathematical operations
 * Contains intentional bugs for the pipeline to detect and fix
 */

class Calculator {
  /**
   * Add two numbers
   * @param {number} a - First number
   * @param {number} b - Second number
   * @returns {number} Sum of a and b
   */
  add(a, b) {
    return a + b;
  }

  /**
   * Divide two numbers
   * @param {number} a - Numerator
   * @param {number} b - Denominator
   * @returns {number} Result of a / b
   * 
   * BUG 1: Missing division by zero check
   */
  divide(a, b) {
    if (b === 0) {
      throw new Error('Division by zero');
    }
    return a / b;
  }

  /**
   * Calculate factorial of a number
   * @param {number} n - Number to calculate factorial for
   * @returns {number} Factorial of n
   * 
   * BUG 2: Doesn't handle negative numbers properly
   */
  factorial(n) {
    if (n < 0) {
      throw new Error('Factorial not defined for negative numbers');
    }
    if (n === 0 || n === 1) {
      return 1;
    }
    return n * this.factorial(n - 1);
  }

  /**
   * Multiply two numbers
   * @param {number} a - First number
   * @param {number} b - Second number
   * @returns {number} Product of a and b
   */
  multiply(a, b) {
    return a * b;
  }
}

module.exports = { Calculator };

