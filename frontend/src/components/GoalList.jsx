import React, { useState } from 'react';
import { Plus, Target, Trash2, Edit3, X } from 'lucide-react';
import { goalService } from '../services/api';

export const GoalList = ({ goals, onUpdate }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const [newGoal, setNewGoal] = useState({
    name: '', target_amount: '', current_amount: '0', deadline: '', color: '#3B82F6'
  });

  const formatCurrency = (val) => new Intl.NumberFormat('ru-RU', {
    style: 'currency', currency: 'RUB', maximumFractionDigits: 0
  }).format(val);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await goalService.create({
        ...newGoal,
        target_amount: parseFloat(newGoal.target_amount),
        current_amount: parseFloat(newGoal.current_amount)
      });
      setNewGoal({ name: '', target_amount: '', current_amount: '0', deadline: '', color: '#3B82F6' });
      setIsAdding(false);
      onUpdate();
    } catch (error) {
      console.error("Failed to create goal", error);
    }
  };

  const handleDeposit = async (id, currentVal) => {
    const newVal = prompt("Введите новую текущую сумму накоплений:", currentVal);
    if (newVal !== null && !isNaN(parseFloat(newVal))) {
      try {
        await goalService.deposit(id, newVal);
        onUpdate();
      } catch (e) { console.error(e); }
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Удалить эту цель?')) {
      try {
        await goalService.delete(id);
        onUpdate();
      } catch (e) { console.error(e); }
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Target size={20} className="text-primary" /> Финансовые цели
        </h3>
        <button
          onClick={() => setIsAdding(!isAdding)}
          className="text-primary hover:bg-blue-50 p-1 rounded transition"
        >
          {isAdding ? <X size={20} /> : <Plus size={20} />}
        </button>
      </div>

      {isAdding && (
        <form onSubmit={handleSubmit} className="mb-6 p-3 bg-gray-50 rounded border border-blue-100 space-y-2">
          <input
            type="text" placeholder="Название (на машину)" className="w-full border rounded p-2 text-sm"
            value={newGoal.name} onChange={e => setNewGoal({...newGoal, name: e.target.value})} required
          />
          <div className="flex gap-2">
            <input
              type="number" placeholder="Цель (₽)" className="w-1/2 border rounded p-2 text-sm"
              value={newGoal.target_amount} onChange={e => setNewGoal({...newGoal, target_amount: e.target.value})} required
            />
            <input
              type="number" placeholder="Уже есть (₽)" className="w-1/2 border rounded p-2 text-sm"
              value={newGoal.current_amount} onChange={e => setNewGoal({...newGoal, current_amount: e.target.value})}
            />
          </div>
          <button type="submit" className="w-full bg-primary text-white py-1 rounded text-sm hover:bg-blue-600">
            Создать
          </button>
        </form>
      )}

      <div className="space-y-4 overflow-y-auto flex-1 pr-2">
        {goals.length === 0 && !isAdding && (
          <p className="text-gray-400 text-sm text-center py-4">Нет активных целей</p>
        )}

        {goals.map((g) => (
          <div key={g.id} className="border rounded-lg p-3 hover:shadow-md transition group relative">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h4 className="font-medium text-gray-800">{g.name}</h4>
                <p className="text-xs text-gray-500">
                  {formatCurrency(g.current_amount)} из {formatCurrency(g.target_amount)}
                </p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-primary">{g.percentage}%</span>
              </div>
            </div>

            <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-2">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${Math.min(g.percentage, 100)}%` }}
              />
            </div>

            <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => handleDeposit(g.id, g.current_amount)}
                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
              >
                <Edit3 size={12} /> Изменить сумму
              </button>
              <button
                onClick={() => handleDelete(g.id)}
                className="text-xs text-red-500 hover:underline"
              >
                Удалить
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};