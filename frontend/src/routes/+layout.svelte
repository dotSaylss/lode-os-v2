<script lang="ts">
    import '../app.css';
    import { page } from '$app/state';
    let { children } = $props();
</script>

<div class="min-h-screen bg-[#f8f9fa] text-slate-800 dark:bg-slate-900 dark:text-slate-100 font-sans transition-colors duration-300">
    <header class="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="font-bold text-xl tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                <div class="w-8 h-8 rounded-lg bg-blue-600 dark:bg-blue-500 flex items-center justify-center text-white font-black">M</div>
                <span>MOGUL <span class="text-slate-400 font-normal">Label Manager</span></span>
            </div>
            <nav class="flex gap-6 items-center">
                <a href="/" class="text-sm font-medium {page.url.pathname === '/' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'} transition-colors">Dashboard</a>
                <a href="/label" class="text-sm font-medium {page.url.pathname.startsWith('/label') ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'} transition-colors">Label</a>
                <a href="/services" class="text-sm font-medium {page.url.pathname.startsWith('/services') ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-800 dark:hover:text-white'} transition-colors">Services</a>
                <button class="text-sm font-medium text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors">Settings</button>
                <div class="w-px h-4 bg-slate-300 dark:bg-slate-700 mx-2"></div>
                <div class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 flex items-center justify-center text-xs font-bold text-slate-600 dark:text-slate-300">
                    JF
                </div>
            </nav>
        </div>
    </header>
    
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {@render children()}
    </main>
</div>
