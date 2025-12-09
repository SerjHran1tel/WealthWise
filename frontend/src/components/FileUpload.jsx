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
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Импорт данных</h3>

      <label className={`
        relative flex flex-col items-center justify-center w-full h-32
        border-2 border-dashed rounded-xl cursor-pointer transition-all duration-300
        ${loading ? 'bg-slate-50 border-slate-300' : 'border-blue-200 bg-slate-50 hover:bg-blue-50 hover:border-blue-400'}
      `}>
        <div className="flex flex-col items-center justify-center pt-5 pb-6 text-center">
          {loading ? (
             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
          ) : (
             <UploadCloud className="w-8 h-8 text-blue-500 mb-2" />
          )}
          <p className="text-sm text-slate-600 font-medium">
            {loading ? 'Обработка...' : 'Нажмите для выбора CSV/PDF'}
          </p>
          <p className="text-xs text-slate-400 mt-1">Сбер, Тинькофф, Альфа</p>
        </div>
        <input type="file" className="hidden" accept=".csv,.pdf" onChange={handleFileChange} disabled={loading} />
      </label>

      {status && (
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className={`mt-3 flex items-center gap-2 text-sm p-3 rounded-lg font-medium
            ${status.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}
        >
          {status.type === 'success' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {status.text}
        </motion.div>
      )}
    </div>
  );
};