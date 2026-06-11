<script lang="ts">
	import { tick } from 'svelte';
	import Icon from '$lib/components/Icon.svelte';
	import { api } from '$lib/api';
	import { pendingAsk, clearPending } from '$lib/lodeStore';

	let { data } = $props();

	type CapSchema = { key: string; label: string; description: string };
	type CapConfig = { enabled: boolean; permission: 'allow' | 'approval' | 'deny' };
	type Connector = {
		id: string;
		name: string;
		category: string;
		tagline: string;
		description: string;
		status: string;
		account?: string;
		capabilities_schema: CapSchema[];
		agent_action?: { label: string; prompt: string };
		tone: string;
		highlight: boolean;
	};
	type Config = {
		enabled: boolean;
		connected?: boolean | null;
		account?: string;
		capabilities: Record<string, CapConfig>;
		settings: Record<string, unknown>;
	};

	const connector = $derived<Connector>(data.connector);
	// Local, editable copy of the config (autosaved to the backend on change).
	let config = $state<Config>(structuredClone(data.config));

	const AV_TONE: Record<string, string> = {
		sage: 'av-sage',
		terra: 'av-terra',
		slate: 'av-slate',
		amber: 'av-amber'
	};
	const avTone = (t: string) => AV_TONE[t] ?? 'av-slate';
	const initial = (name: string) => name.charAt(0).toUpperCase();

	const PERMISSIONS: { key: CapConfig['permission']; label: string; icon: string }[] = [
		{ key: 'allow', label: 'Allow', icon: 'circle-check' },
		{ key: 'approval', label: 'Needs approval', icon: 'shield-check' },
		{ key: 'deny', label: 'Deny', icon: 'search-x' }
	];

	// ── Autosave (debounced PUT) ──────────────────────────────────────────────
	let saveState = $state<'idle' | 'saving' | 'saved'>('idle');
	let saveTimer: ReturnType<typeof setTimeout> | undefined;
	// Guards against overlapping PUTs: only the most recent request may write
	// its response back into `config`, so a slow stale save can't revert edits.
	let saveSeq = 0;

	async function persist() {
		const seq = ++saveSeq;
		saveState = 'saving';
		try {
			const res = await fetch(api(`/api/v1/connectors/${connector.id}/config`), {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(config)
			});
			if (seq !== saveSeq) return; // a newer save is in flight or done
			if (res.ok) {
				config = await res.json();
				saveState = 'saved';
				setTimeout(() => (saveState = 'idle'), 1600);
			} else {
				saveState = 'idle';
			}
		} catch {
			if (seq === saveSeq) saveState = 'idle';
		}
	}

	function queueSave() {
		clearTimeout(saveTimer);
		saveState = 'saving';
		saveTimer = setTimeout(persist, 450);
	}

	function toggleCapability(key: string) {
		const cap = config.capabilities[key];
		if (!cap) return;
		config.capabilities[key] = { ...cap, enabled: !cap.enabled };
		queueSave();
	}

	function setPermission(key: string, permission: CapConfig['permission']) {
		const cap = config.capabilities[key];
		if (!cap) return;
		config.capabilities[key] = { ...cap, permission };
		queueSave();
	}

	const capConfig = (key: string): CapConfig =>
		config.capabilities[key] ?? { enabled: true, permission: 'allow' };

	// ── Agent action (real, config-respecting) ────────────────────────────────
	let running = $state(false);
	let result = $state<string>('');
	let trace = $state<{ label: string }[]>([]);
	// When the chat hands off here, the question being replayed is shown above
	// the result so the draft has its context.
	let replayedAsk = $state<string>('');
	let actionCard: HTMLElement | undefined = $state();

	async function runAction(message = '') {
		if (running) return;
		running = true;
		result = '';
		trace = [];
		try {
			const res = await fetch(api(`/api/v1/connectors/${connector.id}/action`), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message })
			});
			if (res.ok) {
				const data = await res.json();
				result = data.response ?? '';
				trace = data.trace ?? [];
			} else {
				result = 'I could not run that action just now. Please try again.';
			}
		} catch {
			result = 'I could not reach the agent. Is the backend running?';
		} finally {
			running = false;
		}
	}

	// Chat → page handoff: when "See this in {connector}" is clicked, the ask is
	// replayed through the connector's agent so the full work product (the
	// drafted pitch, the matched brief, the trace) renders here at full width.
	$effect(() => {
		const pending = $pendingAsk;
		if (pending && pending.page === `/connectors/${connector.id}`) {
			clearPending();
			replayedAsk = pending.prompt;
			void runAction(pending.prompt);
			tick().then(() =>
				actionCard?.scrollIntoView({ behavior: 'smooth', block: 'start' })
			);
		}
	});

	// Minimal, safe markdown → HTML for the agent result (bold, bullets, rules,
	// paragraphs). Escapes HTML first so agent text can never inject markup.
	function renderResult(md: string): string {
		const esc = md
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;');
		const lines = esc.split('\n');
		let html = '';
		let inList = false;
		const inline = (s: string) =>
			s
				.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
				.replace(/`(.+?)`/g, '<code>$1</code>');
		for (const raw of lines) {
			const line = raw.trim();
			if (!line) {
				if (inList) { html += '</ul>'; inList = false; }
				continue;
			}
			if (/^\*\*\*+$/.test(line) || /^---+$/.test(line)) {
				if (inList) { html += '</ul>'; inList = false; }
				html += '<hr/>';
				continue;
			}
			const bullet = line.match(/^[*-]\s+(.*)$/);
			if (bullet) {
				if (!inList) { html += '<ul>'; inList = true; }
				html += `<li>${inline(bullet[1])}</li>`;
				continue;
			}
			if (inList) { html += '</ul>'; inList = false; }
			html += `<p>${inline(line)}</p>`;
		}
		if (inList) html += '</ul>';
		return html;
	}

	function askLode() {
		const prompt = connector.agent_action?.prompt ?? `Tell me about my ${connector.name} connection.`;
		window.dispatchEvent(new CustomEvent('lode:open', { detail: { prompt } }));
	}

	const hasAgentAction = $derived(!!connector.agent_action);
</script>

<div class="v3-stage-wide cfg">
	<a class="cfg-back" href="/connectors">
		<Icon name="arrow-left" size={16} color="var(--ink-500)" /> Connectors
	</a>

	<header class="cfg-head">
		<span class="cfg-logo {avTone(connector.tone)}">{initial(connector.name)}</span>
		<div class="cfg-id">
			<div class="cfg-name-row">
				<h1>{connector.name}</h1>
				<span class="cfg-status" class:off={connector.status !== 'connected'}>
					<span class="cfg-dot"></span>
					{connector.status === 'connected' ? 'Connected' : 'Available'}
				</span>
			</div>
			<p>{connector.tagline}</p>
			<div class="cfg-head-meta">
				<span class="cfg-head-meta-item">
					<Icon name="users" size={13} color="var(--ink-muted)" />
					{config.account ?? connector.account ?? 'No account'}
				</span>
				<span class="cfg-head-meta-item">
					<Icon name="clock" size={13} color="var(--ink-muted)" />
					Sync: {(config.settings?.sync_frequency as string) ?? 'manual'}
				</span>
			</div>
		</div>
		<div class="cfg-save" class:show={saveState !== 'idle'}>
			{#if saveState === 'saving'}Saving…{:else if saveState === 'saved'}<Icon name="check" size={14} color="var(--sg-600)" /> Saved{/if}
		</div>
	</header>

	<!-- What this connection does: the lead, not a buried card row. -->
	<p class="cfg-lead">{connector.description}</p>

	<!-- Capabilities + Permissions -->
	{#if connector.capabilities_schema.length}
		<section class="cfg-card">
			<div class="cfg-card-head">
				<span class="eyebrow">Capabilities &amp; permissions</span>
				<span class="cfg-hint">What Lode may do, and when it must ask you first</span>
			</div>

			<div class="cfg-caps">
				{#each connector.capabilities_schema as cap (cap.key)}
					{@const cc = capConfig(cap.key)}
					<div class="cfg-cap" class:off={!cc.enabled}>
						<div class="cfg-cap-main">
							<button
								class="cfg-switch {cc.enabled ? 'on' : ''}"
								role="switch"
								aria-checked={cc.enabled}
								aria-label="Toggle {cap.label}"
								onclick={() => toggleCapability(cap.key)}
							>
								<span class="cfg-knob"></span>
							</button>
							<div class="cfg-cap-text">
								<span class="cfg-cap-label">{cap.label}</span>
								<span class="cfg-cap-desc">{cap.description}</span>
							</div>
						</div>

						<div class="cfg-perm" class:disabled={!cc.enabled}>
							{#each PERMISSIONS as p}
								<button
									class="cfg-perm-btn {cc.permission === p.key ? 'active ' + p.key : ''}"
									disabled={!cc.enabled}
									onclick={() => setPermission(cap.key, p.key)}
									title={p.label}
								>
									<Icon name={p.icon} size={13} color="currentColor" />
									<span>{p.label}</span>
								</button>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	<!-- Agent actions -->
	{#if hasAgentAction}
		<section class="cfg-card" bind:this={actionCard}>
			<div class="cfg-card-head">
				<span class="eyebrow">Agent action</span>
				<span class="cfg-hint">Lode acts here and respects the permissions above</span>
			</div>

			{#if replayedAsk}
				<p class="cfg-replay"><Icon name="message-circle" size={13} /> {replayedAsk}</p>
			{/if}

			<div class="cfg-action-row">
				<button class="cfg-run" onclick={() => runAction()} disabled={running}>
					{#if running}
						<span class="cfg-spinner"></span> Working…
					{:else}
						<Icon name="play" size={15} color="#fff" /> {connector.agent_action?.label}
					{/if}
				</button>
				<button class="cfg-ask" onclick={askLode}>Ask Lode about this connector</button>
			</div>

			{#if trace.length}
				<div class="cfg-trace">
					{#each trace as t}
						<span class="cfg-trace-step"><Icon name="check" size={12} color="var(--sg-600)" /> {t.label}</span>
					{/each}
				</div>
			{/if}

			{#if result}
				<!-- eslint-disable-next-line svelte/no-at-html-tags — sanitized in renderResult -->
				<div class="cfg-result">{@html renderResult(result)}</div>
			{/if}
		</section>
	{/if}
</div>

<style>
	.cfg-back {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		font-weight: 600;
		color: var(--ink-500);
		text-decoration: none;
		transition: color 0.14s;
	}
	.cfg-back:hover {
		color: var(--ink-900);
	}

	.cfg-head {
		display: flex;
		align-items: center;
		gap: 16px;
		margin-top: 16px;
	}
	.cfg-logo {
		flex: none;
		width: 52px;
		height: 52px;
		border-radius: var(--r-md);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 22px;
		font-weight: 700;
	}
	.av-sage { background: var(--sg-100); color: var(--sg-700); }
	.av-terra { background: var(--terra-100); color: var(--terra-600); }
	.av-slate { background: var(--slate-100); color: var(--slate-600); }
	.av-amber { background: var(--amber-50); color: var(--amber-600); }

	.cfg-id { flex: 1; min-width: 0; }
	.cfg-name-row {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.cfg-head h1 {
		font-size: 26px;
		font-weight: 600;
		color: var(--ink-900);
		margin: 0;
	}
	.cfg-status {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		font-weight: 600;
		color: var(--sg-700);
		background: var(--sg-50);
		padding: 3px 10px;
		border-radius: var(--r-pill);
	}
	.cfg-status.off {
		color: var(--amber-600);
		background: var(--amber-50);
	}
	.cfg-status.off .cfg-dot {
		background: var(--amber-500);
	}
	.cfg-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--sg-500);
		display: inline-block;
	}
	.cfg-id p {
		margin: 4px 0 0;
		font-size: 14px;
		color: var(--ink-500);
	}
	.cfg-save {
		flex: none;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--ink-muted);
		opacity: 0;
		transition: opacity 0.2s;
	}
	.cfg-save.show { opacity: 1; }

	.cfg-card {
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-sm);
		padding: 24px 26px;
	}
	.cfg-card-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
		margin-bottom: 18px;
	}
	.cfg-hint {
		font-size: 12px;
		color: var(--ink-muted);
	}

	.cfg-head-meta {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 4px 16px;
		margin-top: 8px;
	}
	.cfg-head-meta-item {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--ink-muted);
		white-space: nowrap;
	}

	/* The connector's story leads the page in the editorial voice; the cards
	   below it are the controls. */
	.cfg-lead {
		margin: 4px 0 0;
		font-family: var(--font-serif);
		font-size: 18px;
		line-height: 1.6;
		letter-spacing: -0.005em;
		color: var(--ink-700);
		max-width: 64ch;
	}

	/* Capabilities */
	.cfg-caps {
		display: flex;
		flex-direction: column;
	}
	.cfg-cap {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 18px;
		padding: 16px 0;
		border-top: 1px solid var(--paper-200);
		flex-wrap: wrap;
		transition: opacity 0.15s;
	}
	.cfg-cap:first-child {
		border-top: none;
		padding-top: 4px;
	}
	.cfg-cap.off {
		opacity: 0.62;
	}
	.cfg-cap-main {
		display: flex;
		align-items: center;
		gap: 13px;
		min-width: 240px;
		flex: 1;
	}
	.cfg-cap-text {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.cfg-cap-label {
		font-size: 14px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.cfg-cap-desc {
		font-size: 12.5px;
		line-height: 1.45;
		color: var(--ink-500);
		max-width: 52ch;
	}

	/* On-brand switch */
	.cfg-switch {
		flex: none;
		width: 40px;
		height: 23px;
		border-radius: var(--r-pill);
		background: var(--paper-300);
		padding: 2px;
		display: flex;
		align-items: center;
		transition: background 0.18s;
		cursor: pointer;
		border: none;
	}
	.cfg-switch.on {
		background: var(--sg-500);
	}
	.cfg-knob {
		width: 19px;
		height: 19px;
		border-radius: 50%;
		background: #fff;
		box-shadow: var(--v3-sh-xs);
		transform: translateX(0);
		transition: transform 0.18s;
	}
	.cfg-switch.on .cfg-knob {
		transform: translateX(17px);
	}

	/* 3-state permission segmented control */
	.cfg-perm {
		flex: none;
		display: inline-flex;
		gap: 4px;
		background: var(--paper-100);
		border-radius: var(--r-md);
		padding: 4px;
	}
	.cfg-perm.disabled {
		opacity: 0.45;
	}
	.cfg-perm-btn {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 12px;
		font-weight: 600;
		color: var(--ink-500);
		background: transparent;
		border: none;
		padding: 6px 11px;
		border-radius: var(--r-sm);
		cursor: pointer;
		transition: all 0.14s;
	}
	.cfg-perm-btn:not(:disabled):hover {
		color: var(--ink-900);
	}
	.cfg-perm-btn:disabled {
		cursor: not-allowed;
	}
	.cfg-perm-btn.active {
		background: var(--paper-0);
		box-shadow: var(--v3-sh-xs);
	}
	.cfg-perm-btn.active.allow { color: var(--sg-700); }
	.cfg-perm-btn.active.approval { color: var(--amber-600); }
	.cfg-perm-btn.active.deny { color: var(--terra-600); }

	/* Agent action */
	.cfg-action-row {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
		align-items: center;
	}
	.cfg-run {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		font-size: 14px;
		font-weight: 600;
		color: #fff;
		background: var(--sg-500);
		border: none;
		padding: 11px 18px;
		border-radius: var(--r-md);
		cursor: pointer;
		transition: background 0.15s, transform 0.1s;
	}
	.cfg-run:hover:not(:disabled) {
		background: var(--sg-600);
	}
	.cfg-run:active:not(:disabled) {
		transform: translateY(1px);
	}
	.cfg-run:disabled {
		opacity: 0.7;
		cursor: default;
	}
	.cfg-ask {
		font-size: 13.5px;
		font-weight: 600;
		color: var(--ink-500);
		background: transparent;
		border: 1px solid var(--paper-200);
		padding: 11px 16px;
		border-radius: var(--r-md);
		cursor: pointer;
		transition: all 0.14s;
	}
	.cfg-ask:hover {
		border-color: var(--sg-200);
		color: var(--ink-900);
	}
	.cfg-spinner {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		border: 2px solid rgba(255, 255, 255, 0.45);
		border-top-color: #fff;
		animation: cfg-spin 0.7s linear infinite;
	}
	@keyframes cfg-spin {
		to { transform: rotate(360deg); }
	}

	.cfg-replay {
		display: flex;
		align-items: center;
		gap: 7px;
		margin: 0 0 14px;
		font-size: 13px;
		font-weight: 500;
		color: var(--ink-700);
		background: var(--paper-50);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-md);
		padding: 9px 13px;
		max-width: 70ch;
	}

	.cfg-trace {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 16px;
	}
	.cfg-trace-step {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 12px;
		font-weight: 500;
		color: var(--ink-700);
		background: var(--sg-50);
		border: 1px solid var(--sg-100);
		padding: 4px 10px;
		border-radius: var(--r-pill);
	}

	.cfg-result {
		margin-top: 16px;
		padding: 6px 20px 18px;
		background: var(--paper-50);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-lg);
		font-size: 13.5px;
		line-height: 1.65;
		color: var(--ink-900);
	}
	.cfg-result :global(p) {
		margin: 12px 0 0;
	}
	.cfg-result :global(strong) {
		font-weight: 600;
		color: var(--ink-900);
	}
	.cfg-result :global(code) {
		font-family: var(--font-mono);
		font-size: 12px;
		background: var(--paper-100);
		padding: 1px 5px;
		border-radius: var(--r-xs);
	}
	.cfg-result :global(ul) {
		margin: 8px 0 0;
		padding-left: 20px;
	}
	.cfg-result :global(li) {
		margin: 4px 0;
	}
	.cfg-result :global(hr) {
		margin: 16px 0;
		border: none;
		border-top: 1px solid var(--paper-200);
	}

	.cfg > * + * {
		margin-top: 18px;
	}

	@media (max-width: 520px) {
		.cfg-head {
			flex-wrap: wrap;
			gap: 12px;
		}
		.cfg-name-row {
			flex-wrap: wrap;
			gap: 8px;
		}
		.cfg-head h1 {
			font-size: 22px;
		}
		.cfg-id {
			flex: 1 1 200px;
		}
		.cfg-head-meta {
			gap: 4px 12px;
		}
		.cfg-lead {
			font-size: 16.5px;
		}
		.cfg-card {
			padding: 20px 18px;
		}
	}
</style>
