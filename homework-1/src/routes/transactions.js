const { Router } = require('express');
const { validateTransaction } = require('../validators/transactionValidator');
const { createTransaction } = require('../models/transaction');
const { transactions, addTransaction, filterTransactions } = require('../utils/helpers');

const router = Router();

// POST /transactions - Create a new transaction
router.post('/', (req, res) => {
  const { valid, errors } = validateTransaction(req.body);

  if (!valid) {
    return res.status(400).json({ error: 'Validation failed', details: errors });
  }

  const transaction = createTransaction(req.body);
  addTransaction(transaction);

  return res.status(201).json(transaction);
});

// GET /transactions - List all transactions (with optional filters)
router.get('/', (req, res) => {
  const { accountId, type, from, to } = req.query;
  const result = filterTransactions({ accountId, type, from, to });
  return res.status(200).json(result);
});

// GET /transactions/:id - Get a specific transaction
router.get('/:id', (req, res) => {
  const transaction = transactions.find((t) => t.id === req.params.id);

  if (!transaction) {
    return res.status(404).json({ error: 'Transaction not found' });
  }

  return res.status(200).json(transaction);
});

module.exports = router;

