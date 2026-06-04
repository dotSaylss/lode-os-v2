<script lang="ts">
    import FinancialOverview from '$lib/components/FinancialOverview.svelte';
    import ActionItems from '$lib/components/ActionItems.svelte';
    import AgentChat from '$lib/components/AgentChat.svelte';
    
    let { data } = $props();
</script>

<div class="mb-8">
    <h1 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">Overview</h1>
    <p class="text-slate-500 dark:text-slate-400 mt-1">Manage your artists and royalty flows.</p>
</div>

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:h-[calc(100vh-16rem)]">
    <!-- Left Column: Financials & Actions -->
    <div class="lg:col-span-2 flex flex-col gap-6">
        <FinancialOverview context={data.artistContext} />
        <ActionItems context={data.artistContext} />
    </div>

    <!-- Right Column: Agent Chat -->
    <div class="lg:col-span-1 h-full min-h-[500px]">
        <AgentChat />
    </div>
</div>
