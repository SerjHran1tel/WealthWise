import React, { useState } from 'react';
import {
	Table,
	TableBody,
	TableCell,
	TableContainer,
	TableHead,
	TableRow,
	Paper,
	IconButton,
	Select,
	MenuItem,
	Chip,
	Box,
	Typography,
} from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';
import { transactionService } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';

export const TransactionList = ({ transactions = [], categories = [], onTransactionUpdate }) => {
	const [editingId, setEditingId] = useState(null);

	const formatCurrency = (amount) =>
		new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 2 }).format(amount);

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
		<TableContainer component={Paper} variant="outlined">
			<Table size="small">
				<TableHead sx={{ bgcolor: 'action.hover' }}>
					<TableRow>
						<TableCell>Дата</TableCell>
						<TableCell>Категория</TableCell>
						<TableCell>Описание</TableCell>
						<TableCell align="right">Сумма</TableCell>
						<TableCell />
					</TableRow>
				</TableHead>
				<TableBody>
					<AnimatePresence>
						{transactions.map((t) => (
							<motion.tr
								key={t.id}
								initial={{ opacity: 0 }}
								animate={{ opacity: 1 }}
								exit={{ opacity: 0 }}
								component={TableRow}
								sx={{ '&:hover': { bgcolor: 'action.hover' } }}
							>
								<TableCell>
									{new Date(t.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}
								</TableCell>
								<TableCell>
									{editingId === t.id ? (
										<Select
											size="small"
											value={t.category?.id || ''}
											onChange={(e) => handleCategoryChange(t.id, e.target.value)}
											onClose={() => setEditingId(null)}
											autoFocus
										>
											<MenuItem value="" disabled>Выбрать...</MenuItem>
											{categories.map((c) => (
												<MenuItem key={c.id} value={c.id}>
													{c.name}
												</MenuItem>
											))}
										</Select>
									) : (
										<Chip
											label={t.category ? t.category.name : 'Без категории'}
											size="small"
											color={t.category ? 'primary' : 'default'}
											variant="outlined"
											onClick={() => setEditingId(t.id)}
											sx={{ cursor: 'pointer' }}
										/>
									)}
								</TableCell>
								<TableCell>
									<Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
										{t.description}
									</Typography>
								</TableCell>
								<TableCell align="right">
									<Typography
										variant="body2"
										fontWeight="bold"
										color={t.is_income ? 'success.main' : 'text.primary'}
									>
										{t.is_income ? '+' : ''}
										{formatCurrency(t.amount)}
									</Typography>
								</TableCell>
								<TableCell align="right">
									<IconButton size="small" onClick={() => handleDelete(t.id)} color="error">
										<DeleteIcon fontSize="small" />
									</IconButton>
								</TableCell>
							</motion.tr>
						))}
					</AnimatePresence>
				</TableBody>
			</Table>
		</TableContainer>
	);
};