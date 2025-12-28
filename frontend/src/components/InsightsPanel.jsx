import React from 'react';
import { AlertTriangle, TrendingUp, Info, Zap, CalendarClock } from 'lucide-react';

export const InsightsPanel = ({ insights }) => {
	if (!insights || insights.length === 0) return null;

	const getIcon = (type) => {
		switch (type) {
			case 'anomaly': return <AlertTriangle className="text-rose-500" size={20} />;
			case 'warning': return <TrendingUp className="text-orange-500" size={20} />;
			case 'recommendation': return <Zap className="text-yellow-500" size={20} />;
			case 'prediction': return <CalendarClock className="text-purple-500" size={20} />; // <-- Иконка прогноза
			default: return <Info className="text-blue-500" size={20} />;
		}
	};

	const getStyle = (type) => {
		switch (type) {
			case 'anomaly': return 'bg-rose-50 border-rose-100 text-rose-900';
			case 'warning': return 'bg-orange-50 border-orange-100 text-orange-900';
			case 'recommendation': return 'bg-yellow-50 border-yellow-100 text-yellow-900';
			case 'prediction': return 'bg-purple-50 border-purple-100 text-purple-900'; // <-- Стиль прогноза
			default: return 'bg-blue-50 border-blue-100 text-blue-900';
		}
	};

	return (
		<section className="insights-panel">
			<h2 className="insights-panel__title">
				<Zap size={22} className="insights-panel__title-icon" />
				<span>AI Аналитика и Прогнозы</span>
			</h2>

			<div className="insights-panel__grid">
				{insights.map((insight) => (
					<div
						key={insight.id}
						className={`insight-card insight-card--${insight.type || 'info'}`}
					>
						<div className="insight-card__icon-container">
							{getIcon(insight.type)}
						</div>
						<div className="insight-card__content">
							<h3 className="insight-card__title">{insight.title}</h3>
							<p className="insight-card__description">{insight.description}</p>
						</div>
					</div>
				))}
			</div>
		</section>
	);
};