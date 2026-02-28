import React, { useState, useEffect } from 'react';
import {
	Paper,
	Typography,
	Box,
	Grid,
	Alert,
	CircularProgress,
} from '@mui/material';
import {
	CalendarMonth as CalendarIcon,
	TrendingUp as TrendingUpIcon,
	Warning as AlertCircleIcon,
	EmojiEvents as TargetIcon,
} from '@mui/icons-material';

export const WeeklyReport = () => {
	const [report, setReport] = useState(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		fetchReport();
	}, []);

	const fetchReport = async () => {
		try {
			const res = await fetch('http://localhost:8000/api/reports/weekly');
			const data = await res.json();
			setReport(data);
		} catch (error) {
			console.error('Failed to load report:', error);
		} finally {
			setLoading(false);
		}
	};

	if (loading) return (
		<Box sx={{ textAlign: 'center', py: 8 }}>
			<CircularProgress />
		</Box>
	);
	if (!report) return null;

	return (
		<Paper sx={{ p: 3, mb: 4 }}>
			<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
				<Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
					<CalendarIcon color="primary" />
					Еженедельный отчёт
				</Typography>
				<Typography variant="body2" color="text.secondary">
					{report.period}
				</Typography>
			</Box>

			{/* Stats */}
			<Grid container spacing={2} sx={{ mb: 3 }}>
				<Grid item xs={4}>
					<Paper variant="outlined" sx={{ p: 2, bgcolor: 'primary.light' }}>
						<Typography variant="caption" color="primary.contrastText">Расходы</Typography>
						<Typography variant="h5" fontWeight="bold" color="primary.contrastText">
							{report.stats.expenses.toLocaleString()} ₽
						</Typography>
					</Paper>
				</Grid>
				<Grid item xs={4}>
					<Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light' }}>
						<Typography variant="caption" color="success.contrastText">Доходы</Typography>
						<Typography variant="h5" fontWeight="bold" color="success.contrastText">
							{report.stats.income.toLocaleString()} ₽
						</Typography>
					</Paper>
				</Grid>
				<Grid item xs={4}>
					<Paper variant="outlined" sx={{ p: 2, bgcolor: 'secondary.light' }}>
						<Typography variant="caption" color="secondary.contrastText">Баланс</Typography>
						<Typography variant="h5" fontWeight="bold" color="secondary.contrastText">
							{report.stats.balance.toLocaleString()} ₽
						</Typography>
					</Paper>
				</Grid>
			</Grid>

			{/* Comparison */}
			<Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
				<Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
					<TrendingUpIcon color="action" />
					<Typography variant="body2" fontWeight="medium">Сравнение с прошлой неделей</Typography>
				</Box>
				<Typography
					variant="h6"
					fontWeight="bold"
					color={report.comparison.change_percent > 0 ? 'error.main' : 'success.main'}
				>
					{report.comparison.change_percent > 0 ? '+' : ''}
					{report.comparison.change_percent}%
				</Typography>
			</Paper>

			{/* Issues */}
			{report.issues.length > 0 && (
				<Box sx={{ mb: 3 }}>
					<Typography variant="body2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
						<AlertCircleIcon color="warning" />
						Требует внимания
					</Typography>
					<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
						{report.issues.map((issue, idx) => (
							<Alert key={idx} severity="warning" sx={{ py: 0 }}>
								{issue}
							</Alert>
						))}
					</Box>
				</Box>
			)}

			{/* Recommendations */}
			<Box>
				<Typography variant="body2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
					<TargetIcon color="primary" />
					Рекомендации AI
				</Typography>
				<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
					{report.recommendations.map((rec, idx) => (
						<Alert key={idx} severity="info" sx={{ py: 0 }}>
							{rec}
						</Alert>
					))}
				</Box>
			</Box>
		</Paper>
	);
};