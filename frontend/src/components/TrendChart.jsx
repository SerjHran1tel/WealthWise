import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export const TrendChart = ({ transactions }) => {
  // Безопасное извлечение массива транзакций
  const transactionsList = React.useMemo(() => {
    if (!transactions) return [];
    if (Array.isArray(transactions)) return transactions;
    if (transactions.items && Array.isArray(transactions.items)) return transactions.items;
    return [];
  }, [transactions]);

  const groupedData = transactionsList
    .filter(t => !t.is_income)
    .reduce((acc, t) => {
      // Безопасное извлечение даты
      try {
        const dateKey = t.date.split('T')[0];
        acc[dateKey] = (acc[dateKey] || 0) + t.amount;
      } catch (e) {
        // Игнорируем ошибки парсинга
      }
      return acc;
    }, {});

  const data = Object.keys(groupedData)
    .sort()
    .map(dateKey => ({
      date: dateKey,
      amount: groupedData[dateKey],
      displayDate: format(parseISO(dateKey), 'd MMM', { locale: ru })
    }));

  if (data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm mt-6 flex items-center justify-center text-gray-400" style={{ height: 300 }}>
        Нет данных для графика
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm mt-6 flex flex-col">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Динамика расходов</h3>

      {/* ЯВНАЯ ВЫСОТА */}
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="displayDate" fontSize={12} tickLine={false} />
            <YAxis fontSize={12} tickLine={false} tickFormatter={(val) => `₽${val/1000}k`} />
            <Tooltip
              cursor={{fill: '#f3f4f6'}}
              formatter={(value) => [`${value.toLocaleString()} ₽`, 'Сумма']}
            />
            <Bar dataKey="amount" fill="#3B82F6" radius={[4, 4, 0, 0]} barSize={20} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};