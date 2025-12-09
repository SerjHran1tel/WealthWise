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
    <div className="mb-8">
      <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
        <Zap size={20} className="text-yellow-500 fill-current" />
        AI Аналитика и Прогнозы
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {insights.map((insight) => (
          <div
            key={insight.id}
            className={`p-4 rounded-2xl border ${getStyle(insight.type)} transition-all hover:shadow-md`}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex-shrink-0">
                {getIcon(insight.type)}
              </div>
              <div>
                <h3 className="font-semibold text-sm">{insight.title}</h3>
                <p className="text-sm opacity-90 mt-1 leading-relaxed">{insight.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};