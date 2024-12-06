// src/components/Dashboard.js
import React, { useEffect, useState } from 'react';
import { Container, Typography, List, ListItem, ListItemText, Box } from '@mui/material';
import { getBankAccounts } from '../api';

function Dashboard({ userId, token }) {
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await getBankAccounts(userId, token);
        setAccounts(response.data);
      } catch (error) {
        console.error('Failed to fetch accounts:', error);
      }
    };
    fetchAccounts();
  }, [userId, token]);

  return (
    <Container>
      <Box sx={{ mt: 8 }}>
        <Typography variant="h4" gutterBottom>
          Dashboard
        </Typography>
        <List>
          {accounts.map(account => (
            <ListItem key={account.id} sx={{ borderBottom: '1px solid #ddd' }}>
              <ListItemText
                primary={`Account Number: ${account.account_number}`}
                secondary={`Balance: ${account.balance}`}
              />
            </ListItem>
          ))}
        </List>
      </Box>
    </Container>
  );
}

export default Dashboard;