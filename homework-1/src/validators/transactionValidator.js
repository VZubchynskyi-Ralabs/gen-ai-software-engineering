const VALID_CURRENCIES = new Set([
  'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'CNY',
  'HKD', 'SGD', 'NOK', 'SEK', 'DKK', 'MXN', 'INR', 'BRL', 'ZAR',
  'KRW', 'PLN', 'CZK', 'HUF', 'RON', 'TRY', 'THB', 'MYR', 'IDR',
  'PHP', 'AED', 'SAR',
]);

const VALID_TYPES = new Set(['deposit', 'withdrawal', 'transfer']);
const ACCOUNT_REGEX = /^ACC-[A-Z0-9]{5}$/i;

function validateTransaction(data) {
  const errors = [];

  if (!data.type || !VALID_TYPES.has(data.type)) {
    errors.push({ field: 'type', message: 'Type must be one of: deposit, withdrawal, transfer' });
  }

  if (data.amount === undefined || data.amount === null || data.amount === '') {
    errors.push({ field: 'amount', message: 'Amount is required' });
  } else {
    const amt = Number(data.amount);
    if (!isFinite(amt) || amt <= 0) {
      errors.push({ field: 'amount', message: 'Amount must be a positive number' });
    } else if (!/^\d+(\.\d{1,2})?$/.test(String(data.amount))) {
      errors.push({ field: 'amount', message: 'Amount must have at most 2 decimal places' });
    }
  }

  if (!data.currency) {
    errors.push({ field: 'currency', message: 'Currency is required' });
  } else if (!VALID_CURRENCIES.has(data.currency.toUpperCase())) {
    errors.push({ field: 'currency', message: 'Invalid currency code. Must be a valid ISO 4217 code' });
  }

  const type = data.type;

  if (type === 'withdrawal' || type === 'transfer') {
    if (!data.fromAccount) {
      errors.push({ field: 'fromAccount', message: 'fromAccount is required for withdrawal and transfer' });
    } else if (!ACCOUNT_REGEX.test(data.fromAccount)) {
      errors.push({ field: 'fromAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
    }
  } else if (data.fromAccount && !ACCOUNT_REGEX.test(data.fromAccount)) {
    errors.push({ field: 'fromAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
  }

  if (type === 'deposit' || type === 'transfer') {
    if (!data.toAccount) {
      errors.push({ field: 'toAccount', message: 'toAccount is required for deposit and transfer' });
    } else if (!ACCOUNT_REGEX.test(data.toAccount)) {
      errors.push({ field: 'toAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
    }
  } else if (data.toAccount && !ACCOUNT_REGEX.test(data.toAccount)) {
    errors.push({ field: 'toAccount', message: 'Account number must follow format ACC-XXXXX (alphanumeric)' });
  }

  return { valid: errors.length === 0, errors };
}

module.exports = { validateTransaction };

