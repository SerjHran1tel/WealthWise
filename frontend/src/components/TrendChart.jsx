import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export const TrendChart = ({ transactions = [] }) => {
	// Группируем расходы по дням
	const groupedData = transactions
		.filter(t => !t.is_income)
		.reduce((acc, t) => {
			const dateKey = t.date.split('T')[0]; // берём только YYYY-MM-DD
			acc[dateKey] = (acc[dateKey] || 0) + t.amount;
			return acc;
		}, {});

	// Преобразуем в массив и сортируем по дате
	const data = Object.keys(groupedData)
		.sort()
		.slice(-14) // показываем последние 14 дней
		.map(dateKey => ({
			date: dateKey,
			amount: groupedData[dateKey],
			displayDate: format(parseISO(dateKey), 'd MMM', { locale: ru })
		}));

	if (data.length === 0) {
		return (
			<Paper sx={{ p: 4, textAlign: 'center', height: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
				<Typography color="text.secondary">Нет данных для отображения динамики</Typography>
			</Paper>
		);
	}

	return (
		<Paper sx={{ p: 3 }}>
			<Typography variant="h6" gutterBottom>
				Динамика расходов
			</Typography>
			<Box sx={{ width: '100%', height: 320 }}>
				<ResponsiveContainer width="100%" height="100%">
					<BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
						<CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
						<XAxis
							dataKey="displayDate"
							tick={{ fontSize: 12, fill: '#64748b' }}
							tickLine={false}
						/>
						<YAxis
							tick={{ fontSize: 12, fill: '#64748b' }}
							tickLine={false}
							tickFormatter={(val) => val >= 1000 ? `${val / 1000}т` : val}
						/>
						<Tooltip
							formatter={(value) => [`${Number(value).toLocaleString('ru-RU')} ₽`, 'Расходы']}
							contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
							cursor={{ fill: '#f1f5f9' }}
						/>
						<Bar dataKey="amount" fill="#6366f1" radius={[8, 8, 0, 0]} barSize={28} />
					</BarChart>
				</ResponsiveContainer>
			</Box>
		</Paper>
	);
};