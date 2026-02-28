import React from 'react';
import {
	Paper,
	Typography,
	Box,
	Alert,
	AlertTitle,
} from '@mui/material';
import {
	Warning as WarningIcon,
	TrendingUp as TrendingUpIcon,
	Info as InfoIcon,
	Bolt as ZapIcon,
	CalendarToday as CalendarClockIcon,
} from '@mui/icons-material';

export const InsightsPanel = ({ insights }) => {
	if (!insights || insights.length === 0) return null;

	const getIcon = (type) => {
		switch (type) {
			case 'anomaly': return <WarningIcon color="error" />;
			case 'warning': return <TrendingUpIcon color="warning" />;
			case 'recommendation': return <ZapIcon color="warning" />;
			case 'prediction': return <CalendarClockIcon color="secondary" />;
			default: return <InfoIcon color="info" />;
		}
	};

	const getSeverity = (type) => {
		switch (type) {
			case 'anomaly': return 'error';
			case 'warning': return 'warning';
			case 'recommendation': return 'warning';
			case 'prediction': return 'info';
			default: return 'info';
		}
	};

	return (
		<Box sx={{ mb: 4 }}>
			<Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
				<ZapIcon color="warning" />
				AI Аналитика и Прогнозы
			</Typography>
			<Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
				{insights.map((insight) => (
					<Alert
						key={insight.id}
						severity={getSeverity(insight.type)}
						icon={getIcon(insight.type)}
						sx={{ borderRadius: 2 }}
					>
						<AlertTitle>{insight.title}</AlertTitle>
						<Typography variant="body2">{insight.description}</Typography>
					</Alert>
				))}
			</Box>
		</Box>
	);
};