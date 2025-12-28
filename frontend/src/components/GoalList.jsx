import React, { useState } from 'react';
import { Plus, Target, Trash2, Edit3, X } from 'lucide-react';
import { goalService } from '../services/api';

export const GoalList = ({ goals, onUpdate }) => {
	const [isAdding, setIsAdding] = useState(false);
	const [editingId, setEditingId] = useState(null);

	const [newGoal, setNewGoal] = useState({
		name: '', target_amount: '', current_amount: '0', deadline: '', color: '#3B82F6'
	});

	const formatCurrency = (val) => new Intl.NumberFormat('ru-RU', {
		style: 'currency', currency: 'RUB', maximumFractionDigits: 0
	}).format(val);

	const handleSubmit = async (e) => {
		e.preventDefault();
		try {
			await goalService.create({
				...newGoal,
				target_amount: parseFloat(newGoal.target_amount),
				current_amount: parseFloat(newGoal.current_amount)
			});
			setNewGoal({ name: '', target_amount: '', current_amount: '0', deadline: '', color: '#3B82F6' });
			setIsAdding(false);
			onUpdate();
		} catch (error) {
			console.error("Failed to create goal", error);
		}
	};

	const handleDeposit = async (id, currentVal) => {
		const newVal = prompt("Введите новую текущую сумму накоплений:", currentVal);
		if (newVal !== null && !isNaN(parseFloat(newVal))) {
			try {
				await goalService.deposit(id, newVal);
				onUpdate();
			} catch (e) { console.error(e); }
		}
	};

	const handleDelete = async (id) => {
		if (window.confirm('Удалить эту цель?')) {
			try {
				await goalService.delete(id);
				onUpdate();
			} catch (e) { console.error(e); }
		}
	};

	return (
		<div className="goals-card">
			<div className="goals-card__header">
				<h3 className="goals-card__title">
					<Target size={20} />
					<span>Финансовые цели</span>
				</h3>
				<button
					onClick={() => setIsAdding(!isAdding)}
					className={`goals-card__add-btn ${isAdding ? 'goals-card__add-btn--active' : ''}`}
				>
					{isAdding ? <X size={20} /> : <Plus size={20} />}
				</button>
			</div>

			{isAdding && (
				<form onSubmit={handleSubmit} className="goal-form">
					<input
						type="text"
						placeholder="На что копим? (например, Машина)"
						className="goal-form__input"
						value={newGoal.name}
						onChange={e => setNewGoal({ ...newGoal, name: e.target.value })}
						required
					/>
					<div className="goal-form__row">
						<input
							type="number"
							placeholder="Цель (₽)"
							className="goal-form__input"
							value={newGoal.target_amount}
							onChange={e => setNewGoal({ ...newGoal, target_amount: e.target.value })}
							required
						/>
						<input
							type="number"
							placeholder="Уже есть (₽)"
							className="goal-form__input"
							value={newGoal.current_amount}
							onChange={e => setNewGoal({ ...newGoal, current_amount: e.target.value })}
						/>
					</div>
					<button type="submit" className="goal-form__submit">
						Создать цель
					</button>
				</form>
			)}

			<div className="goals-list">
				{goals.length === 0 && !isAdding && (
					<div className="goals-list__empty">Пока целей нет. Самое время поставить первую!</div>
				)}

				{goals.map((g) => (
					<div key={g.id} className="goal-item">
						<div className="goal-item__header">
							<div className="goal-item__info">
								<h4 className="goal-item__name">{g.name}</h4>
								<p className="goal-item__amounts">
									{formatCurrency(g.current_amount)} <span>из</span> {formatCurrency(g.target_amount)}
								</p>
							</div>
							<div className="goal-item__percentage">{g.percentage}%</div>
						</div>

						<div className="goal-item__progress-bg">
							<div
								className="goal-item__progress-fill"
								style={{ width: `${Math.min(g.percentage, 100)}%` }}
							/>
						</div>

						<div className="goal-item__actions">
							<button
								onClick={() => handleDeposit(g.id, g.current_amount)}
								className="goal-item__btn goal-item__btn--edit"
							>
								<Edit3 size={14} />
								<span>Изменить сумму</span>
							</button>
							<button
								onClick={() => handleDelete(g.id)}
								className="goal-item__btn goal-item__btn--delete"
							>
								<Trash2 size={14} />
							</button>
						</div>
					</div>
				))}
			</div>
		</div>
	);
};