const { Router } = require('express');
const { calculateBalance, calculateSummary } = require('../utils/helpers');

const router = Router();

const ACCOUNT_REGEX = /^ACC-[A-Z0-9]{5}$/i;

function validateAccountId(req, res, next) {
  if (!ACCOUNT_REGEX.test(req.params.accountId)) {
    return res.status(400).json({
      error: 'Invalid account ID format. Must follow ACC-XXXXX (alphanumeric)',
    });
  }
  next();
}

// GET /accounts/:accountId/balance
router.get('/:accountId/balance', validateAccountId, (req, res) => {
  const { accountId } = req.params;
  const balance = calculateBalance(accountId);

  return res.status(200).json({ accountId, balance });
});

// GET /accounts/:accountId/summary (Task 4 - Option A)
router.get('/:accountId/summary', validateAccountId, (req, res) => {
  const { accountId } = req.params;
  const summary = calculateSummary(accountId);

  return res.status(200).json({ accountId, ...summary });
});

module.exports = router;

