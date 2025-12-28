import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, AlertCircle, Target, Loader2 } from 'lucide-react';

export const WeeklyReport = () => {
	const [report, setReport] = useState(null);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		fetchReport();
	}, []);

	const fetchReport = async () => {
		try {
			const res = await fetch('http://localhost:8000/api/reports/weekly');
			const data = await res.json();
			setReport(data);
		} catch (error) {
			console.error('Failed to load report:', error);
		} finally {
			setLoading(false);
		}
	};

	if (loading) return (
		<div className="report-loading">
			<Loader2 size={32} className="animate-spin" />
			<span>Формируем ваш отчёт...</span>
		</div>
	);

	if (!report) return null;

	return (
		<div className="weekly-report">
			<header className="weekly-report__header">
				<div className="weekly-report__title-box">
					<div className="weekly-report__icon-main">
						<Calendar size={24} />
					</div>
					<div>
						<h2 className="weekly-report__title">Еженедельный отчёт</h2>
						<span className="weekly-report__period">{report.period}</span>
					</div>
				</div>
			</header>

			{/* Краткая статистика */}
			<div className="weekly-report__stats-grid">
				<div className="report-stat report-stat--expense">
					<p className="report-stat__label">Расходы</p>
					<p className="report-stat__value">{report.stats.expenses.toLocaleString()} ₽</p>
				</div>
				<div className="report-stat report-stat--income">
					<p className="report-stat__label">Доходы</p>
					<p className="report-stat__value">{report.stats.income.toLocaleString()} ₽</p>
				</div>
				<div className="report-stat report-stat--balance">
					<p className="report-stat__label">Баланс</p>
					<p className="report-stat__value">{report.stats.balance.toLocaleString()} ₽</p>
				</div>
			</div>

			{/* Сравнение */}
			<div className="weekly-report__comparison">
				<div className="weekly-report__section-header">
					<TrendingUp size={18} />
					<span className="weekly-report__section-title">Динамика к прошлой неделе</span>
				</div>
				<div className={`weekly-report__change-value ${report.comparison.change_percent > 0 ? 'weekly-report__change-value--negative' : 'weekly-report__change-value--positive'
					}`}>
					{report.comparison.change_percent > 0 ? 'Увеличение трат на' : 'Снижение трат на'}
					<strong> {Math.abs(report.comparison.change_percent)}%</strong>
				</div>
			</div>

			{/* Проблемы (Issues) */}
			{report.issues.length > 0 && (
				<div className="weekly-report__section weekly-report__section--issues">
					<div className="weekly-report__section-header">
						<AlertCircle size={18} />
						<span className="weekly-report__section-title">Требует внимания</span>
					</div>
					<div className="weekly-report__list">
						{report.issues.map((issue, idx) => (
							<div key={idx} className="weekly-report__issue-item">
								{issue}
							</div>
						))}
					</div>
				</div>
			)}

			{/* Рекомендации AI */}
			<div className="weekly-report__section weekly-report__section--recommendations">
				<div className="weekly-report__section-header">
					<Target size={18} />
					<span className="weekly-report__section-title">AI Рекомендации</span>
				</div>
				<div className="weekly-report__list">
					{report.recommendations.map((rec, idx) => (
						<div key={idx} className="weekly-report__rec-item">
							<span className="weekly-report__rec-bullet">•</span>
							{rec}
						</div>
					))}
				</div>
			</div>
		</div>
	);
};