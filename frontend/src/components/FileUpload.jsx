import React, { useState } from 'react';
import { Upload, Check, AlertCircle } from 'lucide-react';
import { transactionService } from '../services/api';

export const FileUpload = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await transactionService.upload(file);
      setMessage({ type: 'success', text: `Импортировано: ${result.imported_count}` });
      if (onUploadSuccess) onUploadSuccess();
    } catch (error) {
      console.error(error);
      setMessage({ type: 'error', text: 'Ошибка загрузки. Проверьте формат CSV.' });
    } finally {
      setLoading(false);
      // Очистка инпута, чтобы можно было загрузить тот же файл снова
      e.target.value = null;
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm mb-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800 flex items-center gap-2">
        <Upload size={20} /> Загрузка выписки
      </h3>

      <div className="flex items-center gap-4">
        <label className="cursor-pointer bg-primary text-white px-4 py-2 rounded hover:bg-blue-600 transition flex items-center gap-2">
           {loading ? 'Загрузка...' : 'Выбрать файл (CSV)'}
           <input
             type="file"
             accept=".csv"
             onChange={handleFileChange}
             disabled={loading}
             className="hidden"
           />
        </label>

        {message && (
          <div className={`flex items-center gap-2 text-sm ${message.type === 'success' ? 'text-success' : 'text-danger'}`}>
            {message.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
            {message.text}
          </div>
        )}
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Поддерживается формат: Дата; Описание; Сумма (разделитель ; или ,)
      </p>
    </div>
  );
};