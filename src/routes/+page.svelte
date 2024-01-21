<script lang="ts">
	import type { PageData } from './$types';
	import searchTerm from '$lib/search';
	import Fuse from 'fuse.js';
	import { FaceFrown, Icon } from 'svelte-hero-icons';
	import type { Arg, Syscall } from '$lib';
	import SyscallDialog from '$lib/SyscallDialog.svelte';
	let swapNumberFormat = false;
	export let data: PageData;
	let registers = ['rdi', 'rsi', 'rdx', 'r10', 'r8', 'r9'];
	// return a nice looking message when no keys are found
	$: fuse = new Fuse<Syscall>(data.syscalls, {
		keys: [
			{ name: 'name', weight: 0.6 },
			{ name: 'nr', weight: 0.01 },
			{
				name: 'args',
				getFn: (syscall) => syscall.args.map((arg: Arg) => `${arg.fulltype} ${arg.name}`),
				weight: 0.4
			},
			{ name: 'path', weight: 0.01 },
			{ name: 'line', weight: 0.01 }
		],
		threshold: 0.3
	});
	const padArrayRight = <T>(array: T[], length: number, fillWith: T) =>
		array.concat(new Array(length).fill(fillWith)).slice(0, length);
	const modifiers = ['struct', 'union', 'enum', 'unsigned'];
	const splitType = (type: string) => {
		let last2 = '';
		let rest = type;
		let modifier = '';
		if (rest.endsWith('*')) {
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
			e.preventDefault();
		}
	}}
/>

<div class="h-full overflow-x-auto">
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
				{#each searchResults as syscall}
					{@const { name, nr, args, path, line } = syscall}
					<tr>
						<td
							class="px-1.5 py-2 text-center border w-16 dark:border-neutral-800 border-slate-100"
						>
							{nr > 1023 !== swapNumberFormat ? '0x' + nr.toString(16) : nr}
						</td>
						<td
							class="min-w-0 px-3 py-2 border dark:border-neutral-800 border-slate-100 whitespace-nowrap"
						>
							<SyscallDialog {syscall} version={data.version}/>
						</td>
						{#each padArrayRight( args, 6, { fulltype: '', search: '', name: '' } ) as { fulltype, search, name }}
							{@const { modifier, rest, last2 } = splitType(fulltype)}
							<td
								class="min-w-0 px-3 py-2 border border-l-0 dark:border-neutral-800 border-slate-100"
							>
								<a
									href="https://elixir.bootlin.com/linux/{data.version}/C/ident/{search}"
									target="_blank"
								>
									<span class="text-xs font-semibold dark:text-neutral-200">{modifier}</span>
									<span class="font-semibold">{rest}</span>
									<span class="font-semibold whitespace-nowrap">{last2}</span>
									<br />
									<span class="block text-slate-500 dark:text-neutral-400">{name}</span>
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
