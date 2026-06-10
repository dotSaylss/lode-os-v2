<script lang="ts">
	import Icon from '$lib/components/Icon.svelte';

	// Renders the workspace's connected library (e.g. Kai's Untitled playlists)
	// so the catalog the agents pitch from is the same one the user can see.
	// `onPitch(track)` hands the cross-connector ask (library → Disco) to the orb.
	let { context, onPitch } = $props();

	const lib = $derived(context?.library);
	const tracks = $derived(context?.tracks ?? []);
	const groups = $derived(
		(lib?.playlists ?? [])
			.map((name: string) => ({
				name,
				tracks: tracks.filter((t: any) => t.playlist === name)
			}))
			.filter((g: { tracks: any[] }) => g.tracks.length)
	);

	const released = (iso: string) =>
		new Date(iso + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', year: 'numeric' });

	const soundLine = (t: any) =>
		t.sound ? `${t.sound.genres.join(' · ')} — ${t.sound.tempo}, ${t.sound.vocals}` : '';
</script>

{#if lib && groups.length}
	<div class="lib-card">
		<div class="lib-head">
			<span class="eyebrow">Your library</span>
			<a class="lib-source" href={`/connectors/${lib.connector}`}>
				<Icon name="library" size={14} />
				Synced from {lib.name}
				<span class="lib-dot"></span>
			</a>
		</div>

		{#each groups as group}
			<div class="lib-playlist">
				<div class="lib-playlist-head">
					<Icon name="music" size={13} class="lib-playlist-icon" />
					<span class="lib-playlist-name">{group.name}</span>
					<span class="lib-playlist-count">{group.tracks.length}</span>
				</div>
				<ul class="lib-rows">
					{#each group.tracks as track}
						<li class="lib-row">
							<div class="lib-row-main">
								<span class="lib-title">{track.title}</span>
								<span class="lib-meta">{soundLine(track)}</span>
							</div>
							<span class="lib-released">{released(track.released)}</span>
							<button
								class="lib-pitch"
								onclick={() => onPitch?.(track)}
								title={`Ask Lode to pitch "${track.title}" into Disco's live briefs`}
							>
								<Icon name="send" size={13} />
								Pitch via Disco
							</button>
						</li>
					{/each}
				</ul>
			</div>
		{/each}
	</div>
{/if}

<style>
	.lib-card {
		background: var(--paper-0);
		border: 1px solid var(--paper-200);
		border-radius: var(--r-2xl);
		box-shadow: var(--v3-sh-md);
		padding: 30px 32px;
	}
	.lib-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 18px;
	}
	.lib-source {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		font-size: 12px;
		font-weight: 500;
		color: var(--ink-500);
		background: var(--paper-100);
		border-radius: var(--r-pill);
		padding: 5px 13px;
		text-decoration: none;
		transition: color 0.15s ease;
	}
	.lib-source:hover {
		color: var(--ink-900);
	}
	.lib-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--sg-500);
	}
	.lib-playlist + .lib-playlist {
		margin-top: 20px;
	}
	.lib-playlist-head {
		display: flex;
		align-items: center;
		gap: 7px;
		padding-bottom: 8px;
		border-bottom: 1px solid var(--paper-200);
		color: var(--ink-500);
	}
	.lib-playlist-name {
		font-size: 12.5px;
		font-weight: 600;
		letter-spacing: 0.02em;
		color: var(--ink-700);
	}
	.lib-playlist-count {
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--ink-muted);
		background: var(--paper-100);
		border-radius: var(--r-pill);
		padding: 2px 8px;
	}
	.lib-rows {
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.lib-row {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 11px 10px;
		margin: 0 -10px;
		border-radius: var(--r-sm);
		transition: background 0.15s ease;
	}
	.lib-row:hover {
		background: var(--paper-50);
	}
	.lib-row + .lib-row {
		border-top: 1px solid var(--paper-100);
	}
	.lib-row-main {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
		flex: 1;
	}
	.lib-title {
		font-size: 14px;
		font-weight: 600;
		color: var(--ink-900);
	}
	.lib-meta {
		font-size: 12px;
		color: var(--ink-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.lib-released {
		font-family: var(--font-mono);
		font-size: 11.5px;
		color: var(--ink-muted);
		white-space: nowrap;
	}
	.lib-pitch {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		font-weight: 600;
		color: var(--ink-500);
		background: transparent;
		border: 1px solid var(--paper-200);
		border-radius: var(--r-pill);
		padding: 6px 12px;
		cursor: pointer;
		white-space: nowrap;
		transition:
			color 0.15s ease,
			border-color 0.15s ease,
			background 0.15s ease;
	}
	.lib-row:hover .lib-pitch,
	.lib-pitch:hover {
		color: var(--sg-600);
		border-color: var(--sg-300);
		background: var(--sg-50);
	}
</style>
