// src/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000'; // Adjust if necessary

export const registerUser = (userData) => axios.post(`${API_URL}/users/register`, userData, {
  headers: {
    'Content-Type': 'application/json'
  }
});

export const loginUser = (credentials) => axios.post(`${API_URL}/users/login`, credentials, {
  headers: {
    'Content-Type': 'application/json'
  }
});

export const getBankAccounts = (userId, token) => axios.get(`${API_URL}/bank_accounts`, {
  headers: { Authorization: `Bearer ${token}` },
  params: { user_id: userId }
});

export const createBankAccount = (accountData, token) => axios.post(`${API_URL}/bank_accounts`, accountData, {
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  }
});

export const deposit = (depositData, token) => axios.post(`${API_URL}/bank_accounts/deposit`, depositData, {
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  }
});

export const withdraw = (withdrawData, token) => axios.post(`${API_URL}/bank_accounts/withdraw`, withdrawData, {
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  }
});

export const transfer = (transferData, token) => axios.post(`${API_URL}/bank_accounts/transfer`, transferData, {
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  }
});