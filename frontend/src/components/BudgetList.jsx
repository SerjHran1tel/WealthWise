import React, { useState } from 'react';
import { Plus, Trash2, AlertTriangle } from 'lucide-react';
import { budgetService } from '../services/api';

export const BudgetList = ({ budgets, categories, dateRange, onUpdate }) => {
	const [isAdding, setIsAdding] = useState(false);
	const [newBudget, setNewBudget] = useState({ categoryId: '', amount: '' });

	const formatCurrency = (val) => new Intl.NumberFormat('ru-RU', {
		style: 'currency', currency: 'RUB', maximumFractionDigits: 0
	}).format(val);

	const handleSubmit = async (e) => {
		e.preventDefault();
		if (!newBudget.categoryId || !newBudget.amount) return;

		try {
			await budgetService.create(newBudget.categoryId, newBudget.amount);
			setNewBudget({ categoryId: '', amount: '' });
			setIsAdding(false);
			onUpdate(); // Обновляем данные
		} catch (error) {
			console.error("Failed to create budget", error);
		}
	};

	const handleDelete = async (id) => {
		if (window.confirm('Удалить этот бюджет?')) {
			try {
				await budgetService.delete(id);
				onUpdate();
			} catch (error) {
				console.error("Failed to delete budget", error);
			}
		}
	};

	return (
		<div className="budget-card">
			<div className="budget-card__header">
				<h3 className="budget-card__title">Бюджеты</h3>
				<button
					onClick={() => setIsAdding(!isAdding)}
					className={`budget-card__toggle-btn ${isAdding ? 'budget-card__toggle-btn--active' : ''}`}
				>
					{isAdding ? <X size={18} /> : <Plus size={18} />}
				</button>
			</div>

			{isAdding && (
				<form onSubmit={handleSubmit} className="budget-form">
					<div className="budget-form__group">
						<select
							className="budget-form__select"
							value={newBudget.categoryId}
							onChange={(e) => setNewBudget({ ...newBudget, categoryId: e.target.value })}
							required
						>
							<option value="">Категория</option>
							{categories.map(c => (
								<option key={c.id} value={c.id}>{c.name}</option>
							))}
						</select>
						<input
							type="number"
							placeholder="Лимит (₽)"
							className="budget-form__input"
							value={newBudget.amount}
							onChange={(e) => setNewBudget({ ...newBudget, amount: e.target.value })}
							required
						/>
					</div>
					<button type="submit" className="budget-form__submit">
						Установить лимит
					</button>
				</form>
			)}

			<div className="budget-list">
				{budgets.length === 0 && !isAdding && (
					<div className="budget-list__empty">Нет активных лимитов</div>
				)}

				{budgets.map((b) => (
					<div key={b.id} className="budget-item">
						<div className="budget-item__info">
							<span className="budget-item__name">{b.category_name}</span>
							<span className="budget-item__values">
								<span className="budget-item__spent">{formatCurrency(b.spent_amount)}</span>
								<span className="budget-item__separator">/</span>
								<span className="budget-item__limit">{formatCurrency(b.limit_amount)}</span>
							</span>
						</div>

						<div className="budget-item__progress-container">
							<div
								className={`budget-item__progress-bar ${b.is_exceeded ? 'budget-item__progress-bar--danger' :
										b.percentage > 80 ? 'budget-item__progress-bar--warning' : ''
									}`}
								style={{ width: `${Math.min(b.percentage, 100)}%` }}
							/>
						</div>

						{b.is_exceeded && (
							<div className="budget-item__alert">
								<AlertTriangle size={12} />
								<span>Превышено на {formatCurrency(b.spent_amount - b.limit_amount)}</span>
							</div>
						)}

						<button
							onClick={() => handleDelete(b.id)}
							className="budget-item__delete"
							aria-label="Удалить"
						>
							<Trash2 size={14} />
						</button>
					</div>
				))}
			</div>
		</div>
	);
};