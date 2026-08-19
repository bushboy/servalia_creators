/** Role-aware sidebar labels. */
export function navLabelsForRoles(roles: string[] | undefined): string[] {
  const list = roles || [];
  const isAdmin = list.includes('admin');
  const isOperator = isAdmin || list.includes('operator');
  const labels = ['Home', 'Library'];
  if (isOperator) labels.push('Audit');
  if (isAdmin) {
    labels.push('Settings');
    labels.push('Tenants');
  }
  return labels;
}

export function roleFlags(roles: string[] | undefined) {
  const list = roles || [];
  const isAdmin = list.includes('admin');
  const isOperator = isAdmin || list.includes('operator');
  return { isAdmin, isOperator };
}
