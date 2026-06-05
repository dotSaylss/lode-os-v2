<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';
	import Icon from '$lib/components/Icon.svelte';
	import LodeOrb from '$lib/components/LodeOrb.svelte';

	let { children } = $props();

	const nav = [
		{ href: '/', label: 'Today', icon: 'sun', match: (p: string) => p === '/' },
		{ href: '/label', label: 'Catalog', icon: 'audio-lines', match: (p: string) => p.startsWith('/label') },
		{ href: '/services', label: 'Services', icon: 'waypoints', match: (p: string) => p.startsWith('/services') }
	];
</script>

<div class="appv3">
	<aside class="v3-rail">
		<div class="v3-rail-panel">
			<div class="v3-rail-brand">
				<img src="/logo-mark.svg" alt="" width="30" height="30" />
				<span class="v3-rail-word">Lode<i>OS</i></span>
			</div>

			<nav class="v3-rail-nav">
				{#each nav as item}
					<a href={item.href} class="v3-rail-item {item.match(page.url.pathname) ? 'active' : ''}">
						<span class="v3-rail-ico"><Icon name={item.icon} size={20} /></span>
						<span class="v3-rail-label">{item.label}</span>
					</a>
				{/each}
			</nav>

			<div class="v3-rail-foot">
				<button class="v3-rail-item" type="button">
					<span class="v3-rail-ico"><Icon name="settings-2" size={20} /></span>
					<span class="v3-rail-label">Settings</span>
				</button>
				<button class="v3-rail-item" type="button">
					<span class="v3-rail-ico v3-rail-avatar">JF</span>
					<span class="v3-rail-label">June Freedom</span>
				</button>
			</div>
		</div>
	</aside>

	<main class="v3-main">
		{@render children()}
	</main>

	<LodeOrb />
</div>
