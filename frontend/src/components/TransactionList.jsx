import React, { useState } from 'react';
import { Trash2, ShoppingBag, Coffee, Car, Home } from 'lucide-react';
import { transactionService } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

const getCategoryIcon = (name) => {
	const n = name.toLowerCase();
	if (n.includes('продукт')) return <ShoppingBag size={14} />;
	if (n.includes('кафе') || n.includes('ресторан')) return <Coffee size={14} />;
	if (n.includes('транспорт') || n.includes('taxi')) return <Car size={14} />;
	if (n.includes('дом') || n.includes('жкх')) return <Home size={14} />;
	return <div className="w-2 h-2 rounded-full bg-current" />;
};

export const TransactionList = ({ transactions = [], categories = [], onTransactionUpdate }) => {
	const [editingId, setEditingId] = useState(null);

	const formatCurrency = (amount) => new Intl.NumberFormat('ru-RU', {
		style: 'currency', currency: 'RUB', maximumFractionDigits: 2
	}).format(amount);

	const handleDelete = async (id) => {
		if (window.confirm('Удалить?')) {
			await transactionService.delete(id);
			onTransactionUpdate();
		}
	};

	const handleCategoryChange = async (transactionId, newCategoryId) => {
		await transactionService.update(transactionId, { category_id: newCategoryId });
		onTransactionUpdate();
		setEditingId(null);
	};

	if (!transactions.length) return null;

	return (
		<div className="transactions-table-container">
			<table className="transactions-table">
				<thead className="transactions-table__head">
					<tr>
						<th className="transactions-table__th">Дата</th>
						<th className="transactions-table__th">Категория</th>
						<th className="transactions-table__th">Описание</th>
						<th className="transactions-table__th transactions-table__th--right">Сумма</th>
						<th className="transactions-table__th"></th>
					</tr>
				</thead>
				<tbody className="transactions-table__body">
					<AnimatePresence>
						{transactions.map((t) => (
							<motion.tr
								key={t.id}
								initial={{ opacity: 0, y: 4 }}
								animate={{ opacity: 1, y: 0 }}
								exit={{ opacity: 0, x: -20 }}
								className="transactions-table__row"
							>
								<td className="transactions-table__td transactions-table__td--date">
									{new Date(t.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
								</td>

								<td className="transactions-table__td">
									{editingId === t.id ? (
										<select
											className="category-select"
											autoFocus
											defaultValue={t.category?.id || ""}
											onChange={(e) => handleCategoryChange(t.id, e.target.value)}
											onBlur={() => setEditingId(null)}
										>
											<option value="" disabled>Выбрать...</option>
											{categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
										</select>
									) : (
										<div
											onClick={() => setEditingId(t.id)}
											className={`category-tag ${t.category ? 'category-tag--active' : 'category-tag--empty'}`}
										>
											<span className="category-tag__icon">
												{t.category ? getCategoryIcon(t.category.name) : <Plus size={12} />}
											</span>
											<span className="category-tag__name">
												{t.category ? t.category.name : 'Категория'}
											</span>
										</div>
									)}
								</td>

								<td className="transactions-table__td transactions-table__td--desc" title={t.description}>
									{t.description}
								</td>

								<td className={`transactions-table__td transactions-table__td--amount ${t.is_income ? 'transactions-table__td--income' : ''}`}>
									{t.is_income ? '+' : ''}{formatCurrency(t.amount)}
								</td>

								<td className="transactions-table__td transactions-table__td--actions">
									<button
										onClick={() => handleDelete(t.id)}
										className="action-btn action-btn--delete"
										aria-label="Удалить"
									>
										<Trash2 size={16} />
									</button>
								</td>
							</motion.tr>
						))}
					</AnimatePresence>
				</tbody>
			</table>
		</div>
	);
};