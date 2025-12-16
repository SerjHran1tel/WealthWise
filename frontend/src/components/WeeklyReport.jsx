import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, AlertCircle, Target } from 'lucide-react';

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

  if (loading) return <div className="text-center py-8">Загрузка отчёта...</div>;
  if (!report) return null;

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <Calendar className="text-blue-500" size={24} />
          Еженедельный отчёт
        </h2>
        <span className="text-sm text-slate-500">{report.period}</span>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-xs text-blue-600 mb-1">Расходы</p>
          <p className="text-2xl font-bold text-blue-900">
            {report.stats.expenses.toLocaleString()} ₽
          </p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <p className="text-xs text-green-600 mb-1">Доходы</p>
          <p className="text-2xl font-bold text-green-900">
            {report.stats.income.toLocaleString()} ₽
          </p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg">
          <p className="text-xs text-purple-600 mb-1">Баланс</p>
          <p className="text-2xl font-bold text-purple-900">
            {report.stats.balance.toLocaleString()} ₽
          </p>
        </div>
      </div>

      {/* Сравнение */}
      <div className="mb-6 p-4 bg-slate-50 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp size={16} className="text-slate-600" />
          <span className="text-sm font-medium text-slate-700">
            Сравнение с прошлой неделей
          </span>
        </div>
        <p className={`text-lg font-bold ${
          report.comparison.change_percent > 0 ? 'text-red-600' : 'text-green-600'
        }`}>
          {report.comparison.change_percent > 0 ? '+' : ''}
          {report.comparison.change_percent}%
        </p>
      </div>

      {/* Проблемы */}
      {report.issues.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle size={16} className="text-orange-500" />
            <span className="text-sm font-medium text-slate-700">Требует внимания</span>
          </div>
          <div className="space-y-2">
            {report.issues.map((issue, idx) => (
              <div key={idx} className="text-sm text-orange-700 bg-orange-50 p-2 rounded">
                {issue}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Рекомендации */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Target size={16} className="text-blue-500" />
          <span className="text-sm font-medium text-slate-700">Рекомендации AI</span>
        </div>
        <div className="space-y-2">
          {report.recommendations.map((rec, idx) => (
            <div key={idx} className="text-sm text-slate-700 bg-blue-50 p-3 rounded-lg">
              • {rec}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};