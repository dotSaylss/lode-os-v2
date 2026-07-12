<script lang="ts">
	/**
	 * Settings: only real, working controls. Workspace switching (backend
	 * persona scope), the sidebar preference, the live connection list, and
	 * device-local data (chat history, intro replay). No mock toggles.
	 */
	import { goto, invalidateAll } from '$app/navigation';
	import { api } from '$lib/api';
	import { railLocked, setRailLocked } from '$lib/lodeStore';
	import { clearAllThreads } from '$lib/chatStore';
	import Icon from '$lib/components/Icon.svelte';

	let { data } = $props();

	type Persona = { id: string; name: string; role: string; tagline: string; home: string };
	type Connector = {
		id: string;
		name: string;
		tagline: string;
		status: 'connected' | 'available';
		tone: string;
	};

	const personas = $derived<Persona[]>(data.personas ?? []);
	const connectors = $derived<Connector[]>(data.connectors ?? []);
	const connected = $derived(connectors.filter((c) => c.status === 'connected'));

	const AV_TONE: Record<string, string> = {
		sage: 'av-sage',
		terra: 'av-terra',
		slate: 'av-slate',
		amber: 'av-amber'
	};
	const avTone = (t: string) => AV_TONE[t] ?? 'av-slate';
	const initials = (name: string) =>
		name
			.split(/\s+/)
			.map((w) => w[0])
			.slice(0, 2)
			.join('')
			.toUpperCase();

	let switching = $state(false);

	async function switchPersona(p: Persona) {
		if (switching || p.id === data.activePersona) return;
		switching = true;
		try {
			const res = await fetch(api('/api/v1/persona'), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ id: p.id })
			});
			if (res.ok) await invalidateAll();
		} catch (e) {
			console.error('Failed to switch workspace', e);
		} finally {
			switching = false;
		}
	}

	// Clearing history is destructive, so the button asks twice (inline, no
	// modal) and resets itself if the second tap never comes.
	let confirmClear = $state(false);
	let cleared = $state(false);
	let confirmTimer: ReturnType<typeof setTimeout> | undefined;

	function clearHistory() {
		if (!confirmClear) {
			confirmClear = true;
			clearTimeout(confirmTimer);
			confirmTimer = setTimeout(() => (confirmClear = false), 3500);
			return;
		}
		clearTimeout(confirmTimer);
		clearAllThreads();
		confirmClear = false;
		cleared = true;
		setTimeout(() => (cleared = false), 2500);
	}

	function replayIntro() {
		try {
			localStorage.removeItem('lode_intro_seen');
		} catch {}
		goto('/?intro=1');
	}
</script>

<div class="v3-stage set">
	<header class="v3-header">
		<div>
			<span class="v3-date">Settings</span>
			<h1>Your workspace, your rules</h1>
		</div>
	</header>

	<!-- Workspace -->
	<section class="set-card">
		<div class="set-card-head">
			<span class="eyebrow">Workspace</span>
			<span class="set-hint">Scopes your data, connections, and what every agent sees</span>
		</div>
		<div class="set-rows">
			{#each personas as p (p.id)}
				<button
					class="set-row set-workspace {p.id === data.activePersona ? 'active' : ''}"
					type="button"
					disabled={switching}
					onclick={() => switchPersona(p)}
				>
					<span class="set-avatar">{initials(p.name)}</span>
					<span class="set-row-text">
						<b>{p.name}</b>
						<span>{p.role}</span>
					</span>
					{#if p.id === data.activePersona}
						<Icon name="check" size={16} color="var(--sg-600)" />
					{/if}
				</button>
			{/each}
		</div>
	</section>

	<!-- Sidebar -->
	<section class="set-card">
		<div class="set-card-head">
			<span class="eyebrow">Sidebar</span>
			<span class="set-hint">Takes effect immediately</span>
		</div>
		<div class="set-row plain">
			<span class="set-row-text">
				<b>Navigation rail</b>
				<span>Pinned keeps it open; auto-hide reveals it on hover</span>
			</span>
			<div class="set-seg">
				<button
					class="set-seg-btn {$railLocked ? 'active' : ''}"
					type="button"
					onclick={() => setRailLocked(true)}
				>
					Pinned open
				</button>
				<button
					class="set-seg-btn {!$railLocked ? 'active' : ''}"
					type="button"
					onclick={() => setRailLocked(false)}
				>
					Auto-hide
				</button>
			</div>
		</div>
	</section>

	<!-- Connections -->
	<section class="set-card">
		<div class="set-card-head">
			<span class="eyebrow">Connections</span>
			<a class="set-link" href="/connectors">All connectors <Icon name="arrow-right" size={13} /></a>
		</div>
		{#if connected.length}
			<div class="set-rows">
				{#each connected as c (c.id)}
					<a class="set-row set-conn" href="/connectors/{c.id}">
						<span class="set-dot" title="Connected"></span>
						<span class="set-logo {avTone(c.tone)}">{c.name.slice(0, 1)}</span>
						<span class="set-row-text">
							<b>{c.name}</b>
							<span>{c.tagline}</span>
						</span>
						<span class="set-perm-link">Permissions <Icon name="chevron-right" size={14} /></span>
					</a>
				{/each}
			</div>
		{:else}
			<p class="set-empty">Nothing connected yet. Add platforms from the Connectors page.</p>
		{/if}
	</section>

	<!-- Data -->
	<section class="set-card">
		<div class="set-card-head">
			<span class="eyebrow">Data</span>
			<span class="set-hint">Chats are stored on this device only</span>
		</div>
		<div class="set-rows">
			<div class="set-row plain">
				<span class="set-row-text">
					<b>Chat history</b>
					<span>Removes every conversation across all workspaces</span>
				</span>
				{#if cleared}
					<span class="set-done"><Icon name="check" size={14} color="var(--sg-600)" /> Cleared</span>
				{:else}
					<button
						class="set-action {confirmClear ? 'danger' : ''}"
						type="button"
						onclick={clearHistory}
					>
						<Icon name="trash-2" size={14} />
						{confirmClear ? 'Tap again to confirm' : 'Clear'}
					</button>
				{/if}
			</div>
			<div class="set-row plain">
				<span class="set-row-text">
					<b>Guided intro</b>
					<span>Replay the first-run walkthrough for this workspace</span>
				</span>
				<button class="set-action" type="button" onclick={replayIntro}>
					<Icon name="rotate-ccw" size={14} /> Replay
				</button>
			</div>
		</div>
	</section>
</div>

<style>
	.set > * + * {
		margin-top: 18px;
	}
	.set-card {
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-sm);
		padding: 24px 26px;
	}
	.set-card-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
		margin-bottom: 14px;
	}
	.set-hint {
		font-size: 12px;
		color: var(--ink-muted);
	}
	.set-link {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--sg-600);
		text-decoration: none;
		transition: color 0.14s;
	}
	.set-link:hover {
		color: var(--sg-700);
	}
	.set-rows {
		display: flex;
		flex-direction: column;
	}
	.set-row {
		display: flex;
		align-items: center;
		gap: 13px;
		width: 100%;
		padding: 12px 10px;
		margin: 0 -10px;
		border: none;
		border-radius: var(--r-md);
		background: transparent;
		text-align: left;
		text-decoration: none;
		transition: background 0.14s;
	}
	.set-row + .set-row {
		border-top: 1px solid var(--paper-100);
		border-radius: 0 0 var(--r-md) var(--r-md);
	}
	.set-workspace,
	.set-conn {
		cursor: pointer;
	}
	.set-workspace:hover,
	.set-conn:hover {
		background: var(--paper-50);
	}
	.set-workspace.active {
		background: var(--sg-50);
	}
	.set-workspace:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.set-row.plain {
		flex-wrap: wrap;
		row-gap: 10px;
	}
	.set-row-text {
		flex: 1;
		min-width: 180px;
	}
	.set-row-text b {
		display: block;
		font-size: 14px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.set-row-text span {
		display: block;
		font-size: 12.5px;
		color: var(--ink-500);
		margin-top: 1px;
	}
	.set-avatar {
		flex: none;
		width: 34px;
		height: 34px;
		border-radius: 50%;
		background: var(--sg-300);
		color: var(--sg-700);
		font-size: 12px;
		font-weight: 700;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.set-dot {
		flex: none;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--sg-500);
		box-shadow: 0 0 0 3px var(--sg-50);
	}
	.set-logo {
		flex: none;
		width: 34px;
		height: 34px;
		border-radius: var(--r-sm);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
		font-weight: 700;
	}
	.av-sage { background: var(--sg-100); color: var(--sg-700); }
	.av-terra { background: var(--terra-100); color: var(--terra-600); }
	.av-slate { background: var(--slate-100); color: var(--slate-600); }
	.av-amber { background: var(--amber-50); color: var(--amber-600); }
	.set-perm-link {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		flex: none;
		font-size: 12px;
		font-weight: 600;
		color: var(--ink-muted);
		transition: color 0.14s;
	}
	.set-conn:hover .set-perm-link {
		color: var(--sg-600);
	}

	/* Segmented control, modeled on the connector permission segments */
	.set-seg {
		display: flex;
		gap: 4px;
		background: var(--paper-100);
		border-radius: var(--r-md);
		padding: 4px;
		flex: none;
	}
	.set-seg-btn {
		font-size: 12.5px;
		font-weight: 600;
		padding: 7px 13px;
		border: none;
		border-radius: var(--r-sm);
		background: transparent;
		color: var(--ink-500);
		cursor: pointer;
		transition: all 0.14s;
	}
	.set-seg-btn.active {
		background: var(--paper-0);
		color: var(--sg-700);
		box-shadow: var(--v3-sh-xs);
	}

	.set-action {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		flex: none;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--ink-500);
		background: transparent;
		border: 1px solid var(--paper-200);
		border-radius: var(--r-md);
		padding: 8px 14px;
		cursor: pointer;
		transition: all 0.14s;
	}
	.set-action:hover {
		border-color: var(--sg-200);
		color: var(--ink-900);
	}
	.set-action.danger {
		color: var(--terra-600);
		border-color: var(--terra-200);
		background: var(--terra-50);
	}
	.set-done {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--sg-700);
	}
	.set-empty {
		margin: 0;
		padding: 18px;
		text-align: center;
		border: 1px dashed var(--paper-300);
		border-radius: var(--r-lg);
		font-size: 13.5px;
		color: var(--ink-muted);
	}

	@media (max-width: 640px) {
		.set-card {
			padding: 20px 18px;
		}
		/* Rows wrap and the text block drops its 180px floor so long persona /
		   account names never force horizontal overflow on a phone. */
		.set-row {
			flex-wrap: wrap;
			row-gap: 8px;
		}
		.set-row-text {
			min-width: 0;
		}
		.set-perm-link {
			margin-left: 47px;
		}
	}
</style>
