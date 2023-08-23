<script lang="ts">
	import Select from '$lib/Select.svelte';
	import '../app.css';
	import { createLabel, melt } from '@melt-ui/svelte';
	import searchTerm from '$lib/search';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Icon, Moon, Sun } from 'svelte-hero-icons';
	let body: HTMLBodyElement | null;
	let darkMode = true;

	const bindBody = (node: any) => (body = node);

	$: darkMode && body ? body.classList.add('dark') : body?.classList.remove('dark');
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

<svelte:body use:bindBody />

<div class="transition-colors dark:text-neutral-100 dark:bg-black">
	<header class="mx-8">
		<nav class="mb-4">
			<div class="flex flex-row justify-between pt-8">
				<h1 class="text-lg font-bold">syscalls</h1>
				<button on:click={() => (darkMode = !darkMode)}><Icon src={darkMode ? Sun : Moon} class="w-6 h-6" /></button>
			</div>
			<div class="grid grid-cols-5 gap-2 mt-8">
				<Select
					labelText="Arch"
					options={arches}
					defaultVal={new URL($page.url).pathname.substring(1) || 'x86-64'}
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
						class="h-10 px-3 py-2 bg-white border rounded-md text-slate-700 dark:bg-black dark:text-slate-300 border-slate-300 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
						placeholder="Search"
					/>
				</div>
			</div>
		</nav>
	</header>
	<main>
		<slot />
	</main>
	<footer class="mt-16" />
</div>

<style lang="postcss">
	:global(html) {
		font-family: 'JetBrains Mono';
	}
</style>
