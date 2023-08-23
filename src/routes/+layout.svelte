<script lang="ts">
	import Select from '$lib/Select.svelte';
	import '../app.css';
	import { createLabel, melt } from '@melt-ui/svelte';
	import searchTerm from '$lib/search';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	const {
		elements: { root }
	} = createLabel();

	const arches = {
		x86: ['x86-32', 'x86-64', 'x86-x32'],
		arm: ['arm-generic', 'arm-eabi', 'arm-oabi', 'arm64-generic']
	};

	const versions = {
		v5: ['latest']
	};
</script>

<div class="mx-8 font-mono">
	<nav class="mb-4">
		<div>
			<h1 class="mt-8 text-lg font-bold">syscalls</h1>
		</div>
		<div class="grid grid-cols-5 gap-2 mt-8">
			<Select
				labelText="Arch"
				options={arches}
				defaultVal={new URL($page.url).pathname.substring(1) || "x86-64"}
				onValueChange={({ next }) => {
					goto(`/${next}`, { invalidateAll: true, noScroll: true });
					return next;
				}}
			/>
			<Select labelText="Version" options={versions} defaultVal="latest" />
			<div />
			<div class="flex flex-col col-span-2 gap-1">
				<label
					use:melt={$root}
					for="search"
					class="block text-sm font-medium text-slate-600"
					data-melt-part="root"
				>
					<span>Search</span>
				</label>
				<input
					bind:value={$searchTerm}
					type="search"
					id="search"
					class="h-10 px-3 py-2 border rounded-md text-slate-700 border-slate-300 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
					placeholder="Search"
				/>
			</div>
		</div>
	</nav>

	<main>
		<slot />
	</main>
	<footer class="mt-16" />
</div>
