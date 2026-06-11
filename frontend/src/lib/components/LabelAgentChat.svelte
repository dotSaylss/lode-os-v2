<script lang="ts">
	import { fade, slide } from 'svelte/transition';
	import { api } from '$lib/api';
	import Icon from '$lib/components/Icon.svelte';

	let {
		greeting = "I'm your LabelAgent. I reason across the entire roster at once: audits, bulk registrations, forecasts. Try asking for the biggest opportunity across the roster."
	}: { greeting?: string } = $props();

	type TraceEvent = {
		kind: 'agent' | 'tool' | 'handoff';
		agent?: string | null;
		label: string;
		detail?: string | null;
	};
	type Msg = {
		id: number;
		role: 'agent' | 'user';
		content: string;
		trace?: TraceEvent[];
		runtime?: string;
	};

	let messages = $state<Msg[]>([{ id: 1, role: 'agent', content: greeting }]);
	let inputMessage = $state('');
	let isTyping = $state(false);
	let sessionId = $state<string | null>(null);

	export async function ask(prompt: string) {
		inputMessage = prompt;
		await sendMessage();
	}

	async function sendMessage() {
		if (!inputMessage.trim() || isTyping) return;
		const userMsg = inputMessage;
		messages = [...messages, { id: Date.now(), role: 'user', content: userMsg }];
		inputMessage = '';
		isTyping = true;

		try {
			const res = await fetch(api('/api/v1/label/chat'), {
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
						trace: data.trace ?? [],
						runtime: data.runtime
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
					content: "I'm having trouble reaching the LabelAgent backend. Make sure the API server is running."
				}
			];
		} finally {
			isTyping = false;
		}
	}

	const stepIcon = (kind: string) =>
		kind === 'handoff' ? 'arrow-left-right' : kind === 'tool' ? 'wrench' : 'check';
</script>

<div class="chat-card">
	<div class="chat-head">
		<img src="/logo-mark.svg" alt="" width="30" height="30" />
		<div class="chat-head-meta">
			<b>LabelAgent</b>
			<span><span class="chat-live"></span> Catalog-wide · A2A → ActionAgent</span>
		</div>
		<span class="chat-model">Gemini 2.5 Pro</span>
	</div>

	<div class="chat-thread">
		{#each messages as msg (msg.id)}
			{#if msg.role === 'agent' && msg.trace && msg.trace.length > 0}
				<div in:slide={{ duration: 300 }} class="trace">
					<div class="trace-head">
						<span class="eyebrow">Agent trace</span>
						<span class="trace-rule"></span>
						{#if msg.runtime}<span class="trace-runtime">{msg.runtime}</span>{/if}
					</div>
					{#each msg.trace as step, i (i)}
						<div class="trace-step">
							<div class="trace-rail">
								<span class="trace-node {step.kind}">
									<Icon
										name={stepIcon(step.kind)}
										size={12}
										color={step.kind === 'handoff' ? 'var(--sg-700)' : 'var(--ink-500)'}
									/>
								</span>
								{#if i < (msg.trace?.length ?? 0) - 1}<span class="trace-line"></span>{/if}
							</div>
							<div class="trace-body">
								<p class="trace-label {step.kind === 'handoff' ? 'is-handoff' : ''}">{step.label}</p>
								{#if step.detail}<p class="trace-detail">{step.detail}</p>{/if}
							</div>
						</div>
					{/each}
				</div>
			{/if}
			<div in:slide={{ duration: 300 }} class="v3-orb-bubble {msg.role === 'user' ? 'user' : 'lode'}">
				<p class="wrap">{msg.content}</p>
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
			sendMessage();
		}}
	>
		<input bind:value={inputMessage} placeholder="Ask the LabelAgent about your catalog…" />
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

	/* A2A trace timeline */
	.trace {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.trace-head {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 6px;
	}
	.trace-rule {
		height: 1px;
		flex: 1;
		background: var(--paper-200);
	}
	.trace-runtime {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--ink-muted);
	}
	.trace-step {
		display: flex;
		align-items: flex-start;
		gap: 11px;
	}
	.trace-rail {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding-top: 1px;
	}
	.trace-node {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--paper-100);
		flex: none;
	}
	.trace-node.handoff {
		background: var(--sg-100);
		box-shadow: 0 0 0 2px var(--sg-50);
	}
	.trace-line {
		width: 1px;
		flex: 1;
		min-height: 12px;
		background: var(--paper-200);
		margin: 3px 0;
	}
	.trace-body {
		padding-bottom: 8px;
	}
	.trace-label {
		margin: 0;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--ink-700);
	}
	.trace-label.is-handoff {
		color: var(--sg-700);
	}
	.trace-detail {
		margin: 2px 0 0;
		font-size: 11px;
		color: var(--ink-muted);
		line-height: 1.4;
	}
</style>
