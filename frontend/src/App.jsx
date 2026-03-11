import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
	Box,
	Container,
	AppBar,
	Toolbar,
	Typography,
	IconButton,
	Button,
	Paper,
	Badge,
	CircularProgress,
	BottomNavigation,
	BottomNavigationAction,
	Alert,
	Snackbar,
} from '@mui/material';
import {
	Dashboard as DashboardIcon,
	CalendarMonth as CalendarIcon,
	Refresh as RefreshIcon,
	ChevronLeft as ChevronLeftIcon,
	ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';

import { FileUpload } from './components/FileUpload';
import { TransactionList } from './components/TransactionList';
import { CategoryChart } from './components/CategoryChart';
import { SummaryCards } from './components/SummaryCards';
import { TrendChart } from './components/TrendChart';
import { BudgetList } from './components/BudgetList';
import { InsightsPanel } from './components/InsightsPanel';
import { ChatWidget } from './components/ChatWidget';
import { GoalList } from './components/GoalList';
import { WeeklyReport } from './components/WeeklyReport';

import {
	transactionService,
	categoryService,
	budgetService,
	insightService,
	goalService,
} from './services/api';

function App() {
	const [transactions, setTransactions] = useState([]);
	const [categories, setCategories] = useState([]);
	const [budgets, setBudgets] = useState([]);
	const [insights, setInsights] = useState([]);
	const [goals, setGoals] = useState([]);
	const [error, setError] = useState(null);
	const [loading, setLoading] = useState(false);
	const [dateFilter, setDateFilter] = useState(() => format(new Date(), 'yyyy-MM'));
	const [activeView, setActiveView] = useState('dashboard');

	const getPeriodBounds = () => {
		const [year, month] = dateFilter.split('-');
		const lastDay = new Date(year, month, 0).getDate();
		return {
			startDate: `${year}-${month}-01`,
			endDate: `${year}-${month}-${lastDay}`,
		};
	};

	const { startDate, endDate } = getPeriodBounds();

	const fetchData = async () => {
		setLoading(true);
		try {
			const [cats, transRes, buds, ins, gls] = await Promise.all([
				categoryService.getAll(),
				transactionService.getAll({ start_date: startDate, end_date: endDate }),
				budgetService.getStatus(startDate, endDate),
				insightService.getAll(),
				goalService.getAll(),
			]);

			setCategories(cats || []);
			setTransactions(transRes?.items || transRes || []);
			setBudgets(buds || []);
			setInsights(ins || []);
			setGoals(gls || []);
			setError(null);
		} catch (err) {
			setError('Не удалось загрузить данные. Проверьте соединение с сервером.');
			console.error('Fetch error:', err);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		fetchData();
	}, [dateFilter]);

	const handleRefresh = () => {
		fetchData();
	};

	const changeMonth = (delta) => {
		const [year, month] = dateFilter.split('-').map(Number);
		const newDate = new Date(year, month - 1 + delta, 1);
		setDateFilter(format(newDate, 'yyyy-MM'));
	};

	const displayMonth = format(parseISO(`${dateFilter}-01`), 'LLLL yyyy', { locale: ru });

	return (

		<Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
			<AppBar position="fixed" color="inherit" elevation={0} sx={{ backdropFilter: 'blur(12px)', bgcolor: 'rgba(255,255,255,0.8)' }}>
				<Toolbar sx={{ justifyContent: 'space-between' }}>
					<Box sx={{ display: 'flex', alignItems: 'center', gap: 4 }}>
						<Typography variant="h5" sx={{ fontWeight: 700, background: 'linear-gradient(135deg, #3B82F6, #6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
							WealthWise
						</Typography>
						<Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1, bgcolor: 'rgba(255,255,255,0.6)', borderRadius: 10, p: 0.5 }}>
							<Button
								startIcon={<DashboardIcon />}
								onClick={() => setActiveView('dashboard')}
								variant={activeView === 'dashboard' ? 'contained' : 'text'}
								sx={{ borderRadius: 10 }}
							>
								Дашборд
							</Button>
							<Button
								startIcon={<CalendarIcon />}
								onClick={() => setActiveView('report')}
								variant={activeView === 'report' ? 'contained' : 'text'}
								sx={{ borderRadius: 10 }}
							>
								Отчёт
							</Button>
						</Box>
					</Box>

					<Box
						sx={{
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'space-between',
							width: '100%',
							flexWrap: 'wrap',
							gap: 1,
						}}
					>
						{/* Блок с месяцем */}
						<Paper
							elevation={0}
							sx={{
								display: 'flex',
								alignItems: 'center',
								bgcolor: 'rgba(255,255,255,0.7)',
								borderRadius: 20,
								p: 0.2,
								ml: 1, 
								flex: { xs: '1 1 auto', sm: '0 1 auto' },
								minWidth: { xs: '140px', sm: 'auto' },
							}}
						>
							<IconButton onClick={() => changeMonth(-1)} size="small" sx={{ p: 0.5 }}>
								<ChevronLeftIcon fontSize="small" />
							</IconButton>
							<Typography
								variant="body2"
								sx={{
									fontWeight: 600,
									px: 1,
									fontSize: { xs: '0.8rem', sm: '0.9rem' },
									whiteSpace: 'nowrap',
								}}
							>
								{displayMonth}
							</Typography>
							<IconButton onClick={() => changeMonth(1)} size="small" sx={{ p: 0.5 }}>
								<ChevronRightIcon fontSize="small" />
							</IconButton>
						</Paper>

						{/* Кнопка обновления */}
						<IconButton
							onClick={handleRefresh}
							disabled={loading}
							size="small"
							sx={{
								bgcolor: 'rgba(255,255,255,0.7)',
								'&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
							}}
						>
							{loading ? <CircularProgress size={20} /> : <RefreshIcon fontSize="small" />}
						</IconButton>
					</Box>
				</Toolbar>
			</AppBar>

			<Container maxWidth="xl" sx={{ pt: { xs: 10, sm: 12 }, pb: { xs: 10, sm: 12 } }}>
				<AnimatePresence mode="wait">
					{activeView === 'dashboard' ? (
						<motion.div
							key="dashboard"
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							exit={{ opacity: 0 }}
						>
							<InsightsPanel insights={insights} />
							<SummaryCards transactions={transactions} />

							<Box sx={{ display: 'grid', gridTemplateColumns: { lg: '1fr 2fr' }, gap: 4 }}>
								{/* Left column */}
								<Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
									<FileUpload onUploadSuccess={handleRefresh} />
									<BudgetList budgets={budgets} categories={categories} onUpdate={handleRefresh} />
									<CategoryChart transactions={transactions} />
									<GoalList goals={goals} onUpdate={handleRefresh} />
								</Box>

								{/* Right column */}
								<Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
									<TrendChart transactions={transactions} />

									<Paper sx={{ p: 3 }}>
										<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
											<Typography variant="h6">История операций</Typography>
											<Badge badgeContent={transactions.length} color="primary" showZero>
												<Typography variant="body2">операций</Typography>
											</Badge>
										</Box>
										{loading && transactions.length === 0 ? (
											<Box sx={{ textAlign: 'center', py: 8 }}>
												<CircularProgress />
											</Box>
										) : (
											<TransactionList
												transactions={transactions}
												categories={categories}
												onTransactionUpdate={handleRefresh}
											/>
										)}
									</Paper>
								</Box>
							</Box>
						</motion.div>
					) : (
						<motion.div
							key="report"
							initial={{ opacity: 0, y: 30 }}
							animate={{ opacity: 1, y: 0 }}
							exit={{ opacity: 0, y: -30 }}
						>
							<WeeklyReport />
						</motion.div>
					)}
				</AnimatePresence>
			</Container>
			<Snackbar
				open={!!error}
				autoHideDuration={6000}
				onClose={() => setError(null)}
				anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }} // можно изменить
			>
				<Alert
					onClose={() => setError(null)}
					severity="error"
					variant="filled" // или "standard" / "outlined"
					sx={{ width: '100%' }}
				>
					{error}
				</Alert>
			</Snackbar>

			<BottomNavigation
				value={activeView}
				onChange={(event, newValue) => setActiveView(newValue)}
				showLabels
				sx={{ display: { xs: 'flex', md: 'none' }, position: 'fixed', bottom: 0, left: 0, right: 0 }}
			>
				<BottomNavigationAction label="Дашборд" value="dashboard" icon={<DashboardIcon />} />
				<BottomNavigationAction label="Отчёт" value="report" icon={<CalendarIcon />} />
			</BottomNavigation>
			<ChatWidget />
		</Box>
	);
}

export default App;