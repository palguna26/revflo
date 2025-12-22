import type { Issue, Notification, PRDetail, RepoSummary, User, PRSummary } from '@/types/api';

const rawBase = (import.meta.env.VITE_API_BASE as string | undefined)?.trim();
const API_BASE =
  rawBase && (rawBase.startsWith('http://') || rawBase.startsWith('https://'))
    ? rawBase
    : rawBase
      ? `https://${rawBase}` // Assume https if no schema but value exists
      : '/api'; // Fallback to proxy

export { API_BASE };

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('qr_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    (headers as any)['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers,
    ...options,
  });

  if (!res.ok) {
    // Let callers handle 401/other errors (e.g. redirect + toast)
    const errorText = await res.text();
    throw new Error(errorText || `Request failed with status ${res.status}`);
  }

  // Some endpoints may legitimately return no content
  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const api = {
  async getMe(): Promise<User> {
    return request<User>('/me');
  },

  async getRepos(): Promise<RepoSummary[]> {
    return request<RepoSummary[]>('/repos');
  },

  async getRepo(owner: string, repo: string): Promise<RepoSummary> {
    return request<RepoSummary>(`/repos/${owner}/${repo}`);
  },

  async getIssues(owner: string, repo: string): Promise<Issue[]> {
    return request<Issue[]>(`/repos/${owner}/${repo}/issues`);
  },

  async generateChecklist(owner: string, repo: string, issueNumber: number): Promise<Issue> {
    return request<Issue>(`/repos/${owner}/${repo}/issues/${issueNumber}/checklist`, {
      method: 'POST',
      body: JSON.stringify({}), // Assuming an empty body for POST
    });
  },

  async getIssue(owner: string, repo: string, issueNumber: number): Promise<Issue> {
    return request<Issue>(`/repos/${owner}/${repo}/issues/${issueNumber}`);
  },

  async regenerateChecklist(owner: string, repo: string, issueNumber: number): Promise<void> {
    await request<void>(`/repos/${owner}/${repo}/issues/${issueNumber}/checklist`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },

  async getPR(owner: string, repo: string, prNumber: number): Promise<PRDetail> {
    return request<PRDetail>(`/repos/${owner}/${repo}/prs/${prNumber}`);
  },

  async getPullRequests(owner: string, repo: string): Promise<PRSummary[]> {
    return request<PRSummary[]>(`/repos/${owner}/${repo}/prs`);
  },

  async revalidatePR(owner: string, repo: string, prNumber: number): Promise<void> {
    await request<void>(`/repos/${owner}/${repo}/prs/${prNumber}/revalidate`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },

  async getNotifications(): Promise<Notification[]> {
    return request<Notification[]>('/notifications');
  },

  async updateManagedRepos(managedRepos: string[]): Promise<User> {
    return request<User>('/me/managed_repos', {
      method: 'PUT',
      body: JSON.stringify(managedRepos),
    });
  },

  async addRepo(fullName: string): Promise<RepoSummary> {
    return request<RepoSummary>('/repos/add', {
      method: 'POST',
      body: JSON.stringify({ full_name: fullName }),
    });
  },

  async runReview(owner: string, repo: string, issueNumber: number, prNumber: number): Promise<any> {
    return request<any>(`/repos/${owner}/${repo}/issues/${issueNumber}/pulls/${prNumber}/review`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },

  async getPRReview(owner: string, repo: string, prNumber: number): Promise<any> {
    return request<any>(`/repos/${owner}/${repo}/prs/${prNumber}/review`);
  },

  async getAvailableRepos(): Promise<any[]> {
    return request<any[]>('/repos/available');
  },

  async getRecentActivity(): Promise<{ prs: any[]; issues: any[] }> {
    return request<{ prs: any[]; issues: any[] }>('/me/recent-activity');
  },

  async logout(): Promise<void> {
    localStorage.removeItem('qr_token');
    await request<void>('/auth/github/logout', { method: 'POST' });
  },

  async generateFix(issueDescription: string, codeSnippet: string): Promise<string> {
    const res = await request<{ fixed_code: string }>('/ai/fix', {
      method: 'POST',
      body: JSON.stringify({ issue_description: issueDescription, code_snippet: codeSnippet }),
    });
    return res.fixed_code;
  },

  async getRepoAudit(owner: string, repo: string): Promise<any> {
    return request<any>(`/repos/${owner}/${repo}/audit/latest`);
  },

  async triggerRepoAudit(owner: string, repo: string): Promise<any> {
    return request<any>(`/repos/${owner}/${repo}/audit/scan`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  },
};
