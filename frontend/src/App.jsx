import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion'; // <-- Анимации
import { FileUpload } from './components/FileUpload';
import { TransactionList } from './components/TransactionList';
import { CategoryChart } from './components/CategoryChart';
import { SummaryCards } from './components/SummaryCards';
import { TrendChart } from './components/TrendChart';
import { BudgetList } from './components/BudgetList';
import { InsightsPanel } from './components/InsightsPanel';
import { ChatWidget } from './components/ChatWidget';
import { GoalList } from './components/GoalList';
import { transactionService, categoryService, budgetService, insightService, goalService } from './services/api';
import { LayoutDashboard, Calendar, RefreshCw } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [insights, setInsights] = useState([]);
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dateFilter, setDateFilter] = useState("2025-12");

  // ... (Оставляем функции getPeriodBounds и fetchData без изменений) ...
  const getPeriodBounds = () => {
    if (!dateFilter) return { startDate: '', endDate: '' };
    const [year, month] = dateFilter.split('-');
    const lastDay = new Date(year, month, 0).getDate();
    return { startDate: `${year}-${month}-01`, endDate: `${year}-${month}-${lastDay}` };
  };

  const fetchData = async () => {
    setLoading(true);
    const { startDate, endDate } = getPeriodBounds();
    try {
      const [cats, trans, buds, ins, gls] = await Promise.all([
        categoryService.getAll().catch(() => []),
        transactionService.getAll({ start_date: startDate, end_date: endDate }).catch(() => []),
        budgetService.getStatus(startDate, endDate).catch(() => []),
        insightService.getAll().catch(() => []),
        goalService.getAll().catch(() => [])
      ]);
      setCategories(cats);
      setTransactions(trans);
      setBudgets(buds);
      setInsights(ins);
      setGoals(gls);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [dateFilter]);
  const handleRefresh = () => { fetchData(); };
  const { startDate, endDate } = getPeriodBounds();

  // Анимационные варианты
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
  };

  return (
    <div className="min-h-screen pb-20 bg-slate-50 text-slate-900 selection:bg-blue-100">
      {/* Glass Header */}
      <header className="sticky top-0 z-40 w-full glass shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-blue-600 to-indigo-600 p-2.5 rounded-xl text-white shadow-lg shadow-blue-500/30">
              <LayoutDashboard size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600">
                WealthWise
              </h1>
              <p className="text-xs text-slate-500 font-medium">Financial AI Assistant</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:block text-xs font-medium text-slate-500 bg-white/50 px-3 py-1.5 rounded-full border border-slate-200">
              {startDate} — {endDate}
            </div>

            <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm hover:border-blue-300 transition-colors cursor-pointer group">
              <Calendar size={16} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
              <input
                type="month"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="bg-transparent border-none text-sm font-medium text-slate-700 focus:ring-0 p-0 outline-none cursor-pointer w-32"
              />
            </div>

            <button onClick={handleRefresh} className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all active:scale-95">
              <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content with Staggered Animation */}
      <motion.main
        className="max-w-7xl mx-auto px-4 sm:px-6 pt-8"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div variants={itemVariants}>
          <InsightsPanel insights={insights} />
        </motion.div>

        <motion.div variants={itemVariants}>
          <SummaryCards transactions={transactions} />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Левая колонка */}
          <motion.div className="lg:col-span-1 flex flex-col gap-8" variants={itemVariants}>
            <FileUpload onUploadSuccess={handleRefresh} />
            <BudgetList budgets={budgets} categories={categories} dateRange={{ startDate, endDate }} onUpdate={handleRefresh} />
            <CategoryChart transactions={transactions} />
          </motion.div>

          {/* Правая колонка */}
          <motion.div className="lg:col-span-2 flex flex-col gap-8" variants={itemVariants}>
             <TrendChart transactions={transactions} />
             <GoalList goals={goals} onUpdate={handleRefresh} />

             <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-white">
                  <h2 className="text-lg font-bold text-slate-800">
                    История операций
                  </h2>
                  <span className="text-xs font-medium px-2 py-1 bg-slate-100 rounded-lg text-slate-500">
                    {transactions.length} записей
                  </span>
                </div>
                {loading && transactions.length === 0 ? (
                  <div className="p-12 text-center text-slate-400">Загрузка данных...</div>
                ) : (
                  <TransactionList transactions={transactions} categories={categories} onTransactionUpdate={handleRefresh} />
                )}
            </div>
          </motion.div>
        </div>
      </motion.main>

      <ChatWidget />
    </div>
  );
}

export default App;