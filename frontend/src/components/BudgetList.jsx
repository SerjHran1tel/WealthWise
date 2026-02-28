import React, { useState } from 'react';
import {
	Paper,
	Typography,
	Box,
	IconButton,
	Button,
	TextField,
	MenuItem,
	LinearProgress,
	Alert,
} from '@mui/material';
import { Add, Delete } from '@mui/icons-material';
import { budgetService } from '../services/api';

export const BudgetList = ({ budgets, categories, onUpdate }) => {
	const [isAdding, setIsAdding] = useState(false);
	const [newBudget, setNewBudget] = useState({ categoryId: '', amount: '' });

	const formatCurrency = (val) =>
		new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(val);

	const handleSubmit = async (e) => {
		e.preventDefault();
		if (!newBudget.categoryId || !newBudget.amount) return;
		try {
			await budgetService.create(newBudget.categoryId, newBudget.amount);
			setNewBudget({ categoryId: '', amount: '' });
			setIsAdding(false);
			onUpdate();
		} catch (error) {
			console.error('Failed to create budget', error);
		}
	};

	const handleDelete = async (id) => {
		if (window.confirm('Удалить этот бюджет?')) {
			try {
				await budgetService.delete(id);
				onUpdate();
			} catch (error) {
				console.error('Failed to delete budget', error);
			}
		}
	};

	return (
		<Paper sx={{ p: 3 }}>
			<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
				<Typography variant="h6">Бюджеты на месяц</Typography>
				<IconButton onClick={() => setIsAdding(!isAdding)} size="small">
					<Add />
				</IconButton>
			</Box>

			{isAdding && (
				<Box component="form" onSubmit={handleSubmit} sx={{ mb: 3, p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
					<TextField
						select
						label="Категория"
						value={newBudget.categoryId}
						onChange={(e) => setNewBudget({ ...newBudget, categoryId: e.target.value })}
						size="small"
						fullWidth
						required
						sx={{ mb: 2 }}
					>
						<MenuItem value="">Выберите категорию</MenuItem>
						{categories.map((c) => (
							<MenuItem key={c.id} value={c.id}>
								{c.name}
							</MenuItem>
						))}
					</TextField>
					<TextField
						label="Лимит (₽)"
						type="number"
						value={newBudget.amount}
						onChange={(e) => setNewBudget({ ...newBudget, amount: e.target.value })}
						size="small"
						fullWidth
						required
						sx={{ mb: 2 }}
					/>
					<Button type="submit" variant="contained" fullWidth>
						Сохранить
					</Button>
				</Box>
			)}

			<Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
				{budgets.length === 0 && !isAdding && (
					<Typography color="text.secondary" align="center" py={2}>
						Нет активных бюджетов
					</Typography>
				)}

				{budgets.map((b) => (
					<Box key={b.id} sx={{ position: 'relative', '&:hover .delete-btn': { opacity: 1 } }}>
						<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
							<Typography variant="body2" fontWeight="medium">
								{b.category_name}
							</Typography>
							<Typography variant="body2" color="text.secondary">
								{formatCurrency(b.spent_amount)} / {formatCurrency(b.limit_amount)}
							</Typography>
						</Box>
						<LinearProgress
							variant="determinate"
							value={Math.min(b.percentage, 100)}
							color={b.is_exceeded ? 'error' : b.percentage > 80 ? 'warning' : 'success'}
							sx={{ height: 8, borderRadius: 4 }}
						/>
						{b.is_exceeded && (
							<Alert severity="error" sx={{ mt: 1, py: 0, fontSize: '0.75rem' }}>
								Превышение на {formatCurrency(b.spent_amount - b.limit_amount)}
							</Alert>
						)}
						<IconButton
							className="delete-btn"
							onClick={() => handleDelete(b.id)}
							size="small"
							sx={{ position: 'absolute', top: 0, right: -24, opacity: 0, transition: 'opacity 0.2s' }}
						>
							<Delete fontSize="small" />
						</IconButton>
					</Box>
				))}
			</Box>
		</Paper>
	);
};