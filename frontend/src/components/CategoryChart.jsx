import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

export const CategoryChart = ({ transactions }) => {
  // Агрегация данных для графика
  const dataMap = transactions
    .filter(t => !t.is_income && t.category) // Берем только расходы с категорией
    .reduce((acc, t) => {
      const name = t.category.name;
      acc[name] = (acc[name] || 0) + t.amount;
      return acc;
    }, {});

  const data = Object.keys(dataMap).map(name => ({
    name,
    value: dataMap[name]
  }));

  if (data.length === 0) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm h-80 flex flex-col">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Расходы по категориям</h3>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value.toLocaleString()} ₽`} />
            <Legend verticalAlign="bottom" height={36}/>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};