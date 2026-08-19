import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { getApiErrorMessage } from '@/lib/apiError';
import {
  approveAsset,
  createBook,
  createCampaign,
  createEdition,
  createAuthor,
  evaluateAsset,
  fetchAssets,
  fetchAuthor,
  fetchAuthors,
  fetchBook,
  fetchBooks,
  fetchDocuments,
  fetchEditions,
  fetchLatestCampaign,
  generateAssets,
  patchAuthor,
  patchBook,
  patchEdition,
  rejectAsset,
  reviseAsset,
  sendMindMessage,
  updatePublishingStatus,
  uploadDocument,
  waitForJob,
} from '@/lib/api/creator';

function toastError(error: unknown, fallback: string) {
  toast.error(getApiErrorMessage(error, fallback));
}

export const AUTHORS_KEY = 'authors';
export const BOOKS_KEY = 'books';

export function useAuthors() {
  return useQuery({ queryKey: [AUTHORS_KEY], queryFn: fetchAuthors });
}

export function useAuthor(authorId: string | undefined) {
  return useQuery({
    queryKey: [AUTHORS_KEY, authorId],
    queryFn: () => fetchAuthor(authorId!),
    enabled: Boolean(authorId),
  });
}

export function useBooks(authorId?: string) {
  return useQuery({
    queryKey: [BOOKS_KEY, authorId],
    queryFn: () => fetchBooks(authorId),
  });
}

export function useBook(bookId: string | undefined) {
  return useQuery({
    queryKey: [BOOKS_KEY, 'one', bookId],
    queryFn: () => fetchBook(bookId!),
    enabled: Boolean(bookId),
  });
}

export function useEditions(bookId: string | undefined) {
  return useQuery({
    queryKey: ['editions', bookId],
    queryFn: () => fetchEditions(bookId!),
    enabled: Boolean(bookId),
  });
}

export function useDocuments(bookId: string | undefined) {
  return useQuery({
    queryKey: ['documents', bookId],
    queryFn: () => fetchDocuments(bookId!),
    enabled: Boolean(bookId),
  });
}

export function useAssets(bookId: string | undefined) {
  return useQuery({
    queryKey: ['assets', bookId],
    queryFn: () => fetchAssets(bookId!),
    enabled: Boolean(bookId),
  });
}

export function useLatestCampaign(bookId: string | undefined) {
  return useQuery({
    queryKey: ['campaign', bookId],
    queryFn: () => fetchLatestCampaign(bookId!),
    enabled: Boolean(bookId),
  });
}

export function usePatchAuthor(authorId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; context?: Record<string, unknown> }) =>
      patchAuthor(authorId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AUTHORS_KEY] });
      toast.success('Author profile saved.');
    },
    onError: (error) => toastError(error, 'Could not save author'),
  });
}

export function useCreateAuthor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createAuthor,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [AUTHORS_KEY] });
      toast.success('Author created.');
    },
    onError: (error) => toastError(error, 'Could not create author'),
  });
}

export function useCreateBook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createBook,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [BOOKS_KEY] });
      toast.success('Book created.');
    },
    onError: (error) => toastError(error, 'Could not create book'),
  });
}

export function usePatchBook(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof patchBook>[1]) =>
      patchBook(bookId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [BOOKS_KEY] });
      toast.success('Book saved.');
    },
    onError: (error) => toastError(error, 'Could not save book'),
  });
}

export function useCreateEdition(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Parameters<typeof createEdition>[1]) =>
      createEdition(bookId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['editions', bookId] });
      toast.success('Edition added.');
    },
    onError: (error) => toastError(error, 'Could not add edition'),
  });
}

export function usePatchEdition(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      editionId,
      payload,
    }: {
      editionId: string;
      payload: Parameters<typeof patchEdition>[1];
    }) => patchEdition(editionId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['editions', bookId] });
      toast.success('Edition saved.');
    },
    onError: (error) => toastError(error, 'Could not save edition'),
  });
}

export function useUploadDocument(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, rights }: { file: File; rights: string }) =>
      uploadDocument(bookId, file, rights),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents', bookId] });
      toast.success('Excerpt uploaded.');
    },
    onError: (error) => toastError(error, 'Could not upload excerpt'),
  });
}

export function useGenerateAssets(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { job_id } = await generateAssets(bookId);
      return waitForJob(job_id, { intervalMs: 1500, timeoutMs: 240_000 });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['assets', bookId] });
      toast.success('Five assets generated.');
    },
    onError: (error) => toastError(error, 'Could not generate assets'),
  });
}

export function useEvaluateAsset(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: evaluateAsset,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['assets', bookId] });
    },
    onError: (error) => toastError(error, 'Could not run governance review'),
  });
}

export function useApproveAsset(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: approveAsset,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['assets', bookId] });
      toast.success('Asset approved.');
    },
    onError: (error) => toastError(error, 'Could not approve asset'),
  });
}

export function useRejectAsset(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ assetId, note }: { assetId: string; note: string }) =>
      rejectAsset(assetId, note),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['assets', bookId] });
      toast.success('Asset rejected.');
    },
    onError: (error) => toastError(error, 'Could not reject asset'),
  });
}

export function useReviseAsset(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      assetId,
      correction,
    }: {
      assetId: string;
      correction: string;
    }) => reviseAsset(assetId, correction),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['assets', bookId] });
      toast.success('New version created with your preference applied.');
    },
    onError: (error) => toastError(error, 'Could not revise asset'),
  });
}

export function useCreateCampaign(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => createCampaign(bookId, { campaign_type: 'launch' }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['campaign', bookId] });
      toast.success('Launch board created.');
    },
    onError: (error) => toastError(error, 'Could not create campaign'),
  });
}

export function usePublishingStatus(bookId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      editionId,
      payload,
    }: {
      editionId: string;
      payload: Parameters<typeof updatePublishingStatus>[1];
    }) => updatePublishingStatus(editionId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['editions', bookId] });
      toast.success('Publishing status saved.');
    },
    onError: (error) => toastError(error, 'Could not update status'),
  });
}

export function useMindChat(authorId: string) {
  return useMutation({
    mutationFn: async (message: string) => {
      const enqueued = await sendMindMessage(authorId, message);
      const job = await waitForJob(enqueued.job_id, {
        intervalMs: 1500,
        timeoutMs: 180_000,
      });
      const result = job.result || {};
      const reply = String(result.reply || '').trim();
      if (!reply) {
        throw new Error('Mind returned an empty reply');
      }
      return {
        reply,
        mind_id: String(result.mind_id || ''),
        source: String(result.source || 'minds'),
      };
    },
    onError: (error) => toastError(error, 'Mind is not available'),
  });
}
