import React, { useState, useEffect } from 'react';
import {
	Paper,
	Typography,
	Box,
	Grid,
	Alert,
	CircularProgress,
	Chip,
	LinearProgress,
	Button,
	Divider,
} from '@mui/material';
import {
	CalendarMonth as CalendarIcon,
	TrendingUp as TrendingUpIcon,
	Warning as AlertCircleIcon,
	EmojiEvents as TargetIcon,
	PlaylistAddCheck as ActionsIcon,
	Flag as GoalIcon,
	Refresh as RefreshIcon,
} from '@mui/icons-material';
import { reportService } from '../services/api';

export const WeeklyReport = () => {
	const [report, setReport] = useState(null);
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [error, setError] = useState(null);

	useEffect(() => {
		fetchReport();
	}, []);

	const fetchReport = async () => {
		try {
			setError(null);
			const data = await reportService.getWeekly();
			setReport(data);
		} catch (error) {
			console.error('Failed to load report:', error);
			setError('Не удалось загрузить отчёт. Проверьте соединение с сервером.');
		} finally {
			setLoading(false);
		}
	};

	const handleRefresh = async () => {
		setRefreshing(true);
		try {
			const data = await reportService.refreshWeekly();
			setReport(data);
			setError(null);
		} catch (err) {
			setError('Не удалось обновить отчёт.');
		} finally {
			setRefreshing(false);
		}
	};

	if (loading) return (
		<Box sx={{ textAlign: 'center', py: 8 }}>
			<CircularProgress />
		</Box>
	);

	if (error) return (
		<Alert severity="error" sx={{ mt: 2 }}>
			{error}
		</Alert>
	);

	if (!report) return null;

	const severityMap = {
		high: 'error',
		medium: 'warning',
		low: 'info',
	};

	const priorityColorMap = {
		high: 'error',
		medium: 'warning',
		low: 'info',
	};

	return (
		<Paper sx={{ p: 3, mb: 4 }}>
			<Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
				<Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
					<CalendarIcon color="primary" />
					Еженедельный отчёт
				</Typography>
				<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
					<Typography variant="body2" color="text.secondary">
						{report.period}
					</Typography>
					<Button
						size="small"
						variant="outlined"
						startIcon={refreshing ? <CircularProgress size={14} /> : <RefreshIcon />}
						onClick={handleRefresh}
						disabled={refreshing}
					>
						{refreshing ? 'Обновляем...' : 'Обновить'}
					</Button>
				</Box>
			</Box>

			{/* Stats */}
			<Grid container spacing={2} sx={{ mb: 3 }}>
				<Grid item xs={12} sm={4}>
					<Paper variant="outlined" sx={{ p: 2, bgcolor: 'primary.light' }}>
						<Typography variant="caption" color="primary.contrastText">Расходы</Typography>
						<Typography variant="h5" fontWeight="bold" color="primary.contrastText">
							{report.stats.expenses.toLocaleString()} ₽
						</Typography>
					</Paper>
				</Grid>
				<Grid item xs={12} sm={4}>
					<Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light' }}>
						<Typography variant="caption" color="success.contrastText">Доходы</Typography>
						<Typography variant="h5" fontWeight="bold" color="success.contrastText">
							{report.stats.income.toLocaleString()} ₽
						</Typography>
					</Paper>
				</Grid>
				<Grid item xs={12} sm={4}>
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

			{/* Top Categories */}
			{report.top_categories && report.top_categories.length > 0 && (
				<Box sx={{ mb: 3 }}>
					<Typography variant="body2" fontWeight="medium" sx={{ mb: 1 }}>
						Топ категорий расходов
					</Typography>
					<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
						{report.top_categories.map((cat, idx) => (
							<Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
								<Typography variant="body2">
									{idx + 1}. {cat.category}
								</Typography>
								<Typography variant="body2" fontWeight="bold">
									{cat.amount.toLocaleString()} ₽
									<Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
										({cat.transactions_count} оп.)
									</Typography>
								</Typography>
							</Box>
						))}
					</Box>
				</Box>
			)}

			{/* Issues */}
			{report.issues && report.issues.length > 0 && (
				<Box sx={{ mb: 3 }}>
					<Typography variant="body2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
						<AlertCircleIcon color="warning" />
						Требует внимания
					</Typography>
					<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
						{report.issues.map((issue, idx) => (
							<Alert key={idx} severity={severityMap[issue.severity] || 'warning'} sx={{ py: 0 }}>
								{issue.message}
							</Alert>
						))}
					</Box>
				</Box>
			)}

			{/* Recommendations */}
			{report.recommendations && report.recommendations.length > 0 && (
				<Box sx={{ mb: 3 }}>
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
			)}

			{/* Actions */}
			{report.actions && report.actions.length > 0 && (
				<Box sx={{ mb: 3 }}>
					<Typography variant="body2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
						<ActionsIcon color="action" />
						Предложенные действия
					</Typography>
					<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
						{report.actions.map((action, idx) => (
							<Paper key={idx} variant="outlined" sx={{ p: 2 }}>
								<Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
									<Chip
										label={action.priority === 'high' ? 'Важно' : action.priority === 'medium' ? 'Средне' : 'Низкий'}
										color={priorityColorMap[action.priority] || 'default'}
										size="small"
									/>
									<Typography variant="body2" fontWeight="bold">
										{action.title}
									</Typography>
								</Box>
								<Typography variant="body2" color="text.secondary">
									{action.description}
								</Typography>
							</Paper>
						))}
					</Box>
				</Box>
			)}

			{/* Goals Progress */}
			{report.goals_progress && report.goals_progress.length > 0 && (
				<Box>
					<Typography variant="body2" fontWeight="medium" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
						<GoalIcon color="success" />
						Прогресс по целям
					</Typography>
					<Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
						{report.goals_progress.map((goal, idx) => (
							<Box key={idx}>
								<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
									<Typography variant="body2">{goal.name}</Typography>
									<Typography variant="body2" fontWeight="bold">
										{goal.percentage}%
									</Typography>
								</Box>
								<LinearProgress
									variant="determinate"
									value={Math.min(goal.percentage, 100)}
									color={goal.status === 'completed' ? 'success' : 'primary'}
									sx={{ height: 8, borderRadius: 4 }}
								/>
								<Typography variant="caption" color="text.secondary">
									{goal.current.toLocaleString()} / {goal.target.toLocaleString()} ₽
								</Typography>
							</Box>
						))}
					</Box>
				</Box>
			)}
		</Paper>
	);
};