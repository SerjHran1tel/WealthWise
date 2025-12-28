import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
	plugins: [react(), tailwindcss()],
	server: {
		open: true, // Автоматически открывать браузер
		watch: {
			usePolling: true, // Это полезно для некоторых файловых систем
		},
	},
})
