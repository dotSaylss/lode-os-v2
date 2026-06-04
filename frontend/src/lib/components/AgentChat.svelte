<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, slide } from 'svelte/transition';
    
    let messages = $state([
        { id: 1, role: 'agent', content: "Hi there! I'm your Mogul Orchestrator. I've analyzed June Freedom's profile and noticed missing Neighboring Rights. Would you like me to draft an email to ASCAP or SoundExchange to claim the estimated $2,400?" }
    ]);
    let inputMessage = $state('');
    let isTyping = $state(false);
    
    async function sendMessage() {
        if (!inputMessage.trim()) return;
        const userMsg = inputMessage;
        messages = [...messages, { id: Date.now(), role: 'user', content: userMsg }];
        inputMessage = '';
        isTyping = true;
        
        try {
            const res = await fetch('http://localhost:8000/api/v1/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg })
            });
            
            if (res.ok) {
                const data = await res.json();
                messages = [...messages, { 
                    id: Date.now() + 1,
                    role: 'agent', 
                    content: data.response 
                }];
            } else {
                throw new Error('Backend responded with an error');
            }
        } catch (error) {
            messages = [...messages, { 
                id: Date.now() + 1,
                role: 'agent', 
                content: "I'm having trouble connecting to the ADK graph backend right now. Make sure the FastAPI server is running!" 
            }];
        } finally {
            isTyping = false;
        }
    }
</script>

<div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 flex flex-col h-full overflow-hidden transition-all hover:shadow-md">
    <div class="px-6 py-5 border-b border-slate-100 dark:border-slate-700/50 bg-white/50 dark:bg-slate-800/30 flex items-center justify-between backdrop-blur-md z-10">
        <div class="flex items-center gap-3">
            <div class="relative flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 shadow-sm text-white font-bold text-sm">
                OA
                <span class="absolute bottom-0 right-0 w-3 h-3 border-2 border-white dark:border-slate-800 rounded-full bg-emerald-400"></span>
            </div>
            <div>
                <h2 class="text-sm font-bold text-slate-800 dark:text-white tracking-tight">Orchestrator</h2>
                <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Powered by ADK 2.0</p>
            </div>
        </div>
        <button class="w-8 h-8 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center justify-center text-slate-400 transition-colors">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
        </button>
    </div>
    
    <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fcfcfc] dark:bg-transparent">
        {#each messages as msg (msg.id)}
            <div in:slide={{ duration: 300 }} class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="max-w-[85%] rounded-2xl px-5 py-3.5 text-[15px] leading-relaxed shadow-sm {msg.role === 'user' ? 'bg-slate-800 text-white rounded-br-sm dark:bg-indigo-600' : 'bg-white border border-slate-200/60 dark:bg-slate-700 dark:border-slate-600 text-slate-700 dark:text-slate-200 rounded-bl-sm'}">
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
                    placeholder="Ask the Orchestrator to analyze..." 
                    class="w-full bg-[#f4f4f5] dark:bg-slate-900 border border-slate-200/50 dark:border-slate-700 rounded-full pl-5 pr-12 py-3 text-[15px] focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all dark:text-white outline-none placeholder:text-slate-400"
                />
                <div class="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
                    <button type="button" class="p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
                    </button>
                </div>
            </div>
            <button 
                type="submit" 
                disabled={!inputMessage.trim()}
                class="w-12 h-12 rounded-full bg-slate-800 dark:bg-indigo-600 text-white flex items-center justify-center hover:bg-slate-700 dark:hover:bg-indigo-500 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <svg class="w-5 h-5 translate-x-px -translate-y-px" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
            </button>
        </form>
    </div>
</div>
