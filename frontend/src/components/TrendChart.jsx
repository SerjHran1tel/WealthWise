// src/components/TrendChart.jsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export const TrendChart = ({ transactions = [] }) => {
  const groupedData = transactions
    .filter(t => !t.is_income)
    .reduce((acc, t) => {
      const dateKey = t.date.split('T')[0];
      acc[dateKey] = (acc[dateKey] || 0) + t.amount;
      return acc;
    }, {});

  const data = Object.keys(groupedData)
    .sort()
    .slice(-14) // показываем только последние 14 дней для красоты
    .map(dateKey => ({
      date: dateKey,
      amount: groupedData[dateKey],
      displayDate: format(parseISO(dateKey), 'd MMM', { locale: ru })
    }));

  if (data.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-white/50 p-8 flex items-center justify-center h-80">
        <p className="text-slate-400 text-center">Нет данных для отображения динамики</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-white/50 p-6">
      <h3 className="text-lg font-semibold mb-6 text-slate-800">Динамика расходов</h3>

      <div className="w-full h-80">
        <BarChart width={600} height={320} data={data} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
          <XAxis
            dataKey="displayDate"
            tick={{ fontSize: 12, fill: '#64748b' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#64748b' }}
            tickLine={false}
            tickFormatter={(val) => val >= 1000 ? `${val/1000}т` : val}
          />
          <Tooltip
            formatter={(value) => [`${Number(value).toLocaleString('ru-RU')} ₽`, 'Расходы']}
            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
            cursor={{ fill: '#f1f5f9' }}
          />
          <Bar
            dataKey="amount"
            fill="#6366f1"
            radius={[8, 8, 0, 0]}
            barSize={28}
          />
        </BarChart>
      </div>
    </div>
  );
};