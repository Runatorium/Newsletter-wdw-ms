const base = "/api/v1";

function qs(
  params: Record<string, string | number | boolean | null | undefined>,
): string {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === null || v === undefined || v === "") continue;
    u.set(k, String(v));
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${base}${path}`, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  return r.json() as Promise<T>;
}

export type PeriodCounts = {
  last_day: number;
  last_week: number;
  last_month: number;
};

export type DiverRead = {
  id: number;
  full_name: string;
  email: string;
  role: string;
  phone: string | null;
  location: string | null;
  created_at: string;
  updated_at: string;
  email_verified: boolean;
  profile_verified: boolean;
};

export type CompanyRead = {
  id: number;
  company: string;
  email: string;
  role: string;
  created_at: string;
  updated_at: string;
  email_verified: boolean;
  phone: string | null;
};

export type DiverList = { items: DiverRead[]; total: number };
export type CompanyList = { items: CompanyRead[]; total: number };

export type SubDiver = {
  diver: DiverRead;
  subscription: {
    id: number;
    plan: string;
    status: string;
    billing_cycle: string;
    start_date: string;
    end_date: string | null;
  };
};

export type SubCompany = {
  company: CompanyRead;
  subscription: {
    id: number;
    plan: string;
    status: string;
    billing_cycle: string;
    start_date: string;
    next_billing_date: string | null;
  };
};

export type SubDiverList = { items: SubDiver[]; total: number };
export type SubCompanyList = { items: SubCompany[]; total: number };

export type DiverListParams = {
  skip?: number;
  limit?: number;
  q?: string;
  email_verified?: boolean;
  profile_verified?: boolean;
  created_from?: string;
  created_to?: string;
};

export type CompanyListParams = {
  skip?: number;
  limit?: number;
  q?: string;
  email_verified?: boolean;
  created_from?: string;
  created_to?: string;
};

export type SubscriptionListParams = {
  skip?: number;
  limit?: number;
  q?: string;
  plan?: string;
  status?: string;
};

export const api = {
  divers: (p: DiverListParams = {}) =>
    j<DiverList>(`/divers${qs(p)}`),

  companies: (p: CompanyListParams = {}) =>
    j<CompanyList>(`/companies${qs(p)}`),

  newUsers: () => j<PeriodCounts>(`/stats/new-users`),
  newCompanies: () => j<PeriodCounts>(`/stats/new-companies`),

  activeDiverSubs: (p: SubscriptionListParams = {}) =>
    j<SubDiverList>(`/subscriptions/divers/active${qs(p)}`),

  activeCompanySubs: (p: SubscriptionListParams = {}) =>
    j<SubCompanyList>(`/subscriptions/companies/active${qs(p)}`),
};
