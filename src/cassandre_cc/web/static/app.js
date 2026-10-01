// Cassandre CC dashboard. Talks only to this app's own /v1/ API — no
// external network calls, no invented bank endpoints.

(function () {
  "use strict";

  const facilityList = document.getElementById("facility-list");
  const appMain = document.getElementById("app-main");
  const tpl = document.getElementById("tpl-facility-detail");

  let activeFacilityId = null;
  let activePeriod = null;

  const CHIP_CLASS = {
    compliant: "chip--ok",
    verified: "chip--ok",
    received: "chip--ok",
    renewed: "chip--ok",
    closed: "chip--ok",
    active: "chip--ok",
    near_threshold: "chip--near",
    due: "chip--near",
    reviewed: "chip--near",
    pending: "chip--near",
    indeterminate: "chip--unknown",
    not_due: "chip--unknown",
    incomplete: "chip--unknown",
    draft: "chip--unknown",
    open: "chip--unknown",
    waived_for_scope: "chip--unknown",
    superseded: "chip--unknown",
    potential_breach: "chip--breach",
    confirmed_breach: "chip--breach",
    rejected: "chip--breach",
    declined: "chip--breach",
  };

  function chip(value, kind) {
    const cls = CHIP_CLASS[value] || "chip--unknown";
    const label = (value || "—").replace(/_/g, " ");
    return `<span class="${kind}-chip ${cls}">${label}</span>`;
  }

  async function api(path, options) {
    const resp = await fetch(path, options);
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      const err = new Error("request failed");
      err.status = resp.status;
      err.body = body;
      throw err;
    }
    return body;
  }

  function showError(el, err) {
    el.hidden = false;
    const failure = err.body && err.body.detail ? err.body.detail : err.body;
    el.textContent =
      typeof failure === "object" && failure !== null
        ? `${failure.failure || "ERROR"}: ${failure.message || JSON.stringify(failure)}`
        : String(failure);
  }

  async function loadFacilities() {
    const facilities = await api("/v1/facilities");
    facilityList.innerHTML = "";
    facilities.forEach((f) => {
      const btn = document.createElement("button");
      btn.className = "facility-card" + (f.facility_id === activeFacilityId ? " active" : "");
      btn.innerHTML = `<span class="fc-name">${f.borrower_name}</span><span class="fc-ref">${f.external_facility_ref} · ${f.state}</span>`;
      btn.addEventListener("click", () => selectFacility(f.facility_id));
      facilityList.appendChild(btn);
    });
    if (!activeFacilityId && facilities.length) {
      selectFacility(facilities[0].facility_id);
    }
  }

  function formatMoney(m) {
    if (!m) return "—";
    return `₹${m.amount} ${m.unit}`;
  }

  async function selectFacility(facilityId) {
    activeFacilityId = facilityId;
    activePeriod = null;
    await loadFacilities();
    await renderFacility(facilityId);
  }

  async function renderFacility(facilityId) {
    appMain.innerHTML = "";
    const node = tpl.content.cloneNode(true);
    appMain.appendChild(node);

    const detail = await api(`/v1/facilities/${facilityId}${activePeriod ? `?period=${activePeriod}` : ""}`);
    activePeriod = detail.calculation.period;

    appMain.querySelector('[data-field="external_ref"]').textContent = detail.external_borrower_ref;
    appMain.querySelector('[data-field="borrower_name"]').textContent = detail.borrower_name;
    appMain.querySelector('[data-field="sanctioned_limit"]').textContent = `₹${detail.sanctioned_limit_crore} crore`;
    appMain.querySelector('[data-field="facility_state"]').textContent = detail.state.toUpperCase();

    const periodSelect = appMain.querySelector("#period-select");
    periodSelect.innerHTML = detail.periods.map((p) => `<option value="${p}">${p}</option>`).join("");
    periodSelect.value = activePeriod;
    periodSelect.addEventListener("change", async () => {
      activePeriod = periodSelect.value;
      await renderFacility(facilityId);
    });

    renderCalculation(detail.calculation);
    renderEvidence(detail.evidence);
    renderRuleVersions(detail.rule_versions);
    renderCureTasks(detail.cure_tasks);
    renderClosure(facilityId, detail.closure_checklist, detail.closure_ready, detail.state);

    appMain.querySelector("#recompute-btn").addEventListener("click", async () => {
      const calc = await api(`/v1/facilities/${facilityId}/calculations:recompute?period=${activePeriod}`, { method: "POST" });
      renderCalculation(calc);
      await renderAudit(facilityId);
      await renderFacilityCureAndWaivers(facilityId);
    });

    appMain.querySelector("#import-form").addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const form = ev.target;
      const payload = Object.fromEntries(new FormData(form).entries());
      payload.facility_id = facilityId;
      const errBox = appMain.querySelector("#import-result");
      errBox.hidden = true;
      try {
        const result = await api("/v1/imports:financials", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        activePeriod = payload.period;
        await renderFacility(facilityId);
      } catch (err) {
        showError(errBox, err);
      }
    });

    appMain.querySelector("#rule-version-form").addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const form = ev.target;
      const payload = Object.fromEntries(new FormData(form).entries());
      payload.debtor_ageing_cutoff_days = parseInt(payload.debtor_ageing_cutoff_days, 10);
      const errBox = appMain.querySelector("#rule-version-result");
      errBox.hidden = true;
      try {
        await api(`/v1/facilities/${facilityId}/rule-versions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const updated = await api(`/v1/facilities/${facilityId}?period=${activePeriod}`);
        renderRuleVersions(updated.rule_versions);
        form.reset();
      } catch (err) {
        showError(errBox, err);
      }
    });

    await renderFacilityCureAndWaivers(facilityId);
    await renderRenewal(facilityId);
    await renderCases();
    await renderAudit(facilityId);
    await renderShadowScore(facilityId);
  }

  function renderCalculation(calc) {
    appMain.querySelector('[data-field="period"]').textContent = calc.period;
    const isIndeterminate = calc.result_state === "indeterminate";

    const icon = appMain.querySelector("#dp-state-icon");
    icon.classList.toggle("is-indeterminate", isIndeterminate);
    icon.textContent = isIndeterminate ? "?" : "✓";

    appMain.querySelector('[data-field="result_state"]').textContent = isIndeterminate
      ? "Indeterminate"
      : "Calculated";

    const banner = appMain.querySelector("#dp-missing-banner");
    if (isIndeterminate) {
      banner.hidden = false;
      appMain.querySelector('[data-field="missing_fields"]').textContent = calc.missing_fields.join(", ");
    } else {
      banner.hidden = true;
    }

    const rows = appMain.querySelector("#dp-rows");
    rows.innerHTML = "";
    const entries = [
      ["Eligible stock", formatMoney(calc.eligible_stock)],
      ["Eligible receivables", formatMoney(calc.eligible_receivables)],
      ["Proposed DP", formatMoney(calc.proposed_dp)],
      ["Usable cap", formatMoney(calc.usable_cap)],
      ["Indicative headroom", formatMoney(calc.headroom)],
      ["Rule-set version", calc.rule_set_version != null ? `v${calc.rule_set_version} (${calc.rule_set_state})` : "—"],
      ["Covenant finding", calc.covenant_finding ? chip(calc.covenant_finding, "finding") + (calc.waiver_applied ? " <em>waived</em>" : "") : "—"],
    ];
    entries.forEach(([label, value]) => {
      const row = document.createElement("div");
      row.innerHTML = `<dt>${label}</dt><dd>${value}</dd>`;
      rows.appendChild(row);
    });
  }

  function renderEvidence(evidence) {
    const tbody = appMain.querySelector("#evidence-table tbody");
    tbody.innerHTML = "";
    evidence.forEach((e) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${e.field_name.replace(/_/g, " ")}</td><td>${e.period}</td><td>${chip(e.state, "evidence")}</td><td>${e.reviewer || "—"}</td>`;
      tbody.appendChild(tr);
    });
  }

  function renderRuleVersions(versions) {
    const tbody = appMain.querySelector("#rule-versions-table tbody");
    tbody.innerHTML = "";
    versions.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>v${r.version}</td>
        <td>${(parseFloat(r.stock_margin) * 100).toFixed(0)}% / ${(parseFloat(r.receivable_margin) * 100).toFixed(0)}%</td>
        <td>${r.debtor_ageing_cutoff_days}d</td>
        <td>${r.effective_from || "—"}</td>
        <td>${chip(r.state, "rule")} ${r.state === "reviewed" ? `<button class="btn btn-small" data-approve-rule="${r.rule_set_id}">Approve</button>` : ""}</td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-approve-rule]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const errBox = appMain.querySelector("#rule-version-result");
        errBox.hidden = true;
        try {
          await api(`/v1/rule-versions/${btn.dataset.approveRule}:approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ approver: "checker.arvind", effective_from: new Date().toISOString().slice(0, 10) }),
          });
          const updated = await api(`/v1/facilities/${activeFacilityId}?period=${activePeriod}`);
          renderRuleVersions(updated.rule_versions);
          renderCalculation(updated.calculation);
        } catch (err) {
          showError(errBox, err);
        }
      });
    });
  }

  function renderCureTasks(cureTasks) {
    const tbody = appMain.querySelector("#cure-tasks-table tbody");
    tbody.innerHTML = "";
    cureTasks.forEach((c) => {
      const tr = document.createElement("tr");
      const when = new Date(c.opened_at).toLocaleDateString();
      tr.innerHTML = `<td>${c.cure_id}</td><td>${c.test_id}</td><td>${c.period}</td><td>${when}</td><td>${chip(c.status, "evidence")}</td>`;
      tbody.appendChild(tr);
    });
  }

  async function renderFacilityCureAndWaivers(facilityId) {
    const waivers = await api(`/v1/waivers?facility_id=${facilityId}`);
    const tbody = appMain.querySelector("#waivers-table tbody");
    tbody.innerHTML = "";
    waivers.forEach((w) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${w.waiver_id}</td>
        <td>${w.test_id}</td>
        <td>${w.scoped_period}${w.expires_after_period ? " – " + w.expires_after_period : ""}</td>
        <td>${w.submitted_by}</td>
        <td>${chip(w.state, "evidence")} ${w.state === "reviewed" ? `<button class="btn btn-small" data-approve-waiver="${w.waiver_id}">Approve</button>` : ""}</td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-approve-waiver]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const errBox = appMain.querySelector("#waiver-error");
        errBox.hidden = true;
        try {
          await api(`/v1/waivers/${btn.dataset.approveWaiver}:approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ approver: "credit.suresh" }),
          });
          await renderFacility(facilityId);
        } catch (err) {
          showError(errBox, err);
        }
      });
    });
  }

  async function renderRenewal(facilityId) {
    const renewals = await api("/v1/renewals");
    const mine = renewals.filter((r) => r.facility_id === facilityId);
    const block = appMain.querySelector("#renewal-block");
    if (!mine.length) {
      block.innerHTML = "<p class=\"loading\">No renewal cycle open.</p>";
      return;
    }
    block.innerHTML = mine
      .map(
        (r) => `
      <div class="renewal-row">
        <span>${r.review_cycle_period}</span>
        ${chip(r.decision, "evidence")}
        ${r.decision === "pending" ? `
          <button class="btn btn-small" data-renew="${r.renewal_id}" data-decision="renewed">Renew</button>
          <button class="btn btn-small" data-renew="${r.renewal_id}" data-decision="declined">Decline</button>
        ` : `<span class="loading">decided by ${r.decided_by || "—"}</span>`}
      </div>`
      )
      .join("");

    block.querySelectorAll("button[data-renew]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await api(`/v1/renewals/${btn.dataset.renew}:decide`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision: btn.dataset.decision, decided_by: "credit.suresh" }),
        });
        await renderRenewal(facilityId);
      });
    });
  }

  function renderClosure(facilityId, checklist, ready, facilityState) {
    const block = appMain.querySelector("#closure-block");
    const closeBtn = appMain.querySelector("#close-facility-btn");
    if (!checklist) {
      block.innerHTML = "<p class=\"loading\">No closure checklist.</p>";
      closeBtn.hidden = true;
      return;
    }
    const items = [
      ["dues_reconciled", "Dues reconciled"],
      ["security_released", "Security released"],
      ["linked_exposures_clear", "Linked exposures clear"],
      ["originals_returned", "Originals returned"],
    ];
    block.innerHTML = items
      .map(
        ([key, label]) => `
      <label class="closure-item">
        <input type="checkbox" data-closure-key="${key}" ${checklist[key] ? "checked" : ""} ${facilityState === "closed" ? "disabled" : ""} />
        ${label}
      </label>`
      )
      .join("");

    block.querySelectorAll("input[data-closure-key]").forEach((input) => {
      input.addEventListener("change", async () => {
        await api(`/v1/facilities/${facilityId}/closure`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ [input.dataset.closureKey]: input.checked, actor: "ops.rahul" }),
        });
        await renderFacility(facilityId);
      });
    });

    closeBtn.hidden = facilityState === "closed";
    closeBtn.disabled = !ready;
    closeBtn.onclick = async () => {
      const errBox = appMain.querySelector("#closure-error");
      errBox.hidden = true;
      try {
        await api(`/v1/facilities/${facilityId}:close`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ actor: "ops.rahul" }),
        });
        await renderFacility(facilityId);
        await loadFacilities();
      } catch (err) {
        showError(errBox, err);
      }
    };
  }

  async function renderCases() {
    const tbody = appMain.querySelector("#cases-table tbody");
    const errorBanner = appMain.querySelector("#case-error");
    tbody.innerHTML = "";
    const cases = await api("/v1/cases");
    cases.forEach((c) => {
      const tr = document.createElement("tr");
      const canApprove = c.state === "reviewed";
      tr.innerHTML = `
        <td>${c.case_id}</td>
        <td>${c.subject_type} · ${c.subject_id}</td>
        <td>${c.submitted_by}</td>
        <td>${chip(c.state, "evidence")}</td>
        <td>${canApprove ? `<button class="btn btn-small" data-case="${c.case_id}" data-submitter="${c.submitted_by}">Approve as submitter</button> <button class="btn btn-small" data-case="${c.case_id}" data-submitter="">Approve as checker.arvind</button>` : ""}</td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-case]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        errorBanner.hidden = true;
        const caseId = btn.dataset.case;
        const approver = btn.dataset.submitter || "checker.arvind";
        try {
          await api(`/v1/cases/${caseId}:approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ approver }),
          });
          await renderCases();
          await renderAudit(activeFacilityId);
        } catch (err) {
          showError(errorBanner, err);
        }
      });
    });
  }

  async function renderAudit(facilityId) {
    const tbody = appMain.querySelector("#audit-table tbody");
    if (!tbody) return;
    const events = await api(`/v1/audit-events`);
    tbody.innerHTML = "";
    events.slice(0, 15).forEach((e) => {
      const tr = document.createElement("tr");
      const when = new Date(e.occurred_at).toLocaleString();
      tr.innerHTML = `<td>${when}</td><td>${e.actor}</td><td>${e.action}</td><td>${e.detail}</td>`;
      tbody.appendChild(tr);
    });
  }

  async function renderShadowScore(facilityId) {
    const badge = document.getElementById("shadow-score-badge");
    try {
      const result = await api(`/v1/facilities/${facilityId}/shadow-score?period=${activePeriod}`);
      badge.textContent = `shadow score: ${result.score}/100 (heuristic, not predictive)`;
      badge.title = result.disclaimer + " Basis: " + result.basis;
    } catch (err) {
      badge.textContent = "shadow score unavailable";
    }
  }

  loadFacilities();
})();
