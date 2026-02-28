import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
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
			<Paper sx={{ p: 4, textAlign: 'center', height: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
				<Typography color="text.secondary">Нет данных о расходах за выбранный период</Typography>
			</Paper>
		);
	}

	return (
		<Paper sx={{ p: 3 }}>
			<Typography variant="h6" gutterBottom>
				Расходы по категориям
			</Typography>
			<Box sx={{ width: '100%', height: 320, display: 'flex', justifyContent: 'center' }}>
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
						formatter={(value) => <span style={{ color: '#374151', fontSize: '0.875rem' }}>{value}</span>}
					/>
				</PieChart>
			</Box>
		</Paper>
	);
};