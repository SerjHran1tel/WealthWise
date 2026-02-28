import { createTheme } from '@mui/material/styles';

const theme = createTheme({
	palette: {
		primary: {
			main: '#3B82F6', // blue-500
		},
		secondary: {
			main: '#6366f1', // indigo-500
		},
		error: {
			main: '#ef4444', // red-500
		},
		warning: {
			main: '#f59e0b', // amber-500
		},
		info: {
			main: '#3b82f6', // blue-500
		},
		success: {
			main: '#10b981', // emerald-500
		},
		background: {
			default: '#f8fafc',
			paper: '#ffffff',
		},
	},
	typography: {
		fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
		h1: { fontWeight: 700 },
		h2: { fontWeight: 600 },
		h3: { fontWeight: 600 },
		h4: { fontWeight: 600 },
		h5: { fontWeight: 600 },
		h6: { fontWeight: 600 },
		subtitle1: { fontWeight: 500 },
		body1: { fontWeight: 400 },
		button: { textTransform: 'none' },
	},
	shape: {
		borderRadius: 12,
	},
	components: {
		MuiButton: {
			styleOverrides: {
				root: {
					borderRadius: 9999, // full rounded
					padding: '8px 20px',
				},
			},
		},
		MuiPaper: {
			styleOverrides: {
				root: {
					backgroundImage: 'none',
					boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
				},
			},
		},
	},
});

export default theme;