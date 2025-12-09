import React, { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { transactionService } from '../services/api';

const formatCurrency = (amount, currency) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency || 'RUB'
  }).format(amount);
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('ru-RU');
};

export const TransactionList = ({ transactions, categories, onTransactionUpdate }) => {
  // Состояние: ID транзакции, которая сейчас редактируется
  const [editingId, setEditingId] = useState(null);

  const handleDelete = async (id) => {
    if (window.confirm('Удалить эту операцию?')) {
      try {
        await transactionService.delete(id);
        onTransactionUpdate(); // Обновляем список
      } catch (error) {
        console.error("Failed to delete", error);
      }
    }
  };

  const handleCategoryChange = async (transactionId, newCategoryId) => {
    try {
      await transactionService.update(transactionId, { category_id: newCategoryId });
      onTransactionUpdate(); // Обновляем список и графики
      setEditingId(null); // Выходим из режима редактирования
    } catch (error) {
      console.error("Failed to update category", error);
    }
  };

  if (!transactions.length) {
    return (
      <div className="text-center p-8 text-gray-500 bg-white rounded-lg">
        Нет данных. Загрузите файл.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase">
            <tr>
              <th className="px-6 py-3">Дата</th>
              <th className="px-6 py-3">Категория</th>
              <th className="px-6 py-3">Описание</th>
              <th className="px-6 py-3 text-right">Сумма</th>
              <th className="px-6 py-3 w-10"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {transactions.map((t) => (
              <tr key={t.id} className="hover:bg-gray-50 transition group">
                <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                  {formatDate(t.date)}
                </td>

                <td className="px-6 py-4">
                  {/* Если эта строка в режиме редактирования - показываем Select */}
                  {editingId === t.id ? (
                    <select
                      className="border rounded px-2 py-1 text-xs w-full bg-white focus:ring-2 focus:ring-primary outline-none"
                      autoFocus
                      defaultValue={t.category?.id || ""}
                      onChange={(e) => handleCategoryChange(t.id, e.target.value)}
                      onBlur={() => setEditingId(null)} // Если кликнули мимо - отмена
                    >
                      <option value="" disabled>Выберите категорию</option>
                      {categories.map(cat => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    /* Иначе показываем кликабельный бейдж */
                    <div
                      onClick={() => setEditingId(t.id)}
                      className="cursor-pointer hover:opacity-80 inline-flex items-center"
                      title="Нажмите, чтобы изменить"
                    >
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border
                        ${t.category ? 'bg-blue-50 text-blue-700 border-blue-100' : 'bg-gray-100 text-gray-600 border-gray-200'}`}>
                        {t.category ? t.category.name : 'Без категории'}
                      </span>
                    </div>
                  )}
                </td>

                <td className="px-6 py-4 text-gray-700">
                  {t.description}
                </td>

                <td className={`px-6 py-4 text-right font-medium
                  ${t.is_income ? 'text-success' : 'text-gray-900'}`}>
                  {t.is_income ? '+' : ''}{formatCurrency(t.amount, t.currency)}
                </td>

                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleDelete(t.id)}
                    className="text-gray-400 hover:text-danger opacity-0 group-hover:opacity-100 transition"
                    title="Удалить"
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};