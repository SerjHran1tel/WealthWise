import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, XCircle } from 'lucide-react';
import { transactionService } from '../services/api';
import { motion } from 'framer-motion';

export const FileUpload = ({ onUploadSuccess }) => {
	const [loading, setLoading] = useState(false);
	const [status, setStatus] = useState(null); // success | error

	const handleFileChange = async (e) => {
		const file = e.target.files[0];
		if (!file) return;

		setLoading(true);
		setStatus(null);

		try {
			const result = await transactionService.upload(file);
			if (result.status === 'success') {
				setStatus({ type: 'success', text: `+${result.imported_count} записей` });
				onUploadSuccess();
			} else {
				setStatus({ type: 'error', text: 'Ошибка формата' });
			}
		} catch {
			setStatus({ type: 'error', text: 'Сбой загрузки' });
		} finally {
			setLoading(false);
			e.target.value = null;
		}
	};

	return (
		<div className="file-upload">
			<h3 className="file-upload__title">Импорт операций</h3>

			<label className={`file-upload__dropzone ${loading ? 'file-upload__dropzone--loading' : ''}`}>
				<div className="file-upload__content">
					{loading ? (
						<div className="file-upload__loader">
							<Loader2 size={32} className="animate-spin" />
						</div>
					) : (
						<div className="file-upload__icon">
							<UploadCloud size={32} />
						</div>
					)}

					<p className="file-upload__text">
						{loading ? 'Анализируем файл...' : 'Выберите CSV или PDF'}
					</p>
					<p className="file-upload__hint">Сбербанк, Тинькофф, Альфа-Банк</p>
				</div>
				<input
					type="file"
					className="file-upload__input"
					accept=".csv,.pdf"
					onChange={handleFileChange}
					disabled={loading}
				/>
			</label>

			{status && (
				<motion.div
					initial={{ opacity: 0, y: 10 }}
					animate={{ opacity: 1, y: 0 }}
					className={`file-upload__status file-upload__status--${status.type}`}
				>
					{status.type === 'success' ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
					<span>{status.text}</span>
				</motion.div>
			)}
		</div>
	);
};