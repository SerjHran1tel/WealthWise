import React, { useState } from 'react';
import { Paper, Typography, Box, Button, CircularProgress, Alert, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { CloudUpload, CheckCircle, Error, DeleteForever } from '@mui/icons-material';
import { transactionService } from '../services/api';
import { motion } from 'framer-motion';

export const FileUpload = ({ onUploadSuccess }) => {
	const [loading, setLoading] = useState(false);
	const [clearing, setClearing] = useState(false);
	const [status, setStatus] = useState(null); // { type: 'success'|'error', text }
	const [confirmOpen, setConfirmOpen] = useState(false);

	const handleFileChange = async (e) => {
		const file = e.target.files[0];
		if (!file) return;

		setLoading(true);
		setStatus(null);

		try {
			const result = await transactionService.upload(file);
			setStatus({
				type: 'success',
				text: result.imported_count ? `+${result.imported_count} записей` : 'Файл обработан успешно'
			});
			onUploadSuccess();
		} catch (error) {
			console.error('Upload error:', error);
			const errorMessage = error.response?.data?.detail || error.message || 'Сбой загрузки';
			setStatus({ type: 'error', text: errorMessage });
		} finally {
			setLoading(false);
			e.target.value = null;
		}
	};

	const handleClearConfirm = async () => {
		setConfirmOpen(false);
		setClearing(true);
		setStatus(null);
		try {
			const result = await transactionService.clearAll();
			setStatus({ type: 'success', text: result.message });
			onUploadSuccess();
		} catch (error) {
			setStatus({ type: 'error', text: 'Ошибка при очистке данных' });
		} finally {
			setClearing(false);
		}
	};

	return (
		<Paper sx={{ p: 3 }}>
			<Typography variant="h6" gutterBottom>
				Импорт данных
			</Typography>

			<Button
				component="label"
				variant="outlined"
				startIcon={<CloudUpload />}
				disabled={loading || clearing}
				fullWidth
				sx={{ height: 100, borderStyle: 'dashed' }}
			>
				{loading ? <CircularProgress size={24} /> : 'Нажмите для выбора CSV/PDF'}
				<input type="file" hidden accept=".csv,.pdf" onChange={handleFileChange} />
			</Button>
			<Typography variant="caption" color="text.secondary" align="center" display="block" sx={{ mt: 1 }}>
				Сбер, Тинькофф, Альфа
			</Typography>

			<Button
				variant="text"
				color="error"
				size="small"
				startIcon={clearing ? <CircularProgress size={14} /> : <DeleteForever />}
				disabled={loading || clearing}
				onClick={() => setConfirmOpen(true)}
				sx={{ mt: 1 }}
				fullWidth
			>
				Очистить все транзакции
			</Button>

			{status && (
				<motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
					<Alert severity={status.type} icon={status.type === 'success' ? <CheckCircle /> : <Error />} sx={{ mt: 2 }}>
						{status.text}
					</Alert>
				</motion.div>
			)}

			<Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
				<DialogTitle>Очистить все транзакции?</DialogTitle>
				<DialogContent>
					<Typography>Все транзакции будут удалены безвозвратно. После этого загрузите файл заново.</Typography>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setConfirmOpen(false)}>Отмена</Button>
					<Button onClick={handleClearConfirm} color="error" variant="contained">Удалить всё</Button>
				</DialogActions>
			</Dialog>
		</Paper>
	);
};
