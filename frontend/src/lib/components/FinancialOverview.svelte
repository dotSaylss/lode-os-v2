<script lang="ts">
    let { context } = $props();
    
    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
    };
</script>

<div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 flex flex-col h-full transition-all hover:shadow-md">
    <div class="flex items-center justify-between mb-8">
        <h2 class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3">
            <span class="w-2 h-8 rounded-full bg-blue-500/20 block"></span>
            Financial Overview
        </h2>
        <span class="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full text-xs font-medium tracking-wide">
            {context?.artist_profile?.name || 'Artist'}
        </span>
    </div>
    
    <div class="mb-10">
        <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-widest font-semibold mb-2">Year to Date Earnings</p>
        <p class="text-5xl font-light text-slate-900 dark:text-white tracking-tighter">
            {formatCurrency(context?.artist_profile?.ytd_earnings || 0)}
        </p>
    </div>
    
    <div class="mt-auto">
        <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-widest font-semibold mb-4">Connected Revenue Sources</p>
        <div class="flex flex-wrap gap-3">
            {#each (context?.connected_sources || []) as source}
                <div class="px-4 py-2 bg-[#f8f9fa] dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 rounded-xl text-sm font-medium border border-slate-200 dark:border-slate-700 flex items-center shadow-sm">
                    <span class="inline-block w-2 h-2 rounded-full {source.status === 'connected' || source.status === 'active' ? 'bg-emerald-400' : 'bg-amber-400'} mr-2 shadow-sm"></span>
                    {source.name}
                </div>
            {/each}
        </div>
    </div>
</div>
