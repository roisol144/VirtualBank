// src/components/AccountManagement.js
import React, { useState } from 'react';
import { TextField, Button, Container, Typography, Box, Grid } from '@mui/material';
import { createBankAccount, deposit, withdraw, transfer } from '../api';

function AccountManagement({ token }) {
  const [accountData, setAccountData] = useState({
    user_id: '',
    currency: 'USD',
    account_type: 'CHECKINGS',
  });
  const [transactionData, setTransactionData] = useState({
    account_number: '',
    amount: '',
  });
  const [transferData, setTransferData] = useState({
    from_account_number: '',
    to_account_number: '',
    amount: '',
  });

  const handleAccountChange = (e) => {
    setAccountData({ ...accountData, [e.target.name]: e.target.value });
  };

  const handleTransactionChange = (e) => {
    setTransactionData({ ...transactionData, [e.target.name]: e.target.value });
  };

  const handleTransferChange = (e) => {
    setTransferData({ ...transferData, [e.target.name]: e.target.value });
  };

  const handleCreateAccount = async (e) => {
    e.preventDefault();
    try {
      const response = await createBankAccount(accountData, token);
      console.log('Account created:', response.data);
    } catch (error) {
      console.error('Failed to create account:', error);
    }
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    try {
      const response = await deposit(transactionData, token);
      console.log('Deposit successful:', response.data);
    } catch (error) {
      console.error('Failed to deposit:', error);
    }
  };

  const handleWithdraw = async (e) => {
    e.preventDefault();
    try {
      const response = await withdraw(transactionData, token);
      console.log('Withdrawal successful:', response.data);
    } catch (error) {
      console.error('Failed to withdraw:', error);
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    try {
      const response = await transfer(transferData, token);
      console.log('Transfer successful:', response.data);
    } catch (error) {
      console.error('Failed to transfer:', error);
    }
  };

  return (
    <Container>
      <Box sx={{ mt: 8 }}>
        <Typography variant="h4" gutterBottom>
          Account Management
        </Typography>
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6">Create Account</Typography>
            <form onSubmit={handleCreateAccount}>
              <TextField
                name="user_id"
                label="User ID"
                value={accountData.user_id}
                onChange={handleAccountChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <TextField
                name="currency"
                label="Currency"
                value={accountData.currency}
                onChange={handleAccountChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <TextField
                name="account_type"
                label="Account Type"
                value={accountData.account_type}
                onChange={handleAccountChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>
                Create Account
              </Button>
            </form>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="h6">Deposit/Withdraw</Typography>
            <form onSubmit={handleDeposit}>
              <TextField
                name="account_number"
                label="Account Number"
                value={transactionData.account_number}
                onChange={handleTransactionChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <TextField
                name="amount"
                label="Amount"
                value={transactionData.amount}
                onChange={handleTransactionChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>
                Deposit
              </Button>
              <Button onClick={handleWithdraw} variant="contained" color="secondary" fullWidth sx={{ mt: 2 }}>
                Withdraw
              </Button>
            </form>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="h6">Transfer Funds</Typography>
            <form onSubmit={handleTransfer}>
              <TextField
                name="from_account_number"
                label="From Account Number"
                value={transferData.from_account_number}
                onChange={handleTransferChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <TextField
                name="to_account_number"
                label="To Account Number"
                value={transferData.to_account_number}
                onChange={handleTransferChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <TextField
                name="amount"
                label="Amount"
                value={transferData.amount}
                onChange={handleTransferChange}
                fullWidth
                margin="normal"
                variant="outlined"
              />
              <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>
                Transfer
              </Button>
            </form>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}

export default AccountManagement;