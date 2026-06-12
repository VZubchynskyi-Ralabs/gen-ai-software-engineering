/**
 * Simple Calculator CLI Application
 * This application has intentional bugs and security issues for the 4-agent pipeline to fix
 */

const readline = require('readline');
const chalk = require('chalk');
const { Calculator } = require('./calculator');
const { UserManager } = require('./userManager');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const calculator = new Calculator();
const userManager = new UserManager();

console.log(chalk.blue('================================='));
console.log(chalk.blue('  Calculator CLI Application'));
console.log(chalk.blue('=================================\n'));

function showMenu() {
  console.log(chalk.green('\nMenu:'));
  console.log('1. Add numbers');
  console.log('2. Divide numbers');
  console.log('3. Calculate factorial');
  console.log('4. User login (admin only)');
  console.log('5. Exit\n');
}

function promptUser() {
  rl.question(chalk.yellow('Select an option (1-5): '), (choice) => {
    handleChoice(choice);
  });
}

function handleChoice(choice) {
  switch (choice) {
    case '1':
      rl.question('Enter first number: ', (num1) => {
        rl.question('Enter second number: ', (num2) => {
          const result = calculator.add(parseFloat(num1), parseFloat(num2));
          console.log(chalk.cyan(`Result: ${result}`));
          showMenu();
          promptUser();
        });
      });
      break;
    
    case '2':
      rl.question('Enter numerator: ', (num1) => {
        rl.question('Enter denominator: ', (num2) => {
          // BUG 1: No check for division by zero
          const result = calculator.divide(parseFloat(num1), parseFloat(num2));
          console.log(chalk.cyan(`Result: ${result}`));
          showMenu();
          promptUser();
        });
      });
      break;
    
    case '3':
      rl.question('Enter a number for factorial: ', (num) => {
        // BUG 2: Factorial doesn't handle negative numbers properly
        const result = calculator.factorial(parseInt(num));
        console.log(chalk.cyan(`Result: ${result}`));
        showMenu();
        promptUser();
      });
      break;
    
    case '4':
      rl.question('Enter username: ', (username) => {
        rl.question('Enter password: ', (password) => {
          // SECURITY ISSUE: Insecure password comparison and potential SQL injection
          const isAuthenticated = userManager.authenticate(username, password);
          if (isAuthenticated) {
            console.log(chalk.green('Login successful!'));
          } else {
            console.log(chalk.red('Login failed!'));
          }
          showMenu();
          promptUser();
        });
      });
      break;
    
    case '5':
      console.log(chalk.blue('\nGoodbye!'));
      rl.close();
      process.exit(0);
      break;
    
    default:
      console.log(chalk.red('Invalid option. Please try again.'));
      showMenu();
      promptUser();
  }
}

showMenu();
promptUser();

module.exports = { handleChoice };

