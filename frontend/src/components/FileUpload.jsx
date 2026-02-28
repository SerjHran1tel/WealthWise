import React, { useState } from 'react';
import { Paper, Typography, Box, Button, CircularProgress, Alert } from '@mui/material';
import { CloudUpload, CheckCircle, Error } from '@mui/icons-material';
import { transactionService } from '../services/api';
import { motion } from 'framer-motion';

export const FileUpload = ({ onUploadSuccess }) => {
	const [loading, setLoading] = useState(false);
	const [status, setStatus] = useState(null); // { type: 'success'|'error', text }

	const handleFileChange = async (e) => {
		const file = e.target.files[0];
		if (!file) return;

		setLoading(true);
		setStatus(null);

		try {
			const result = await transactionService.upload(file);
			// Предполагаем успех, если запрос выполнен без ошибок
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

	return (
		<Paper sx={{ p: 3 }}>
			<Typography variant="h6" gutterBottom>
				Импорт данных
			</Typography>

			<Button
				component="label"
				variant="outlined"
				startIcon={<CloudUpload />}
				disabled={loading}
				fullWidth
				sx={{ height: 100, borderStyle: 'dashed' }}
			>
				{loading ? <CircularProgress size={24} /> : 'Нажмите для выбора CSV/PDF'}
				<input type="file" hidden accept=".csv,.pdf" onChange={handleFileChange} />
			</Button>
			<Typography variant="caption" color="text.secondary" align="center" display="block" sx={{ mt: 1 }}>
				Сбер, Тинькофф, Альфа
			</Typography>

			{status && (
				<motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
					<Alert severity={status.type} icon={status.type === 'success' ? <CheckCircle /> : <Error />} sx={{ mt: 2 }}>
						{status.text}
					</Alert>
				</motion.div>
			)}
		</Paper>
	);
};