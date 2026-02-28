import React from 'react';
import { Paper, Typography, Box, Grid } from '@mui/material';
import { TrendingDown, TrendingUp, AccountBalanceWallet } from '@mui/icons-material';
import { motion } from 'framer-motion';

export const SummaryCards = ({ transactions = [] }) => {
	const income = transactions.filter(t => t.is_income).reduce((acc, t) => acc + t.amount, 0);
	const expense = transactions.filter(t => !t.is_income).reduce((acc, t) => acc + t.amount, 0);
	const balance = income - expense;

	const format = (val) =>
		new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(val);

	const Card = ({ title, amount, icon: Icon, color }) => (
		<motion.div whileHover={{ y: -5 }}>
			<Paper sx={{ p: 3, position: 'relative', overflow: 'hidden' }}>
				<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
					<Box>
						<Typography variant="body2" color="text.secondary" gutterBottom>
							{title}
						</Typography>
						<Typography variant="h4" fontWeight="bold">
							{amount}
						</Typography>
					</Box>
					<Box sx={{ p: 1.5, bgcolor: `${color}.light`, borderRadius: 2, color: `${color}.main` }}>
						<Icon fontSize="large" />
					</Box>
				</Box>
			</Paper>
		</motion.div>
	);

	return (
		<Grid container spacing={3} sx={{ mb: 4 }}>
			<Grid item xs={12} md={4}>
				<Card title="Расходы" amount={format(expense)} icon={TrendingDown} color="error" />
			</Grid>
			<Grid item xs={12} md={4}>
				<Card title="Доходы" amount={format(income)} icon={TrendingUp} color="success" />
			</Grid>
			<Grid item xs={12} md={4}>
				<Card title="Баланс" amount={format(balance)} icon={AccountBalanceWallet} color="primary" />
			</Grid>
		</Grid>
	);
};