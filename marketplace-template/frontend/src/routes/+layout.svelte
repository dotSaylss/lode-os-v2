<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<main class="v3-main">
	{@render children()}
</main>
