export function exportRanking(run) {
  const blob = new Blob([JSON.stringify(run, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `ranking-${run.id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
