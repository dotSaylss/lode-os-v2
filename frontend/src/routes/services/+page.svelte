<script lang="ts">
    import MatchmakerChat from '$lib/components/MatchmakerChat.svelte';

    let { data } = $props();

    type Provider = {
        id: string;
        name: string;
        category: string;
        specialty: string;
        genres: string[];
        rating: number;
        reviews: number;
        turnaround: string;
        rate: string;
        location: string;
        verified: boolean;
        bio: string;
    };

    const providers: Provider[] = $derived(data.providers ?? []);

    let chat = $state<MatchmakerChat | null>(null);
    let brief = $state('');
    let activeCategory = $state<string>('all');

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

    // Soft, on-brand accent per category (matches existing slate/blue/indigo/rose/emerald system).
    const CATEGORY_ACCENT: Record<string, string> = {
        mixing: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-300',
        mastering: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-300',
        cover_art: 'bg-rose-50 text-rose-600 dark:bg-rose-900/20 dark:text-rose-300',
        vocal_production: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-300',
        sync_licensing: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20 dark:text-emerald-300',
        music_video: 'bg-amber-50 text-amber-600 dark:bg-amber-900/20 dark:text-amber-300',
        promotion: 'bg-sky-50 text-sky-600 dark:bg-sky-900/20 dark:text-sky-300',
        session_musician: 'bg-teal-50 text-teal-600 dark:bg-teal-900/20 dark:text-teal-300'
    };

    function label(cat: string) {
        return CATEGORY_LABELS[cat] ?? cat;
    }
    function accent(cat: string) {
        return CATEGORY_ACCENT[cat] ?? 'bg-slate-100 text-slate-600';
    }
    function initials(name: string) {
        return name
            .split(' ')
            .map((p) => p[0])
            .join('')
            .slice(0, 2)
            .toUpperCase();
    }

    const categories = $derived([
        'all',
        ...Array.from(new Set(providers.map((p) => p.category)))
    ]);

    const visibleProviders = $derived(
        activeCategory === 'all'
            ? providers
            : providers.filter((p) => p.category === activeCategory)
    );

    function runBrief() {
        const text = brief.trim();
        if (!text || !chat) return;
        chat.send(text);
        brief = '';
    }

    const examples = [
        'I need my track mixed, mastered, and cover art for a lo-fi hip-hop single.',
        'Assemble a team for a pop single: vocal production, mix, master, and a music video.',
        'Find me a mastering engineer, and check the live web for current going rates in 2026.'
    ];
</script>

<div class="mb-8">
    <h1 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
        Service Ecosystem
    </h1>
    <p class="text-slate-500 dark:text-slate-400 mt-1">
        Bring your song to life. Describe what it needs and the Matchmaker assembles a vetted team —
        grounded in the provider marketplace.
    </p>
</div>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:h-[calc(100vh-13rem)]">
    <!-- Left: Brief + marketplace -->
    <div class="lg:col-span-2 flex flex-col gap-6 lg:overflow-y-auto lg:pr-1">
        <!-- Brief composer -->
        <div
            class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 transition-all hover:shadow-md"
        >
            <h2
                class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3 mb-5"
            >
                <span class="w-2 h-8 rounded-full bg-indigo-500/20 block"></span>
                Describe your song's needs
            </h2>
            <form
                onsubmit={(e) => {
                    e.preventDefault();
                    runBrief();
                }}
                class="flex flex-col gap-4"
            >
                <textarea
                    bind:value={brief}
                    rows="3"
                    placeholder="e.g. I need my track mixed, mastered, and cover art for a lo-fi hip-hop single."
                    class="w-full bg-[#f4f4f5] dark:bg-slate-900 border border-slate-200/50 dark:border-slate-700 rounded-2xl px-5 py-4 text-[15px] leading-relaxed focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all dark:text-white outline-none placeholder:text-slate-400 resize-none"
                ></textarea>
                <div class="flex items-center justify-between gap-4 flex-wrap">
                    <div class="flex flex-wrap gap-2">
                        {#each examples as ex}
                            <button
                                type="button"
                                onclick={() => (brief = ex)}
                                class="text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-3 py-1.5 rounded-full transition-colors"
                            >
                                {ex.length > 38 ? ex.slice(0, 38) + '…' : ex}
                            </button>
                        {/each}
                    </div>
                    <button
                        type="submit"
                        disabled={!brief.trim()}
                        class="shrink-0 px-6 py-2.5 rounded-full bg-slate-800 dark:bg-indigo-600 text-white text-sm font-semibold flex items-center gap-2 hover:bg-slate-700 dark:hover:bg-indigo-500 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Find my team
                        <span>&rarr;</span>
                    </button>
                </div>
            </form>
        </div>

        <!-- Marketplace -->
        <div
            class="bg-white dark:bg-slate-800/50 backdrop-blur-xl rounded-3xl shadow-sm border border-slate-200/60 dark:border-slate-700 p-8 transition-all hover:shadow-md"
        >
            <div class="flex items-center justify-between mb-6">
                <h2
                    class="text-xl font-medium tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-3"
                >
                    <span class="w-2 h-8 rounded-full bg-blue-500/20 block"></span>
                    Vetted Marketplace
                </h2>
                <span
                    class="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded-full text-xs font-medium tracking-wide"
                >
                    {providers.length} providers
                </span>
            </div>

            <!-- Category filter -->
            <div class="flex flex-wrap gap-2 mb-6">
                {#each categories as cat}
                    <button
                        onclick={() => (activeCategory = cat)}
                        class="text-xs font-semibold px-3.5 py-1.5 rounded-full border transition-all {activeCategory ===
                        cat
                            ? 'bg-slate-800 dark:bg-indigo-600 text-white border-transparent shadow-sm'
                            : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'}"
                    >
                        {cat === 'all' ? 'All' : label(cat)}
                    </button>
                {/each}
            </div>

            {#if visibleProviders.length === 0}
                <div
                    class="p-6 text-center border border-dashed border-slate-300 dark:border-slate-700 rounded-2xl"
                >
                    <p class="text-sm font-medium text-slate-500 dark:text-slate-400">
                        No providers loaded. Is the backend running on port 8002?
                    </p>
                </div>
            {:else}
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {#each visibleProviders as p (p.id)}
                        <div
                            class="group flex flex-col p-5 bg-[#fcfcfc] dark:bg-slate-800/80 border border-slate-200/70 dark:border-slate-700 rounded-2xl transition-all hover:shadow-md hover:border-slate-300 dark:hover:border-slate-600"
                        >
                            <div class="flex items-start gap-3">
                                <div
                                    class="shrink-0 w-11 h-11 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-sm"
                                >
                                    {initials(p.name)}
                                </div>
                                <div class="min-w-0 flex-1">
                                    <div class="flex items-center gap-1.5">
                                        <h3
                                            class="text-[15px] font-semibold text-slate-800 dark:text-white tracking-tight truncate"
                                        >
                                            {p.name}
                                        </h3>
                                        {#if p.verified}
                                            <svg
                                                class="w-4 h-4 text-blue-500 shrink-0"
                                                fill="currentColor"
                                                viewBox="0 0 20 20"
                                                aria-label="Verified"
                                            >
                                                <path
                                                    fill-rule="evenodd"
                                                    d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                                    clip-rule="evenodd"
                                                />
                                            </svg>
                                        {/if}
                                    </div>
                                    <span
                                        class="inline-block mt-1 text-[11px] font-semibold px-2 py-0.5 rounded-full {accent(
                                            p.category
                                        )}"
                                    >
                                        {label(p.category)}
                                    </span>
                                </div>
                                <div class="text-right shrink-0">
                                    <div
                                        class="flex items-center gap-1 text-sm font-semibold text-slate-800 dark:text-white"
                                    >
                                        <svg
                                            class="w-3.5 h-3.5 text-amber-400"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                                            />
                                        </svg>
                                        {p.rating}
                                    </div>
                                    <p class="text-[11px] text-slate-400">{p.reviews} reviews</p>
                                </div>
                            </div>

                            <p
                                class="mt-3 text-[13px] text-slate-600 dark:text-slate-300 leading-relaxed"
                            >
                                {p.specialty}
                            </p>

                            <div class="mt-3 flex flex-wrap gap-1.5">
                                {#each p.genres.slice(0, 3) as g}
                                    <span
                                        class="text-[10.5px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-700/50 px-2 py-0.5 rounded-md"
                                    >
                                        {g}
                                    </span>
                                {/each}
                            </div>

                            <div
                                class="mt-4 pt-3 border-t border-slate-200/70 dark:border-slate-700 flex items-center justify-between text-xs"
                            >
                                <span class="font-semibold text-slate-700 dark:text-slate-200">
                                    {p.rate}
                                </span>
                                <span class="text-slate-400 dark:text-slate-500">
                                    {p.turnaround}
                                </span>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>

    <!-- Right: Matchmaker chat -->
    <div class="lg:col-span-1 h-full min-h-[500px]">
        <MatchmakerChat bind:this={chat} />
    </div>
</div>
