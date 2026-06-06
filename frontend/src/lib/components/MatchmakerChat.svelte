<script lang="ts">
	import { fade, slide } from 'svelte/transition';
	import { api } from '$lib/api';
	import Icon from '$lib/components/Icon.svelte';

	let { seedMessage = '' } = $props<{ seedMessage?: string }>();

	type ProviderEvidence = {
		id?: string;
		name: string;
		category?: string;
		specialty?: string;
		genres?: string[];
		rating?: number;
		rate?: string;
		turnaround?: string;
		verified?: boolean;
	};
	type WebSource = { title: string; uri: string; domain: string };
	type Evidence = {
		providers: ProviderEvidence[];
		web_sources: WebSource[];
		search_queries: string[];
		grounded: boolean;
		rag_loaded: number;
		tool_calls: string[];
	};
	type Message = {
		id: number;
		role: 'agent' | 'user';
		content: string;
		evidence?: Evidence;
	};

	let messages = $state<Message[]>([
		{
			id: 1,
			role: 'agent',
			content:
				"I'm the LodeOS Matchmaker. Describe your song and what it needs — mixing, mastering, cover art, vocals, sync, video, promo — and I'll assemble the right team of vetted providers, explain why each fits, and propose how splits and rights get routed."
		}
	]);

	const CATEGORY_LABELS: Record<string, string> = {
		mixing: 'Mixing',
		mastering: 'Mastering',
		cover_art: 'Cover Art',
		vocal_production: 'Vocal Production',
		sync_licensing: 'Sync Licensing',
		music_video: 'Music Video',
		promotion: 'Promotion',
		session_musician: 'Session Players'
	};
	const catLabel = (c?: string) => (c ? (CATEGORY_LABELS[c] ?? c) : '');
	const hasEvidence = (e?: Evidence) => !!e && (e.providers.length > 0 || e.web_sources.length > 0);
	let inputMessage = $state('');
	let isTyping = $state(false);
	let sessionId = $state<string | null>(null);
	let scroller: HTMLDivElement | null = $state(null);

	function scrollToBottom() {
		if (scroller) {
			requestAnimationFrame(() => {
				scroller!.scrollTop = scroller!.scrollHeight;
			});
		}
	}

	export async function send(text: string) {
		const userMsg = text.trim();
		if (!userMsg) return;
		messages = [...messages, { id: Date.now(), role: 'user', content: userMsg }];
		inputMessage = '';
		isTyping = true;
		scrollToBottom();

		try {
			const res = await fetch(api('/api/v1/services/chat'), {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ message: userMsg, session_id: sessionId })
			});

			if (res.ok) {
				const data = await res.json();
				sessionId = data.session_id;
				messages = [
					...messages,
					{
						id: Date.now() + 1,
						role: 'agent',
						content: data.response,
						evidence: data.evidence as Evidence | undefined
					}
				];
			} else {
				throw new Error('Backend responded with an error');
			}
		} catch (error) {
			messages = [
				...messages,
				{
					id: Date.now() + 1,
					role: 'agent',
					content:
						"I'm having trouble reaching the Matchmaker backend. Make sure the API server is running."
				}
			];
		} finally {
			isTyping = false;
			scrollToBottom();
		}
	}

	function sendCurrent() {
		send(inputMessage);
	}
</script>

<div class="chat-card">
	<div class="chat-head">
		<img src="/logo-mark.svg" alt="" width="30" height="30" />
		<div class="chat-head-meta">
			<b>Matchmaker</b>
			<span><span class="chat-live"></span> Gemini 2.5 Pro · grounded in marketplace</span>
		</div>
		<span class="chat-model">Multi-turn</span>
	</div>

	<div class="chat-thread" bind:this={scroller}>
		{#each messages as msg (msg.id)}
			<div in:slide={{ duration: 280 }} class="msg {msg.role}">
				<div class="v3-orb-bubble {msg.role === 'user' ? 'user' : 'lode'}">
					<p class="wrap">{msg.content}</p>
				</div>

				{#if msg.role === 'agent' && hasEvidence(msg.evidence)}
					{@const ev = msg.evidence!}
					<div in:slide={{ duration: 280 }} class="ev">
						<div class="ev-head">
							<Icon name="shield-check" size={15} color="var(--sg-600)" />
							<span class="eyebrow ev-title">Grounded sources</span>
							{#if ev.rag_loaded > 0}
								<span class="ev-count">{ev.rag_loaded} vetted providers searched</span>
							{/if}
						</div>

						{#if ev.providers.length > 0}
							<p class="ev-sub">From the vetted marketplace</p>
							<div class="ev-list">
								{#each ev.providers as p (p.name)}
									<div class="ev-prov">
										<span class="ev-dot"></span>
										<span class="ev-prov-name">{p.name}</span>
										{#if p.verified}
											<Icon name="badge-check" size={14} color="var(--sg-500)" />
										{/if}
										{#if p.category}
											<span class="ev-cat">{catLabel(p.category)}</span>
										{/if}
										<span class="ev-meta">
											{#if p.rating}
												<span class="ev-rating"><Icon name="star" size={11} color="var(--amber-500)" /> {p.rating}</span>
											{/if}
											{#if p.rate}<span class="ev-rate">{p.rate}</span>{/if}
										</span>
									</div>
								{/each}
							</div>
						{/if}

						{#if ev.web_sources.length > 0}
							<p class="ev-sub">Live web research <span class="ev-unvetted">· unvetted</span></p>
							<div class="ev-web">
								{#each ev.web_sources as w (w.uri)}
									<a class="ev-link" href={w.uri} target="_blank" rel="noopener noreferrer">
										<Icon name="link" size={12} color="var(--slate-500)" />
										<span class="ev-link-label">{w.domain || w.title}</span>
									</a>
								{/each}
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/each}
		{#if isTyping}
			<div in:fade class="v3-orb-bubble lode">
				<div class="typing"><span></span><span></span><span></span></div>
			</div>
		{/if}
	</div>

	<form
		class="v3-orb-composer chat-composer"
		onsubmit={(e) => {
			e.preventDefault();
			sendCurrent();
		}}
	>
		<input bind:value={inputMessage} placeholder="Refine: add a video, set a budget, adjust splits…" />
		<button class="v3-orb-send" type="submit" disabled={!inputMessage.trim() || isTyping} aria-label="Send">
			<Icon name="arrow-up" size={16} color="#fff" />
		</button>
	</form>
</div>

<style>
	.chat-card {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-md);
		overflow: hidden;
	}
	.chat-head {
		display: flex;
		align-items: center;
		gap: 11px;
		padding: 16px 18px;
		border-bottom: 1px solid var(--paper-200);
		background: linear-gradient(180deg, var(--sg-50), var(--paper-0));
	}
	.chat-head-meta {
		flex: 1;
		min-width: 0;
	}
	.chat-head-meta b {
		display: block;
		font-size: 14px;
		font-weight: 700;
		color: var(--ink-900);
	}
	.chat-head-meta span {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 11px;
		color: var(--ink-muted);
		margin-top: 1px;
	}
	.chat-live {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--sg-500);
	}
	.chat-model {
		flex: none;
		font-size: 10.5px;
		font-weight: 600;
		color: var(--sg-700);
		background: var(--sg-50);
		border: 1px solid var(--sg-100);
		border-radius: var(--r-pill);
		padding: 4px 10px;
	}
	.chat-thread {
		flex: 1;
		overflow-y: auto;
		padding: 18px;
		display: flex;
		flex-direction: column;
		gap: 14px;
		min-height: 0;
	}
	.chat-composer {
		margin: 14px;
	}
	.wrap {
		white-space: pre-wrap;
	}
	.msg {
		display: flex;
		flex-direction: column;
	}
	.msg.user {
		align-items: flex-end;
	}
	.msg.agent {
		align-items: flex-start;
	}

	/* evidence panel */
	.ev {
		margin-top: 10px;
		width: 100%;
		border: 1px solid var(--sg-100);
		background: var(--sg-50);
		border-radius: var(--r-lg);
		padding: 13px 14px;
	}
	.ev-head {
		display: flex;
		align-items: center;
		gap: 7px;
		margin-bottom: 11px;
	}
	.ev-title {
		color: var(--sg-700);
	}
	.ev-count {
		margin-left: auto;
		font-size: 10.5px;
		font-weight: 500;
		color: var(--sg-600);
	}
	.ev-sub {
		font-size: 10px;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--ink-muted);
		margin: 0 0 7px;
	}
	.ev-unvetted {
		text-transform: none;
		letter-spacing: 0;
		font-weight: 400;
	}
	.ev-list {
		display: flex;
		flex-direction: column;
		gap: 6px;
		margin-bottom: 12px;
	}
	.ev-prov {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-md);
		padding: 8px 11px;
	}
	.ev-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--sg-500);
		flex: none;
	}
	.ev-prov-name {
		font-size: 13px;
		font-weight: 600;
		color: var(--ink-900);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.ev-cat {
		font-size: 10px;
		font-weight: 500;
		color: var(--ink-500);
		background: var(--paper-100);
		padding: 2px 7px;
		border-radius: var(--r-xs);
		flex: none;
	}
	.ev-meta {
		margin-left: auto;
		display: flex;
		align-items: center;
		gap: 9px;
		flex: none;
	}
	.ev-rating {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-size: 11px;
		color: var(--ink-500);
		font-family: var(--font-mono);
	}
	.ev-rate {
		font-size: 11px;
		font-weight: 500;
		color: var(--ink-700);
		font-family: var(--font-mono);
	}
	.ev-web {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}
	.ev-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		background: var(--paper-0);
		border: 1px solid var(--slate-200);
		border-radius: var(--r-sm);
		padding: 5px 10px;
		font-size: 11.5px;
		color: var(--slate-600);
		text-decoration: none;
		transition: border-color 0.14s, background 0.14s;
		max-width: 100%;
	}
	.ev-link:hover {
		border-color: var(--slate-400);
		background: var(--slate-50);
	}
	.ev-link-label {
		font-weight: 500;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
</style>
