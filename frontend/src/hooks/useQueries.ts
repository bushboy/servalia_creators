import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { toast } from 'sonner';
import { getApiErrorMessage } from '@/lib/apiError';
import {
  AuditFilters,
  createApiKey,
  createMember,
  createTenant,
  fetchApiKeys,
  fetchAuditEvents,
  fetchJobs,
  fetchMembers,
  fetchMyTenants,
  fetchSystemEvents,
  fetchTenantDetails,
  fetchVerticals,
  revokeApiKey,
  revokeMember,
  retryJob,
  updateTenantDetails,
} from '@/lib/api/queries';
import type {
  ApiKeyCreate,
  TenantCreateRequest,
  TenantMembershipCreate,
  TenantUpdate,
} from '@/types';

export const VERTICALS_QUERY_KEY = 'verticals';
export const AUDIT_QUERY_KEY = 'audit';

function toastApiError(error: unknown, fallback: string) {
  toast.error(getApiErrorMessage(error, fallback));
}

export function useVerticals() {
  return useQuery({
    queryKey: [VERTICALS_QUERY_KEY],
    queryFn: fetchVerticals,
  });
}

export function useAuditEvents(filters: AuditFilters = {}) {
  return useQuery({
    queryKey: [AUDIT_QUERY_KEY, filters],
    queryFn: () => fetchAuditEvents(filters),
  });
}

export const API_KEYS_QUERY_KEY = 'api-keys';
export const MEMBERS_QUERY_KEY = 'members';
export const TENANT_DETAILS_QUERY_KEY = 'tenant-details';
export const MY_TENANTS_QUERY_KEY = 'my-tenants';

export function useApiKeys() {
  return useQuery({
    queryKey: [API_KEYS_QUERY_KEY],
    queryFn: fetchApiKeys,
  });
}

export function useCreateApiKeyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ApiKeyCreate) => createApiKey(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [API_KEYS_QUERY_KEY] });
      toast.success('API key created.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to create API key');
    },
  });
}

export function useRevokeApiKeyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (apiKeyId: string) => revokeApiKey(apiKeyId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [API_KEYS_QUERY_KEY] });
      toast.success('API key revoked.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to revoke API key');
    },
  });
}

export function useMembers() {
  return useQuery({
    queryKey: [MEMBERS_QUERY_KEY],
    queryFn: fetchMembers,
  });
}

export function useCreateMemberMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TenantMembershipCreate) => createMember(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [MEMBERS_QUERY_KEY] });
      toast.success('Member invited.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to invite member');
    },
  });
}

export function useRevokeMemberMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (membershipId: string) => revokeMember(membershipId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [MEMBERS_QUERY_KEY] });
      toast.success('Member revoked.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to revoke member');
    },
  });
}

export function useTenantDetails() {
  return useQuery({
    queryKey: [TENANT_DETAILS_QUERY_KEY],
    queryFn: fetchTenantDetails,
  });
}

export function useUpdateTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TenantUpdate) => updateTenantDetails(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [TENANT_DETAILS_QUERY_KEY] });
      toast.success('Tenant details updated.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to update tenant');
    },
  });
}

export function useMyTenants() {
  return useQuery({
    queryKey: [MY_TENANTS_QUERY_KEY],
    queryFn: fetchMyTenants,
  });
}

export function useCreateTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TenantCreateRequest) => createTenant(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [MY_TENANTS_QUERY_KEY] });
      toast.success('Tenant created.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to create tenant');
    },
  });
}

export const JOBS_QUERY_KEY = 'jobs';
export const SYSTEM_EVENTS_QUERY_KEY = 'system-events';

export function useJobs(status?: string) {
  return useQuery({
    queryKey: [JOBS_QUERY_KEY, status],
    queryFn: () => fetchJobs(status),
    refetchInterval: 3000,
  });
}

export function useRetryJobMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => retryJob(jobId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [JOBS_QUERY_KEY] });
      toast.success('Job queued for retry.');
    },
    onError: (error) => {
      toastApiError(error, 'Failed to retry job');
    },
  });
}

export function useSystemEvents() {
  return useQuery({
    queryKey: [SYSTEM_EVENTS_QUERY_KEY],
    queryFn: fetchSystemEvents,
    refetchInterval: 5000,
  });
}
