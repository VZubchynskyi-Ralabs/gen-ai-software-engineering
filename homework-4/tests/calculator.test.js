/**
 * Basic tests for Calculator class
 * These tests will initially fail due to the bugs
 */

const { Calculator } = require('../src/calculator');

describe('Calculator', () => {
  let calculator;

  beforeEach(() => {
    calculator = new Calculator();
  });

  describe('add', () => {
    test('should add two positive numbers', () => {
      expect(calculator.add(2, 3)).toBe(5);
    });

    test('should add negative numbers', () => {
      expect(calculator.add(-2, -3)).toBe(-5);
    });
  });

  describe('divide', () => {
    test('should divide two numbers', () => {
      expect(calculator.divide(10, 2)).toBe(5);
    });

    test('should handle division by zero', () => {
      // This test will fail initially due to BUG 1
      expect(() => calculator.divide(10, 0)).toThrow('Division by zero');
    });
  });

  describe('factorial', () => {
    test('should calculate factorial of positive number', () => {
      expect(calculator.factorial(5)).toBe(120);
    });

    test('should return 1 for factorial of 0', () => {
      expect(calculator.factorial(0)).toBe(1);
    });

    test('should handle negative numbers', () => {
      // This test will fail initially due to BUG 2
      expect(() => calculator.factorial(-5)).toThrow('Factorial not defined for negative numbers');
    });
  });

  describe('multiply', () => {
    test('should multiply two numbers', () => {
      expect(calculator.multiply(4, 5)).toBe(20);
    });
  });
});

