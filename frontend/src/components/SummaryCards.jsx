import React from 'react';
import { ArrowUpRight, ArrowDownRight, Wallet } from 'lucide-react';
import { motion } from 'framer-motion';

export const SummaryCards = ({ transactions = [] }) => {
  const income = transactions.filter(t => t.is_income).reduce((acc, t) => acc + t.amount, 0);
  const expense = transactions.filter(t => !t.is_income).reduce((acc, t) => acc + t.amount, 0);
  const balance = income - expense;

  const format = (val) => new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(val);

  const Card = ({ title, amount, icon: Icon, colorClass, bgClass }) => (
    <motion.div
      whileHover={{ y: -5 }}
      className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 relative overflow-hidden group"
    >
      <div className={`absolute top-0 right-0 w-32 h-32 ${bgClass} rounded-full -mr-16 -mt-16 opacity-10 group-hover:scale-150 transition-transform duration-500`} />

      <div className="flex justify-between items-start relative z-10">
        <div>
          <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
          <h3 className="text-3xl font-bold text-slate-800 tracking-tight">{amount}</h3>
        </div>
        <div className={`p-3 rounded-xl ${bgClass} ${colorClass}`}>
          <Icon size={24} />
        </div>
      </div>
    </motion.div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <Card
        title="Расходы"
        amount={format(expense)}
        icon={ArrowDownRight}
        colorClass="text-rose-600"
        bgClass="bg-rose-100"
      />
      <Card
        title="Доходы"
        amount={format(income)}
        icon={ArrowUpRight}
        colorClass="text-emerald-600"
        bgClass="bg-emerald-100"
      />
      <Card
        title="Баланс"
        amount={format(balance)}
        icon={Wallet}
        colorClass="text-blue-600"
        bgClass="bg-blue-100"
      />
    </div>
  );
};