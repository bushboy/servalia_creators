import api from '@/lib/api';
import type {
  ApiKey,
  ApiKeyCreate,
  ApiKeySecret,
  ApiResponse,
  AuditEvent,
  Job,
  SystemEvent,
  Tenant,
  TenantCreateRequest,
  TenantDetails,
  TenantMembership,
  TenantMembershipCreate,
  TenantUpdate,
  VerticalInfo,
} from '@/types';

export async function fetchVerticals(): Promise<VerticalInfo[]> {
  const { data } = await api.get<VerticalInfo[]>('/verticals');
  return data;
}

export interface AuditFilters {
  customer_id?: string;
  vertical?: string;
  action?: string;
  agent_id?: string;
  limit?: number;
}

export async function fetchAuditEvents(
  filters: AuditFilters = {}
): Promise<AuditEvent[]> {
  const params = new URLSearchParams();
  if (filters.customer_id) params.set('customer_id', filters.customer_id);
  if (filters.vertical) params.set('vertical', filters.vertical);
  if (filters.action) params.set('action', filters.action);
  if (filters.agent_id) params.set('agent_id', filters.agent_id);
  if (filters.limit) params.set('limit', String(filters.limit));

  const { data } = await api.get<AuditEvent[]>(
    `/audit${params.toString() ? `?${params.toString()}` : ''}`
  );
  return data;
}

export async function fetchApiKeys(): Promise<ApiKey[]> {
  const { data } = await api.get<ApiKey[]>('/admin/api-keys');
  return data;
}

export async function createApiKey(
  payload: ApiKeyCreate
): Promise<ApiKeySecret> {
  const { data } = await api.post<ApiKeySecret>('/admin/api-keys', payload);
  return data;
}

export async function revokeApiKey(apiKeyId: string): Promise<void> {
  await api.delete(`/admin/api-keys/${apiKeyId}`);
}

export async function fetchMembers(): Promise<TenantMembership[]> {
  const { data } = await api.get<TenantMembership[]>('/admin/members');
  return data;
}

export async function createMember(
  payload: TenantMembershipCreate
): Promise<TenantMembership> {
  const { data } = await api.post<TenantMembership>('/admin/members', payload);
  return data;
}

export async function revokeMember(membershipId: string): Promise<void> {
  await api.delete(`/admin/members/${membershipId}`);
}

export async function fetchTenantDetails(): Promise<TenantDetails> {
  const { data } = await api.get<TenantDetails>('/admin/tenant');
  return data;
}

export async function updateTenantDetails(
  payload: TenantUpdate
): Promise<TenantDetails> {
  const { data } = await api.patch<TenantDetails>('/admin/tenant', payload);
  return data;
}

export async function fetchMyTenants(): Promise<Tenant[]> {
  const { data } = await api.get<ApiResponse<Tenant[]>>('/me/tenants');
  return data.data;
}

export async function createTenant(
  payload: TenantCreateRequest
): Promise<Tenant> {
  const { data } = await api.post<ApiResponse<Tenant>>('/tenants', payload);
  return data.data;
}

export async function fetchJobs(status?: string, limit = 100): Promise<Job[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  const { data } = await api.get<Job[]>(
    `/jobs${params.toString() ? `?${params.toString()}` : ''}`
  );
  return data;
}

export async function retryJob(jobId: string): Promise<Job> {
  const { data } = await api.post<Job>(`/jobs/${jobId}/retry`);
  return data;
}

export async function fetchSystemEvents(): Promise<SystemEvent[]> {
  const { data } = await api.get<SystemEvent[]>('/admin/system/events');
  return data;
}
