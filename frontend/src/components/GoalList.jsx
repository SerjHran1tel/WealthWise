import React, { useState } from 'react';
import {
	Paper,
	Typography,
	Box,
	IconButton,
	Button,
	TextField,
	LinearProgress,
	Dialog,
	DialogTitle,
	DialogContent,
	DialogActions,
} from '@mui/material';
import {
	Add as PlusIcon,
	EmojiEvents as TargetIcon,
	Delete as TrashIcon,
	Edit as EditIcon,
	Close as XIcon,
} from '@mui/icons-material';
import { goalService } from '../services/api';

export const GoalList = ({ goals, onUpdate }) => {
	const [isAdding, setIsAdding] = useState(false);
	const [editingId, setEditingId] = useState(null);
	const [depositDialog, setDepositDialog] = useState({ open: false, id: null, currentAmount: 0 });

	const [newGoal, setNewGoal] = useState({
		name: '', target_amount: '', current_amount: '0', deadline: '', color: '#3B82F6'
	});

	const formatCurrency = (val) =>
		new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(val);

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
			console.error('Failed to create goal', error);
		}
	};

	const handleDeposit = async () => {
		const { id, currentAmount } = depositDialog;
		try {
			await goalService.deposit(id, currentAmount);
			onUpdate();
			setDepositDialog({ open: false, id: null, currentAmount: 0 });
		} catch (e) {
			console.error(e);
		}
	};

	const handleDelete = async (id) => {
		if (window.confirm('Удалить эту цель?')) {
			try {
				await goalService.delete(id);
				onUpdate();
			} catch (e) {
				console.error(e);
			}
		}
	};

	return (
		<Paper sx={{ p: 3 }}>
			<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
				<Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
					<TargetIcon color="primary" />
					Финансовые цели
				</Typography>
				<IconButton onClick={() => setIsAdding(!isAdding)} size="small">
					{isAdding ? <XIcon /> : <PlusIcon />}
				</IconButton>
			</Box>

			{isAdding && (
				<Box component="form" onSubmit={handleSubmit} sx={{ mb: 3, p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
					<TextField
						label="Название"
						size="small"
						fullWidth
						required
						value={newGoal.name}
						onChange={(e) => setNewGoal({ ...newGoal, name: e.target.value })}
						sx={{ mb: 2 }}
					/>
					<Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
						<TextField
							label="Цель (₽)"
							type="number"
							size="small"
							fullWidth
							required
							value={newGoal.target_amount}
							onChange={(e) => setNewGoal({ ...newGoal, target_amount: e.target.value })}
						/>
						<TextField
							label="Уже есть (₽)"
							type="number"
							size="small"
							fullWidth
							value={newGoal.current_amount}
							onChange={(e) => setNewGoal({ ...newGoal, current_amount: e.target.value })}
						/>
					</Box>
					<Button type="submit" variant="contained" fullWidth>
						Создать
					</Button>
				</Box>
			)}

			<Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
				{goals.length === 0 && !isAdding && (
					<Typography color="text.secondary" align="center" py={2}>
						Нет активных целей
					</Typography>
				)}

				{goals.map((g) => (
					<Paper
						key={g.id}
						variant="outlined"
						sx={{ p: 2, position: 'relative', '&:hover .actions': { opacity: 1 } }}
					>
						<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
							<Box>
								<Typography variant="subtitle2">{g.name}</Typography>
								<Typography variant="caption" color="text.secondary">
									{formatCurrency(g.current_amount)} из {formatCurrency(g.target_amount)}
								</Typography>
							</Box>
							<Typography variant="body2" fontWeight="bold" color="primary">
								{g.percentage}%
							</Typography>
						</Box>

						<LinearProgress
							variant="determinate"
							value={Math.min(g.percentage, 100)}
							sx={{ height: 8, borderRadius: 4, mb: 2 }}
						/>

						<Box
							className="actions"
							sx={{
								position: 'absolute',
								top: 8,
								right: 8,
								opacity: 0,
								transition: 'opacity 0.2s',
								display: 'flex',
								gap: 1,
							}}
						>
							<IconButton
								size="small"
								onClick={() => setDepositDialog({ open: true, id: g.id, currentAmount: g.current_amount })}
							>
								<EditIcon fontSize="small" />
							</IconButton>
							<IconButton size="small" onClick={() => handleDelete(g.id)} color="error">
								<TrashIcon fontSize="small" />
							</IconButton>
						</Box>
					</Paper>
				))}
			</Box>

			{/* Deposit Dialog */}
			<Dialog open={depositDialog.open} onClose={() => setDepositDialog({ open: false, id: null, currentAmount: 0 })}>
				<DialogTitle>Изменить сумму накоплений</DialogTitle>
				<DialogContent>
					<TextField
						autoFocus
						margin="dense"
						label="Текущая сумма (₽)"
						type="number"
						fullWidth
						value={depositDialog.currentAmount}
						onChange={(e) => setDepositDialog({ ...depositDialog, currentAmount: e.target.value })}
					/>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setDepositDialog({ open: false, id: null, currentAmount: 0 })}>Отмена</Button>
					<Button onClick={handleDeposit} variant="contained">Сохранить</Button>
				</DialogActions>
			</Dialog>
		</Paper>
	);
};