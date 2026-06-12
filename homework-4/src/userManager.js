/**
 * User Management Module
 * Contains intentional security vulnerabilities for the pipeline to detect
 */

class UserManager {
  constructor() {
    // SECURITY ISSUE 1: Hardcoded credentials
    this.hardcodedPassword = 'admin123';
    this.adminUsername = 'admin';
  }

  /**
   * Authenticate a user
   * @param {string} username - Username
   * @param {string} password - Password
   * @returns {boolean} Whether authentication succeeded
   *
   * SECURITY ISSUES:
   * 1. Hardcoded credentials in code
   * 2. Using == instead of === (insecure comparison)
   * 3. Potential for SQL injection if this were connected to a database
   * 4. No password hashing
   */
  authenticate(username, password) {
    // SECURITY: Using == instead of === allows type coercion attacks
    // SECURITY: Hardcoded credentials
    if (username == this.adminUsername && password == this.hardcodedPassword) {
      return true;
    }

    // This simulates a SQL query that would be vulnerable to SQL injection
    const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`;
    console.log(`[DEBUG] Simulated query: ${query}`);

    return false;
  }

  /**
   * Validate password strength
   * @param {string} password - Password to validate
   * @returns {boolean} Whether password is strong enough
   */
  validatePasswordStrength(password) {
    // Missing proper validation - too simplistic
    return password && password.length >= 6;
  }

  /**
   * Generate session token
   * @param {string} username - Username
   * @returns {string} Session token
   *
   * SECURITY: Predictable token generation
   */
  generateSessionToken(username) {
    // SECURITY: Using timestamp makes tokens predictable
    return `${username}_${Date.now()}`;
  }
}

module.exports = { UserManager };

