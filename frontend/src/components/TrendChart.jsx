import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export const TrendChart = ({ transactions }) => {
  // Группировка транзакций по дням
  const groupedData = transactions
    .filter(t => !t.is_income) // Смотрим только расходы
    .reduce((acc, t) => {
      // Преобразуем строку даты в формат YYYY-MM-DD для ключа
      const dateKey = t.date.split('T')[0];
      acc[dateKey] = (acc[dateKey] || 0) + t.amount;
      return acc;
    }, {});

  // Преобразуем объект в массив и сортируем по дате
  const data = Object.keys(groupedData)
    .sort()
    .map(dateKey => ({
      date: dateKey,
      amount: groupedData[dateKey],
      // Форматированная дата для оси X (например, "10 дек")
      displayDate: format(parseISO(dateKey), 'd MMM', { locale: ru })
    }));

  if (data.length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm h-80 flex flex-col mt-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Динамика расходов</h3>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
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