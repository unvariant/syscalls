<script>
	export let data;
</script>

<table>
	<!-- {#each data.all as [name, { path, line, args }] }
		<tr>
			<td>{name}</td>
			<td>{path}:{line}</td>
			<td>{args.map(arg => `${arg.type} ${arg.name}`)}</td>
		</tr>
	{/each} -->
</table>