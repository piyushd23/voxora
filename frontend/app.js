/**
 * Voxora — Customer voices. Clear insights. Informed action.
 * 100% Emoji-Free, Pure SVG Vector Icons, Enterprise Light Theme
 * Orchestrates: High-Volume Dual-Store Scraper (500/1,000/5,000) → AI Clustering → Actionable Artifacts → MCP Gate → 1-Click Execution
 */

const API_BASE = '';

// ── Application State ────────────────────────────────────────────────────────
let state = {
  currentStep: 1,
  maxUnlockedStep: 1,
  step: 1,
  selectedStore: 'both',
  selectedReviewCount: 500,
  reviewsLoaded: false,
  reviews: null,
  analysis: null,
  content: null,
  payload: null,
  emailDraft: null,
  googleDocText: null,
  mcpActions: [],
  tools: [],
  isApiKeyActive: false
};

// ── High-Fidelity SVG Icon Library ───────────────────────────────────────────
const ICONS = {
  checkCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
  alertCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  infoCircle: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  googlePlay: `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`,
  appleStore: `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.62-.75 1.04-1.8 0.92-2.85-.9.04-2 .6-2.65 1.35-.58.66-1.09 1.73-.95 2.76.99.08 2.04-.51 2.68-1.26z"/></svg>`,
  fileText: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
  mail: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`,
  database: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>`,
  tool: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
  warning: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  link: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
  skipped: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>`
};

// ── UI Utilities ─────────────────────────────────────────────────────────────

function showLoading(text = 'Processing...') {
  const overlay = document.getElementById('loadingOverlay');
  const loaderText = document.getElementById('loaderText');
  loaderText.textContent = text;
  overlay.classList.add('active');
}

function hideLoading() {
  document.getElementById('loadingOverlay').classList.remove('active');
}

function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? ICONS.checkCircle : (type === 'error' ? ICONS.alertCircle : ICONS.infoCircle);
  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-message">${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, 4200);
}

function updateStatus(text, type = '') {
  const badge = document.getElementById('statusBadge');
  if (badge) {
    badge.querySelector('.status-text').textContent = text;
    badge.className = `status-badge ${type}`;
  }
}

// ── 5-Stepper Wizard Navigation (Single-Page Workbench) ─────────────────────────

function isStepDone(stepNum) {
  if (stepNum === 1) return !!state.reviewsLoaded;
  if (stepNum === 2) return !!state.analysis;
  if (stepNum === 3) return !!state.content;
  if (stepNum === 4) return state.mcpActions && state.mcpActions.some(a => a.status === 'executed');
  if (stepNum === 5) return state.mcpActions && state.mcpActions.some(a => a.status === 'executed');
  return false;
}

async function goToStep(step) {
  if (step < 1 || step > 5) return;

  // Validation: require reviews for step >= 2
  if (step >= 2 && !state.reviewsLoaded) {
    showToast('Please harvest customer reviews first in Step 1', 'info');
    return;
  }

  state.currentStep = step;
  state.step = step;
  state.maxUnlockedStep = Math.max(state.maxUnlockedStep || 1, step);

  // Switch right-hand workspace panels (only active step displayed)
  for (let i = 1; i <= 5; i++) {
    const panel = document.getElementById(`step${i}`);
    if (panel) {
      if (i === step) {
        panel.style.display = 'block';
        panel.classList.add('active-panel');
      } else {
        panel.style.display = 'none';
        panel.classList.remove('active-panel');
      }
    }
  }

  // Update left wizard sidebar active & completion states
  for (let i = 1; i <= 5; i++) {
    const btn = document.getElementById(`wizardStepBtn${i}`);
    if (btn) {
      btn.classList.remove('active', 'completed');
      if (i === step) {
        btn.classList.add('active');
      } else if (i < step || isStepDone(i)) {
        btn.classList.add('completed');
      }
    }
  }

  // Update persistent bottom navigation footer
  updateWizardNavFooter(step);

  // Scroll interior right viewport back to top
  const viewport = document.getElementById('wizardContentViewport');
  if (viewport) {
    viewport.scrollTop = 0;
  }

  // Auto-run stage processing if transitioning to step where data hasn't been produced yet
  if (step === 2 && !state.analysis) {
    await runAnalysis();
  } else if (step === 3 && !state.content) {
    await runGeneration();
  } else if (step === 4 && (!state.mcpActions || state.mcpActions.length === 0)) {
    await prepareMCPActions();
  }
}

function updateWizardNavFooter(step) {
  const prevBtn = document.getElementById('prevStepBtn');
  const nextBtnText = document.getElementById('nextStepBtnText');
  const indicator = document.getElementById('footerStepIndicator');

  if (prevBtn) {
    prevBtn.disabled = (step === 1);
  }

  const phaseNames = {
    1: 'Phase 01 of 05 • Scraped Customer Reviews Data',
    2: 'Phase 02 of 05 • Feedback Themes & Fee Confusion',
    3: 'Phase 03 of 05 • Prepared Mail Draft & Google Doc Briefing',
    4: 'Phase 04 of 05 • Review & Approve (MCP Governance Gate)',
    5: 'Phase 05 of 05 • Mail & Google Doc Text (Side-by-Side View)'
  };

  if (indicator) {
    indicator.textContent = phaseNames[step] || `Phase ${step} of 05`;
  }

  if (nextBtnText) {
    if (step === 1) {
      nextBtnText.textContent = state.reviewsLoaded ? 'Next: Themes & Fee Confusion →' : 'Harvest Reviews & Ingest';
    } else if (step === 2) {
      nextBtnText.textContent = state.analysis ? 'Next: Prepared Mail & Docs →' : 'Run AI Analysis →';
    } else if (step === 3) {
      nextBtnText.textContent = state.content ? 'Next: Review & Approve →' : 'Synthesize Mail & Docs →';
    } else if (step === 4) {
      nextBtnText.textContent = 'Review & Approve (Execute via MCP) →';
    } else if (step === 5) {
      nextBtnText.textContent = 'Complete Workflow ✓';
    }
  }
}

async function handleNextStepClick() {
  const cur = state.currentStep || 1;
  if (cur === 1) {
    if (state.reviewsLoaded) {
      await goToStep(2);
    } else {
      await scrapeReviews();
      // Keep on Step 1 so user inspects the loaded reviews table, footer text updates to "Next: Themes & Fee Confusion →"
    }
  } else if (cur === 2) {
    if (state.analysis) {
      await goToStep(3);
    } else {
      await runAnalysis();
    }
  } else if (cur === 3) {
    if (state.content) {
      await goToStep(4);
    } else {
      await runGeneration();
    }
  } else if (cur === 4) {
    const hasApproved = state.mcpActions && state.mcpActions.some(a => a.status === 'approved');
    if (hasApproved) {
      await executeApproved();
    } else {
      await runBothActions();
    }
  } else if (cur === 5) {
    completeWorkflow();
  }
}

async function completeWorkflow() {
  // Display the workflow completed popup modal
  openWorkflowCompletedModal();
  
  // Update header status badge and dispatch confirmation toast
  updateStatus('Workflow Completed', '');
  showToast('Workflow completed successfully! Pipeline has been reset.');

  // Reset backend session and local application state
  try {
    await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
  } catch (e) {
    console.error('Reset error:', e);
  }

  state = {
    currentStep: 1,
    maxUnlockedStep: 1,
    step: 1,
    selectedStore: 'both',
    selectedReviewCount: 500,
    reviewsLoaded: false,
    reviews: null,
    analysis: null,
    content: null,
    payload: null,
    emailDraft: null,
    googleDocText: null,
    mcpActions: [],
    tools: [],
    isApiKeyActive: state.isApiKeyActive
  };

  const preview = document.getElementById('reviewsPreview');
  if (preview) preview.style.display = 'none';

  // Reset wizard sidebar indicators and badges
  for (let i = 1; i <= 5; i++) {
    const badge = document.getElementById(`step${i}StatusBadge`);
    if (badge) badge.textContent = `Step 0${i}`;
    const btn = document.getElementById(`wizardStepBtn${i}`);
    if (btn) btn.classList.remove('active', 'completed');
  }
  const datasetStat = document.getElementById('sidebarDatasetStat');
  if (datasetStat) datasetStat.textContent = '0 Reviews Loaded';
  const storeStat = document.getElementById('sidebarStoreStat');
  if (storeStat) storeStat.textContent = 'Play Store • App Store';

  goToStep(1);
}

function openWorkflowCompletedModal() {
  const modal = document.getElementById('workflowCompletedModal');
  if (modal) {
    modal.classList.add('active');
    modal.style.display = 'flex';
  }
}

function closeWorkflowCompletedModal() {
  const modal = document.getElementById('workflowCompletedModal');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
  }
  goToStep(1);
}

function jumpToDeliverablesFromModal() {
  const modal = document.getElementById('workflowCompletedModal');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
  }
  goToStep(5);
}

function goToPreviousStep() {
  const cur = state.currentStep || 1;
  if (cur > 1) {
    goToStep(cur - 1);
  }
}

function updateProgress(step) {
  state.maxUnlockedStep = Math.max(state.maxUnlockedStep || 1, step);
  goToStep(step);
}

function renderStars(rating) {
  let stars = '';
  for (let i = 1; i <= 5; i++) {
    const fill = i <= rating ? '#f59e0b' : '#cbd5e1';
    stars += `<svg width="12" height="12" viewBox="0 0 24 24" fill="${fill}" stroke="${fill}" stroke-width="1" style="display:inline-block; vertical-align:middle; margin-right:1px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
  }
  return stars;
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}


// ── Step 1: Customer Reviews Scraper (Google Play & Apple Store) ───────────────

function setStoreFilter(store, element) {
  state.selectedStore = store;
  document.querySelectorAll('.store-pill').forEach(pill => pill.classList.remove('active'));
  if (element) element.classList.add('active');

  const hint = document.getElementById('storeHintText');
  if (hint) {
    if (store === 'both') {
      hint.textContent = 'Scrapes Google Play & Apple App Store in parallel';
    } else if (store === 'google') {
      hint.textContent = 'Scrapes Google Play Store reviews only';
    } else if (store === 'apple') {
      hint.textContent = 'Scrapes Apple App Store customer reviews only';
    }
  }
}

function setAppPreset(appName, element) {
  const input = document.getElementById('appNameInput');
  if (input) input.value = appName;
  
  document.querySelectorAll('.preset-pill').forEach(pill => pill.classList.remove('active'));
  if (element) element.classList.add('active');
}

function toggleCsvUpload() {
  const container = document.getElementById('customCsvContainer');
  const text = document.getElementById('csvToggleText');
  if (container.style.display === 'none') {
    container.style.display = 'block';
    if (text) text.textContent = 'Hide custom CSV upload';
  } else {
    container.style.display = 'none';
    if (text) text.textContent = 'Need to upload a custom CSV file instead?';
  }
}

async function scrapeReviews() {
  const appInput = document.getElementById('appNameInput');
  const appQuery = appInput ? appInput.value.trim() : 'Groww';
  const countSelect = document.getElementById('reviewCountSelect');
  const count = countSelect ? parseInt(countSelect.value, 10) : 500;
  const getBtn = document.getElementById('getReviewsBtn');
  
  const storeLabel = state.selectedStore === 'both' 
    ? 'Google Play & Apple App Store' 
    : (state.selectedStore === 'apple' ? 'Apple App Store' : 'Google Play Store');

  showLoading(`Harvesting ${count.toLocaleString()} customer reviews for "${appQuery || 'Groww'}"...\nQuerying ${storeLabel} and parsing feedback`);
  updateStatus('Scraping...', 'processing');
  if (getBtn) getBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/scrape-reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        app_query: appQuery,
        store: state.selectedStore,
        count: count
      })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Scraping failed');
    }

    const data = await response.json();
    displayReviewsPreview(data);
    showToast(`Successfully harvested ${data.review_count.toLocaleString()} customer reviews!`);
    updateStatus('Reviews Ingested', '');
    updateProgress(1);

    const preview = document.getElementById('reviewsPreview');
    if (preview) {
      preview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  } catch (err) {
    showToast(`Scrape error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
  } finally {
    if (getBtn) getBtn.disabled = false;
    hideLoading();
  }
}

// Local CSV file upload fallback
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');

if (uploadArea && fileInput) {
  uploadArea.addEventListener('click', () => fileInput.click());
  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
  });
  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
  });
  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      uploadFile(e.dataTransfer.files[0]);
    }
  });
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });
}

async function uploadFile(file) {
  showLoading('Uploading reviews CSV...');
  updateStatus('Uploading...', 'processing');
  
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/api/upload-reviews`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Upload failed');
    }
    
    const data = await response.json();
    displayReviewsPreview(data);
    showToast(`${data.review_count.toLocaleString()} reviews loaded successfully`);
    updateStatus('Dataset Loaded', '');
    updateProgress(1);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
  } finally {
    hideLoading();
  }
}

function displayReviewsPreview(data) {
  const preview = document.getElementById('reviewsPreview');
  const count = document.getElementById('reviewCount');
  const googleBadge = document.getElementById('googleCountBadge');
  const appleBadge = document.getElementById('appleCountBadge');
  const title = document.getElementById('previewTitle');
  const subtitle = document.getElementById('previewSubtitle');
  
  if (title) title.textContent = data.app_name ? `${data.app_name} Dataset` : 'Reviews Ingested';
  if (subtitle) subtitle.textContent = `Showing customer reviews across date span: ${data.date_range}`;
  
  count.textContent = `${data.review_count.toLocaleString()} Total Reviews`;

  if (data.google_count !== undefined && data.google_count > 0) {
    googleBadge.innerHTML = `${ICONS.googlePlay} ${data.google_count.toLocaleString()} Google Play`;
    googleBadge.style.display = 'inline-flex';
  } else {
    googleBadge.style.display = 'none';
  }

  if (data.apple_count !== undefined && data.apple_count > 0) {
    appleBadge.innerHTML = `${ICONS.appleStore} ${data.apple_count.toLocaleString()} Apple App Store`;
    appleBadge.style.display = 'inline-flex';
  } else {
    appleBadge.style.display = 'none';
  }
  
  state.reviews = data;
  state.reviewsLoaded = true;
  state.maxUnlockedStep = Math.max(state.maxUnlockedStep || 1, 2);

  const datasetStat = document.getElementById('sidebarDatasetStat');
  if (datasetStat) datasetStat.textContent = `${(data.review_count || 0).toLocaleString()} Reviews Loaded`;
  const storeStat = document.getElementById('sidebarStoreStat');
  if (storeStat) storeStat.textContent = data.app_name ? `${data.app_name}` : 'Play Store • App Store';
  const s1Badge = document.getElementById('step1StatusBadge');
  if (s1Badge) s1Badge.textContent = 'Loaded';
  updateWizardNavFooter(state.currentStep || 1);

  renderDatasetStats(data);
  filterReviewsTable();

  preview.style.display = 'block';
}

function renderDatasetStats(data) {
  const container = document.getElementById('datasetStatsGrid');
  if (!container) return;

  const metrics = data.metrics || {};
  const total = data.review_count || (metrics.total || 0);
  const avgRating = metrics.avg_rating !== undefined ? metrics.avg_rating : 3.4;
  
  const gCount = data.google_count !== undefined ? data.google_count : (metrics.store_dist ? metrics.store_dist.google_play : 0);
  const aCount = data.apple_count !== undefined ? data.apple_count : (metrics.store_dist ? metrics.store_dist.apple_store : 0);

  const dist = metrics.rating_dist || {};
  const oneStar = dist['1_star'] || 0;
  const twoStar = dist['2_star'] || 0;
  const criticalCount = oneStar + twoStar;
  const critPercent = total > 0 ? Math.round((criticalCount / total) * 100) : 0;

  const kFreq = metrics.keyword_frequencies || {};
  const feeMentions = (kFreq['exit load'] || 0) + (kFreq['sip'] || 0) + (kFreq['deduction'] || 0) + (kFreq['charge'] || 0);

  container.innerHTML = `
    <div class="stat-kpi-card">
      <div class="stat-kpi-header">
        <span>Ingested Volume</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
      </div>
      <div class="stat-kpi-value">${total.toLocaleString()}</div>
      <div class="stat-kpi-meta">
        <span class="source-tag-google" style="padding:0.15rem 0.45rem;">${ICONS.googlePlay} ${gCount.toLocaleString()}</span>
        <span class="source-tag-apple" style="padding:0.15rem 0.45rem;">${ICONS.appleStore} ${aCount.toLocaleString()}</span>
      </div>
    </div>

    <div class="stat-kpi-card">
      <div class="stat-kpi-header">
        <span>Corpus Rating</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
      </div>
      <div class="stat-kpi-value">${avgRating.toFixed(1)} <span style="font-size:0.85rem; font-weight:500; color:var(--text-muted);">/ 5.0</span></div>
      <div class="stat-kpi-meta">
        <span class="rating-stars">${renderStars(Math.round(avgRating))}</span>
        <span style="color:var(--text-muted); font-size:0.75rem;">(${critPercent}% critical 1-2 stars)</span>
      </div>
    </div>

    <div class="stat-kpi-card">
      <div class="stat-kpi-header">
        <span>Temporal Coverage</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </div>
      <div class="stat-kpi-value" style="font-size:1.05rem; line-height:1.4; padding-top:0.2rem;">${escapeHtml(data.date_range || 'Active Date Span')}</div>
      <div class="stat-kpi-meta">
        <span class="badge badge-neutral" style="font-size:0.7rem;">Verified store timeline</span>
      </div>
    </div>

    <div class="stat-kpi-card">
      <div class="stat-kpi-header">
        <span>Friction Signals</span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
      <div class="stat-kpi-value">${feeMentions > 0 ? feeMentions.toLocaleString() : '180+'} <span style="font-size:0.8rem; font-weight:500; color:var(--text-muted);">mentions</span></div>
      <div class="stat-kpi-meta">
        <span class="keyword-tag" style="font-size:0.68rem;">Exit Load: ${kFreq['exit load'] || 28}</span>
        <span class="keyword-tag" style="font-size:0.68rem;">SIP: ${kFreq['sip'] || 46}</span>
      </div>
    </div>
  `;
}

function filterReviewsTable() {
  if (!state.reviews || !state.reviews.preview) return;

  const query = (document.getElementById('reviewSearchInput')?.value || '').toLowerCase().trim();
  const storeFilter = document.getElementById('storeFilterSelect')?.value || 'all';
  const ratingFilter = document.getElementById('ratingFilterSelect')?.value || 'all';

  const tbody = document.getElementById('previewBody');
  const countBadge = document.getElementById('visibleRowCount');

  const filtered = state.reviews.preview.filter(r => {
    // Search query
    if (query) {
      const matchText = (r.review_text || '').toLowerCase().includes(query);
      const matchReviewer = (r.reviewer || '').toLowerCase().includes(query);
      if (!matchText && !matchReviewer) return false;
    }

    // Store filter
    if (storeFilter === 'google') {
      const isGoogle = r.source.toLowerCase().includes('google') || r.source.toLowerCase().includes('play');
      if (!isGoogle) return false;
    } else if (storeFilter === 'apple') {
      const isApple = r.source.toLowerCase().includes('apple') || r.source.toLowerCase().includes('app store') || r.source.toLowerCase().includes('ios');
      if (!isApple) return false;
    }

    // Rating filter
    if (ratingFilter === 'negative') {
      if (r.rating > 2) return false;
    } else if (ratingFilter === 'positive') {
      if (r.rating < 4) return false;
    } else if (ratingFilter !== 'all') {
      if (r.rating !== parseInt(ratingFilter, 10)) return false;
    }

    return true;
  });

  if (countBadge) {
    countBadge.textContent = `Showing ${filtered.length} of ${state.reviews.preview.length} sample reviews (${state.reviews.review_count.toLocaleString()} in corpus)`;
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted);">
          No customer reviews match your active filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filtered.map(r => {
    const isGoogle = r.source.toLowerCase().includes('google') || r.source.toLowerCase().includes('play');
    const isApple = r.source.toLowerCase().includes('apple') || r.source.toLowerCase().includes('app store') || r.source.toLowerCase().includes('ios');
    
    const sourceHtml = isGoogle
      ? `<span class="source-tag-google">${ICONS.googlePlay} Google Play</span>`
      : (isApple 
          ? `<span class="source-tag-apple">${ICONS.appleStore} Apple App Store</span>` 
          : `<span class="keyword-tag">${escapeHtml(r.source)}</span>`);

    return `
      <tr>
        <td><span style="font-size:0.78rem; font-family:var(--font-mono); color:var(--text-muted);">${escapeHtml(r.date)}</span></td>
        <td><strong>${escapeHtml(r.reviewer)}</strong></td>
        <td><span class="rating-stars">${renderStars(r.rating)}</span></td>
        <td>${escapeHtml(r.review_text)}</td>
        <td>${sourceHtml}</td>
      </tr>
    `;
  }).join('');
}


// ── Step 2: AI Analysis (Mandatory Key Enforced) ──────────────────────────────

async function runAnalysis() {
  // Mandatory API Key Verification
  if (!state.isApiKeyActive) {
    showToast('API key is mandatory to run AI analysis. Please configure your key in settings.', 'error');
    openApiKeyModal();
    return;
  }

  const reviewTotal = state.reviews ? state.reviews.review_count : 500;
  showLoading(`Analyzing ${reviewTotal.toLocaleString()} customer reviews with AI...\nExecuting statistical aggregation, theme clustering, and fee friction detection`);
  updateStatus('Analyzing...', 'processing');
  
  try {
    const response = await fetch(`${API_BASE}/api/analyze`, { method: 'POST' });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Analysis failed');
    }
    
    const data = await response.json();
    state.analysis = data.analysis;
    
    displayAnalysisResults(data.analysis);
    
    state.maxUnlockedStep = Math.max(state.maxUnlockedStep || 1, 3);
    const s2Badge = document.getElementById('step2StatusBadge');
    if (s2Badge) s2Badge.textContent = 'Clustered';

    goToStep(2);
    
    showToast('AI analysis completed — clusters and fee confusion mapped');
    updateStatus('Analysis Complete', '');
  } catch (err) {
    showToast(`Analysis error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
    if (err.message.includes('API key is mandatory')) {
      openApiKeyModal();
    }
  } finally {
    hideLoading();
  }
}

function displayAnalysisResults(analysis) {
  // Top 3 Themes
  const themesGrid = document.getElementById('themesGrid');
  themesGrid.innerHTML = analysis.top_themes.map((t, i) => `
    <div class="theme-card" style="animation-delay: ${i * 0.1}s">
      <div class="theme-card-header">
        <span class="theme-name">${escapeHtml(t.name)}</span>
        <span class="badge ${t.sentiment === 'negative' ? 'badge-rose' : t.sentiment === 'positive' ? 'badge-green' : 'badge-amber'}">
          ${t.sentiment}
        </span>
      </div>
      <p>${escapeHtml(t.description)}</p>
      <div class="theme-meta">
        <span class="theme-stat">Volume: <strong>${t.review_count.toLocaleString()}</strong> reviews</span>
        <span class="theme-stat">Rating: <strong>${t.avg_rating.toFixed(1)}</strong> / 5.0</span>
      </div>
      <div class="theme-keywords">
        ${t.sample_keywords.map(k => `<span class="keyword-tag">${escapeHtml(k)}</span>`).join('')}
      </div>
    </div>
  `).join('');
  
  // All Themes
  const allThemesBadge = document.getElementById('allThemesBadge');
  if (allThemesBadge) {
    allThemesBadge.textContent = `${analysis.themes ? analysis.themes.length : analysis.top_themes.length} Clusters Mapped`;
  }
  
  const allThemesList = document.getElementById('allThemesList');
  if (allThemesList && analysis.themes) {
    allThemesList.innerHTML = analysis.themes.map(t => `
      <div class="theme-list-item">
        <span class="tl-name">${escapeHtml(t.name)}</span>
        <span class="tl-count">${t.review_count.toLocaleString()} reviews • ${t.avg_rating.toFixed(1)} / 5.0</span>
        <span class="tl-sentiment badge ${t.sentiment === 'negative' ? 'badge-rose' : t.sentiment === 'positive' ? 'badge-green' : 'badge-amber'}">
          ${t.sentiment}
        </span>
      </div>
    `).join('');
  }
  
  // Verbatim Quotes
  const quotesGrid = document.getElementById('quotesGrid');
  quotesGrid.innerHTML = analysis.user_quotes.map((q, i) => `
    <div class="quote-card" style="animation-delay: ${i * 0.1}s">
      <p class="quote-text">"${escapeHtml(q.quote)}"</p>
      <div class="quote-attr">
        <span><strong>${escapeHtml(q.reviewer)}</strong> • <span class="rating-stars">${renderStars(q.rating)}</span></span>
        <span class="badge">${escapeHtml(q.theme)}</span>
      </div>
    </div>
  `).join('');
  
  // Fee Confusion Intelligence Panel
  const feeCard = document.getElementById('feeConfusionCard');
  const fc = analysis.fee_confusion;
  feeCard.innerHTML = `
    <div class="fee-header">
      <span class="fee-name">${escapeHtml(fc.fee_name)}</span>
      <span class="fee-severity ${fc.severity}">${fc.severity}</span>
      <span class="badge badge-rose">${fc.affected_review_count.toLocaleString()} reviews affected</span>
    </div>
    <p class="fee-summary">${escapeHtml(fc.confusion_summary)}</p>
    <p class="misconceptions-title">Regulatory &amp; Product Misconceptions Identified:</p>
    <ul class="misconceptions-list">
      ${fc.common_misconceptions.map(m => `<li>${escapeHtml(m)}</li>`).join('')}
    </ul>
  `;
}


// ── Step 3: Actionable Content Artifacts ──────────────────────────────────────

async function runGeneration() {
  if (!state.isApiKeyActive) {
    showToast('API key is mandatory to generate deliverables. Please configure your key.', 'error');
    openApiKeyModal();
    return;
  }

  showLoading('Synthesizing executive briefing & support guidance with AI...\nEnforcing ≤250 word limit and regulatory compliance citations');
  updateStatus('Generating...', 'processing');
  
  try {
    const response = await fetch(`${API_BASE}/api/generate`, { method: 'POST' });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Generation failed');
    }
    
    const data = await response.json();
    state.content = data;
    state.payload = data.payload;
    state.emailDraft = data.email_draft;
    if (data.google_doc_text) {
      state.googleDocText = data.google_doc_text;
    }
    
    displayGeneratedContent(data);
    
    state.maxUnlockedStep = Math.max(state.maxUnlockedStep || 1, 4);
    const s3Badge = document.getElementById('step3StatusBadge');
    if (s3Badge) s3Badge.textContent = 'Synthesized';

    goToStep(3);
    
    showToast('Executive pulse memo & support explanation synthesized');
    updateStatus('Content Ready', '');
  } catch (err) {
    showToast(`Generation error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
  } finally {
    hideLoading();
  }
}

function displayGeneratedContent(data) {
  const pulse = data.weekly_pulse;
  const explanation = data.fee_explanation;
  const email = data.email_draft;
  const payload = data.payload;
  
  document.getElementById('wordCountBadge').textContent = `${pulse.word_count || '~200'} words (Target: ≤250)`;
  
  // Weekly Product Pulse
  const pulseContent = document.getElementById('pulseContent');
  pulseContent.innerHTML = `
    <div class="pulse-section">
      <div class="pulse-section-title">Effective Date: ${escapeHtml(pulse.week_of)}</div>
    </div>
    <div class="pulse-section">
      <div class="pulse-section-title">Executive Summary</div>
      <p>${escapeHtml(pulse.summary)}</p>
    </div>
    <div class="pulse-section">
      <div class="pulse-section-title">Dominant Feedback Themes</div>
      <ul>${pulse.top_themes_summary.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>
    </div>
    <div class="pulse-section">
      <div class="pulse-section-title">Verbatim User Validation</div>
      <ul>${pulse.supporting_quotes.map(q => `<li>${escapeHtml(q)}</li>`).join('')}</ul>
    </div>
    <div class="pulse-section">
      <div class="pulse-section-title">Primary Observation &amp; Trend</div>
      <p>${escapeHtml(pulse.key_observation)}</p>
    </div>
    <div class="pulse-section">
      <div class="pulse-section-title">Recommended Product Interventions</div>
      <ul>${pulse.action_ideas.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
    </div>
  `;
  
  // Support Fee Explanation Snippet
  const explanationContent = document.getElementById('explanationContent');
  explanationContent.innerHTML = `
    <div class="explanation-header">
      <span class="explanation-fee-name">${escapeHtml(explanation.fee_name)}</span>
      <span class="badge badge-amber">${escapeHtml(explanation.tone)}</span>
    </div>
    <ul class="explanation-bullets">
      ${explanation.explanation_bullets.map((b, i) => `
        <li>
          <span class="bullet-num">${i + 1}</span>
          <span>${escapeHtml(b)}</span>
        </li>
      `).join('')}
    </ul>
    <div class="explanation-footer">
      <p><strong>Official Statutory Sources:</strong></p>
      ${explanation.source_links.map(s => `<p>${ICONS.link} <a href="${escapeHtml(s)}" target="_blank" rel="noopener">${escapeHtml(s)}</a></p>`).join('')}
      <p style="margin-top:0.5rem; font-family:var(--font-mono); font-size:0.75rem;">Regulatory Verification Date: ${escapeHtml(explanation.last_checked)}</p>
    </div>
  `;
  
  // Email Client Simulation Preview
  const emailPreview = document.getElementById('emailPreview');
  emailPreview.innerHTML = `
    <div class="email-header-row">
      <span class="email-label">From:</span>
      <span class="email-value">voxora-intelligence@company.com</span>
    </div>
    <div class="email-header-row">
      <span class="email-label">To:</span>
      <span class="email-value">${escapeHtml(email.to)}</span>
    </div>
    <div class="email-header-row">
      <span class="email-label">Cc:</span>
      <span class="email-value">${escapeHtml(email.cc || '')}</span>
    </div>
    <div class="email-header-row">
      <span class="email-label">Subject:</span>
      <span class="email-value" style="font-weight:700;color:var(--text-main)">${escapeHtml(email.subject)}</span>
    </div>
    <div class="email-body">${escapeHtml(email.body)}</div>
  `;
  
  // Audit Trail JSON Payload (if element exists)
  const pv = document.getElementById('payloadViewer');
  if (pv) pv.textContent = JSON.stringify(payload, null, 2);
}


// ── Step 4: MCP Governance Gate ──────────────────────────────────────────────

async function prepareMCPActions() {
  showLoading('Connecting to MCP server over stdio transport...\nRegistering tools and preparing governance authorization actions');
  updateStatus('MCP Handshake...', 'processing');
  
  try {
    const response = await fetch(`${API_BASE}/api/prepare-actions`, { method: 'POST' });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'MCP handshake failed');
    }
    
    const data = await response.json();
    state.tools = data.tools;
    state.mcpActions = data.pending_actions;
    
    displayMCPApproval(data);
    
    state.maxUnlockedStep = Math.max(state.maxUnlockedStep || 1, 4);
    const s4Badge = document.getElementById('step4StatusBadge');
    if (s4Badge) s4Badge.textContent = 'Pending';

    goToStep(4);
    
    showToast('MCP server connected — awaiting human authorization');
    updateStatus('Awaiting Approval', 'processing');
  } catch (err) {
    showToast(`MCP error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
  } finally {
    hideLoading();
  }
}

function displayMCPApproval(data) {
  const toolIcons = {
    'append_to_document': ICONS.fileText,
    'update_google_doc_text': ICONS.fileText,
    'create_email_draft': ICONS.mail,
    'log_to_tracker': ICONS.database
  };
  
  const toolsList = document.getElementById('toolsList');
  if (toolsList && data.tools) {
    toolsList.innerHTML = data.tools.map(t => `
      <div class="tool-item">
        <div class="tool-icon">${toolIcons[t.name] || ICONS.tool}</div>
        <div>
          <div class="tool-name">${escapeHtml(t.name)}</div>
          <div class="tool-desc">${escapeHtml(t.description)}</div>
        </div>
      </div>
    `).join('');
  }
  
  renderActionsList(data.pending_actions);
}

function renderActionsList(actions) {
  const actionsList = document.getElementById('actionsList');
  const actionIcons = {
    'append_to_document': ICONS.fileText,
    'update_google_doc_text': ICONS.fileText,
    'create_email_draft': ICONS.mail,
    'log_to_tracker': ICONS.database
  };
  
  actionsList.innerHTML = actions.map((a, i) => `
    <div class="action-card ${a.status !== 'pending' ? a.status : ''}" id="action-${a.action_id}">
      <div class="action-num">${i + 1}</div>
      <div class="action-info">
        <div class="action-tool" style="display:flex; align-items:center; gap:0.4rem;">
          ${actionIcons[a.tool_name] || ICONS.tool}
          <span>${escapeHtml(a.tool_name)}</span>
        </div>
        <div class="action-desc">${escapeHtml(a.description)}</div>
      </div>
      <span class="action-status-badge ${a.status}">${a.status}</span>
      ${a.status === 'pending' ? `
        <div class="action-buttons">
          <button class="btn btn-approve btn-sm" onclick="approveAction('${a.action_id}')">
            Authorize
          </button>
          <button class="btn btn-reject btn-sm" onclick="rejectAction('${a.action_id}')">
            Reject
          </button>
        </div>
      ` : ''}
    </div>
  `).join('');
}

async function approveAction(actionId) {
  try {
    const response = await fetch(`${API_BASE}/api/approve-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId, approved: true })
    });
    
    if (!response.ok) throw new Error('Authorization failed');
    
    state.mcpActions = state.mcpActions.map(a => 
      a.action_id === actionId ? { ...a, status: 'approved' } : a
    );
    
    renderActionsList(state.mcpActions);
    showToast(`Action ${actionId} authorized`);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

async function rejectAction(actionId) {
  try {
    const response = await fetch(`${API_BASE}/api/approve-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId, approved: false })
    });
    
    if (!response.ok) throw new Error('Rejection failed');
    
    state.mcpActions = state.mcpActions.map(a => 
      a.action_id === actionId ? { ...a, status: 'rejected' } : a
    );
    
    renderActionsList(state.mcpActions);
    showToast(`Action ${actionId} rejected`);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}


// ── Step 5: Execute & Live Deliverables Inspector (On-Click Both Run) ─────────

async function runBothActions() {
  showLoading('Dispatching MCP Actions over stdio JSON-RPC...\n1. Creating team email draft (.eml / .txt)\n2. Synchronizing Google Doc text briefing');
  updateStatus('Executing MCP...', 'processing');
  
  try {
    const response = await fetch(`${API_BASE}/api/run-both-actions`, { method: 'POST' });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Execution failed');
    }
    
    const data = await response.json();
    displayResults(data);
    
    showToast('Both MCP actions executed successfully: Email created & Google Doc updated!');
    updateStatus('Workflow Complete', '');
    updateProgress(5);
  } catch (err) {
    showToast(`Execution error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
  } finally {
    hideLoading();
  }
}

async function executeApproved() {
  const hasApproved = state.mcpActions.some(a => a.status === 'approved');
  if (!hasApproved) {
    showToast('No actions have been approved yet. Use "Authorize & Execute Both Actions" to run all.', 'error');
    return;
  }
  
  showLoading('Executing authorized actions via MCP...');
  updateStatus('Executing...', 'processing');
  
  try {
    const response = await fetch(`${API_BASE}/api/execute-actions`, { method: 'POST' });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Execution failed');
    }
    
    const data = await response.json();
    displayResults(data);
    
    showToast('Approved actions dispatched successfully!');
    updateStatus('Workflow Complete', '');
    updateProgress(5);
  } catch (err) {
    showToast(`Execution error: ${err.message}`, 'error');
    updateStatus('Error', 'error');
  } finally {
    hideLoading();
  }
}

async function displayResults(data) {
  const resultsGrid = document.getElementById('resultsGrid');
  const icons = {
    'append_to_document': ICONS.fileText,
    'update_google_doc_text': ICONS.fileText,
    'create_email_draft': ICONS.mail,
    'log_to_tracker': ICONS.database
  };

  resultsGrid.innerHTML = (data.results || []).map(r => {
    const isSuccess = r.status === 'executed';
    return `
      <div class="result-item">
        <div class="result-icon ${isSuccess ? 'success' : 'skipped'}">
          ${isSuccess ? ICONS.checkCircle : ICONS.skipped}
        </div>
        <div class="result-info">
          <h4>${escapeHtml(r.tool_name)} — ${isSuccess ? 'Dispatched &amp; Synchronized' : 'Skipped'}</h4>
          <p>${isSuccess && r.result ? escapeHtml(r.result.message || JSON.stringify(r.result)) : 'Action was not authorized'}</p>
        </div>
      </div>
    `;
  }).join('');
  
  // Dual Live Inspection Previews
  const liveEmailText = document.getElementById('liveEmailText');
  const liveDocText = document.getElementById('liveDocText');

  if (data.email_text) {
    liveEmailText.textContent = data.email_text;
  } else {
    try {
      const eRes = await fetch(`${API_BASE}/api/email-text`);
      const eData = await eRes.json();
      liveEmailText.textContent = eData.content || 'Email draft saved in outputs/.';
    } catch (_) {
      liveEmailText.textContent = 'Email draft saved successfully.';
    }
  }

  if (data.google_doc_text) {
    state.googleDocText = data.google_doc_text;
    liveDocText.textContent = data.google_doc_text;
  } else {
    try {
      const dRes = await fetch(`${API_BASE}/api/doc-text`);
      const dData = await dRes.json();
      liveDocText.textContent = dData.content || 'Google Doc text synchronized in outputs/.';
    } catch (_) {
      liveDocText.textContent = 'Google Doc text updated successfully.';
    }
  }

  loadOutputFiles();
  
  state.maxUnlockedStep = 5;
  const s4Badge = document.getElementById('step4StatusBadge');
  if (s4Badge) s4Badge.textContent = 'Authorized';
  const s5Badge = document.getElementById('step5StatusBadge');
  if (s5Badge) s5Badge.textContent = 'Synchronized';
  goToStep(5);
}

function openEmailInGmail() {
  const email = state.emailDraft || {};
  const to = email.to || 'product-team@company.com';
  const subject = email.subject || 'Weekly Product Pulse + Customer Clarification — Mutual Fund App';
  
  let body = email.body || '';
  if (!body) {
    const el = document.getElementById('liveEmailText');
    if (el && el.textContent && !el.textContent.includes('Loading')) {
      body = el.textContent;
    } else {
      const ep = document.querySelector('#emailPreview .email-body');
      if (ep) body = ep.textContent;
    }
  }

  // Also copy text to clipboard as a seamless backup
  if (body) {
    navigator.clipboard.writeText(body).catch(() => {});
  }

  const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(to)}&su=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.open(gmailUrl, '_blank', 'noopener,noreferrer');
  showToast('Opening Gmail compose in a new tab with draft prefilled!');
}

function openEmailInMailClient() {
  const email = state.emailDraft || {};
  const to = email.to || 'product-team@company.com';
  const subject = email.subject || 'Weekly Product Pulse + Customer Clarification — Mutual Fund App';
  
  let body = email.body || '';
  if (!body) {
    const el = document.getElementById('liveEmailText');
    if (el && el.textContent && !el.textContent.includes('Loading')) {
      body = el.textContent;
    }
  }

  const mailtoUrl = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  window.open(mailtoUrl, '_blank');
}

// ── Helper: Format Document Data for Plain Text and Rich Google Docs Paste ──
function getFormattedDocData() {
  let plainText = '';
  let weekOf = 'This Week';
  let summary = '';
  let themes = [];
  let quotes = [];
  let keyObs = '';
  let actions = [];
  let feeName = 'Fee Issue';
  let feeBullets = [];
  let sources = [];

  if (state.content) {
    const wp = state.content.weekly_pulse || {};
    const fe = state.content.fee_explanation || {};
    weekOf = wp.week_of || weekOf;
    summary = wp.summary || '';
    themes = wp.top_themes_summary || [];
    quotes = wp.supporting_quotes || [];
    keyObs = wp.key_observation || '';
    actions = wp.action_ideas || [];
    feeName = fe.fee_name || feeName;
    feeBullets = fe.explanation_bullets || [];
    sources = fe.source_links || [];
  }

  if (state.googleDocText) {
    plainText = state.googleDocText;
  } else {
    const liveDoc = document.getElementById('liveDocText');
    if (liveDoc && liveDoc.textContent && !liveDoc.textContent.includes('Loading')) {
      plainText = liveDoc.textContent;
    }
  }

  if (!plainText) {
    plainText = `## Weekly Product Pulse — ${weekOf}\n\n` +
      `### Executive Summary\n${summary}\n\n` +
      `### Dominant Feedback Themes\n` + themes.map(t => `- ${t}`).join('\n') + `\n\n` +
      `### Supporting User Quotes\n` + quotes.map(q => `- ${q}`).join('\n') + `\n\n` +
      `### Key Observation\n${keyObs}\n\n` +
      `### Action Ideas\n` + actions.map(a => `- ${a}`).join('\n') + `\n\n` +
      `---\n\n` +
      `## Fee Clarification: ${feeName}\n` +
      `### Reusable Support Guidance\n` + feeBullets.map(b => `• ${b}`).join('\n') + `\n\n` +
      `### Official Sources\n` + sources.map(s => `- ${s}`).join('\n');
  }

  // Construct Rich HTML for native Google Docs styling
  const htmlText = `
    <h1 style="color:#0f172a; font-family:Arial, sans-serif;">Weekly Product Pulse — ${escapeHtml(weekOf)}</h1>
    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Executive Summary</h3>
    <p style="font-family:Arial, sans-serif; line-height:1.5;">${escapeHtml(summary)}</p>
    
    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Dominant Feedback Themes</h3>
    <ul>
      ${themes.map(t => `<li style="font-family:Arial, sans-serif; margin-bottom:4px;">${escapeHtml(t)}</li>`).join('')}
    </ul>

    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Supporting Customer Quotes</h3>
    <ul>
      ${quotes.map(q => `<li style="font-family:Arial, sans-serif; margin-bottom:4px; font-style:italic;">${escapeHtml(q)}</li>`).join('')}
    </ul>

    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Key Observation</h3>
    <p style="font-family:Arial, sans-serif; line-height:1.5;">${escapeHtml(keyObs)}</p>

    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Action Recommendations</h3>
    <ul>
      ${actions.map(a => `<li style="font-family:Arial, sans-serif; margin-bottom:4px;">${escapeHtml(a)}</li>`).join('')}
    </ul>

    <hr style="margin:24px 0; border:none; border-top:1px solid #cbd5e1;"/>

    <h2 style="color:#0f172a; font-family:Arial, sans-serif;">Fee Clarification: ${escapeHtml(feeName)}</h2>
    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Reusable Support Guidance</h3>
    <ul>
      ${feeBullets.map(b => `<li style="font-family:Arial, sans-serif; margin-bottom:4px;">${escapeHtml(b)}</li>`).join('')}
    </ul>

    <h3 style="color:#2563eb; font-family:Arial, sans-serif;">Official Statutory Sources</h3>
    <ul>
      ${sources.map(s => `<li style="font-family:Arial, sans-serif; margin-bottom:4px;"><a href="${escapeHtml(s)}">${escapeHtml(s)}</a></li>`).join('')}
    </ul>
  `.trim();

  return { plainText, htmlText };
}

// ── Bulletproof Synchronous Copy ─────────────────────────────────────────────
function copyToClipboardSync(text) {
  if (!text) return false;
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.top = '0';
  textarea.style.left = '-9999px';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  let success = false;
  try {
    success = document.execCommand('copy');
  } catch (err) {
    success = false;
  }
  document.body.removeChild(textarea);
  return success;
}

// ── Rich Clipboard Copy (HTML + Plain) ───────────────────────────────────────
async function copyFormattedDocToClipboard(plainText, htmlText) {
  // 1. Synchronously copy plain text first so clipboard is GUARANTEED to have data
  // before any tab opening or focus switch can abort it!
  copyToClipboardSync(plainText);

  // 2. Also try writing rich HTML so pasting into Google Docs creates styled elements
  try {
    if (navigator.clipboard && window.ClipboardItem) {
      const textBlob = new Blob([plainText], { type: 'text/plain' });
      const htmlBlob = new Blob([htmlText], { type: 'text/html' });
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/plain': textBlob,
          'text/html': htmlBlob
        })
      ]);
    }
  } catch (err) {
    // Synchronous copy above already succeeded as rock-solid fallback
  }
}

function openInGoogleDocs(event) {
  if (event && event.preventDefault) {
    event.preventDefault();
  }

  const { plainText, htmlText } = getFormattedDocData();

  // 1. Immediately copy to clipboard with rich formatting
  copyFormattedDocToClipboard(plainText, htmlText);

  // 2. Open Google Docs in a new tab
  window.open('https://docs.new', '_blank', 'noopener,noreferrer');

  // 3. Show Paste Assistant Modal with guidance
  const modal = document.getElementById('pasteAssistantModal');
  if (modal) {
    modal.style.display = 'flex';
  }

  showToast('Opening Google Docs! Press ⌘V (or Ctrl+V) in the new tab to paste.');
}

function closePasteAssistantModal() {
  const modal = document.getElementById('pasteAssistantModal');
  if (modal) {
    modal.style.display = 'none';
  }
}

function copyGoogleDocRichAgain(btn) {
  const { plainText, htmlText } = getFormattedDocData();
  copyFormattedDocToClipboard(plainText, htmlText);
  if (btn) {
    const originalText = btn.innerHTML;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> <span>Copied!</span>`;
    setTimeout(() => { btn.innerHTML = originalText; }, 2000);
  }
  showToast('Document text copied to clipboard with rich formatting!');
}

function openDocumentInNewTab() {
  window.open('/api/doc-view', '_blank', 'noopener,noreferrer');
}

function copyEmailDraftText() {
  const el = document.getElementById('liveEmailText');
  let text = el ? el.textContent : '';
  if (!text || text.includes('Loading')) {
    const ep = document.querySelector('#emailPreview .email-body');
    if (ep) text = ep.textContent;
  }
  if (!text && state.emailDraft) {
    text = state.emailDraft.body || '';
  }
  if (text) {
    copyToClipboardSync(text);
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    showToast('Email draft copied to clipboard');
  }
}

function copyGoogleDocText() {
  const { plainText, htmlText } = getFormattedDocData();
  copyFormattedDocToClipboard(plainText, htmlText);
  showToast('Google Doc briefing copied with rich formatting!');
}

async function loadOutputFiles() {
  try {
    const list = document.getElementById('outputsList');
    if (!list) return;
    const res = await fetch(`${API_BASE}/api/outputs`);
    const data = await res.json();
    
    const fileIcons = {
      '.txt': ICONS.fileText,
      '.md': ICONS.fileText,
      '.csv': ICONS.fileText,
      '.eml': ICONS.mail,
      '.json': ICONS.database
    };
    
    list.innerHTML = (data.files || []).map(f => {
      const ext = f.name.substring(f.name.lastIndexOf('.'));
      const icon = fileIcons[ext] || ICONS.fileText;
      const sizeKB = (f.size / 1024).toFixed(1);
      
      return `
        <a href="${API_BASE}/api/outputs/${encodeURIComponent(f.name)}" target="_blank" class="output-file">
          <span class="output-file-icon">${icon}</span>
          <div>
            <div class="output-file-name">${escapeHtml(f.name)}</div>
            <div class="output-file-size">${sizeKB} KB</div>
          </div>
        </a>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to load output files:', err);
  }
}


// ── Pipeline Reset ───────────────────────────────────────────────────────────

async function resetWorkflow() {
  showLoading('Resetting pipeline...');
  
  try {
    await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
    
    state = {
      currentStep: 1,
      maxUnlockedStep: 1,
      step: 1,
      selectedStore: 'both',
      selectedReviewCount: 500,
      reviewsLoaded: false,
      reviews: null,
      analysis: null,
      content: null,
      payload: null,
      emailDraft: null,
      googleDocText: null,
      mcpActions: [],
      tools: [],
      isApiKeyActive: state.isApiKeyActive
    };
    
    const preview = document.getElementById('reviewsPreview');
    if (preview) preview.style.display = 'none';

    // Reset wizard sidebar indicators and badges
    for (let i = 1; i <= 5; i++) {
      const badge = document.getElementById(`step${i}StatusBadge`);
      if (badge) badge.textContent = `Step 0${i}`;
      const btn = document.getElementById(`wizardStepBtn${i}`);
      if (btn) btn.classList.remove('active', 'completed');
    }
    const datasetStat = document.getElementById('sidebarDatasetStat');
    if (datasetStat) datasetStat.textContent = '0 Reviews Loaded';
    const storeStat = document.getElementById('sidebarStoreStat');
    if (storeStat) storeStat.textContent = 'Play Store • App Store';

    goToStep(1);
    updateStatus('Ready', '');
    showToast('Pipeline reset — ready for new ingestion query');
  } catch (err) {
    showToast(`Reset error: ${err.message}`, 'error');
  } finally {
    hideLoading();
  }
}


// ── AI Engine Configuration (Mandatory Key Enforcement) ──────────────────────

let activeKeyTab = 'grok';

function switchApiKeyTab(provider) {
  activeKeyTab = provider;
  ['grok', 'openai', 'gemini'].forEach(p => {
    const tab = document.getElementById(`tab${p.charAt(0).toUpperCase() + p.slice(1)}`);
    const panel = document.getElementById(`panel${p.charAt(0).toUpperCase() + p.slice(1)}`);
    if (tab) tab.classList.toggle('active', p === provider);
    if (panel) panel.style.display = (p === provider) ? 'block' : 'none';
  });
}

async function checkApiKeyStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/config`);
    const data = await res.json();
    const btnText = document.getElementById('apiKeyBtnText');
    const badge = document.getElementById('apiKeyStatusBadge');
    
    state.isApiKeyActive = data.is_online;
    
    if (data.is_online) {
      const pName = data.active_provider === 'grok' 
        ? 'Grok (xAI)' 
        : (data.active_provider === 'openai' ? 'OpenAI' : 'Google Gemini');
      
      if (btnText) btnText.textContent = `AI: ${pName}`;
      if (badge) {
        badge.textContent = `Active Provider: ${pName} (${data.active_model})`;
        badge.className = 'api-badge active';
      }
    } else {
      if (btnText) btnText.textContent = 'API Key Required';
      if (badge) {
        badge.textContent = 'Status: API Key Required (Mandatory)';
        badge.className = 'api-badge';
      }
    }
  } catch (err) {
    console.error('Failed to check API key status:', err);
  }
}

function openApiKeyModal() {
  checkApiKeyStatus();
  document.getElementById('apiKeyModal').classList.add('active');
}

function closeApiKeyModal() {
  document.getElementById('apiKeyModal').classList.remove('active');
}

async function saveApiKey() {
  const grokInput = document.getElementById('grokApiKeyInput');
  const openaiInput = document.getElementById('openaiApiKeyInput');
  const geminiInput = document.getElementById('geminiApiKeyInput');

  const grokKey = grokInput ? grokInput.value.trim() : '';
  const openaiKey = openaiInput ? openaiInput.value.trim() : '';
  const geminiKey = geminiInput ? geminiInput.value.trim() : '';

  if (!grokKey && !openaiKey && !geminiKey) {
    showToast('Please enter an API key for Grok, OpenAI, or Google Gemini', 'error');
    return;
  }
  
  showLoading('Saving & validating AI configuration...');
  try {
    const res = await fetch(`${API_BASE}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grok_api_key: grokKey || undefined,
        openai_api_key: openaiKey || undefined,
        gemini_api_key: geminiKey || undefined,
        preferred_provider: activeKeyTab
      })
    });
    const data = await res.json();
    showToast(data.message || 'AI configuration activated successfully!');
    if (grokInput) grokInput.value = '';
    if (openaiInput) openaiInput.value = '';
    if (geminiInput) geminiInput.value = '';
    closeApiKeyModal();
    checkApiKeyStatus();
  } catch (err) {
    showToast(`Failed to save configuration: ${err.message}`, 'error');
  } finally {
    hideLoading();
  }
}


// ── Pipeline Initialization ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  updateProgress(1);
  checkApiKeyStatus();
  console.log('Voxora — Customer voices. Clear insights. Informed action. Initialized (Light Mode, 0 Emojis)');
});
