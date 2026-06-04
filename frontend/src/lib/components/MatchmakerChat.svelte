<script lang="ts">
    import { fade, slide } from 'svelte/transition';
    import { api } from '$lib/api';

    let { seedMessage = '' } = $props<{ seedMessage?: string }>();

    let messages = $state([
        {
            id: 1,
            role: 'agent',
            content:
                "Hi! I'm the LodeOS Matchmaker. Describe your song and what it needs — mixing, mastering, cover art, vocals, sync, video, promo — and I'll assemble the right team of vetted providers, explain why each fits, and propose how splits and rights get routed."
        }
    ]);
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
                    { id: Date.now() + 1, role: 'agent', content: data.response }
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
                class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}"
            >
                <div
                    class="max-w-[85%] rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm whitespace-pre-wrap {msg.role ===
                    'user'
                        ? 'bg-slate-800 text-white rounded-br-sm dark:bg-indigo-600'
                        : 'bg-white border border-slate-200/60 dark:bg-slate-700 dark:border-slate-600 text-slate-700 dark:text-slate-200 rounded-bl-sm'}"
                >
                    {msg.content}
                </div>
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
