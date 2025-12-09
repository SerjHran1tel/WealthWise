import React, { useEffect, useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { TransactionList } from './components/TransactionList';
import { CategoryChart } from './components/CategoryChart';
import { SummaryCards } from './components/SummaryCards';
import { TrendChart } from './components/TrendChart';
import { transactionService, categoryService } from './services/api';
import { LayoutDashboard, Calendar } from 'lucide-react';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);

  // Состояние для фильтра даты (по умолчанию - текущий месяц)
  const [dateFilter, setDateFilter] = useState(() => {
    const now = new Date();
    // Формат YYYY-MM для input type="month"
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      // 1. Вычисляем start_date и end_date на основе выбранного месяца
      const [year, month] = dateFilter.split('-');
      const startDate = `${year}-${month}-01`;
      // Конец месяца: берем "0-й день" следующего месяца, JS сам поймет что это последний день текущего
      const endDate = new Date(year, month, 0).toISOString().split('T')[0];

      // 2. Запрашиваем данные параллельно
      const [transData, catsData] = await Promise.all([
        transactionService.getAll({ start_date: startDate, end_date: endDate }),
        categoryService.getAll()
      ]);

      setTransactions(transData);
      setCategories(catsData);
    } catch (error) {
      console.error("Failed to fetch data", error);
    } finally {
      setLoading(false);
    }
  };

  // Перезагрузка данных при изменении фильтра даты
  useEffect(() => {
    fetchData();
  }, [dateFilter]);

  // Функция для обновления (например после загрузки файла или редактирования)
  const handleRefresh = () => {
    fetchData();
  };

  return (
    <div className="min-h-screen pb-10 font-sans text-gray-900 bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm mb-8 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary p-2 rounded text-white">
              <LayoutDashboard size={24} />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">WealthWise</h1>
          </div>

          {/* Фильтр даты */}
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
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4">
        {/* Сводные карточки (Баланс, Доход, Расход) */}
        <SummaryCards transactions={transactions} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Левая колонка: Загрузка + Графики */}
          <div className="md:col-span-1 space-y-6">
            <FileUpload onUploadSuccess={handleRefresh} />

            <CategoryChart transactions={transactions} />
            <TrendChart transactions={transactions} />
          </div>

          {/* Правая колонка: Список операций */}
          <div className="md:col-span-2">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-800">
                Операции за период ({transactions.length})
              </h2>
            </div>

            {loading ? (
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
      </main>
    </div>
  );
}

export default App;