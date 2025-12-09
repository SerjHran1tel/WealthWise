import React, { useEffect, useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { TransactionList } from './components/TransactionList';
import { CategoryChart } from './components/CategoryChart';
import { SummaryCards } from './components/SummaryCards';
import { TrendChart } from './components/TrendChart';
import { BudgetList } from './components/BudgetList';
import { transactionService, categoryService, budgetService } from './services/api';
import { LayoutDashboard, Calendar } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(false);

  // Дефолтный фильтр (можно менять вручную в коде, если нужно)
  const [dateFilter, setDateFilter] = useState("2025-12");

  const getPeriodBounds = () => {
    if (!dateFilter) return { startDate: '', endDate: '' };
    const [year, month] = dateFilter.split('-');
    const lastDay = new Date(year, month, 0).getDate();
    return {
      startDate: `${year}-${month}-01`,
      endDate: `${year}-${month}-${lastDay}`
    };
  };

  // --- НОВАЯ ЛОГИКА ЗАГРУЗКИ ---
  const fetchData = async () => {
    setLoading(true);
    const { startDate, endDate } = getPeriodBounds();
    console.log(`Запрос данных за: ${startDate} — ${endDate}`);

    // 1. Грузим категории (нужны для всего)
    try {
      const catsData = await categoryService.getAll();
      setCategories(catsData);
    } catch (e) {
      console.error("Ошибка загрузки категорий:", e);
    }

    // 2. Грузим транзакции (НЕЗАВИСИМО)
    try {
      const transData = await transactionService.getAll({ start_date: startDate, end_date: endDate });
      console.log("Успешно загружено транзакций:", transData.length);
      setTransactions(transData);
    } catch (e) {
      console.error("Ошибка загрузки транзакций:", e);
    }

    // 3. Грузим бюджеты (НЕЗАВИСИМО)
    try {
      const budgetsData = await budgetService.getStatus(startDate, endDate);
      setBudgets(budgetsData);
    } catch (e) {
      console.error("Ошибка загрузки бюджетов (возможно нет данных или ошибка сервера):", e);
      // Не ломаем приложение, просто оставляем бюджеты пустыми
      setBudgets([]);
    }

    setLoading(false);
  };
  // -----------------------------

  useEffect(() => {
    fetchData();
  }, [dateFilter]);

  const handleRefresh = () => {
    fetchData();
  };

  const { startDate, endDate } = getPeriodBounds();

  return (
    <div className="min-h-screen pb-10 font-sans text-gray-900 bg-gray-50">
      <header className="bg-white shadow-sm mb-8 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary p-2 rounded text-white">
              <LayoutDashboard size={24} />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">WealthWise</h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-xs text-gray-500 hidden md:block">
              Период: {startDate} — {endDate}
            </div>

            <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg border border-gray-200">
              <Calendar size={18} className="text-gray-500 ml-2" />
              <input
                type="month"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="bg-transparent border-none text-sm focus:ring-0 p-2 text-gray-700 outline-none cursor-pointer"
              />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4">
        {/* Карточки отобразятся, если transactions загрузились */}
        <SummaryCards transactions={transactions} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="md:col-span-1 flex flex-col gap-6">
            <FileUpload onUploadSuccess={handleRefresh} />

            <BudgetList
              budgets={budgets}
              categories={categories}
              dateRange={{ startDate, endDate }}
              onUpdate={handleRefresh}
            />

            <CategoryChart transactions={transactions} />
          </div>

          <div className="md:col-span-2 flex flex-col gap-6">
             <TrendChart transactions={transactions} />

             <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-800">
                  Операции за период ({transactions.length})
                </h2>
              </div>

              {loading && transactions.length === 0 ? (
                <div className="text-center p-10 text-gray-500 bg-white rounded-lg shadow-sm">
                  Загрузка данных...
                </div>
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
      </main>
    </div>
  );
}

export default App;