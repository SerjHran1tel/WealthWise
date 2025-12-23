// src/App.jsx
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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        {/* Fixed Header */}
        <motion.header
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          className="fixed top-0 left-0 right-0 z-40 glass border-b border-white/20 backdrop-blur-lg"
        >
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-8">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                WealthWise
              </h1>

              <nav className="hidden md:flex items-center gap-1 bg-white/60 backdrop-blur rounded-full px-2 py-1 border border-white/30">
                <button
                  onClick={() => setActiveView('dashboard')}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-full transition-all ${
                    activeView === 'dashboard'
                      ? 'bg-white shadow-md text-blue-700'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <LayoutDashboard size={18} />
                  <span className="font-medium">Дашборд</span>
                </button>
                <button
                  onClick={() => setActiveView('report')}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-full transition-all ${
                    activeView === 'report'
                      ? 'bg-white shadow-md text-blue-700'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Calendar size={18} />
                  <span className="font-medium">Отчёт</span>
                </button>
              </nav>
            </div>

            <div className="flex items-center gap-4">
              {/* Month Picker */}
              <div className="flex items-center gap-3 bg-white/70 backdrop-blur rounded-full px-4 py-2.5 border border-white/40 shadow-sm">
                <button onClick={() => changeMonth(-1)} className="p-1 hover:bg-white/60 rounded-full transition">
                  <ChevronLeft size={18} />
                </button>
                <span className="font-semibold text-slate-800 min-w-32 text-center capitalize">
                  {displayMonth}
                </span>
                <button onClick={() => changeMonth(1)} className="p-1 hover:bg-white/60 rounded-full transition">
                  <ChevronRight size={18} />
                </button>
              </div>

              <button
                onClick={handleRefresh}
                disabled={loading}
                className="relative p-3 bg-white/80 backdrop-blur rounded-full shadow-md hover:shadow-lg transition-all hover:scale-105 active:scale-95"
              >
                {loading ? (
                  <Loader2 size={20} className="animate-spin text-blue-600" />
                ) : (
                  <RefreshCw size={20} className="text-blue-600" />
                )}
                {loading && (
                  <span className="absolute inset-0 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                )}
              </button>
            </div>
          </div>
        </motion.header>

        {/* Main Content */}
        <AnimatePresence mode="wait">
          {activeView === 'dashboard' ? (
            <motion.main
              key="dashboard"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="pt-28 pb-12 px-6 max-w-7xl mx-auto"
            >
              <InsightsPanel insights={insights} />

              <SummaryCards transactions={transactions} />

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Левая колонка */}
                <div className="lg:col-span-4 flex flex-col gap-8">
                  <FileUpload onUploadSuccess={handleRefresh} />
                  <BudgetList budgets={budgets} categories={categories} onUpdate={handleRefresh} />
                  <CategoryChart transactions={transactions} />
                  <GoalList goals={goals} onUpdate={handleRefresh} />
                </div>

                {/* Правая колонка */}
                <div className="lg:col-span-8 flex flex-col gap-8">
                  <TrendChart transactions={transactions} />

                  <div className="bg-white/80 backdrop-blur rounded-2xl shadow-xl border border-white/50 overflow-hidden">
                    <div className="p-6 border-b border-slate-100/60 bg-gradient-to-r from-blue-500/10 to-indigo-500/10">
                      <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold text-slate-800">История операций</h2>
                        <span className="text-sm font-medium px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full">
                          {transactions.length} операций
                        </span>
                      </div>
                    </div>
                    <div className="p-6">
                      {loading && transactions.length === 0 ? (
                        <div className="text-center py-16 text-slate-400">Загрузка операций...</div>
                      ) : (
                        <TransactionList
                          transactions={transactions}
                          categories={categories}
                          onTransactionUpdate={handleRefresh}
                        />
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </motion.main>
          ) : (
            <motion.main
              key="report"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              className="pt-28 pb-12 px-6 max-w-5xl mx-auto"
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