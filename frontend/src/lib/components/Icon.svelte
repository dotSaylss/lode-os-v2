<script lang="ts">
	/**
	 * Thin Lucide wrapper for the LodeOS v3 look: stroke-width 1.5, 20px default.
	 * Icons are statically imported (tree-shaken, SSR-safe). Add new names to the
	 * `icons` map below as needed.
	 */
	import Sun from '@lucide/svelte/icons/sun';
	import AudioLines from '@lucide/svelte/icons/audio-lines';
	import Waypoints from '@lucide/svelte/icons/waypoints';
	import Settings2 from '@lucide/svelte/icons/settings-2';
	import Check from '@lucide/svelte/icons/check';
	import Clock from '@lucide/svelte/icons/clock';
	import Music from '@lucide/svelte/icons/music';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import ArrowUp from '@lucide/svelte/icons/arrow-up';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ArrowLeftRight from '@lucide/svelte/icons/arrow-left-right';
	import Wrench from '@lucide/svelte/icons/wrench';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import BadgeCheck from '@lucide/svelte/icons/badge-check';
	import Star from '@lucide/svelte/icons/star';
	import Link from '@lucide/svelte/icons/link';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import Plus from '@lucide/svelte/icons/plus';
	import Coins from '@lucide/svelte/icons/coins';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import FilePen from '@lucide/svelte/icons/file-pen';
	import SearchX from '@lucide/svelte/icons/search-x';
	import Paperclip from '@lucide/svelte/icons/paperclip';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import Send from '@lucide/svelte/icons/send';
	import Pin from '@lucide/svelte/icons/pin';
	import PinOff from '@lucide/svelte/icons/pin-off';
	import Users from '@lucide/svelte/icons/users-round';
	import Library from '@lucide/svelte/icons/library-big';
	import Activity from '@lucide/svelte/icons/activity';
	import Handshake from '@lucide/svelte/icons/handshake';
	import PanelLeftOpen from '@lucide/svelte/icons/panel-left-open';
	import PanelLeftClose from '@lucide/svelte/icons/panel-left-close';
	import Plug from '@lucide/svelte/icons/plug-zap';
	import CircleCheck from '@lucide/svelte/icons/circle-check-big';
	import Gem from '@lucide/svelte/icons/gem';
	import Zap from '@lucide/svelte/icons/zap';

	const icons: Record<string, any> = {
		sun: Sun,
		'audio-lines': AudioLines,
		waypoints: Waypoints,
		'settings-2': Settings2,
		check: Check,
		clock: Clock,
		music: Music,
		'chevron-right': ChevronRight,
		'arrow-up': ArrowUp,
		'arrow-right': ArrowRight,
		'arrow-left': ArrowLeft,
		'arrow-left-right': ArrowLeftRight,
		wrench: Wrench,
		'shield-check': ShieldCheck,
		'badge-check': BadgeCheck,
		star: Star,
		link: Link,
		sparkles: Sparkles,
		plus: Plus,
		coins: Coins,
		'trending-up': TrendingUp,
		'file-pen': FilePen,
		'search-x': SearchX,
		paperclip: Paperclip,
		'triangle-alert': TriangleAlert,
		send: Send,
		pin: Pin,
		'pin-off': PinOff,
		users: Users,
		library: Library,
		activity: Activity,
		handshake: Handshake,
		'panel-left-open': PanelLeftOpen,
		'panel-left-close': PanelLeftClose,
		plug: Plug,
		'circle-check': CircleCheck,
		gem: Gem,
		zap: Zap
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
