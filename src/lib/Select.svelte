<script lang="ts">
	export let labelText: string;
	export let options: { [key: string]: string[] };
	export let defaultVal: string;
	export let onValueChange: CreateSelectProps['onValueChange'] = ({ next }) => next;
	import { createSelect, melt, type CreateSelectProps } from '@melt-ui/svelte';
	import { Icon, ChevronDown, Check } from "svelte-hero-icons"
	import { fly } from 'svelte/transition';
	const {
		elements: { trigger, menu, option, group, groupLabel, label },
		states: { valueLabel, open },
		helpers: { isSelected }
	} = createSelect({
		forceVisible: true,
		positioning: {
			placement: 'bottom',
			fitViewport: true,
			sameWidth: true
		},
		defaultValue: defaultVal,
		onValueChange
	});
</script>

<div class="flex flex-col gap-1">
	<!-- svelte-ignore a11y-label-has-associated-control - $label contains the 'for' attribute -->
	<label class="block text-sm font-medium text-slate-600 dark:text-slate-400" use:melt={$label}
		>{labelText}</label
	>
	<button
		class="flex items-center justify-between h-10 px-3 py-2 transition-opacity bg-white border rounded-md dark:bg-black text-slate-700 dark:text-slate-300 hover:opacity-90 border-slate-300 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
		use:melt={$trigger}
		aria-label={labelText}
	>
		{$valueLabel || 'Unknown'}
		<Icon src={ChevronDown} class="w-5 h-5" />
	</button>
	{#if $open}
		<div
			class="z-10 flex max-h-[300px] flex-col
      overflow-y-auto rounded-md bg-white dark:bg-black
      p-1 focus:!ring-0 border border-neutral-300 dark:border-neutral-700 font-mono"
			use:melt={$menu}
			transition:fly={{ duration: 150, y: -5 }}
		>
			{#each Object.entries(options) as [key, arr]}
				<div use:melt={$group(key)}>
					<div
						class="py-1 pl-4 pr-4 font-semibold text-neutral-800 dark:text-neutral-200"
						use:melt={$groupLabel(key)}
					>
						{key}
					</div>
					{#each arr as item}
						<div
							class="relative cursor-pointer rounded-md py-1 pl-8 pr-4 text-neutral-800 dark:text-neutral-200
              focus:z-10 focus:text-slate-700
            data-[highlighted]:bg-slate-50 dark:data-[highlighted]:bg-neutral-900 data-[selected]:bg-slate-100 dark:data-[selected]:bg-neutral-800
            data-[highlighted]:text-slate-900 data-[selected]:text-slate-900"
							use:melt={$option({ value: item, label: item })}
						>
							{item}
						</div>
					{/each}
				</div>
			{/each}
		</div>
	{/if}
</div>
