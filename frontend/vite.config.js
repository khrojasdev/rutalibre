import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En dev, /api se proxya al backend local. En producción, el frontend usa
// VITE_API_URL (la URL de Render) definida como variable de entorno.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})
