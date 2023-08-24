<script lang="ts">
	import type { PageData } from './$types';
	import searchTerm from '$lib/search';
	import Fuse from 'fuse.js';
	let swapNumberFormat = false;
	export let data: PageData;
	$: lst = Object.entries(data.syscalls).map(([name, nr]) => ({ name, nr }));
	$: fuse = new Fuse(lst, { keys: ['name', 'nr'], threshold: 0.3 });
</script>

<svelte:body
	on:keydown={(e) => {
		console.log(e);
		if (e.key === 'Enter') {
			swapNumberFormat = true;
		}
	}}
	on:keyup={(e) => {
		if (e.key === 'Enter') {
			swapNumberFormat = false;
		}
	}}
/>

<table class="w-full mr-8 overflow-x-scroll border-collapse rounded-md table-auto">
	<thead class="sticky top-0 h-12 text-lg bg-slate-100 dark:bg-neutral-900">
		<tr>
			<th>nr</th>
			<th>name</th>
		</tr>
	</thead>
	<tbody>
		{#each $searchTerm ? fuse.search($searchTerm).map((x) => x.item) : lst as { name, nr }}
			<tr>
				<td
					class="px-1.5 py-2 text-center border-r border-b w-16 border-slate-100 dark:border-neutral-800"
					>{nr > 1023 !== swapNumberFormat ? '0x' + nr.toString(16) : nr}</td
				>
				<td class="px-3 py-2 border-b dark:border-neutral-800 border-slate-100">{name}</td>
			</tr>
		{/each}
	</tbody>
</table>
