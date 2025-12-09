import React from 'react';
import { ArrowUpCircle, ArrowDownCircle, Wallet } from 'lucide-react';

export const SummaryCards = ({ transactions }) => {
  // Считаем доходы
  const income = transactions
    .filter(t => t.is_income)
    .reduce((acc, t) => acc + t.amount, 0);

  // Считаем расходы
  const expense = transactions
    .filter(t => !t.is_income)
    .reduce((acc, t) => acc + t.amount, 0);

  // Считаем баланс
  const balance = income - expense;

  // Форматтер валюты
  const format = (val) => new Intl.NumberFormat('ru-RU', {
    style: 'currency', currency: 'RUB', maximumFractionDigits: 0
  }).format(val);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Карточка Расходов */}
      <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-danger">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-gray-500 font-medium">Расходы</p>
            <h3 className="text-2xl font-bold text-gray-800 mt-1">{format(expense)}</h3>
          </div>
          <div className="p-2 bg-red-50 rounded text-danger">
            <ArrowDownCircle size={24} />
          </div>
        </div>
      </div>

      {/* Карточка Доходов */}
      <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-success">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-gray-500 font-medium">Доходы</p>
            <h3 className="text-2xl font-bold text-gray-800 mt-1">{format(income)}</h3>
          </div>
          <div className="p-2 bg-green-50 rounded text-success">
            <ArrowUpCircle size={24} />
          </div>
        </div>
      </div>

      {/* Карточка Баланса */}
      <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-primary">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-gray-500 font-medium">Баланс за период</p>
            <h3 className={`text-2xl font-bold mt-1 ${balance >= 0 ? 'text-gray-800' : 'text-danger'}`}>
              {balance > 0 ? '+' : ''}{format(balance)}
            </h3>
          </div>
          <div className="p-2 bg-blue-50 rounded text-primary">
            <Wallet size={24} />
          </div>
        </div>
      </div>
    </div>
  );
};