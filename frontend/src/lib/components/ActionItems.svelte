<script lang="ts">
    let { context } = $props();
    
    let missingAmount = $derived(context?.neighboring_rights?.estimated_missing || 0);
    let isRegistered = $derived(context?.neighboring_rights?.registered ?? true);
</script>

<div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 transition-all hover:shadow-md">
    <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3">
            <span class="w-2 h-8 rounded-full bg-rose-500/20 block"></span>
            Action Items
        </h2>
        <span class="flex items-center gap-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20 px-3 py-1 rounded-full">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
            </span>
            Action Required
        </span>
    </div>
    
    {#if !isRegistered}
        <div class="group flex items-start p-5 bg-[#fdf2f2] dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/50 rounded-2xl transition-all hover:bg-rose-50 dark:hover:bg-rose-900/40 cursor-pointer">
            <div class="flex-shrink-0 mt-1 p-2 bg-white dark:bg-rose-900/50 rounded-xl shadow-sm text-rose-500">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            </div>
            <div class="ml-4 flex-1">
                <h3 class="text-base font-semibold text-rose-900 dark:text-rose-200 tracking-tight">Missing Neighboring Rights</h3>
                <div class="mt-1.5 text-sm text-rose-700/80 dark:text-rose-300/80 leading-relaxed">
                    <p>Estimated uncollected royalties: <span class="font-bold text-rose-700 dark:text-rose-300">${missingAmount.toLocaleString()}</span>. Your agent can draft a registration for SoundExchange to capture this revenue.</p>
                </div>
                <div class="mt-4 flex items-center justify-between">
                    <button class="text-sm font-semibold text-rose-700 dark:text-rose-400 hover:text-rose-800 dark:hover:text-rose-300 transition-colors flex items-center gap-1">
                        Draft Registration <span class="group-hover:translate-x-1 transition-transform inline-block">&rarr;</span>
                    </button>
                    <span class="text-xs font-medium text-rose-500/60 dark:text-rose-400/50">High Priority</span>
                </div>
            </div>
        </div>
    {:else}
        <div class="p-6 text-center border border-dashed border-slate-300 dark:border-slate-700 rounded-2xl">
            <p class="text-sm font-medium text-slate-500 dark:text-slate-400">All caught up! No pending actions.</p>
        </div>
    {/if}
</div>
