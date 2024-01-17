<script lang="ts">
	import type { PageData } from './$types';
	import searchTerm from '$lib/search';
	import Fuse from 'fuse.js';
	import { FaceFrown, Icon } from 'svelte-hero-icons';
	let swapNumberFormat = false;
	export let data: PageData;
	// let registers = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9'];
	// return a nice looking message when no keys are found
	$: fuse = new Fuse(data.syscalls, { keys: ['name', 'nr', 'args'], threshold: 0.3 });
	const padArrayRight = <T>(array: T[], length: number, fillWith: T) =>
		array.concat(new Array(length).fill(fillWith)).slice(0, length);

	$: searchResults = $searchTerm ? fuse.search($searchTerm).map((x) => x.item) : data.syscalls;
</script>

<svelte:body
	on:keydown={(e) => {
		if (e.key === 'h') {
			swapNumberFormat = true;
		}
	}}
	on:keyup={(e) => {
		if (e.key === 'h') {
			swapNumberFormat = false;
		}
	}}
/>

<div class="h-full overflow-x-scroll">
	{#if searchResults.length !== 0}
		<table class="min-w-full border-collapse rounded-md table-auto">
			<thead class="sticky top-0 left-0 z-10 h-12 text-lg bg-slate-100 dark:bg-neutral-900">
				<tr>
					<th>nr</th>
					<th>name</th>
					<!-- {#each registers as r}
						<th>{r}</th>
					{/each} -->
				</tr>
			</thead>
			<tbody class="border border-white">
				{#each searchResults as { name, nr, args }}
					<tr>
						<td
							class="px-1.5 py-2 text-center border w-16 border-slate-100 dark:border-neutral-800"
						>
							{nr > 1023 !== swapNumberFormat ? '0x' + nr.toString(16) : nr}
						</td>
						<td class="px-3 py-2 border dark:border-neutral-800 border-slate-100">{name}</td>
						{#each padArrayRight(args, 0, ['', '']) as [type, name]}
							<td
								class="px-3 py-2 border border-l-0 dark:border-neutral-800 border-slate-100 whitespace-nowrap"
							>
								<span class="font-semibold">{type}</span>
								<span class="text-slate-500 dark:text-neutral-400">{name}</span>
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<div class="flex items-center justify-center h-full">
			<div class="m-auto">
				<p class="text-xl font-semibold text-center text-slate-500 dark:text-neutral-400">No Reuslts Found</p>
				<Icon src={FaceFrown} class="w-64 h-64 m-auto text-slate-400 dark:text-neutral-500" />
			</div>
		</div>
	{/if}
</div>
