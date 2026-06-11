import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	// Allow the dev server to be reached through the tailnet proxy
	// (tailscale serve → mr.tail72c721.ts.net) for mobile review. Bind IPv4
	// loopback explicitly — node would otherwise take ::1 only, which the
	// proxy's 127.0.0.1 target can't reach.
	server: { host: '127.0.0.1', allowedHosts: ['.ts.net', 'mr'] }
});
