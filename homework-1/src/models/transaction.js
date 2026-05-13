const { randomUUID } = require('crypto');

/**
 * Factory function to create a new transaction object.
 * @param {Object} data - Raw transaction input data
 * @returns {Object} - Immutable transaction record
 */
function createTransaction(data) {
  const transaction = {
    id: randomUUID(),
    fromAccount: data.fromAccount || null,
    toAccount: data.toAccount || null,
    amount: parseFloat(data.amount),
    currency: data.currency.toUpperCase(),
    type: data.type,
    timestamp: new Date().toISOString(),
    status: 'completed',
  };

  return Object.freeze(transaction);
}

module.exports = { createTransaction };

