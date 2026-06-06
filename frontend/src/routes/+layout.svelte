<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import Icon from '$lib/components/Icon.svelte';
	import LodeOrb from '$lib/components/LodeOrb.svelte';
	import Onboarding from '$lib/components/Onboarding.svelte';

	let { children } = $props();

	// Show the guided intro on first visit, or any time ?intro=1 is present
	// (handy for demos). Dismissal is remembered in localStorage.
	let showIntro = $state(false);

	// Rail lock: when locked the rail stays expanded and the main content is
	// pushed over so nothing is covered. When unlocked it auto-reveals on hover.
	let railLocked = $state(false);

	onMount(() => {
		const forced = page.url.searchParams.get('intro') === '1';
		const seen = localStorage.getItem('lode_intro_seen') === '1';
		showIntro = forced || !seen;
		railLocked = localStorage.getItem('lode_rail_locked') === '1';
	});

	function dismissIntro() {
		showIntro = false;
		try {
			localStorage.setItem('lode_intro_seen', '1');
		} catch {}
	}

	function toggleRailLock() {
		railLocked = !railLocked;
		try {
			localStorage.setItem('lode_rail_locked', railLocked ? '1' : '0');
		} catch {}
	}

	const nav = [
		{ href: '/', label: 'Today', icon: 'sun', match: (p: string) => p === '/' },
		{ href: '/label', label: 'Catalog', icon: 'audio-lines', match: (p: string) => p.startsWith('/label') },
		{ href: '/services', label: 'Services', icon: 'handshake', match: (p: string) => p.startsWith('/services') }
	];
</script>

<div class="appv3" class:rail-locked={railLocked}>
	<aside class="v3-rail">
		<div class="v3-rail-panel">
			<div class="v3-rail-brand">
				<img src="/logo-mark.svg" alt="" width="30" height="30" />
				<span class="v3-rail-word">Lode<i>OS</i></span>
				<button
					class="v3-rail-lock"
					type="button"
					onclick={toggleRailLock}
					title={railLocked ? 'Unlock sidebar (auto-hide)' : 'Lock sidebar open'}
					aria-label={railLocked ? 'Unlock sidebar' : 'Lock sidebar open'}
				>
					<Icon name={railLocked ? 'panel-left-close' : 'panel-left-open'} size={17} color="var(--ink-500)" />
				</button>
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

{#if showIntro}
	<Onboarding onEnter={dismissIntro} />
{/if}
