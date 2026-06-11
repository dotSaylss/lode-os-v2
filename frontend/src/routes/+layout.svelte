<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { page } from '$app/state';
	import { goto, invalidateAll } from '$app/navigation';
	import { api } from '$lib/api';
	import { activeThreadId, threads, initChats, recentFor, type ChatThread } from '$lib/chatStore';
	import { railLocked, initRailLock, setRailLocked } from '$lib/lodeStore';
	import Icon from '$lib/components/Icon.svelte';
	import LodeOrb from '$lib/components/LodeOrb.svelte';
	import Onboarding from '$lib/components/Onboarding.svelte';

	let { children, data } = $props();

	type Persona = { id: string; name: string; role: string; tagline: string; home: string };
	const personas = $derived<Persona[]>(data.personas ?? []);
	const active = $derived<Persona | undefined>(
		personas.find((p) => p.id === data.activePersona)
	);
	const initials = (name: string) =>
		name
			.split(/\s+/)
			.map((w) => w[0])
			.slice(0, 2)
			.join('')
			.toUpperCase();

	// ── Workspace switcher ────────────────────────────────────────────────────
	// One product, three demo users (artist / label / creator). Switching tells
	// the backend — which scopes data, connectors, and the agents — then lands
	// on that workspace's home view.
	let switcherOpen = $state(false);
	let switching = $state(false);

	async function switchPersona(p: Persona) {
		if (switching || p.id === data.activePersona) {
			switcherOpen = false;
			return;
		}
		switching = true;
		try {
			const res = await fetch(api('/api/v1/persona'), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ id: p.id })
			});
			if (res.ok) {
				switcherOpen = false;
				await goto(p.home);
				await invalidateAll();
			}
		} catch (e) {
			console.error('Failed to switch workspace', e);
		} finally {
			switching = false;
		}
	}

	// Show the guided intro on first visit, or any time ?intro=1 is present
	// (handy for demos, and how Settings → Replay works). Dismissal is
	// remembered in localStorage; the session flag stops the URL param from
	// re-opening the intro the instant it is dismissed.
	let showIntro = $state(false);
	let introDismissed = $state(false);

	onMount(() => {
		const seen = localStorage.getItem('lode_intro_seen') === '1';
		if (!seen) showIntro = true;
		initRailLock();
		initChats();
	});

	$effect(() => {
		if (page.url.searchParams.get('intro') === '1') {
			if (!introDismissed) showIntro = true;
		} else {
			// The param is gone (dismissIntro strips it), so re-arm: the next
			// ?intro=1 (e.g. Settings → Replay) must open the intro again.
			introDismissed = false;
		}
	});

	function dismissIntro() {
		showIntro = false;
		introDismissed = true;
		try {
			localStorage.setItem('lode_intro_seen', '1');
		} catch {}
		if (page.url.searchParams.has('intro')) goto('/', { replaceState: true });
	}

	// Rail lock: when locked the rail stays expanded and the main content is
	// pushed over so nothing is covered. When unlocked it auto-reveals on hover.
	// The preference lives in lodeStore so Settings can drive it too.
	function toggleRailLock() {
		setRailLocked(!$railLocked);
	}

	// Chat is the focal surface for every workspace; the rest are the deeper
	// detail views. Artists/creators get Today + Services; the label gets
	// Catalog. Connectors are everyone's control plane.
	const NAV = [
		{ href: '/today', label: 'Today', icon: 'sun', match: (p: string) => p.startsWith('/today'), for: ['june', 'kai'] },
		{ href: '/label', label: 'Catalog', icon: 'audio-lines', match: (p: string) => p.startsWith('/label'), for: ['label'] },
		{ href: '/connectors', label: 'Connectors', icon: 'plug', match: (p: string) => p.startsWith('/connectors'), for: ['june', 'label', 'kai'] },
		{ href: '/services', label: 'Services', icon: 'handshake', match: (p: string) => p.startsWith('/services'), for: ['june', 'kai'] }
	];
	const nav = $derived(NAV.filter((item) => item.for.includes(data.activePersona ?? 'june')));

	// Recent conversations for this workspace, shown when the rail is expanded.
	const railRecents = $derived(recentFor($threads, data.activePersona ?? 'june', 4));

	// "New chat" clears the active thread and lands on the chat home; a fresh
	// thread is created on the first send. (The chat page watches the store, so
	// no navigation is needed when already there.)
	function newChat() {
		activeThreadId.set(null);
		if (page.url.pathname !== '/') goto('/');
	}

	function openRecent(t: ChatThread) {
		activeThreadId.set(t.id);
		if (page.url.pathname !== '/') goto('/');
	}
</script>

<div class="appv3" class:rail-locked={$railLocked}>
	<aside class="v3-rail">
		<div class="v3-rail-panel">
			<div class="v3-rail-brand">
				<img src="/logo-mark.svg" alt="" width="30" height="30" />
				<span class="v3-rail-word">Lode<i>OS</i></span>
				<button
					class="v3-rail-lock"
					type="button"
					onclick={toggleRailLock}
					title={$railLocked ? 'Unlock sidebar (auto-hide)' : 'Lock sidebar open'}
					aria-label={$railLocked ? 'Unlock sidebar' : 'Lock sidebar open'}
				>
					<Icon name={$railLocked ? 'panel-left-close' : 'panel-left-open'} size={17} color="var(--ink-500)" />
				</button>
			</div>

			<nav class="v3-rail-nav">
				<a href="/" class="v3-rail-item {page.url.pathname === '/' ? 'active' : ''}">
					<span class="v3-rail-ico"><Icon name="message-circle" size={20} /></span>
					<span class="v3-rail-label">Chat</span>
				</a>
				<button class="v3-rail-item" type="button" onclick={newChat}>
					<span class="v3-rail-ico"><Icon name="pencil-line" size={20} /></span>
					<span class="v3-rail-label">New chat</span>
				</button>
				<span class="v3-rail-sep" aria-hidden="true"></span>
				{#each nav as item}
					<a href={item.href} class="v3-rail-item {item.match(page.url.pathname) ? 'active' : ''}">
						<span class="v3-rail-ico"><Icon name={item.icon} size={20} /></span>
						<span class="v3-rail-label">{item.label}</span>
					</a>
				{/each}
				{#if railRecents.length}
					<div class="v3-rail-recents">
						<span class="v3-rail-recents-head">Recent</span>
						{#each railRecents as t (t.id)}
							<button
								class="v3-rail-item v3-rail-recent"
								type="button"
								title={t.title}
								onclick={() => openRecent(t)}
							>
								<span class="v3-rail-label">{t.title}</span>
							</button>
						{/each}
					</div>
				{/if}
			</nav>

			<div class="v3-rail-foot">
				<a
					href="/settings"
					class="v3-rail-item {page.url.pathname.startsWith('/settings') ? 'active' : ''}"
				>
					<span class="v3-rail-ico"><Icon name="settings-2" size={20} /></span>
					<span class="v3-rail-label">Settings</span>
				</a>
				<div class="v3-switcher">
					{#if switcherOpen}
						<div class="v3-switcher-pop" transition:fade={{ duration: 120 }}>
							<span class="v3-switcher-head">Workspaces</span>
							{#each personas as p (p.id)}
								<button
									class="v3-switcher-row {p.id === data.activePersona ? 'active' : ''}"
									type="button"
									disabled={switching}
									onclick={() => switchPersona(p)}
								>
									<span class="v3-rail-avatar sm">{initials(p.name)}</span>
									<span class="v3-switcher-text">
										<b>{p.name}</b>
										<span>{p.role}</span>
									</span>
									{#if p.id === data.activePersona}
										<Icon name="check" size={14} color="var(--sg-600)" />
									{/if}
								</button>
							{/each}
						</div>
					{/if}
					<button
						class="v3-rail-item"
						type="button"
						aria-expanded={switcherOpen}
						title="Switch workspace"
						onclick={() => (switcherOpen = !switcherOpen)}
					>
						<span class="v3-rail-ico v3-rail-avatar">{initials(active?.name ?? 'June Freedom')}</span>
						<span class="v3-rail-label">{active?.name ?? 'June Freedom'}</span>
					</button>
				</div>
			</div>
		</div>
	</aside>

	<main class="v3-main">
		{@render children()}
	</main>

	<!-- On the chat home the conversation IS Lode; the floating orb only
	     accompanies the deeper workspace views. -->
	{#if page.url.pathname !== '/'}
		<LodeOrb />
	{/if}
</div>

{#if showIntro}
	<Onboarding
		persona={data.activePersona ?? 'june'}
		personaName={active?.name ?? ''}
		onEnter={dismissIntro}
	/>
{/if}
