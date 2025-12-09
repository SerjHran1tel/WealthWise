import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

// Добавляем перехватчик для логирования запросов
api.interceptors.request.use(request => {
  console.log('>>> Starting Request:', request.method.toUpperCase(), request.url, request.params);
  return request;
});

export const transactionService = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/transactions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getAll: async (params = {}) => {
    // Явный запрос с логами
    const response = await api.get('/transactions', { params });
    console.log(`<<< Transactions received: ${response.data.length} items`);
    return response.data;
  },

  delete: async (id) => {
    await api.delete(`/transactions/${id}`);
  },

  update: async (id, data) => {
    const response = await api.put(`/transactions/${id}`, data);
    return response.data;
  }
};

export const categoryService = {
  getAll: async () => {
    const response = await api.get('/categories');
    return response.data;
  },
};

export const budgetService = {
  getStatus: async (startDate, endDate) => {
    const response = await api.get('/budgets/status', {
      params: { start_date: startDate, end_date: endDate }
    });
    return response.data;
  },
  create: async (categoryId, amount) => {
    const response = await api.post('/budgets/', {
      category_id: categoryId,
      amount: parseFloat(amount)
    });
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/budgets/${id}`);
  }
};