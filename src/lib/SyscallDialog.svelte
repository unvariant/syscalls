<script lang="ts">
	import type { Syscall } from '$lib';
	import { createDialog, melt } from '@melt-ui/svelte';
	import { Icon, XMark } from 'svelte-hero-icons';
	import { fade, fly } from 'svelte/transition';

	export let syscall: Syscall;
	export let version: string;

	const {
		elements: { trigger, overlay, content, title, description, close, portalled },
		states: { open }
	} = createDialog();
</script>

<button use:melt={$trigger}>{syscall.name}</button>

<div use:melt={$portalled}>
	{#if $open}
		<div
			use:melt={$overlay}
			class="fixed inset-0 z-50 bg-black/20 dark:bg-white/10"
			transition:fade={{
				duration: 150
			}}
		/>
		<div
			use:melt={$content}
			class="fixed left-[50%] top-[50%] z-50 max-h-[85vh] w-[90vw]
            max-w-[450px] translate-x-[-50%] translate-y-[-50%] rounded-lg bg-white dark:bg-black
            p-6 dark:text-white border dark:border-neutral-800 border-slate-100"
			transition:fly={{
				duration: 300,
				y: 10,
				opacity: 0
			}}
		>
			<h2 use:melt={$title} class="m-0 text-lg font-bold dark:text-white">{syscall.name}</h2>
			<div use:melt={$description} class="mt-4">
				{#each syscall.args as { fulltype, name }, i}
					<div
						class="py-2 border-b dark:border-neutral-800 border-slate-100 {i == 0
							? 'border-t'
							: ''}"
					>
						<span class="font-semibold whitespace-nowrap">{fulltype}</span>
						<span class="text-slate-500 dark:text-neutral-400">{name}</span>
					</div>
				{/each}
			</div>
			<h3 class="m-0 mt-6 mb-2 text-lg font-bold dark:text-white">References</h3>
			{#if syscall.path !== 'undetermined'}
				<a
					href="https://elixir.bootlin.com/linux/{version}/source/{syscall.path}#L{syscall.line}"
					target="_blank"
					class="text-blue-500 underline dark:text-blue-300"
				>
					Elixir Cross Referencer
				</a>
			{/if}
			<button
				use:melt={$close}
				aria-label="close"
				class="absolute inline-flex items-center justify-center w-6 h-6 p-1 rounded-full appearance-none right-4 top-4 hover:bg-slate-100 focus:shadow-slate-400 dark:hover:bg-neutral-800 dark:focus:shadow-neutral-500"
			>
				<Icon src={XMark} class="w-4 h-4 dark:text-white" />
			</button>
		</div>
	{/if}
</div>

<!-- 							{#if path != 'undetermined'}
								<a
									href="https://elixir.bootlin.com/linux/{data.version}/source/{path}#L{line}"
									target="_blank"
								>
									{name}
								</a>
							{:else}
								{name}
							{/if} -->
