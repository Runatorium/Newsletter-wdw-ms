import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import "./App.css";
import {
  api,
  type DiverCertMatchItem,
  type DiverCertMatchResponse,
  type NewsletterEmailPreviewResponse,
  type PeriodCounts,
  type SubCompany,
  type SubDiver,
} from "./api";
import { dayEnd, dayStart, fmtDate } from "./datetime";
import { useQueryDeps, type LoadState } from "./useQueryDeps";

function subscribeHash(fn: () => void) {
  window.addEventListener("hashchange", fn);
  return () => window.removeEventListener("hashchange", fn);
}

function hashPathSnapshot(): string {
  const h = window.location.hash.replace(/^#/, "").replace(/^\//, "");
  if (h === "newsletter") return "/newsletter";
  return "/";
}

function useQueryOnce<T>(loader: () => Promise<T>) {
  return useQueryDeps(loader, []);
}

function triBool(choice: string): boolean | undefined {
  if (choice === "any" || choice === "") return undefined;
  return choice === "true";
}

function escapeHtmlText(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Opens a standalone document so the message can be read like a real inbox tab. */
function openEmailBodyHtmlInNewTab(bodyHtml: string, subject: string) {
  const w = window.open("", "_blank", "noopener,noreferrer");
  if (!w) return;
  const title = escapeHtmlText(subject || "Email preview");
  w.document.open();
  w.document.write(
    `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>${title}</title></head><body>`,
  );
  w.document.write(bodyHtml);
  w.document.write(`</body></html>`);
  w.document.close();
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

function DiversCertMatchTable({
  rows,
  emailSelection,
  onEmailToggle,
}: {
  rows: DiverCertMatchItem[];
  emailSelection?: Set<number>;
  onEmailToggle?: (diverId: number) => void;
}) {
  const emailCol = Boolean(onEmailToggle && emailSelection);
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {emailCol && <th className="cell-check">Email</th>}
            <th>Name</th>
            <th>Email</th>
            <th className="cell-tight">Match</th>
            <th className="cell-tight">Met</th>
            <th>Missing certs</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.diver.id}>
              {emailCol && (
                <td className="cell-check">
                  <input
                    type="checkbox"
                    checked={emailSelection!.has(row.diver.id)}
                    onChange={() => onEmailToggle!(row.diver.id)}
                    aria-label={`Include ${row.diver.full_name} in email send`}
                  />
                </td>
              )}
              <td className="cell-clip" title={row.diver.full_name}>
                {row.diver.full_name}
              </td>
              <td className="cell-clip cell-clip--wide" title={row.diver.email}>
                {row.diver.email}
              </td>
              <td className="cell-tight">{row.match_percent}%</td>
              <td className="cell-tight">
                {row.matched_count}/{row.required_total}
              </td>
              <td
                className="cell-clip cell-clip--wide muted"
                title={row.missing_certifications.join(" · ")}
              >
                {row.missing_certifications.length
                  ? row.missing_certifications.join(" · ")
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NewsletterSection() {
  const [loc, setLoc] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [postedThisWeek, setPostedThisWeek] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState<Set<number>>(() => new Set());
  const [match, setMatch] = useState<DiverCertMatchResponse | null>(null);
  const [matchErr, setMatchErr] = useState<string | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);

  const [emailPick, setEmailPick] = useState<Set<number>>(() => new Set());
  const [previewDiverId, setPreviewDiverId] = useState<number | null>(null);
  const [emailPreview, setEmailPreview] = useState<NewsletterEmailPreviewResponse | null>(null);
  const [emailPreviewErr, setEmailPreviewErr] = useState<string | null>(null);
  const [emailPreviewLoading, setEmailPreviewLoading] = useState(false);
  const [emailSendLoading, setEmailSendLoading] = useState(false);
  const [emailSendNote, setEmailSendNote] = useState<string | null>(null);
  const [emailPreviewTab, setEmailPreviewTab] = useState<"html" | "text">("html");
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3 | 4>(1);
  const [htmlPreviewLightbox, setHtmlPreviewLightbox] = useState(false);

  const jobs = useQueryDeps(
    () =>
      api.jobPositions({
        skip: 0,
        limit: 200,
        location: loc.trim() || undefined,
        posted_from: dayStart(from),
        posted_to: dayEnd(to),
        ...(postedThisWeek ? { posted_this_week: true } : {}),
      }),
    [loc, from, to, postedThisWeek],
  );

  function toggleJob(id: number) {
    setSelectedJobs((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  async function runMatch() {
    if (selectedJobs.size === 0) return;
    setMatchErr(null);
    setMatchLoading(true);
    try {
      const r = await api.diverCertMatches({ job_ids: [...selectedJobs] });
      setMatch(r);
      setEmailPick(new Set());
      setEmailPreview(null);
      setEmailPreviewErr(null);
      setEmailSendNote(null);
      setPreviewDiverId(null);
      const hasResultTables =
        Boolean(r) && !r.message && r.required_certifications.length > 0;
      if (hasResultTables) setWizardStep(3);
    } catch (e) {
      setMatchErr(e instanceof Error ? e.message : String(e));
      setMatch(null);
    } finally {
      setMatchLoading(false);
    }
  }

  useEffect(() => {
    if (!emailPick.size) {
      setPreviewDiverId(null);
      setEmailPreview(null);
      return;
    }
    const sorted = [...emailPick].sort((a, b) => a - b);
    if (previewDiverId === null || !emailPick.has(previewDiverId)) {
      setPreviewDiverId(sorted[0] ?? null);
    }
  }, [emailPick, previewDiverId]);

  function toggleEmailTarget(id: number) {
    setEmailPick((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
    setEmailPreview(null);
    setEmailSendNote(null);
  }

  function addAllFullToEmail() {
    if (!match?.items.length) return;
    setEmailPick((prev) => {
      const n = new Set(prev);
      for (const row of match.items) n.add(row.diver.id);
      return n;
    });
    setEmailPreview(null);
    setEmailSendNote(null);
  }

  function addAllPartialToEmail() {
    if (!match?.partial_items.length) return;
    setEmailPick((prev) => {
      const n = new Set(prev);
      for (const row of match.partial_items) n.add(row.diver.id);
      return n;
    });
    setEmailPreview(null);
    setEmailSendNote(null);
  }

  function clearEmailTargets() {
    setEmailPick(new Set());
    setEmailPreview(null);
    setPreviewDiverId(null);
    setEmailSendNote(null);
  }

  async function loadEmailPreview() {
    const diverId = previewDiverId ?? [...emailPick].sort((a, b) => a - b)[0];
    if (selectedJobs.size === 0 || diverId == null) return;
    setEmailPreviewErr(null);
    setEmailPreviewLoading(true);
    try {
      const r = await api.newsletterEmailPreview({
        job_ids: [...selectedJobs],
        diver_id: diverId,
      });
      setEmailPreview(r);
    } catch (e) {
      setEmailPreviewErr(e instanceof Error ? e.message : String(e));
      setEmailPreview(null);
    } finally {
      setEmailPreviewLoading(false);
    }
  }

  async function sendOutreachEmails() {
    if (selectedJobs.size === 0 || emailPick.size === 0) return;
    if (
      !window.confirm(
        `Send the outreach email to ${emailPick.size} diver(s) for the selected job(s)?`,
      )
    ) {
      return;
    }
    setEmailSendNote(null);
    setEmailSendLoading(true);
    try {
      const r = await api.newsletterEmailSend({
        job_ids: [...selectedJobs],
        diver_ids: [...emailPick],
      });
      const errPart =
        r.errors.length > 0
          ? ` Failures: ${r.errors.map((x) => `#${x.diver_id} ${x.detail}`).join("; ")}`
          : "";
      setEmailSendNote(`Sent ${r.sent} message(s).${errPart}`);
    } catch (e) {
      setEmailSendNote(e instanceof Error ? e.message : String(e));
    } finally {
      setEmailSendLoading(false);
    }
  }

  const emailPickOptions = useMemo(() => {
    if (!match) return [];
    const map = new Map<number, string>();
    for (const row of match.items) map.set(row.diver.id, row.diver.full_name);
    for (const row of match.partial_items) map.set(row.diver.id, row.diver.full_name);
    return [...emailPick]
      .sort((a, b) => a - b)
      .map((id) => ({ id, name: map.get(id) ?? `Diver #${id}` }));
  }, [match, emailPick]);

  function selectAllVisibleJobs() {
    if (!jobs.data?.items.length) return;
    setSelectedJobs(new Set(jobs.data.items.map((j) => j.id)));
  }

  function clearJobSelection() {
    setSelectedJobs(new Set());
  }

  const step3Active = Boolean(
    match && !match.message && match.required_certifications.length > 0,
  );

  function canReachWizardStep(s: 1 | 2 | 3 | 4): boolean {
    if (s <= 1) return true;
    if (s === 2) return selectedJobs.size > 0;
    return step3Active;
  }

  useEffect(() => {
    if (selectedJobs.size !== 0) return;
    setWizardStep(1);
    setMatch(null);
    setMatchErr(null);
    setEmailPick(new Set());
    setEmailPreview(null);
    setEmailPreviewErr(null);
    setEmailSendNote(null);
    setPreviewDiverId(null);
  }, [selectedJobs.size]);

  useEffect(() => {
    if (!match) return;
    if (selectedJobs.size === 0) return;
    const ids = match.job_ids;
    if (selectedJobs.size !== ids.length) {
      invalidateMatchForJobSelection();
      return;
    }
    for (const id of ids) {
      if (!selectedJobs.has(id)) {
        invalidateMatchForJobSelection();
        return;
      }
    }
  }, [selectedJobs, match]);

  function invalidateMatchForJobSelection() {
    setMatch(null);
    setMatchErr(null);
    setEmailPick(new Set());
    setEmailPreview(null);
    setEmailPreviewErr(null);
    setEmailSendNote(null);
    setPreviewDiverId(null);
    setWizardStep((w) => (w > 2 ? 2 : w));
  }

  useEffect(() => {
    if (!emailPreview) setHtmlPreviewLightbox(false);
  }, [emailPreview]);

  useEffect(() => {
    if (!htmlPreviewLightbox) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setHtmlPreviewLightbox(false);
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prevOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [htmlPreviewLightbox]);

  const wizardNav = (
    [
      { step: 1 as const, title: "Select jobs", hint: "Filter & tick postings" },
      { step: 2 as const, title: "Run match", hint: "Compare certifications" },
      { step: 3 as const, title: "Review divers", hint: "Full & partial lists" },
      { step: 4 as const, title: "Email", hint: "Preview & send" },
    ] as const
  ).map(({ step: sn, title, hint }) => {
    const active = wizardStep === sn;
    const reachable = canReachWizardStep(sn);
    const navDisabled = !reachable && !active;
    return (
      <button
        key={sn}
        type="button"
        className={
          "wizard-nav__btn" +
          (active ? " wizard-nav__btn--active" : "") +
          (sn < wizardStep ? " wizard-nav__btn--done" : "") +
          (navDisabled ? " wizard-nav__btn--locked" : "")
        }
        disabled={navDisabled}
        aria-current={active ? "step" : undefined}
        onClick={() => {
          if (!navDisabled) setWizardStep(sn);
        }}
      >
        <span className="wizard-nav__btn-n" aria-hidden>
          {sn}
        </span>
        <span className="wizard-nav__btn-text">
          <span className="wizard-nav__btn-title">{title}</span>
          <span className="wizard-nav__btn-hint">{hint}</span>
        </span>
      </button>
    );
  });

  const htmlPreviewLightboxEl =
    htmlPreviewLightbox &&
    emailPreview &&
    createPortal(
      <div
        className="email-preview-lightbox"
        role="dialog"
        aria-modal="true"
        aria-label="HTML email preview, full screen"
      >
        <button
          type="button"
          className="email-preview-lightbox__backdrop"
          aria-label="Close preview"
          onClick={() => setHtmlPreviewLightbox(false)}
        />
        <div className="email-preview-lightbox__sheet">
          <header className="email-preview-lightbox__header">
            <div className="email-preview-lightbox__titles">
              <span className="email-preview-lightbox__eyebrow">Inbox preview</span>
              <span className="email-preview-lightbox__subject" title={emailPreview.subject}>
                {emailPreview.subject}
              </span>
            </div>
            <div className="email-preview-lightbox__header-actions">
              <button
                type="button"
                className="btn-link"
                onClick={() =>
                  openEmailBodyHtmlInNewTab(emailPreview.body_html, emailPreview.subject)
                }
              >
                Open in new tab
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setHtmlPreviewLightbox(false)}
              >
                Close
              </button>
            </div>
          </header>
          <iframe
            title="Email HTML preview"
            className="email-preview-lightbox__frame"
            sandbox="allow-same-origin"
            srcDoc={emailPreview.body_html}
          />
        </div>
      </div>,
      document.body,
    );

  return (
    <>
    <div className="newsletter-page">
      <header className="page-header">
        <h1 className="page-title">Newsletter &amp; certification match</h1>
        <p className="page-lead">
          Work through each step: pick jobs, run the match, review divers, then send outreach. You can
          jump back anytime using the steps above or <strong>Back</strong> below.
        </p>
      </header>

      <div className="newsletter-wizard">
        <nav className="newsletter-wizard__nav" aria-label="Workflow steps">
          {wizardNav}
        </nav>

        <div className="newsletter-wizard__body">
          {wizardStep === 1 && (
            <div className="wizard-step wizard-step--jobs">
              <div className="panel panel--operator">
                <h2>Open job postings</h2>
                <FilterBar>
                  <label>
                    <span>Location</span>
                    <input
                      type="search"
                      placeholder="e.g. North Sea"
                      value={loc}
                      onChange={(e) => setLoc(e.target.value)}
                    />
                  </label>
                  <label>
                    <span>Posted from</span>
                    <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
                  </label>
                  <label>
                    <span>Posted to</span>
                    <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
                  </label>
                  <label className="filter-bar--checkbox">
                    <span>This week</span>
                    <input
                      type="checkbox"
                      checked={postedThisWeek}
                      onChange={(e) => setPostedThisWeek(e.target.checked)}
                    />
                    <span className="filter-bar__checkbox-label">Posted since Monday (UTC)</span>
                  </label>
                </FilterBar>
                {jobs.err && <p className="error">{jobs.err}</p>}
                {jobs.data && jobs.data.items.length === 0 && !jobs.loading && (
                  <p className="muted" style={{ padding: "0.75rem 1rem" }}>
                    No jobs match these filters.
                  </p>
                )}
                {jobs.data && jobs.data.items.length > 0 && (
                  <>
                    <div className="meta meta--row">
                      <span>
                        Showing {jobs.data.items.length} of {jobs.data.total} ·{" "}
                        <strong>{selectedJobs.size}</strong> selected
                      </span>
                      <span className="meta--row-actions">
                        <button type="button" className="btn-link" onClick={selectAllVisibleJobs}>
                          Select all on page
                        </button>
                        <button type="button" className="btn-link" onClick={clearJobSelection}>
                          Clear selection
                        </button>
                      </span>
                    </div>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th className="cell-check" />
                            <th className="cell-num">#</th>
                            <th>Title</th>
                            <th className="cell-tight">Req. certs</th>
                            <th>Company</th>
                            <th>Location</th>
                            <th>Status</th>
                            <th>Posted</th>
                          </tr>
                        </thead>
                        <tbody>
                          {jobs.data.items.map((j) => (
                            <tr key={j.id}>
                              <td className="cell-check">
                                <input
                                  type="checkbox"
                                  checked={selectedJobs.has(j.id)}
                                  onChange={() => toggleJob(j.id)}
                                  aria-label={`Select job ${j.id}`}
                                />
                              </td>
                              <td className="cell-num">{j.id}</td>
                              <td className="cell-clip" title={j.title}>
                                {j.title}
                              </td>
                              <td className="cell-tight">{j.certification_count}</td>
                              <td className="cell-clip" title={j.company_name ?? undefined}>
                                {j.company_name ?? "—"}
                              </td>
                              <td className="cell-clip" title={j.location ?? undefined}>
                                {j.location ?? "—"}
                              </td>
                              <td className="cell-tight">{j.status}</td>
                              <td className="muted">{fmtDate(j.posted_at)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
                {jobs.loading && <p className="loading" style={{ padding: "0 1rem" }}>Loading…</p>}
              </div>
            </div>
          )}

          {wizardStep === 2 && (
            <div className="wizard-step wizard-step--match">
              <div className="panel panel--operator">
                <h2>Run certification match</h2>
                <p className="wizard-step__intro">
                  <strong>{selectedJobs.size}</strong> job posting(s) are selected. The server merges
                  their required certifications (de-duplicated), then scores every diver against that
                  combined set.
                </p>
                {matchErr && <p className="error">{matchErr}</p>}
                {match?.message && (
                  <p className="muted" style={{ padding: "0.5rem 1rem 0", margin: 0 }}>
                    {match.message}
                  </p>
                )}
                {matchLoading && <p className="loading" style={{ padding: "0.5rem 1rem" }}>Running match…</p>}
              </div>
            </div>
          )}

          {wizardStep === 3 && step3Active && (
            <div className="wizard-step wizard-step--results">
              <div className="panel panel--operator newsletter-results-panel">
                <h2>Diver match results</h2>
                {match && !match.message && match.required_certifications.length > 0 && (
                  <div className="result-chips" aria-label="Match summary">
                    <span className="result-chip result-chip--full">
                      Full match: <strong>{match.items.length}</strong>
                    </span>
                    <span className="result-chip result-chip--partial">
                      Partial: <strong>{match.partial_items.length}</strong>
                    </span>
                  </div>
                )}
                {match && match.required_certifications.length > 0 && (
                  <div className="meta meta--required" style={{ whiteSpace: "normal" }}>
                    <strong>Required certifications (combined):</strong>{" "}
                    {match.required_certifications.join(" · ")}
                  </div>
                )}
                {match && !match.message && !matchLoading && match.required_certifications.length > 0 && (
                  <>
                    <h3 className="panel-subh">Full match — all requirements met</h3>
                    {match.items.length === 0 ? (
                      <p className="muted" style={{ padding: "0.5rem 1rem 0.75rem", margin: 0 }}>
                        No divers meet every required certification.
                      </p>
                    ) : (
                      <DiversCertMatchTable
                        rows={match.items}
                        emailSelection={emailPick}
                        onEmailToggle={toggleEmailTarget}
                      />
                    )}
                    <h3 className="panel-subh">Partially viable — some requirements met</h3>
                    {match.partial_items.length === 0 ? (
                      <p className="muted" style={{ padding: "0.5rem 1rem 0.75rem", margin: 0 }}>
                        No divers with a partial overlap (at least one cert matched, but not all).
                      </p>
                    ) : (
                      <DiversCertMatchTable
                        rows={match.partial_items}
                        emailSelection={emailPick}
                        onEmailToggle={toggleEmailTarget}
                      />
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {wizardStep === 4 && step3Active && (
            <div className="wizard-step wizard-step--email">
              <div className="panel panel--operator">
                <h2>Email outreach</h2>
                <p className="email-outreach__lead" style={{ paddingTop: "0.35rem" }}>
                  Tick <strong>Email</strong> in the previous step (or use shortcuts below). Preview
                  uses the same selected <strong>job postings</strong> as the match. Each diver gets
                  a personalized greeting; the listed roles are identical for everyone.
                </p>
                <p className="wizard-step__intro wizard-step__intro--compact">
                  <strong>{selectedJobs.size}</strong> job(s) · <strong>{emailPick.size}</strong>{" "}
                  diver(s) in send list — go back to step 3 to change table selections.
                </p>
                <div className="email-outreach email-outreach--standalone">
                  <div className="email-outreach__toolbar">
                    <span className="email-outreach__count">
                      <strong>{emailPick.size}</strong> diver(s) in send list
                    </span>
                    <span className="email-outreach__shortcuts">
                      <button type="button" className="btn-link" onClick={addAllFullToEmail}>
                        Add all full matches
                      </button>
                      <button type="button" className="btn-link" onClick={addAllPartialToEmail}>
                        Add all partial matches
                      </button>
                      <button type="button" className="btn-link" onClick={clearEmailTargets}>
                        Clear send list
                      </button>
                    </span>
                  </div>
                  <div className="email-outreach__preview-row">
                    <label className="email-outreach__label">
                      <span>Preview as diver</span>
                      <select
                        value={previewDiverId ?? ""}
                        onChange={(e) => {
                          const v = e.target.value;
                          setPreviewDiverId(v ? Number(v) : null);
                          setEmailPreview(null);
                        }}
                        disabled={emailPickOptions.length === 0}
                      >
                        {emailPickOptions.length === 0 ? (
                          <option value="">— Select divers from step 3 —</option>
                        ) : (
                          emailPickOptions.map((o) => (
                            <option key={o.id} value={o.id}>
                              {o.name} (#{o.id})
                            </option>
                          ))
                        )}
                      </select>
                    </label>
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={
                        selectedJobs.size === 0 ||
                        emailPick.size === 0 ||
                        previewDiverId == null ||
                        emailPreviewLoading
                      }
                      onClick={() => void loadEmailPreview()}
                    >
                      {emailPreviewLoading ? "Loading preview…" : "Update preview"}
                    </button>
                    <button
                      type="button"
                      className="btn-primary"
                      disabled={
                        selectedJobs.size === 0 || emailPick.size === 0 || emailSendLoading
                      }
                      onClick={() => void sendOutreachEmails()}
                    >
                      {emailSendLoading ? "Sending…" : "Send emails"}
                    </button>
                  </div>
                  {emailPreviewErr && <p className="error">{emailPreviewErr}</p>}
                  {emailSendNote && <p className="email-outreach__send-note">{emailSendNote}</p>}
                  {emailPreview && (
                    <div className="email-preview-box">
                      <div className="email-preview-meta">
                        <div>
                          <span className="email-preview-meta__k">Subject</span>
                          <span className="email-preview-meta__v">{emailPreview.subject}</span>
                        </div>
                        <div>
                          <span className="email-preview-meta__k">To</span>
                          <span className="email-preview-meta__v">
                            {emailPreview.to_name} &lt;{emailPreview.to_email}&gt;
                          </span>
                        </div>
                        <div>
                          <span className="email-preview-meta__k">Jobs in body</span>
                          <span className="email-preview-meta__v">{emailPreview.job_count}</span>
                        </div>
                      </div>
                      <div className="email-preview-tabs">
                        <div className="email-preview-tabs__main">
                          <button
                            type="button"
                            className={
                              emailPreviewTab === "html"
                                ? "email-preview-tab email-preview-tab--active"
                                : "email-preview-tab"
                            }
                            onClick={() => setEmailPreviewTab("html")}
                          >
                            HTML (inbox view)
                          </button>
                          <button
                            type="button"
                            className={
                              emailPreviewTab === "text"
                                ? "email-preview-tab email-preview-tab--active"
                                : "email-preview-tab"
                            }
                            onClick={() => setEmailPreviewTab("text")}
                          >
                            Plain text
                          </button>
                        </div>
                        {emailPreviewTab === "html" && (
                          <div className="email-preview-tabs__actions">
                            <button
                              type="button"
                              className="btn-link"
                              onClick={() => setHtmlPreviewLightbox(true)}
                            >
                              Full screen
                            </button>
                            <button
                              type="button"
                              className="btn-link"
                              onClick={() =>
                                openEmailBodyHtmlInNewTab(
                                  emailPreview.body_html,
                                  emailPreview.subject,
                                )
                              }
                            >
                              Open in new tab
                            </button>
                          </div>
                        )}
                      </div>
                      {emailPreviewTab === "html" ? (
                        <iframe
                          title="Email preview"
                          className="email-preview-frame email-preview-frame--wizard"
                          sandbox="allow-same-origin"
                          srcDoc={emailPreview.body_html}
                        />
                      ) : (
                        <pre className="email-preview-text email-preview-text--wizard">
                          {emailPreview.body_text}
                        </pre>
                      )}
                    </div>
                  )}
                  {!emailPreview && !emailPreviewErr && !emailPreviewLoading && emailPick.size > 0 && (
                    <p className="muted email-outreach__hint">
                      Choose a diver and click <strong>Update preview</strong> to see the message.
                    </p>
                  )}
                  {!emailPreview && !emailPreviewErr && !emailPreviewLoading && emailPick.size === 0 && (
                    <p className="muted email-outreach__hint">
                      Add divers from the match tables on step 3, or use the shortcuts above.
                    </p>
                  )}
                  <p className="muted email-outreach__foot">
                    Sending requires SMTP in server env (<code>EMAIL_SEND_ENABLED</code>,{" "}
                    <code>SMTP_HOST</code>, <code>SMTP_FROM_EMAIL</code>, etc.). If not configured,
                    preview still works; send returns an error explaining what is missing.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <footer className="newsletter-wizard__footer">
          <div className="newsletter-wizard__footer-start">
            {wizardStep > 1 && (
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setWizardStep((w) => (w - 1) as 1 | 2 | 3 | 4)}
              >
                Back
              </button>
            )}
          </div>
          <div className="newsletter-wizard__footer-end">
            {wizardStep === 1 && (
              <button
                type="button"
                className="btn-primary btn-primary--lg"
                disabled={selectedJobs.size === 0}
                onClick={() => setWizardStep(2)}
              >
                Continue
              </button>
            )}
            {wizardStep === 2 && (
              <button
                type="button"
                className="btn-primary btn-primary--lg"
                disabled={selectedJobs.size === 0 || matchLoading}
                onClick={() => void runMatch()}
              >
                {matchLoading ? "Running match…" : "Run certification match"}
              </button>
            )}
            {wizardStep === 3 && step3Active && (
              <button
                type="button"
                className="btn-primary btn-primary--lg"
                onClick={() => setWizardStep(4)}
              >
                Continue to email
              </button>
            )}
          </div>
        </footer>
      </div>
    </div>
    {htmlPreviewLightboxEl}
    </>
  );
}

function DashboardHome() {
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
    <>
      <header className="page-header">
        <h1 className="page-title">Overview</h1>
        <p className="page-lead">
          Registration stats, directory search, and subscription status. Use the links below to jump
          to a section.
        </p>
      </header>
      <nav className="page-toc" aria-label="Jump to section">
        <span className="page-toc__label">Jump to</span>
        <a href="#ops-overview">Registration</a>
        <a href="#ops-divers">Divers</a>
        <a href="#ops-companies">Companies</a>
        <a href="#ops-div-subs">Diver subscriptions</a>
        <a href="#ops-co-subs">Company subscriptions</a>
      </nav>

      <section id="ops-overview" className="page-section">
        <StatBlock title="Registration" u={usersS} c={companiesS} />
      </section>

      <section id="ops-divers" className="page-section">
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
      </section>

      <section id="ops-companies" className="page-section">
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
      </section>

      <section id="ops-div-subs" className="page-section">
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
      </section>

      <section id="ops-co-subs" className="page-section">
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
      </section>
    </>
  );
}

export default function App() {
  const path = useSyncExternalStore(subscribeHash, hashPathSnapshot, () => "/");

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Application">
        <div className="sidebar__brand">WDW Ops</div>
        <p className="sidebar__tagline">Internal operator console</p>
        <nav className="sidebar__nav" aria-label="Primary">
          <a
            href="#/"
            className={
              path === "/"
                ? "sidebar__link sidebar__link--active"
                : "sidebar__link"
            }
          >
            <span className="sidebar__link-title">Overview</span>
            <span className="sidebar__link-desc">Sign-ups, directories, billing</span>
          </a>
          <a
            href="#/newsletter"
            className={
              path === "/newsletter"
                ? "sidebar__link sidebar__link--active"
                : "sidebar__link"
            }
          >
            <span className="sidebar__link-title">Newsletter match</span>
            <span className="sidebar__link-desc">Jobs vs diver certifications</span>
          </a>
        </nav>
        <p className="sidebar__foot">
          API <code>/api/v1</code>
          <br />
          Vite proxies to FastAPI :8000
        </p>
      </aside>
      <div className="app-main">
        <main className="app-content">
          {path === "/newsletter" ? <NewsletterSection /> : <DashboardHome />}
        </main>
      </div>
    </div>
  );
}
