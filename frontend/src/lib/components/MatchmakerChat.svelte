<script lang="ts">
    import { fade, slide } from 'svelte/transition';
    import { api } from '$lib/api';

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
                "Hi! I'm the LodeOS Matchmaker. Describe your song and what it needs — mixing, mastering, cover art, vocals, sync, video, promo — and I'll assemble the right team of vetted providers, explain why each fits, and propose how splits and rights get routed."
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
    const hasEvidence = (e?: Evidence) =>
        !!e && (e.providers.length > 0 || e.web_sources.length > 0);
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
                        "I'm having trouble reaching the Matchmaker (ADK) backend. Make sure the FastAPI server is running on port 8002."
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

<div
    class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 flex flex-col h-full overflow-hidden transition-all hover:shadow-md"
>
    <div
        class="px-6 py-5 border-b border-slate-100 dark:border-slate-700/50 bg-white/50 dark:bg-slate-800/30 flex items-center justify-between backdrop-blur-md z-10"
    >
        <div class="flex items-center gap-3">
            <div
                class="relative flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 shadow-sm text-white font-bold text-sm"
            >
                MM
                <span
                    class="absolute bottom-0 right-0 w-3 h-3 border-2 border-white dark:border-slate-800 rounded-full bg-emerald-400"
                ></span>
            </div>
            <div>
                <h2 class="text-sm font-bold text-slate-800 dark:text-white tracking-tight">
                    Matchmaker
                </h2>
                <p class="text-xs font-medium text-slate-500 dark:text-slate-400">
                    Gemini 2.5 Pro &middot; grounded in marketplace
                </p>
            </div>
        </div>
        <span
            class="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 px-3 py-1 rounded-full"
        >
            <span class="relative flex h-2 w-2">
                <span
                    class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"
                ></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Multi-turn
        </span>
    </div>

    <div
        bind:this={scroller}
        class="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fcfcfc] dark:bg-transparent"
    >
        {#each messages as msg (msg.id)}
            <div
                in:slide={{ duration: 300 }}
                class="flex flex-col {msg.role === 'user' ? 'items-end' : 'items-start'}"
            >
                <div
                    class="max-w-[85%] rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm whitespace-pre-wrap {msg.role ===
                    'user'
                        ? 'bg-slate-800 text-white rounded-br-sm dark:bg-indigo-600'
                        : 'bg-white border border-slate-200/60 dark:bg-slate-700 dark:border-slate-600 text-slate-700 dark:text-slate-200 rounded-bl-sm'}"
                >
                    {msg.content}
                </div>

                {#if msg.role === 'agent' && hasEvidence(msg.evidence)}
                    {@const ev = msg.evidence!}
                    <div
                        in:slide={{ duration: 300 }}
                        class="mt-2.5 max-w-[92%] w-full rounded-2xl border border-emerald-200/70 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-900/10 px-4 py-3.5"
                    >
                        <div class="flex items-center gap-2 mb-3">
                            <svg
                                class="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                stroke-width="2"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                            <span
                                class="text-[11px] font-bold uppercase tracking-wide text-emerald-700 dark:text-emerald-300"
                            >
                                Grounded sources
                            </span>
                            {#if ev.rag_loaded > 0}
                                <span
                                    class="ml-auto text-[10.5px] font-medium text-emerald-600/80 dark:text-emerald-400/80"
                                >
                                    {ev.rag_loaded} vetted providers searched
                                </span>
                            {/if}
                        </div>

                        {#if ev.providers.length > 0}
                            <p
                                class="text-[10.5px] font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500 mb-1.5"
                            >
                                From the vetted marketplace
                            </p>
                            <div class="flex flex-col gap-1.5 mb-3">
                                {#each ev.providers as p (p.name)}
                                    <div
                                        class="flex items-center gap-2 rounded-xl bg-white dark:bg-slate-800 border border-slate-200/70 dark:border-slate-700 px-3 py-2"
                                    >
                                        <span
                                            class="shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-500"
                                        ></span>
                                        <span
                                            class="text-[13px] font-semibold text-slate-800 dark:text-white truncate"
                                        >
                                            {p.name}
                                        </span>
                                        {#if p.verified}
                                            <svg
                                                class="w-3.5 h-3.5 text-blue-500 shrink-0"
                                                fill="currentColor"
                                                viewBox="0 0 20 20"
                                                aria-label="Verified"
                                            >
                                                <path
                                                    fill-rule="evenodd"
                                                    d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812z"
                                                    clip-rule="evenodd"
                                                />
                                            </svg>
                                        {/if}
                                        {#if p.category}
                                            <span
                                                class="text-[10px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded shrink-0"
                                            >
                                                {catLabel(p.category)}
                                            </span>
                                        {/if}
                                        <span
                                            class="ml-auto flex items-center gap-2 text-[11px] text-slate-500 dark:text-slate-400 shrink-0"
                                        >
                                            {#if p.rating}
                                                <span class="flex items-center gap-0.5">
                                                    <svg
                                                        class="w-3 h-3 text-amber-400"
                                                        fill="currentColor"
                                                        viewBox="0 0 20 20"
                                                    >
                                                        <path
                                                            d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                                                        />
                                                    </svg>
                                                    {p.rating}
                                                </span>
                                            {/if}
                                            {#if p.rate}
                                                <span
                                                    class="font-medium text-slate-600 dark:text-slate-300"
                                                    >{p.rate}</span
                                                >
                                            {/if}
                                        </span>
                                    </div>
                                {/each}
                            </div>
                        {/if}

                        {#if ev.web_sources.length > 0}
                            <p
                                class="text-[10.5px] font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500 mb-1.5"
                            >
                                Live web research
                                <span class="font-normal lowercase text-slate-400/80"
                                    >· unvetted</span
                                >
                            </p>
                            <div class="flex flex-wrap gap-1.5">
                                {#each ev.web_sources as w (w.uri)}
                                    <a
                                        href={w.uri}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        class="group inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-800 border border-blue-200/70 dark:border-blue-900/40 px-2.5 py-1.5 text-[11.5px] text-blue-700 dark:text-blue-300 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors max-w-full"
                                    >
                                        <svg
                                            class="w-3 h-3 shrink-0 opacity-70"
                                            fill="none"
                                            viewBox="0 0 24 24"
                                            stroke="currentColor"
                                            stroke-width="2"
                                        >
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
                                            />
                                        </svg>
                                        <span class="font-medium truncate">{w.domain || w.title}</span>
                                    </a>
                                {/each}
                            </div>
                        {/if}
                    </div>
                {/if}
            </div>
        {/each}
        {#if isTyping}
            <div in:fade class="flex justify-start">
                <div
                    class="bg-white border border-slate-200/60 dark:bg-slate-700 dark:border-slate-600 rounded-2xl rounded-bl-sm px-5 py-4 shadow-sm flex items-center gap-1.5"
                >
                    <span
                        class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-500 animate-bounce"
                        style="animation-delay: 0ms"
                    ></span>
                    <span
                        class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-500 animate-bounce"
                        style="animation-delay: 150ms"
                    ></span>
                    <span
                        class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-500 animate-bounce"
                        style="animation-delay: 300ms"
                    ></span>
                </div>
            </div>
        {/if}
    </div>

    <div class="p-4 border-t border-slate-100 dark:border-slate-700/50 bg-white dark:bg-slate-800/80">
        <form
            onsubmit={(e) => {
                e.preventDefault();
                sendCurrent();
            }}
            class="flex items-center gap-3"
        >
            <div class="relative flex-1">
                <input
                    type="text"
                    bind:value={inputMessage}
                    placeholder="Refine the brief: add a music video, set a budget, adjust the splits..."
                    class="w-full bg-[#f4f4f5] dark:bg-slate-900 border border-slate-200/50 dark:border-slate-700 rounded-full pl-5 pr-5 py-3 text-[15px] focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all dark:text-white outline-none placeholder:text-slate-400"
                />
            </div>
            <button
                type="submit"
                aria-label="Send message"
                disabled={!inputMessage.trim() || isTyping}
                class="w-12 h-12 rounded-full bg-slate-800 dark:bg-indigo-600 text-white flex items-center justify-center hover:bg-slate-700 dark:hover:bg-indigo-500 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <svg
                    class="w-5 h-5 translate-x-px -translate-y-px"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                </svg>
            </button>
        </form>
    </div>
</div>
