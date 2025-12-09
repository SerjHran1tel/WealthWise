import React from 'react';
import { AlertTriangle, TrendingUp, Info, Zap } from 'lucide-react';

export const InsightsPanel = ({ insights }) => {
  if (!insights || insights.length === 0) return null;

  const getIcon = (type) => {
    switch (type) {
      case 'anomaly': return <AlertTriangle className="text-danger" size={20} />;
      case 'warning': return <TrendingUp className="text-orange-500" size={20} />;
      case 'recommendation': return <Zap className="text-yellow-500" size={20} />;
      default: return <Info className="text-primary" size={20} />;
    }
  };

  const getBgColor = (type) => {
    switch (type) {
      case 'anomaly': return 'bg-red-50 border-red-100';
      case 'warning': return 'bg-orange-50 border-orange-100';
      case 'recommendation': return 'bg-yellow-50 border-yellow-100';
      default: return 'bg-blue-50 border-blue-100';
    }
  };

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Zap size={20} className="text-yellow-500 fill-current" />
        AI Инсайты
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {insights.map((insight) => (
          <div
            key={insight.id}
            className={`p-4 rounded-lg border ${getBgColor(insight.type)} transition hover:shadow-sm`}
          >
            <div className="flex items-start gap-3">
              <div className="mt-1 flex-shrink-0">
                {getIcon(insight.type)}
              </div>
              <div>
                <h3 className="font-semibold text-gray-800 text-sm">{insight.title}</h3>
                <p className="text-gray-600 text-sm mt-1">{insight.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};