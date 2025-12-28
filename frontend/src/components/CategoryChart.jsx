// src/components/CategoryChart.jsx
import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export const CategoryChart = ({ transactions = [] }) => {
  const dataMap = transactions
    .filter(t => !t.is_income && t.category)
    .reduce((acc, t) => {
      const name = t.category.name;
      acc[name] = (acc[name] || 0) + t.amount;
      return acc;
    }, {});

  const data = Object.keys(dataMap).map(name => ({
    name,
    value: dataMap[name]
  }));

  if (data.length === 0) {
    return (
      <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-white/50 p-8 flex items-center justify-center h-80">
        <p className="text-slate-400 text-center">Нет данных о расходах за выбранный период</p>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-white/50 p-6">
      <h3 className="text-lg font-semibold mb-6 text-slate-800">Расходы по категориям</h3>

      <div className="w-full h-80 -ml-4"> {/* фиксированная высота */}
        <PieChart width={350} height={320}>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={110}
            paddingAngle={4}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value) => `${Number(value).toLocaleString('ru-RU')} ₽`}
            contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-sm text-slate-700">{value}</span>}
          />
        </PieChart>
      </div>
    </div>
  );
};