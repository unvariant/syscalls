<script lang="ts">
	export let labelText: string;
	export let options: { [key: string]: string[] };
  export let defaultVal: string;
	import { createSelect, melt } from '@melt-ui/svelte';
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
		defaultValue: defaultVal
	});
</script>

<div class="flex flex-col gap-1">
	<!-- svelte-ignore a11y-label-has-associated-control - $label contains the 'for' attribute -->
	<label class="block text-sm font-medium text-slate-600" use:melt={$label}>{labelText}</label>
	<button
		class="flex items-center justify-between h-10 px-3 py-2 transition-opacity bg-white border rounded-md text-slate-700 hover:opacity-90 border-slate-300 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
		use:melt={$trigger}
		aria-label={labelText}
	>
		{$valueLabel || "Loading..."}
		<!-- <ChevronDown class="square-5" /> -->
	</button>
	{#if $open}
		<div
			class="z-10 flex max-h-[300px] flex-col
      overflow-y-auto rounded-md bg-white
      p-1 focus:!ring-0 border border-slate-300 font-mono"
			use:melt={$menu}
			transition:fly={{ duration: 150, y: -5 }}
		>
			{#each Object.entries(options) as [key, arr]}
				<div use:melt={$group(key)}>
					<div
						class="py-1 pl-4 pr-4 font-semibold text-neutral-800"
						use:melt={$groupLabel(key)}
					>
						{key}
					</div>
					{#each arr as item}
						<div
							class="relative cursor-pointer rounded-md py-1 pl-8 pr-4 text-neutral-800
              focus:z-10 focus:text-magnum-700
            data-[highlighted]:bg-magnum-50 data-[selected]:bg-magnum-100
            data-[highlighted]:text-magnum-900 data-[selected]:text-magnum-900"
							use:melt={$option({ value: item, label: item })}
						>
							{#if $isSelected(item)}
								<div class="check">
									<!--  <Check class="square-4" /> -->
								</div>
							{/if}
							{item}
						</div>
					{/each}
				</div>
			{/each}
		</div>
	{/if}
</div>
