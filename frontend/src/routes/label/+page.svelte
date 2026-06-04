<script lang="ts">
    import LabelAgentChat from '$lib/components/LabelAgentChat.svelte';

    let { data } = $props();
    let p = $derived(data.portfolio);
    let forecast = $derived(data.forecast);

    // Forecast curve geometry for the inline SVG sparkline.
    let curve = $derived.by(() => {
        const pts = forecast?.forecast ?? [];
        const max = forecast?.total_recoverable || 1;
        if (pts.length === 0) return { line: '', area: '', last: { x: 0, y: 100 } };
        const W = 100, H = 100;
        const coords = pts.map((d, i) => {
            const x = pts.length > 1 ? (i / (pts.length - 1)) * W : 0;
            const y = H - (d.cumulative_recovered / max) * H;
            return { x, y };
        });
        const line = coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x.toFixed(2)},${c.y.toFixed(2)}`).join(' ');
        const area = `${line} L${W},${H} L0,${H} Z`;
        return { line, area, last: coords[coords.length - 1] };
    });

    let chat = $state<LabelAgentChat>();

    const fmt = (n: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n || 0);
    const fmtCents = (n: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

    // Roster sorted by biggest uncollected opportunity first.
    let roster = $derived(
        [...(p?.artists || [])].sort((a, b) => (b.total_uncollected || 0) - (a.total_uncollected || 0))
    );

    const gapColor = (type: string) => {
        switch (type) {
            case 'neighboring_rights': return 'bg-rose-50 text-rose-600 border-rose-100 dark:bg-rose-900/20 dark:text-rose-300';
            case 'unclaimed_mechanicals': return 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/20 dark:text-amber-300';
            case 'sync_unmatched': return 'bg-indigo-50 text-indigo-600 border-indigo-100 dark:bg-indigo-900/20 dark:text-indigo-300';
            case 'pro_blackbox': return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300';
            default: return 'bg-slate-100 text-slate-600 border-slate-200';
        }
    };

    function bulkRegister() {
        chat?.ask(
            `Register all ${p.neighboring_rights_artists} artists missing neighboring rights to recover ${fmt(p.neighboring_rights_uncollected)}. Draft the bulk SoundExchange registration now.`
        );
        if (typeof document !== 'undefined') {
            document.getElementById('label-chat')?.scrollIntoView({ behavior: 'smooth' });
        }
    }
</script>

<div class="mb-8 flex items-end justify-between flex-wrap gap-4">
    <div>
        <div class="flex items-center gap-2 mb-1">
            <span class="px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-[11px] font-bold tracking-wide uppercase">Enterprise · A2A</span>
        </div>
        <h1 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Label Portfolio</h1>
        <p class="text-slate-500 dark:text-slate-400 mt-1">{p.label_profile?.name} · {p.total_artists} artists · catalog-wide royalty recovery.</p>
    </div>
</div>

<!-- Hero opportunity + KPI row -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <!-- Hero: total uncollected across the roster -->
    <div class="lg:col-span-2 relative overflow-hidden bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 transition-all hover:shadow-md">
        <div class="absolute -right-10 -top-10 w-48 h-48 rounded-full bg-rose-500/5 blur-2xl"></div>
        <div class="flex items-center justify-between mb-6 relative">
            <h2 class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3">
                <span class="w-2 h-8 rounded-full bg-rose-500/20 block"></span>
                Total Uncollected Across Catalog
            </h2>
            <span class="flex items-center gap-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/20 px-3 py-1 rounded-full">
                <span class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
                </span>
                Recoverable
            </span>
        </div>
        <p class="text-6xl font-light text-slate-900 dark:text-white tracking-tighter relative">{fmt(p.total_uncollected)}</p>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-3 relative leading-relaxed">
            Detected across {p.total_artists} artists. The single biggest lever:
            <span class="font-semibold text-rose-700 dark:text-rose-300">{p.neighboring_rights_artists} artists</span>
            missing neighboring rights worth
            <span class="font-semibold text-rose-700 dark:text-rose-300">{fmt(p.neighboring_rights_uncollected)}</span>.
        </p>
        <button
            onclick={bulkRegister}
            class="mt-6 inline-flex items-center gap-2 bg-slate-900 dark:bg-blue-600 text-white font-semibold text-sm px-6 py-3.5 rounded-2xl shadow-md hover:bg-slate-800 dark:hover:bg-blue-500 transition-all group relative"
        >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Bulk Register All {p.neighboring_rights_artists} Artists
            <span class="group-hover:translate-x-1 transition-transform inline-block">&rarr;</span>
        </button>
    </div>

    <!-- KPI stack -->
    <div class="flex flex-col gap-6">
        <div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-6 transition-all hover:shadow-md">
            <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-widest font-semibold mb-2">Roster YTD Earnings</p>
            <p class="text-3xl font-light text-slate-900 dark:text-white tracking-tighter">{fmt(p.total_ytd)}</p>
        </div>
        <div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-6 transition-all hover:shadow-md">
            <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-widest font-semibold mb-2">Artists Under Management</p>
            <p class="text-3xl font-light text-slate-900 dark:text-white tracking-tighter">{p.total_artists}</p>
            <p class="text-xs text-slate-400 mt-1">{p.neighboring_rights_artists} with open registration gaps</p>
        </div>
    </div>
</div>

<!-- Recovery forecast + per-category gap breakdown -->
{#if forecast?.categories?.length}
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <!-- Per-category gap breakdown -->
    <div class="lg:col-span-2 bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 transition-all hover:shadow-md">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3">
                <span class="w-2 h-8 rounded-full bg-amber-500/20 block"></span>
                Gap Breakdown by Category
            </h2>
            <span class="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full text-xs font-medium tracking-wide">
                {forecast.artists_with_gaps} artists with gaps
            </span>
        </div>
        <div class="space-y-5">
            {#each forecast.categories as c (c.type)}
                <div>
                    <div class="flex items-baseline justify-between mb-1.5">
                        <div class="flex items-center gap-2">
                            <span class="px-2 py-0.5 rounded-md border text-[11px] font-medium {gapColor(c.type)}">{c.label}</span>
                            <span class="text-xs text-slate-400">{c.artists_affected} artists · ~{c.recovery_months}mo to recover</span>
                        </div>
                        <span class="text-sm font-semibold text-slate-800 dark:text-slate-100 tabular-nums">{fmt(c.recoverable)}</span>
                    </div>
                    <div class="h-2 w-full rounded-full bg-slate-100 dark:bg-slate-700/50 overflow-hidden">
                        <div
                            class="h-full rounded-full bg-gradient-to-r from-rose-400 to-rose-500 dark:from-rose-500 dark:to-rose-400"
                            style="width: {Math.max(2, (c.recoverable / forecast.total_recoverable) * 100)}%"
                        ></div>
                    </div>
                </div>
            {/each}
        </div>
    </div>

    <!-- 12-month recovery forecast -->
    <div class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-6 flex flex-col transition-all hover:shadow-md">
        <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-widest font-semibold mb-1">12-Month Recovery Forecast</p>
        <p class="text-3xl font-light text-slate-900 dark:text-white tracking-tighter">{fmt(forecast.total_recoverable)}</p>
        <p class="text-xs text-slate-400 mb-3">projected recovered if bulk registration starts now</p>
        <div class="relative flex-1 min-h-[120px]">
            <svg viewBox="0 0 100 100" preserveAspectRatio="none" class="absolute inset-0 w-full h-full">
                <defs>
                    <linearGradient id="fc-grad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="rgb(16 185 129)" stop-opacity="0.25" />
                        <stop offset="100%" stop-color="rgb(16 185 129)" stop-opacity="0" />
                    </linearGradient>
                </defs>
                <path d={curve.area} fill="url(#fc-grad)" />
                <path d={curve.line} fill="none" stroke="rgb(16 185 129)" stroke-width="1.5" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round" />
            </svg>
        </div>
        <div class="flex justify-between text-[11px] text-slate-400 mt-2 font-medium">
            <span>Now</span>
            <span>Month 6</span>
            <span>Month 12</span>
        </div>
    </div>
</div>
{/if}

<!-- Roster table + chat -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Roster table -->
    <div class="lg:col-span-2 bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 transition-all hover:shadow-md">
        <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3">
                <span class="w-2 h-8 rounded-full bg-blue-500/20 block"></span>
                Catalog Roster
            </h2>
            <span class="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full text-xs font-medium tracking-wide">
                sorted by opportunity
            </span>
        </div>

        <div class="overflow-y-auto max-h-[520px] -mx-2 px-2">
            <table class="w-full text-sm">
                <thead class="sticky top-0 bg-white dark:bg-slate-800 z-10">
                    <tr class="text-left text-xs text-slate-400 uppercase tracking-widest">
                        <th class="font-semibold py-3 pl-2">Artist</th>
                        <th class="font-semibold py-3 text-right">YTD</th>
                        <th class="font-semibold py-3 pl-6">Gaps</th>
                        <th class="font-semibold py-3 text-right pr-2">Uncollected</th>
                    </tr>
                </thead>
                <tbody>
                    {#each roster as a (a.id)}
                        <tr class="border-t border-slate-100 dark:border-slate-700/50 hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors">
                            <td class="py-3.5 pl-2">
                                <div class="flex items-center gap-3">
                                    <div class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 flex items-center justify-center text-[11px] font-bold text-slate-600 dark:text-slate-300 flex-shrink-0">
                                        {a.name.split(' ').map((w: string) => w[0]).join('').slice(0,2)}
                                    </div>
                                    <span class="font-medium text-slate-800 dark:text-slate-100">{a.name}</span>
                                </div>
                            </td>
                            <td class="py-3.5 text-right tabular-nums text-slate-500 dark:text-slate-400">{fmt(a.ytd_earnings)}</td>
                            <td class="py-3.5 pl-6">
                                {#if a.gaps.length === 0}
                                    <span class="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> All clear
                                    </span>
                                {:else}
                                    <div class="flex flex-wrap gap-1.5">
                                        {#each a.gaps as g}
                                            <span class="px-2 py-0.5 rounded-md border text-[11px] font-medium {gapColor(g.type)}">{g.organization}</span>
                                        {/each}
                                    </div>
                                {/if}
                            </td>
                            <td class="py-3.5 text-right tabular-nums pr-2">
                                {#if a.total_uncollected > 0}
                                    <span class="font-semibold text-rose-600 dark:text-rose-400">{fmtCents(a.total_uncollected)}</span>
                                {:else}
                                    <span class="text-slate-300 dark:text-slate-600">—</span>
                                {/if}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>

    <!-- LabelAgent chat -->
    <div id="label-chat" class="lg:col-span-1 h-[600px]">
        <LabelAgentChat bind:this={chat} />
    </div>
</div>
