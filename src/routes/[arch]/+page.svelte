<script lang="ts">
	import type { PageData } from './$types';
	import searchTerm from '$lib/search';
	import Fuse from 'fuse.js';
	import { FaceFrown, Icon } from 'svelte-hero-icons';
	let swapNumberFormat = false;
	export let data: PageData;
	let registers = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9'];
	// return a nice looking message when no keys are found
	$: fuse = new Fuse(data.syscalls, {
		keys: [
			{ name: 'name', weight: 0.5 },
			{ name: 'nr', weight: 0.01, },
			{
				name: 'args',
				getFn: (syscall) =>
					(syscall as any).args.map((arg: { fulltype: string; search: string, name: string }) => `${arg.fulltype} ${arg.name}`),
				weight: 0.5,
			},
			{ name: 'path', weight: 0.01, },
			{ name: 'line', weight: 0.01, },
		],
		threshold: 0.3
	});
	const padArrayRight = <T>(array: T[], length: number, fillWith: T) =>
		array.concat(new Array(length).fill(fillWith)).slice(0, length);
	const modifiers = ["struct", "union", "enum", "unsigned"];
	const splitType = (type: string) => {
		let last2 = "";
		let rest = type;
		let modifier = "";
		if (rest.endsWith("*")) {
			last2 = rest.split(' ').splice(-2).join(' ');
			rest = rest.slice(0, rest.length - last2.length);
		}

		for (const mod of modifiers) {
			if (rest.startsWith(`${mod} `)) {
				modifier = `${mod} `;
				rest = rest.slice(modifier.length);
				break;
			}
		}

		return { modifier, rest, last2 };
	};

	$: searchResults = $searchTerm ? fuse.search($searchTerm).map((x) => x.item) : data.syscalls;
</script>

<svelte:body
	on:keyup={(e) => {
		if (e.key === 'H' && e.shiftKey) {
			swapNumberFormat = !swapNumberFormat;
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
					{#each registers as r}
						<th>{r}</th>
					{/each}
				</tr>
			</thead>
			<tbody class="border border-white">
				{#each searchResults as { name, nr, args, path, line }}
					<tr>
						<td
							class="px-1.5 py-2 text-center border w-16 border-slate-100 dark:border-neutral-800"
						>
							{nr > 1023 !== swapNumberFormat ? '0x' + nr.toString(16) : nr}
						</td>
						<td class="px-3 py-2 border dark:border-neutral-800 border-slate-100">
							{#if path != 'undetermined'}
								<a
									href="https://elixir.bootlin.com/linux/v6.5-rc6/source/{path}#L{line}"
									target="_blank">{name}</a
								>
							{:else}
								{name}
							{/if}
						</td>
						{#each padArrayRight( args, 6, { fulltype: '', search: '', name: ''} ) as { fulltype, search, name}}
							{@const { modifier, rest, last2 } = splitType(fulltype) }
							<td
								class="px-3 py-2 border border-l-0 dark:border-neutral-800 border-slate-100"
							>
								<a
									href="https://elixir.bootlin.com/linux/v6.5-rc6/C/ident/{search}"
									target="_blank"
								>
									<span class="font-semibold dark:text-neutral-200 text-xs">{ modifier }</span>
									<span class="font-semibold">{ rest }</span>
									<span class="font-semibold whitespace-nowrap">{ last2 }</span>
									<br>
									<span class="text-slate-500 dark:text-neutral-400 block">{name}</span>
								</a>
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	{:else}
		<div class="flex items-center justify-center h-full">
			<div class="m-auto">
				<p class="text-xl font-semibold text-center text-slate-500 dark:text-neutral-400">
					No Results Found
				</p>
				<Icon src={FaceFrown} class="w-64 h-64 m-auto text-slate-400 dark:text-neutral-500" />
			</div>
		</div>
	{/if}
</div>
