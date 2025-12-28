import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
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
		.slice(-14)
		.map(dateKey => ({
			date: dateKey,
			amount: groupedData[dateKey],
			displayDate: format(parseISO(dateKey), 'd MMM', { locale: ru })
		}));

	if (data.length === 0) {
		return (
			<div className="trend-chart trend-chart--empty">
				<p className="trend-chart__empty-text">Нет данных для отображения динамики</p>
			</div>
		);
	}

	return (
		<div className="trend-chart">
			<h3 className="trend-chart__title">Динамика расходов</h3>

			<div className="trend-chart__wrapper">
				<ResponsiveContainer width="100%" height={320}>
					<BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
						<defs>
							<linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
								<stop offset="0%" stopColor="#6366f1" stopOpacity={1} />
								<stop offset="100%" stopColor="#a855f7" stopOpacity={0.8} />
							</linearGradient>
						</defs>
						<CartesianGrid
							strokeDasharray="3 3"
							vertical={false}
							stroke="rgba(0,0,0,0.04)"
						/>
						<XAxis
							dataKey="displayDate"
							axisLine={false}
							tickLine={false}
							tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 500 }}
							dy={10}
						/>
						<YAxis
							axisLine={false}
							tickLine={false}
							tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 500 }}
							tickFormatter={(val) => val >= 1000 ? `${val / 1000}к` : val}
						/>
						<Tooltip
							cursor={{ fill: 'rgba(0,0,0,0.02)' }}
							contentStyle={{
								borderRadius: '14px',
								border: 'none',
								boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
								padding: '12px'
							}}
							formatter={(value) => [`${Number(value).toLocaleString('ru-RU')} ₽`, 'Расходы']}
							labelStyle={{ fontWeight: 700, marginBottom: '4px', color: '#1e293b' }}
						/>
						<Bar
							dataKey="amount"
							fill="url(#barGradient)"
							radius={[6, 6, 0, 0]}
							barSize={24}
							animationDuration={1500}
						/>
					</BarChart>
				</ResponsiveContainer>
			</div>
		</div>
	);
};