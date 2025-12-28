import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';
import {
	LayoutDashboard,
	Calendar,
	RefreshCw,
	Loader2,
	ChevronLeft,
	ChevronRight
} from 'lucide-react';

import './App.css';

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
	goalService
} from './services/api';

function App() {
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
			endDate: `${year}-${month}-${lastDay}`
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
				goalService.getAll()
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
		<>
			<div className="app-layout">
				<motion.header
					initial={{ y: -100 }}
					animate={{ y: 0 }}
					className="header"
				>
					<div className="header__container">
						<div className="header__left">
							<h1 className="header__logo">WealthWise</h1>

							<nav className="nav">
								<button
									onClick={() => setActiveView('dashboard')}
									className={`nav__button ${activeView === 'dashboard' ? 'nav__button--active' : ''}`}
								>
									<LayoutDashboard size={18} />
									<span>Дашборд</span>
								</button>
								<button
									onClick={() => setActiveView('report')}
									className={`nav__button ${activeView === 'report' ? 'nav__button--active' : ''}`}
								>
									<Calendar size={18} />
									<span>Отчёт</span>
								</button>
							</nav>
						</div>

						<div className="header__controls">
							<div className="month-picker">
								<button onClick={() => changeMonth(-1)} className="month-picker__nav-btn">
									<ChevronLeft size={18} />
								</button>
								<span className="month-picker__display">{displayMonth}</span>
								<button onClick={() => changeMonth(1)} className="month-picker__nav-btn">
									<ChevronRight size={18} />
								</button>
							</div>

							<button
								onClick={handleRefresh}
								disabled={loading}
								className={`refresh-btn ${loading ? 'refresh-btn--loading' : ''}`}
							>
								<RefreshCw size={20} />
								{loading && <div className="refresh-btn__spinner" />}
							</button>
						</div>
					</div>
				</motion.header>

				<AnimatePresence mode="wait">
					{activeView === 'dashboard' ? (
						<motion.main
							key="dashboard"
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							exit={{ opacity: 0 }}
							className="main-content"
						>
							<InsightsPanel insights={insights} />
							<SummaryCards transactions={transactions} />

							<div className="dashboard-grid">
								<aside className="dashboard-grid__sidebar">
									<FileUpload onUploadSuccess={handleRefresh} />
									<BudgetList budgets={budgets} categories={categories} onUpdate={handleRefresh} />
									<CategoryChart transactions={transactions} />
									<GoalList goals={goals} onUpdate={handleRefresh} />
								</aside>

								<section className="dashboard-grid__main">
									<TrendChart transactions={transactions} />

									<div className="transactions-card">
										<div className="transactions-card__header">
											<h2 className="transactions-card__title">История операций</h2>
											<span className="transactions-card__badge">
												{transactions.length} операций
											</span>
										</div>
										<div className="transactions-card__content">
											{loading && transactions.length === 0 ? (
												<div className="transactions-card__loading">Загрузка операций...</div>
											) : (
												<TransactionList
													transactions={transactions}
													categories={categories}
													onTransactionUpdate={handleRefresh}
												/>
											)}
										</div>
									</div>
								</section>
							</div>
						</motion.main>
					) : (
						<motion.main
							key="report"
							initial={{ opacity: 0, y: 30 }}
							animate={{ opacity: 1, y: 0 }}
							exit={{ opacity: 0, y: -30 }}
							className="main-content main-content--report"
						>
							<WeeklyReport />
						</motion.main>
					)}
				</AnimatePresence>

				<ChatWidget />
			</div>
		</>
	);
}

export default App;