<script lang="ts">
	import type { PageData } from './$types';
	import searchTerm from '$lib/search';
	import Fuse from 'fuse.js';
	export let data: PageData;
	let lst = Object.entries(data).map(([name, nr]) => ({ name, nr }));
	const fuse = new Fuse(lst, { keys: ['name', 'nr'], threshold: 0.3 });
</script>

<table class="w-full overflow-hidden border-collapse rounded-md table-auto">
	<thead class="sticky top-0 h-16 text-lg bg-slate-100">
		<tr>
			<th>nr</th>
			<th>name</th>
		</tr>
	</thead>
	<tbody>
		{#each $searchTerm ? fuse.search($searchTerm).map((x) => x.item) : lst as { name, nr }}
			<tr>
				<td class="px-1.5 py-2 text-center border-r border-b w-16">{nr}</td>
				<td class="px-3 py-2 border-b">{name}</td>
			</tr>
		{/each}
	</tbody>
</table>
