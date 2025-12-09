import React, { useState } from 'react';
import { Plus, Trash2, AlertTriangle } from 'lucide-react';
import { budgetService } from '../services/api';

export const BudgetList = ({ budgets, categories, dateRange, onUpdate }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newBudget, setNewBudget] = useState({ categoryId: '', amount: '' });

  const formatCurrency = (val) => new Intl.NumberFormat('ru-RU', {
    style: 'currency', currency: 'RUB', maximumFractionDigits: 0
  }).format(val);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newBudget.categoryId || !newBudget.amount) return;

    try {
      await budgetService.create(newBudget.categoryId, newBudget.amount);
      setNewBudget({ categoryId: '', amount: '' });
      setIsAdding(false);
      onUpdate(); // Обновляем данные
    } catch (error) {
      console.error("Failed to create budget", error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Удалить этот бюджет?')) {
      try {
        await budgetService.delete(id);
        onUpdate();
      } catch (error) {
        console.error("Failed to delete budget", error);
      }
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Бюджеты на месяц</h3>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="text-primary hover:bg-blue-50 p-1 rounded transition"
          title="Добавить бюджет"
        >
          <Plus size={20} />
        </button>
      </div>

      {/* Форма добавления */}
      {isAdding && (
        <form onSubmit={handleSubmit} className="mb-6 p-3 bg-gray-50 rounded border border-blue-100">
          <div className="flex flex-col gap-2">
            <select
              className="border rounded p-2 text-sm"
              value={newBudget.categoryId}
              onChange={(e) => setNewBudget({...newBudget, categoryId: e.target.value})}
              required
            >
              <option value="">Выберите категорию</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Лимит (₽)"
              className="border rounded p-2 text-sm"
              value={newBudget.amount}
              onChange={(e) => setNewBudget({...newBudget, amount: e.target.value})}
              required
            />
            <button type="submit" className="bg-primary text-white py-1 rounded text-sm hover:bg-blue-600">
              Сохранить
            </button>
          </div>
        </form>
      )}

      {/* Список бюджетов */}
      <div className="space-y-6 overflow-y-auto flex-1 pr-2">
        {budgets.length === 0 && !isAdding && (
          <p className="text-gray-400 text-sm text-center py-4">Нет активных бюджетов</p>
        )}

        {budgets.map((b) => (
          <div key={b.id} className="group relative">
            <div className="flex justify-between text-sm mb-1">
              <span className="font-medium text-gray-700">{b.category_name}</span>
              <span className="text-gray-500">
                {formatCurrency(b.spent_amount)} / {formatCurrency(b.limit_amount)}
              </span>
            </div>

            {/* Прогресс бар */}
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  b.is_exceeded ? 'bg-danger' :
                  b.percentage > 80 ? 'bg-orange-400' : 'bg-success'
                }`}
                style={{ width: `${Math.min(b.percentage, 100)}%` }}
              />
            </div>

            {/* Сообщение о превышении */}
            {b.is_exceeded && (
              <div className="flex items-center gap-1 text-xs text-danger mt-1">
                <AlertTriangle size={12} />
                <span>Превышение на {formatCurrency(b.spent_amount - b.limit_amount)}</span>
              </div>
            )}

            {/* Кнопка удаления (появляется при наведении) */}
            <button
              onClick={() => handleDelete(b.id)}
              className="absolute -right-6 top-0 text-gray-300 hover:text-danger opacity-0 group-hover:opacity-100 transition"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};