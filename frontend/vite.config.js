import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { VantResolver } from '@vant/auto-import-resolver'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [
        VantResolver(),
        IconsResolver({ prefix: 'Icon' })
      ]
    }),
    Components({
      resolvers: [
        VantResolver(),
        IconsResolver({ enabledCollections: ['tabler'] })
      ]
    }),
    Icons({
      autoInstall: true,
      compiler: 'vue3'
    })
  ],
  build: {
    outDir: process.env.DOCKER_BUILD ? 'dist' : '../backend/static',
    emptyOutDir: true
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  }
})
