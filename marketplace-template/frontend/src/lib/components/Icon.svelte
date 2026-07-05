<script lang="ts">
	/**
	 * Thin Lucide wrapper: stroke-width 1.5, 20px default. Icons are statically
	 * imported (tree-shaken, SSR-safe). Add new names to the `icons` map below.
	 */
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import ArrowUp from '@lucide/svelte/icons/arrow-up';
	import ListFilter from '@lucide/svelte/icons/list-filter';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import BadgeCheck from '@lucide/svelte/icons/badge-check';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import Star from '@lucide/svelte/icons/star';
	import Link from '@lucide/svelte/icons/link';
	import MessageCircle from '@lucide/svelte/icons/message-circle';

	const icons: Record<string, any> = {
		'arrow-right': ArrowRight,
		'arrow-up': ArrowUp,
		'list-filter': ListFilter,
		check: Check,
		x: X,
		'badge-check': BadgeCheck,
		'shield-check': ShieldCheck,
		star: Star,
		link: Link,
		'message-circle': MessageCircle
	};

	let {
		name,
		size = 20,
		color = 'currentColor',
		strokeWidth = 1.5,
		class: klass = ''
	}: {
		name: string;
		size?: number;
		color?: string;
		strokeWidth?: number;
		class?: string;
	} = $props();

	const Cmp = $derived(icons[name] ?? null);
</script>

{#if Cmp}
	<Cmp {size} {color} {strokeWidth} class={klass} />
{/if}
