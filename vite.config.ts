import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

import { viteStaticCopy } from 'vite-plugin-static-copy';

const DEV_BACKEND_URL = process.env.VITE_DEV_BACKEND_URL || 'http://localhost:9000';
const DEV_PROXY_PATHS = ['/api', '/ollama', '/openai', '/health', '/oauth', '/ws'];

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/onnxruntime-web/dist/*.jsep.*',

					dest: 'wasm'
				}
			]
		})
	],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
	},
	build: {
		sourcemap: true
	},
	server: {
		proxy: Object.fromEntries(
			DEV_PROXY_PATHS.map((path) => [
				path,
				{
					target: DEV_BACKEND_URL,
					changeOrigin: true,
					ws: true
				}
			])
		),
		watch: {
			ignored: ['**/venv/**', '**/.venv/**', '**/backend/**']
		}
	},
	worker: {
		format: 'es'
	},
	esbuild: {
		pure: process.env.ENV === 'dev' ? [] : ['console.log', 'console.debug', 'console.error']
	}
});
