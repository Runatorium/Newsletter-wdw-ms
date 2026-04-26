import { useState } from "react";
import "./App.css";
import { api, type PeriodCounts, type SubDiver, type SubCompany } from "./api";
import { useQueryDeps, type LoadState } from "./useQueryDeps";

function useQueryOnce<T>(loader: () => Promise<T>) {
  return useQueryDeps(loader, []);
}

function triBool(choice: string): boolean | undefined {
  if (choice === "any" || choice === "") return undefined;
  return choice === "true";
}

function dayStart(s: string): string | undefined {
  if (!s.trim()) return undefined;
  return `${s}T00:00:00`;
}

function dayEnd(s: string): string | undefined {
  if (!s.trim()) return undefined;
  return `${s}T23:59:59.999999`;
}

function fmtDate(s: string) {
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleString();
}

function StatBlock({
  title,
  u,
  c,
}: {
  title: string;
  u: LoadState<PeriodCounts>;
  c: LoadState<PeriodCounts>;
}) {
  return (
    <div className="grid2" style={{ marginTop: "0.5rem" }}>
      <div className="stat-card">
        <h2>
          {title} — new users (auth <code>users</code>)
        </h2>
        {u.err && <p className="error">{u.err}</p>}
        {u.data && !u.loading && (
          <>
            <div className="stat-row">
              <span className="label">Last day</span>
              <span className="value">{u.data.last_day}</span>
            </div>
            <div className="stat-row">
              <span className="label">Last week</span>
              <span className="value">{u.data.last_week}</span>
            </div>
            <div className="stat-row">
              <span className="label">Last month (30d)</span>
              <span className="value">{u.data.last_month}</span>
            </div>
          </>
        )}
        {u.loading && <p className="loading">Loading…</p>}
      </div>
      <div className="stat-card">
        <h2>
          {title} — new companies (profiles)
        </h2>
        {c.err && <p className="error">{c.err}</p>}
        {c.data && !c.loading && (
          <>
            <div className="stat-row">
              <span className="label">Last day</span>
              <span className="value">{c.data.last_day}</span>
            </div>
            <div className="stat-row">
              <span className="label">Last week</span>
              <span className="value">{c.data.last_week}</span>
            </div>
            <div className="stat-row">
              <span className="label">Last month (30d)</span>
              <span className="value">{c.data.last_month}</span>
            </div>
          </>
        )}
        {c.loading && <p className="loading">Loading…</p>}
      </div>
    </div>
  );
}

function FilterBar({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`filter-bar ${className}`.trim()}>{children}</div>;
}

export default function App() {
  const usersS = useQueryOnce(api.newUsers);
  const companiesS = useQueryOnce(api.newCompanies);

  const [dQ, setDQ] = useState("");
  const [dEmail, setDEmail] = useState<"any" | "true" | "false">("any");
  const [dProfile, setDProfile] = useState<"any" | "true" | "false">("any");
  const [dFrom, setDFrom] = useState("");
  const [dTo, setDTo] = useState("");

  const divL = useQueryDeps(
    () =>
      api.divers({
        skip: 0,
        limit: 100,
        q: dQ.trim() || undefined,
        email_verified: triBool(dEmail),
        profile_verified: triBool(dProfile),
        created_from: dayStart(dFrom),
        created_to: dayEnd(dTo),
      }),
    [dQ, dEmail, dProfile, dFrom, dTo],
  );

  const [cQ, setCQ] = useState("");
  const [cEmail, setCEmail] = useState<"any" | "true" | "false">("any");
  const [cFrom, setCFrom] = useState("");
  const [cTo, setCTo] = useState("");

  const comL = useQueryDeps(
    () =>
      api.companies({
        skip: 0,
        limit: 100,
        q: cQ.trim() || undefined,
        email_verified: triBool(cEmail),
        created_from: dayStart(cFrom),
        created_to: dayEnd(cTo),
      }),
    [cQ, cEmail, cFrom, cTo],
  );

  const [sDq, setSDq] = useState("");
  const [sDplan, setSDplan] = useState("");
  const [sDstatus, setSDstatus] = useState("active");

  const dSub = useQueryDeps(
    () =>
      api.activeDiverSubs({
        limit: 200,
        q: sDq.trim() || undefined,
        plan: sDplan.trim() || undefined,
        status: sDstatus,
      }),
    [sDq, sDplan, sDstatus],
  );

  const [sCq, setSCq] = useState("");
  const [sCplan, setSCplan] = useState("");
  const [sCstatus, setSCstatus] = useState("active");

  const cSub = useQueryDeps(
    () =>
      api.activeCompanySubs({
        limit: 200,
        q: sCq.trim() || undefined,
        plan: sCplan.trim() || undefined,
        status: sCstatus,
      }),
    [sCq, sCplan, sCstatus],
  );

  return (
    <div className="app">
      <header className="head">
        <h1>WDW admin dashboard</h1>
        <p>
          API: <code>/api/v1/…</code> — dev UI uses Vite proxy to FastAPI (port 8000).
        </p>
      </header>

      <StatBlock title="Registration" u={usersS} c={companiesS} />

      <div className="panel">
        <h2>Divers</h2>
        <FilterBar>
          <label>
            <span>Search</span>
            <input
              type="search"
              placeholder="Name, email, phone, location"
              value={dQ}
              onChange={(e) => setDQ(e.target.value)}
            />
          </label>
          <label>
            <span>Email verified</span>
            <select
              value={dEmail}
              onChange={(e) => setDEmail(e.target.value as "any" | "true" | "false")}
            >
              <option value="any">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            <span>Profile verified</span>
            <select
              value={dProfile}
              onChange={(e) => setDProfile(e.target.value as "any" | "true" | "false")}
            >
              <option value="any">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            <span>Created from</span>
            <input type="date" value={dFrom} onChange={(e) => setDFrom(e.target.value)} />
          </label>
          <label>
            <span>Created to</span>
            <input type="date" value={dTo} onChange={(e) => setDTo(e.target.value)} />
          </label>
        </FilterBar>
        {divL.err && <p className="error">{divL.err}</p>}
        {divL.data && (
          <>
            <div className="meta">Matching: {divL.data.total}</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th className="cell-num">#</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {divL.data.items.map((d) => (
                    <tr key={d.id}>
                      <td className="cell-num">{d.id}</td>
                      <td className="cell-clip" title={d.full_name}>
                        {d.full_name}
                      </td>
                      <td className="cell-clip cell-clip--wide" title={d.email}>
                        {d.email}
                      </td>
                      <td className="cell-clip" title={d.location ?? undefined}>
                        {d.location ?? "—"}
                      </td>
                      <td className="muted">{fmtDate(d.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {divL.loading && <p className="loading" style={{ padding: "0 1rem" }}>Loading…</p>}
      </div>

      <div className="panel">
        <h2>Companies</h2>
        <FilterBar>
          <label>
            <span>Search</span>
            <input
              type="search"
              placeholder="Name, email, phone, address, site"
              value={cQ}
              onChange={(e) => setCQ(e.target.value)}
            />
          </label>
          <label>
            <span>Email verified</span>
            <select
              value={cEmail}
              onChange={(e) => setCEmail(e.target.value as "any" | "true" | "false")}
            >
              <option value="any">Any</option>
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </label>
          <label>
            <span>Created from</span>
            <input type="date" value={cFrom} onChange={(e) => setCFrom(e.target.value)} />
          </label>
          <label>
            <span>Created to</span>
            <input type="date" value={cTo} onChange={(e) => setCTo(e.target.value)} />
          </label>
        </FilterBar>
        {comL.err && <p className="error">{comL.err}</p>}
        {comL.data && (
          <>
            <div className="meta">Matching: {comL.data.total}</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th className="cell-num">#</th>
                    <th>Company</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {comL.data.items.map((c) => (
                    <tr key={c.id}>
                      <td className="cell-num">{c.id}</td>
                      <td className="cell-clip" title={c.company}>
                        {c.company}
                      </td>
                      <td className="cell-clip cell-clip--wide" title={c.email}>
                        {c.email}
                      </td>
                      <td className="cell-clip" title={c.phone ?? undefined}>
                        {c.phone ?? "—"}
                      </td>
                      <td className="muted">{fmtDate(c.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {comL.loading && <p className="loading" style={{ padding: "0 1rem" }}>Loading…</p>}
      </div>

      <div className="panel">
        <h2>Diver subscriptions</h2>
        <FilterBar>
          <label>
            <span>Search</span>
            <input
              type="search"
              placeholder="Diver name, email, phone"
              value={sDq}
              onChange={(e) => setSDq(e.target.value)}
            />
          </label>
          <label>
            <span>Plan</span>
            <input
              type="text"
              placeholder="e.g. premium"
              value={sDplan}
              onChange={(e) => setSDplan(e.target.value)}
            />
          </label>
          <label>
            <span>Status</span>
            <select value={sDstatus} onChange={(e) => setSDstatus(e.target.value)}>
              <option value="active">active</option>
              <option value="all">all</option>
              <option value="cancelled">cancelled</option>
              <option value="expired">expired</option>
            </select>
          </label>
        </FilterBar>
        {dSub.err && <p className="error">{dSub.err}</p>}
        {dSub.data && dSub.data.items.length === 0 && !dSub.loading && (
          <p className="muted" style={{ padding: "0.75rem 1rem" }}>No matching subscriptions.</p>
        )}
        {dSub.data && dSub.data.items.length > 0 && (
          <>
            <div className="meta">Matching: {dSub.data.total}</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Diver</th>
                    <th>Email</th>
                    <th>Plan</th>
                    <th>Status</th>
                    <th>Cycle</th>
                  </tr>
                </thead>
                <tbody>
                  {(dSub.data.items as SubDiver[]).map((r) => (
                    <tr key={r.subscription.id}>
                      <td className="cell-clip" title={r.diver.full_name}>
                        {r.diver.full_name}
                      </td>
                      <td className="cell-clip cell-clip--wide" title={r.diver.email}>
                        {r.diver.email}
                      </td>
                      <td className="cell-tight">{r.subscription.plan}</td>
                      <td className="cell-tight">{r.subscription.status}</td>
                      <td className="cell-tight">{r.subscription.billing_cycle}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {dSub.loading && <p className="loading" style={{ padding: "0 1rem" }}>Loading…</p>}
      </div>

      <div className="panel">
        <h2>Company subscriptions</h2>
        <FilterBar>
          <label>
            <span>Search</span>
            <input
              type="search"
              placeholder="Company, email, phone"
              value={sCq}
              onChange={(e) => setSCq(e.target.value)}
            />
          </label>
          <label>
            <span>Plan</span>
            <input
              type="text"
              value={sCplan}
              onChange={(e) => setSCplan(e.target.value)}
            />
          </label>
          <label>
            <span>Status</span>
            <select value={sCstatus} onChange={(e) => setSCstatus(e.target.value)}>
              <option value="active">active</option>
              <option value="all">all</option>
              <option value="cancelled">cancelled</option>
              <option value="expired">expired</option>
            </select>
          </label>
        </FilterBar>
        {cSub.err && <p className="error">{cSub.err}</p>}
        {cSub.data && cSub.data.items.length === 0 && !cSub.loading && (
          <p className="muted" style={{ padding: "0.75rem 1rem" }}>No matching subscriptions.</p>
        )}
        {cSub.data && cSub.data.items.length > 0 && (
          <>
            <div className="meta">Matching: {cSub.data.total}</div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Email</th>
                    <th>Plan</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(cSub.data.items as SubCompany[]).map((r) => (
                    <tr key={r.subscription.id}>
                      <td className="cell-clip" title={r.company.company}>
                        {r.company.company}
                      </td>
                      <td className="cell-clip cell-clip--wide" title={r.company.email}>
                        {r.company.email}
                      </td>
                      <td className="cell-tight">{r.subscription.plan}</td>
                      <td className="cell-tight">{r.subscription.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {cSub.loading && <p className="loading" style={{ padding: "0 1rem" }}>Loading…</p>}
      </div>
    </div>
  );
}
