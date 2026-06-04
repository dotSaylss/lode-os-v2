<script lang="ts">
    import { fade, slide } from 'svelte/transition';
    import { api } from '$lib/api';

    let { greeting = "I'm your LabelAgent. I can scan your entire catalog for missing money and register artists in bulk. Ask me \"what's the biggest opportunity across my roster?\"" }: { greeting?: string } = $props();

    type TraceEvent = { kind: 'agent' | 'tool' | 'handoff'; agent?: string | null; label: string; detail?: string | null };
    type Msg = { id: number; role: 'agent' | 'user'; content: string; trace?: TraceEvent[]; runtime?: string };

    let messages = $state<Msg[]>([
        { id: 1, role: 'agent', content: greeting }
    ]);
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
                messages = [...messages, {
                    id: Date.now() + 1,
                    role: 'agent',
                    content: data.response,
                    trace: data.trace ?? [],
                    runtime: data.runtime
                }];
            } else {
                throw new Error('Backend responded with an error');
            }
        } catch (error) {
            messages = [...messages, {
                id: Date.now() + 1,
                role: 'agent',
                content: "I'm having trouble reaching the ADK LabelAgent backend. Make sure the FastAPI server is running on port 8001!"
            }];
        } finally {
            isTyping = false;
        }
    }
</script>

<div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 flex flex-col h-full overflow-hidden transition-all hover:shadow-md">
    <div class="px-6 py-5 border-b border-slate-100 dark:border-slate-700/50 bg-white/50 dark:bg-slate-800/30 flex items-center justify-between backdrop-blur-md z-10">
        <div class="flex items-center gap-3">
            <div class="relative flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 shadow-sm text-white font-bold text-sm">
                LA
                <span class="absolute bottom-0 right-0 w-3 h-3 border-2 border-white dark:border-slate-800 rounded-full bg-emerald-400"></span>
            </div>
            <div>
                <h2 class="text-sm font-bold text-slate-800 dark:text-white tracking-tight">LabelAgent</h2>
                <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Catalog-wide · A2A → ActionAgent</p>
            </div>
        </div>
        <span class="px-2.5 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full text-[11px] font-semibold tracking-wide">
            Gemini 2.5 Pro
        </span>
    </div>

    <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fcfcfc] dark:bg-transparent">
        {#each messages as msg (msg.id)}
            {#if msg.role === 'agent' && msg.trace && msg.trace.length > 0}
                <div in:slide={{ duration: 300 }} class="space-y-1.5">
                    <div class="flex items-center gap-2 mb-1 pl-0.5">
                        <span class="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">Agent Trace</span>
                        <span class="h-px flex-1 bg-slate-100 dark:bg-slate-700/60"></span>
                        {#if msg.runtime}
                            <span class="text-[10px] font-medium text-slate-400 dark:text-slate-500 font-mono">{msg.runtime}</span>
                        {/if}
                    </div>
                    {#each msg.trace as step, i (i)}
                        <div class="flex items-start gap-2.5 pl-0.5">
                            <div class="flex flex-col items-center pt-0.5">
                                {#if step.kind === 'handoff'}
                                    <span class="flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 ring-2 ring-blue-200/60 dark:ring-blue-800/50">
                                        <svg class="w-3 h-3 text-blue-600 dark:text-blue-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7h12m0 0l-4-4m4 4l-4 4m4 6H4m0 0l4 4m-4-4l4-4"/></svg>
                                    </span>
                                {:else if step.kind === 'tool'}
                                    <span class="flex items-center justify-center w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-700">
                                        <svg class="w-3 h-3 text-slate-500 dark:text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 004.486-6.336l-3.276 3.277a3.004 3.004 0 01-2.25-2.25l3.276-3.276a4.5 4.5 0 00-6.336 4.486c.091 1.076-.071 2.264-.904 2.95l-.102.085"/></svg>
                                    </span>
                                {:else}
                                    <span class="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-900/40">
                                        <svg class="w-3 h-3 text-emerald-600 dark:text-emerald-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>
                                    </span>
                                {/if}
                                {#if i < (msg.trace?.length ?? 0) - 1}
                                    <span class="w-px flex-1 min-h-[10px] bg-slate-200 dark:bg-slate-700 mt-1"></span>
                                {/if}
                            </div>
                            <div class="pb-1 -mt-px">
                                <p class="text-xs font-semibold {step.kind === 'handoff' ? 'text-blue-700 dark:text-blue-300' : 'text-slate-700 dark:text-slate-200'}">{step.label}</p>
                                {#if step.detail}
                                    <p class="text-[11px] text-slate-400 dark:text-slate-500 leading-snug">{step.detail}</p>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
            <div in:slide={{ duration: 300 }} class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="max-w-[85%] whitespace-pre-wrap rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm {msg.role === 'user' ? 'bg-slate-800 text-white rounded-br-sm dark:bg-indigo-600' : 'bg-white border border-slate-200/60 dark:bg-slate-700 dark:border-slate-600 text-slate-700 dark:text-slate-200 rounded-bl-sm'}">
                    {msg.content}
                </div>
            </div>
        {/each}
        {#if isTyping}
            <div in:fade class="flex justify-start">
                <div class="bg-white border border-slate-200/60 dark:bg-slate-700 dark:border-slate-600 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-500 animate-bounce" style="animation-delay: 0ms"></span>
                    <span class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-500 animate-bounce" style="animation-delay: 150ms"></span>
                    <span class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-500 animate-bounce" style="animation-delay: 300ms"></span>
                </div>
            </div>
        {/if}
    </div>

    <div class="p-4 border-t border-slate-100 dark:border-slate-700/50 bg-white dark:bg-slate-800/80">
        <form onsubmit={(e) => { e.preventDefault(); sendMessage(); }} class="flex items-center gap-3">
            <div class="relative flex-1">
                <input
                    type="text"
                    bind:value={inputMessage}
                    placeholder="Ask the LabelAgent about your catalog..."
                    class="w-full bg-[#f4f4f5] dark:bg-slate-900 border border-slate-200/50 dark:border-slate-700 rounded-full pl-5 pr-5 py-3 text-[15px] focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all dark:text-white outline-none placeholder:text-slate-400"
                />
            </div>
            <button
                type="submit"
                disabled={!inputMessage.trim() || isTyping}
                class="w-12 h-12 rounded-full bg-blue-600 dark:bg-blue-600 text-white flex items-center justify-center hover:bg-blue-500 dark:hover:bg-blue-500 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <svg class="w-5 h-5 translate-x-px -translate-y-px" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
            </button>
        </form>
    </div>
</div>
