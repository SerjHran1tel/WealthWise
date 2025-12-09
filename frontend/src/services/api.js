import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

export const transactionService = {
  // Загрузка файла
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/transactions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Получение списка с поддержкой фильтров (params: { start_date, end_date })
  getAll: async (params = {}) => {
    const response = await api.get('/transactions', { params });
    return response.data;
  },

  // Удаление
  delete: async (id) => {
    await api.delete(`/transactions/${id}`);
  },

  // Обновление
  update: async (id, data) => {
    const response = await api.put(`/transactions/${id}`, data);
    return response.data;
  }
};

export const categoryService = {
  // Получение всех категорий
  getAll: async () => {
    const response = await api.get('/categories');
    return response.data;
  }
};