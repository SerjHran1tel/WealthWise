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
	useTheme,
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
	const theme = useTheme();
	const [transactions, setTransactions] = useState([]);
	const [categories, setCategories] = useState([]);
	const [budgets, setBudgets] = useState([]);
	const [insights, setInsights] = useState([]);
	const [goals, setGoals] = useState([]);
	const [loading, setLoading] = useState(false);
	const [dateFilter, setDateFilter] = useState('2025-12');
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
		} catch (err) {
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

					<Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
						<Paper elevation={0} sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 0.5, bgcolor: 'rgba(255,255,255,0.7)' }}>
							<IconButton onClick={() => changeMonth(-1)} size="small">
								<ChevronLeftIcon />
							</IconButton>
							<Typography variant="body1" sx={{ fontWeight: 600, minWidth: 130, textAlign: 'center', textTransform: 'capitalize' }}>
								{displayMonth}
							</Typography>
							<IconButton onClick={() => changeMonth(1)} size="small">
								<ChevronRightIcon />
							</IconButton>
						</Paper>

						<IconButton onClick={handleRefresh} disabled={loading}>
							{loading ? <CircularProgress size={24} /> : <RefreshIcon />}
						</IconButton>
					</Box>
				</Toolbar>
			</AppBar>

			<Container maxWidth="xl" sx={{ pt: 12, pb: 6 }}>
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

			<ChatWidget />
		</Box>
	);
}

export default App;