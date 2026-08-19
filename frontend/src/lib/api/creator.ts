import api from '@/lib/api';
import type { AuditEvent, Job } from '@/types';
import type {
  Asset,
  Author,
  Book,
  Campaign,
  Edition,
  MindStatus,
  SourceDocument,
} from '@/types/creator';

export async function fetchAuthors(): Promise<Author[]> {
  const { data } = await api.get<Author[]>('/authors');
  return data;
}

export async function fetchAuthor(authorId: string): Promise<Author> {
  const { data } = await api.get<Author>(`/authors/${authorId}`);
  return data;
}

export async function createAuthor(payload: {
  name: string;
  context: Record<string, unknown>;
}): Promise<Author> {
  const { data } = await api.post<Author>('/authors', payload);
  return data;
}

export async function patchAuthor(
  authorId: string,
  payload: { name?: string; context?: Record<string, unknown> }
): Promise<Author> {
  const { data } = await api.patch<Author>(`/authors/${authorId}`, payload);
  return data;
}

export async function fetchMindStatus(authorId: string): Promise<MindStatus> {
  const { data } = await api.get<MindStatus>(`/authors/${authorId}/mind/status`);
  return data;
}

export async function sendMindMessage(
  authorId: string,
  message: string
): Promise<{ job_id: string; status: string; author_id: string }> {
  const { data } = await api.post(`/authors/${authorId}/mind/message`, {
    message,
  });
  return data;
}

export async function fetchJob(jobId: string): Promise<Job> {
  const { data } = await api.get<Job>(`/jobs/${jobId}`);
  return data;
}

/** Poll a background job. Mind replies often take 1–2 minutes. */
export async function waitForJob(
  jobId: string,
  options?: { intervalMs?: number; timeoutMs?: number }
): Promise<Job> {
  const intervalMs = options?.intervalMs ?? 1500;
  const timeoutMs = options?.timeoutMs ?? 180_000;
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const job = await fetchJob(jobId);
    if (job.status === 'completed') return job;
    if (job.status === 'failed') {
      throw new Error(job.last_error || 'Job failed');
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error('Timed out waiting for the job to finish');
}

export async function fetchBooks(authorId?: string): Promise<Book[]> {
  const { data } = await api.get<Book[]>('/books', {
    params: authorId ? { author_id: authorId } : undefined,
  });
  return data;
}

export async function fetchBook(bookId: string): Promise<Book> {
  const { data } = await api.get<Book>(`/books/${bookId}`);
  return data;
}

export async function createBook(payload: {
  author_id: string;
  working_title: string;
  final_title?: string;
  subtitle?: string;
  description?: string;
}): Promise<Book> {
  const { data } = await api.post<Book>('/books', payload);
  return data;
}

export async function patchBook(
  bookId: string,
  payload: Partial<Book>
): Promise<Book> {
  const { data } = await api.patch<Book>(`/books/${bookId}`, payload);
  return data;
}

export async function fetchEditions(bookId: string): Promise<Edition[]> {
  const { data } = await api.get<Edition[]>(`/books/${bookId}/editions`);
  return data;
}

export async function createEdition(
  bookId: string,
  payload: Partial<Edition> & { format: string }
): Promise<Edition> {
  const { data } = await api.post<Edition>(`/books/${bookId}/editions`, payload);
  return data;
}

export async function patchEdition(
  editionId: string,
  payload: Partial<Edition>
): Promise<Edition> {
  const { data } = await api.patch<Edition>(`/editions/${editionId}`, payload);
  return data;
}

export async function fetchDocuments(bookId: string): Promise<SourceDocument[]> {
  const { data } = await api.get<SourceDocument[]>(`/books/${bookId}/documents`);
  return data;
}

export async function uploadDocument(
  bookId: string,
  file: File,
  rightsDeclaration: string
): Promise<SourceDocument> {
  const body = new FormData();
  body.append('file', file);
  body.append('rights_declaration', rightsDeclaration);
  const { data } = await api.post<SourceDocument>(
    `/books/${bookId}/documents`,
    body
  );
  return data;
}

export async function generateAssets(bookId: string): Promise<{ job_id: string }> {
  const { data } = await api.post(`/books/${bookId}/generate-assets`, {});
  return data;
}

export async function fetchAssets(bookId: string): Promise<Asset[]> {
  const { data } = await api.get<Asset[]>(`/books/${bookId}/assets`);
  return data;
}

export async function evaluateAsset(assetId: string): Promise<Asset> {
  const { data } = await api.post<Asset>(`/assets/${assetId}/evaluate`);
  return data;
}

export async function approveAsset(assetId: string): Promise<Asset> {
  const { data } = await api.post<Asset>(`/assets/${assetId}/approve`);
  return data;
}

export async function rejectAsset(assetId: string, note: string): Promise<Asset> {
  const { data } = await api.post<Asset>(`/assets/${assetId}/reject`, { note });
  return data;
}

export async function reviseAsset(
  assetId: string,
  correction: string
): Promise<Asset> {
  const { data } = await api.post<Asset>(`/assets/${assetId}/revise`, {
    correction,
  });
  return data;
}

async function downloadZip(url: string, filename: string): Promise<void> {
  const response = await api.post(url, {}, { responseType: 'blob' });
  const blob = new Blob([response.data], { type: 'application/zip' });
  const href = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = href;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(href);
}

export async function downloadKdpPackage(editionId: string): Promise<void> {
  await downloadZip(
    `/editions/${editionId}/packages/kdp`,
    'creatortrust-kdp-paperback.zip'
  );
}

export async function downloadIngramPackage(editionId: string): Promise<void> {
  await downloadZip(
    `/editions/${editionId}/packages/ingramspark`,
    'creatortrust-ingramspark-paperback.zip'
  );
}

export async function updatePublishingStatus(
  editionId: string,
  payload: { publishing_status?: string; proof_review_status?: string }
): Promise<Edition> {
  const { data } = await api.post<Edition>(
    `/editions/${editionId}/publishing-status`,
    payload
  );
  return data;
}

export async function createCampaign(
  bookId: string,
  payload: { campaign_type?: string; launch_date?: string }
): Promise<Campaign> {
  const { data } = await api.post<Campaign>(`/books/${bookId}/campaigns`, payload);
  return data;
}

export async function fetchLatestCampaign(
  bookId: string
): Promise<Campaign | null> {
  const { data } = await api.get<Campaign | null>(
    `/books/${bookId}/campaigns/latest`
  );
  return data;
}

export async function fetchBookAudit(bookId: string): Promise<AuditEvent[]> {
  const { data } = await api.get<AuditEvent[]>(`/books/${bookId}/audit`);
  return data;
}

export async function resetDemo(): Promise<void> {
  await api.post('/admin/demo-reset');
}
