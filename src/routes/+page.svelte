<script lang="ts">
	import type { PageData } from './$types';
	import searchTerm from '$lib/search';
	import Fuse from 'fuse.js';
	let swapNumberFormat = false;
	export let data: PageData;
	let registers = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9'];
	$: fuse = new Fuse(data.syscalls, { keys: ['name', 'nr'], threshold: 0.3 });
	const padArrayRight = <T>(array: T[], length: number, fillWith: T) =>
		array.concat(new Array(length).fill(fillWith)).slice(0, length);
</script>

<svelte:body
	on:keydown={(e) => {
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

<div class="h-[82vh] overflow-x-scroll">
	<table class="border-collapse rounded-md table-auto">
		<thead class="sticky top-0 left-0 z-10 h-12 text-lg bg-slate-100 dark:bg-neutral-900">
			<tr>
				<th>nr</th>
				<th class="sticky left-0 z-20 bg-slate-100 dark:bg-neutral-900">name</th>
				{#each registers as r}
					<th>{r}</th>
				{/each}
			</tr>
		</thead>
		<tbody class="border border-white">
			{#each $searchTerm ? fuse
						.search($searchTerm)
						.map((x) => x.item) : data.syscalls as { name, nr, args }}
				<tr>
					<td class="px-1.5 py-2 text-center border w-16 border-slate-100 dark:border-neutral-800">
						{nr > 1023 !== swapNumberFormat ? '0x' + nr.toString(16) : nr}
					</td>
					<td
						class="sticky py-2 pl-3 bg-white border -left-[1px] dark:border-neutral-800 border-slate-100 dark:bg-black bg-clip-padding"
						>{name}</td
					>
					{#each padArrayRight(args, 6, ['', '']) as [type, name]}
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
	<footer class="pt-16" />
</div>
