// src/components/CategoryChart.jsx
import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const CHART_COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e', '#64748b'];

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
		<div className="category-chart">
			<h3 className="category-chart__title">Расходы по категориям</h3>

			<div className="category-chart__wrapper">
				<ResponsiveContainer width="100%" height={320}>
					<PieChart>
						<Pie
							data={data}
							cx="50%"
							cy="50%"
							innerRadius={70}
							outerRadius={100}
							paddingAngle={6}
							dataKey="value"
							stroke="none" // Убираем белую обводку для более чистого вида
						>
							{data.map((entry, index) => (
								<Cell
									key={`cell-${index}`}
									fill={CHART_COLORS[index % CHART_COLORS.length]}
									style={{ filter: 'drop-shadow(0px 4px 6px rgba(0,0,0,0.05))' }}
								/>
							))}
						</Pie>
						<Tooltip
							formatter={(value) => `${Number(value).toLocaleString('ru-RU')} ₽`}
							contentStyle={{
								borderRadius: '12px',
								border: 'none',
								boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
								padding: '10px 14px',
								fontSize: '13px'
							}}
							itemStyle={{ fontWeight: 600 }}
						/>
						<Legend
							verticalAlign="bottom"
							height={36}
							iconType="circle"
							iconSize={8}
							formatter={(value) => <span className="category-chart__legend-item">{value}</span>}
						/>
					</PieChart>
				</ResponsiveContainer>
			</div>
		</div>
	);
};