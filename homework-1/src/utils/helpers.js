// Shared in-memory transaction store
const transactions = [];

function addTransaction(transaction) {
  transactions.push(transaction);
}

/**
 * Filter transactions by optional criteria.
 */
function filterTransactions({ accountId, type, from, to } = {}) {
  return transactions.filter((t) => {
    if (accountId && t.fromAccount !== accountId && t.toAccount !== accountId) return false;
    if (type && t.type !== type) return false;
    if (from && t.timestamp < from) return false;
    if (to) {
      // Include the full "to" date by extending to end of day if only a date is provided
      const toDate = to.length === 10 ? to + 'T23:59:59.999Z' : to;
      if (t.timestamp > toDate) return false;
    }
    return true;
  });
}

/**
 * Calculate balance per currency for a given account.
 * Returns an object: { USD: 450.00, EUR: 200.00, ... }
 */
function calculateBalance(accountId) {
  const balanceByCurrency = {};

  transactions
    .filter((t) => t.status === 'completed')
    .forEach((t) => {
      const currency = t.currency;
      if (!balanceByCurrency[currency]) balanceByCurrency[currency] = 0;

      if (t.toAccount === accountId) {
        balanceByCurrency[currency] += t.amount;
      }
      if (t.fromAccount === accountId) {
        balanceByCurrency[currency] -= t.amount;
      }
    });

  // Round to 2 decimal places
  Object.keys(balanceByCurrency).forEach((currency) => {
    balanceByCurrency[currency] = Math.round(balanceByCurrency[currency] * 100) / 100;
  });

  return balanceByCurrency;
}

/**
 * Calculate transaction summary for a given account.
 */
function calculateSummary(accountId) {
  const relevant = transactions.filter(
    (t) => t.fromAccount === accountId || t.toAccount === accountId
  );

  let totalDeposits = 0;
  let totalWithdrawals = 0;
  let lastTransactionDate = null;

  relevant.forEach((t) => {
    if (t.toAccount === accountId && (t.type === 'deposit' || t.type === 'transfer')) {
      totalDeposits += t.amount;
    }
    if (t.fromAccount === accountId && (t.type === 'withdrawal' || t.type === 'transfer')) {
      totalWithdrawals += t.amount;
    }
    if (!lastTransactionDate || t.timestamp > lastTransactionDate) {
      lastTransactionDate = t.timestamp;
    }
  });

  return {
    transactionCount: relevant.length,
    totalDeposits: Math.round(totalDeposits * 100) / 100,
    totalWithdrawals: Math.round(totalWithdrawals * 100) / 100,
    lastTransactionDate,
  };
}

module.exports = { transactions, addTransaction, filterTransactions, calculateBalance, calculateSummary };

