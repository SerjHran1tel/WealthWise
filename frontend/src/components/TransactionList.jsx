import React, { useState } from 'react';
import { Trash2, ShoppingBag, Coffee, Car, Home, Smartphone } from 'lucide-react';
import { transactionService } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

// Хелпер для иконок (можно расширить)
const getCategoryIcon = (name) => {
  const n = name.toLowerCase();
  if (n.includes('продукт')) return <ShoppingBag size={14} />;
  if (n.includes('кафе') || n.includes('ресторан')) return <Coffee size={14} />;
  if (n.includes('транспорт') || n.includes('taxi')) return <Car size={14} />;
  if (n.includes('дом') || n.includes('жкх')) return <Home size={14} />;
  return <div className="w-2 h-2 rounded-full bg-current" />;
};

export const TransactionList = ({ transactions, categories, onTransactionUpdate }) => {
  const [editingId, setEditingId] = useState(null);

  const formatCurrency = (amount) => new Intl.NumberFormat('ru-RU', {
    style: 'currency', currency: 'RUB', maximumFractionDigits: 2
  }).format(amount);

  const handleDelete = async (id) => {
    if (window.confirm('Удалить?')) {
      await transactionService.delete(id);
      onTransactionUpdate();
    }
  };

  const handleCategoryChange = async (transactionId, newCategoryId) => {
    await transactionService.update(transactionId, { category_id: newCategoryId });
    onTransactionUpdate();
    setEditingId(null);
  };

  if (!transactions.length) return null;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-slate-50 text-slate-500 font-medium">
          <tr>
            <th className="px-6 py-4 rounded-tl-lg">Дата</th>
            <th className="px-6 py-4">Категория</th>
            <th className="px-6 py-4">Описание</th>
            <th className="px-6 py-4 text-right">Сумма</th>
            <th className="px-6 py-4 rounded-tr-lg"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          <AnimatePresence>
            {transactions.map((t) => (
              <motion.tr
                key={t.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="hover:bg-slate-50/80 transition-colors group"
              >
                <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                  {new Date(t.date).toLocaleDateString('ru-RU', {day: 'numeric', month: 'short'})}
                </td>

                <td className="px-6 py-4">
                  {editingId === t.id ? (
                    <select
                      className="border border-blue-300 rounded-lg px-2 py-1.5 text-xs w-full focus:ring-2 focus:ring-blue-100 outline-none bg-white shadow-sm"
                      autoFocus
                      defaultValue={t.category?.id || ""}
                      onChange={(e) => handleCategoryChange(t.id, e.target.value)}
                      onBlur={() => setEditingId(null)}
                    >
                      <option value="" disabled>Выбрать...</option>
                      {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  ) : (
                    <div
                      onClick={() => setEditingId(t.id)}
                      className={`cursor-pointer inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium transition-all hover:scale-105 active:scale-95
                        ${t.category
                          ? 'bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100'
                          : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'}`}
                    >
                      {t.category ? getCategoryIcon(t.category.name) : null}
                      {t.category ? t.category.name : 'Без категории'}
                    </div>
                  )}
                </td>

                <td className="px-6 py-4 text-slate-700 font-medium max-w-xs truncate" title={t.description}>
                  {t.description}
                </td>

                <td className={`px-6 py-4 text-right font-semibold tracking-tight
                  ${t.is_income ? 'text-emerald-600' : 'text-slate-900'}`}>
                  {t.is_income ? '+' : ''}{formatCurrency(t.amount)}
                </td>

                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleDelete(t.id)}
                    className="p-1.5 text-slate-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </motion.tr>
            ))}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  );
};