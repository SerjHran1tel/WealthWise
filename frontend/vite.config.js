import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
	plugins: [react()],
	server: {
		open: true, // Автоматически открывать браузер
		watch: {
			usePolling: true, // Это полезно для некоторых файловых систем
		},
	},
})
