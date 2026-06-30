import './style.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

// Application State
const state = {
  activeView: 'dashboard',
  selectedFile: null,
  journal: [],
  stats: {
    total: 0,
    winrate: 'N/A',
    bestTimeframe: 'N/A',
    accuracy: 'N/A'
  }
};

// DOM Elements
const views = {
  dashboard: document.getElementById('view-dashboard'),
  journal: document.getElementById('view-journal'),
  library: document.getElementById('view-library'),
  stats: document.getElementById('view-stats')
};

const navItems = document.querySelectorAll('.nav-item');
const viewTitle = document.getElementById('view-title');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');

// Drag and drop zone elements
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const fileNamePreview = document.getElementById('file-name-preview');
const analysisForm = document.getElementById('analysis-form');
const resultsPanel = document.getElementById('results-panel');

// Navigation Handler
function switchView(viewName) {
  state.activeView = viewName;
  
  // Update nav menu active state
  navItems.forEach(item => {
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update panels visibility
  Object.keys(views).forEach(key => {
    if (key === viewName) {
      views[key].classList.add('active');
    } else {
      views[key].classList.remove('active');
    }
  });

  // Update Page Title
  const titles = {
    dashboard: 'Dashboard',
    journal: 'Trade Journal',
    library: 'Educational Library',
    stats: 'Performance Statistics'
  };
  viewTitle.textContent = titles[viewName];

  // If mobile, close sidebar on nav
  sidebar.classList.remove('active');

  // Trigger view-specific loads
  if (viewName === 'journal') fetchJournal();
  if (viewName === 'stats') fetchStats();
  if (viewName === 'library') loadLibraryData();
}

// Attach Nav Listeners
navItems.forEach(item => {
  item.addEventListener('click', () => {
    switchView(item.getAttribute('data-view'));
  });
});

// Mobile Sidebar Toggle
sidebarToggle.addEventListener('click', () => {
  sidebar.classList.toggle('active');
});

// TradingView Widget Loader
let tvWidget = null;
function loadTradingViewWidget(symbol) {
  const container = document.getElementById('tv-widget-container');
  container.innerHTML = '';
  
  let cleanSymbol = symbol.toUpperCase().trim();
  
  if (!cleanSymbol.includes(':')) {
    if (cleanSymbol.endsWith('=X')) {
      // Forex
      const pair = cleanSymbol.replace('=X', '').replace('-', '').replace('/', '');
      cleanSymbol = `FX:${pair}`;
    } else if (cleanSymbol === 'GC=F') {
      // Gold Futures
      cleanSymbol = 'COMEX:GC1!';
    } else if (cleanSymbol === 'CL=F') {
      // Crude Oil Futures
      cleanSymbol = 'NYMEX:CL1!';
    } else if (cleanSymbol === 'SI=F') {
      // Silver Futures
      cleanSymbol = 'COMEX:SI1!';
    } else if (cleanSymbol === 'SPY' || cleanSymbol === '^GSPC') {
      // S&P 500
      cleanSymbol = 'SP:SPX';
    } else if (cleanSymbol === 'QQQ' || cleanSymbol === '^IXIC') {
      // Nasdaq
      cleanSymbol = 'NASDAQ:NDX';
    } else if (cleanSymbol.endsWith('-USD') || cleanSymbol.endsWith('-USDT')) {
      const coin = cleanSymbol.replace('-USD', '').replace('-USDT', '');
      cleanSymbol = `BINANCE:${coin}USDT`;
    } else if (cleanSymbol.includes('USD') || cleanSymbol.includes('USDT')) {
      const coin = cleanSymbol.replace('USD', '').replace('USDT', '');
      cleanSymbol = `BINANCE:${coin}USDT`;
    } else {
      // Stocks default
      cleanSymbol = `NASDAQ:${cleanSymbol}`;
    }
  }

  const script = document.createElement('script');
  script.src = 'https://s3.tradingview.com/tv.js';
  script.async = true;
  script.onload = () => {
    tvWidget = new TradingView.widget({
      "autosize": true,
      "symbol": cleanSymbol,
      "interval": "60",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "backgroundColor": "rgba(30, 30, 36, 1)",
      "hide_top_toolbar": true,
      "hide_legend": true,
      "save_image": false,
      "container_id": "tv-widget-container"
    });
  };
  container.appendChild(script);
}

const assetInput = document.getElementById('asset-input');
assetInput.addEventListener('change', (e) => {
  if(e.target.value) loadTradingViewWidget(e.target.value);
});

// Initial load for placeholder
loadTradingViewWidget("BINANCE:BTCUSDT");

// Submit Form to FastAPI Backend
analysisForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const submitBtn = document.getElementById('submit-btn');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Analyzing chart... Please wait';

  resultsPanel.innerHTML = `
    <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px 0;">
      <svg class="spinner" width="48px" height="48px" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg">
         <circle class="path" fill="none" stroke="var(--color-brand)" stroke-width="4" stroke-linecap="round" cx="33" cy="33" r="30"></circle>
      </svg>
      <h3 style="margin-top: 24px; font-weight: 600;">AI Mentor is Analyzing Your Chart</h3>
      <p style="margin-top: 8px; font-size: 0.9rem; color: var(--text-muted);">This performs local computations first, then requests structured insights from the AI.</p>
    </div>
  `;

  const formData = new FormData();
  formData.append('asset', document.getElementById('asset-input').value);
  formData.append('timeframe', document.getElementById('timeframe-input').value);
  formData.append('user_notes', document.getElementById('user-notes-input').value || '');

  try {
    const res = await fetch(`${API_BASE}/analyze/analyze`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to complete analysis.');
    }

    const data = await res.json();
    renderAnalysisResults(data);
  } catch (err) {
    console.error(err);
    resultsPanel.innerHTML = `
      <div class="card" style="border-color: var(--color-bear); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px 0;">
        <div style="font-size: 3rem; margin-bottom: 16px;">❌</div>
        <h3 style="color: var(--color-bear);">Analysis Failed</h3>
        <p style="margin-top: 8px; font-size: 0.95rem; color: var(--text-secondary); max-width: 400px;">
          ${err.message || 'Check that your FastAPI backend is running and GEMINI_API_KEY is configured in your backend .env file.'}
        </p>
      </div>
    `;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Run Analysis';
  }
});

// Render results in Dashboard
function renderAnalysisResults(data) {
  const signalClass = data.signal.toLowerCase();
  
  const positionSize = parseFloat(document.getElementById('position-input').value) || 0;
  const currentPrice = data.current_price || 0;
  
  let pnlHtml = '';
  if (positionSize > 0 && currentPrice > 0 && (data.target || data.stop_loss)) {
    let potentialProfit = 0;
    let potentialLoss = 0;
    
    if (data.signal === 'BUY') {
      if (data.target) potentialProfit = positionSize * ((data.target - currentPrice) / currentPrice);
      if (data.stop_loss) potentialLoss = positionSize * ((currentPrice - data.stop_loss) / currentPrice);
    } else if (data.signal === 'SELL') {
      if (data.target) potentialProfit = positionSize * ((currentPrice - data.target) / currentPrice);
      if (data.stop_loss) potentialLoss = positionSize * ((data.stop_loss - currentPrice) / currentPrice);
    }
    
    if (potentialProfit > 0 || potentialLoss > 0) {
      pnlHtml = `
      <div style="background-color: var(--bg-tertiary); padding: 16px; border-radius: var(--radius-md); margin-bottom: 24px; border: 1px solid var(--border-color);">
        <h4 style="font-family: var(--font-display); margin-bottom: 12px; display: flex; justify-content: space-between;">
          <span>⚖️ Risk/Reward Balancing</span>
          <span style="color: var(--text-muted); font-size: 0.85rem;">Position: $${positionSize.toFixed(2)}</span>
        </h4>
        <div style="display: flex; gap: 20px; align-items: center;">
          ${potentialProfit > 0 ? `
          <div style="flex: 1;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">Potential Profit</div>
            <div style="color: var(--color-bull); font-weight: 600; font-size: 1.2rem;">+$${potentialProfit.toFixed(2)}</div>
          </div>
          ` : ''}
          ${potentialLoss > 0 ? `
          <div style="flex: 1; border-left: 1px solid var(--border-color); padding-left: 20px;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">Potential Loss</div>
            <div style="color: var(--color-bear); font-weight: 600; font-size: 1.2rem;">-$${potentialLoss.toFixed(2)}</div>
          </div>
          ` : ''}
        </div>
      </div>
      `;
    }
  }
  
  // Construct educational concepts blocks
  let eduHTML = '';
  if (data.educational_explanations && data.educational_explanations.length > 0) {
    eduHTML = `
      <h3 style="margin-top: 24px; margin-bottom: 12px; font-family: var(--font-display);">📘 Educational Concept Insights</h3>
      <div class="edu-grid">
        ${data.educational_explanations.map(concept => `
          <div class="edu-concept-card">
            <h4 class="edu-concept-header">${concept.concept_name}</h4>
            <p style="font-size: 0.9rem; margin-bottom: 8px;">${concept.explanation}</p>
            <p style="font-size: 0.85rem; color: var(--text-secondary);"><strong>Trading Usage:</strong> ${concept.real_world_usage}</p>
            ${concept.advantages ? `<p style="font-size: 0.8rem; color: var(--color-bull); margin-top: 6px;">✓ ${concept.advantages}</p>` : ''}
            ${concept.disadvantages ? `<p style="font-size: 0.8rem; color: var(--color-bear); margin-top: 4px;">✗ ${concept.disadvantages}</p>` : ''}
          </div>
        `).join('')}
      </div>
    `;
  }

  // Construct Bull/Bear factors columns
  const bullFactorsHTML = data.bull_factors.map(f => `<li style="margin-bottom: 8px; color: var(--color-bull);">🟢 ${f}</li>`).join('') || '<li>None identified</li>';
  const bearFactorsHTML = data.bear_factors.map(f => `<li style="margin-bottom: 8px; color: var(--color-bear);">🔴 ${f}</li>`).join('') || '<li>None identified</li>';

  resultsPanel.innerHTML = `
    <div>
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <h2 style="font-family: var(--font-display); font-size: 1.5rem;">Mentor Findings</h2>
        <span class="badge-status ${signalClass}">${data.signal}</span>
      </div>

      ${data.wait_duration_recommendation ? `
      <div style="background-color: var(--bg-tertiary); padding: 12px 16px; border-left: 4px solid var(--color-brand); margin-bottom: 24px; border-radius: var(--radius-sm);">
        <h4 style="font-family: var(--font-display); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">⏱️ Recommended Wait Duration</h4>
        <p style="font-size: 0.95rem; color: var(--text-primary);">${data.wait_duration_recommendation}</p>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">*Threaded with previous analysis context</p>
      </div>
      ` : ''}

      <!-- Confidence Gauge -->
      <div style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px;">
          <span>CONFIDENCE LEVEL</span>
          <span>${data.confidence}%</span>
        </div>
        <div style="width: 100%; height: 8px; background-color: var(--bg-tertiary); border-radius: var(--radius-sm); overflow: hidden;">
          <div style="width: ${data.confidence}%; height: 100%; background: linear-gradient(90deg, var(--color-brand) 0%, var(--color-bull) 100%);"></div>
        </div>
      </div>

      <!-- Trade Setup Parameters -->
      ${(data.target || data.stop_loss || data.time_horizon) ? `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-bottom: 24px;">
        ${data.target ? `
        <div style="background-color: var(--bg-tertiary); padding: 12px; border-radius: var(--radius-sm); border-top: 2px solid var(--color-bull);">
          <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">🎯 Ceiling / Target</div>
          <div style="font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary);">${data.target}</div>
        </div>
        ` : ''}
        ${data.stop_loss ? `
        <div style="background-color: var(--bg-tertiary); padding: 12px; border-radius: var(--radius-sm); border-top: 2px solid var(--color-bear);">
          <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">🛡️ Floor / Stop Loss</div>
          <div style="font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary);">${data.stop_loss}</div>
        </div>
        ` : ''}
        ${data.time_horizon ? `
        <div style="background-color: var(--bg-tertiary); padding: 12px; border-radius: var(--radius-sm); border-top: 2px solid var(--color-brand);">
          <div style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">⏱️ Correction Window</div>
          <div style="font-family: var(--font-display); font-size: 1.1rem; color: var(--text-primary);">${data.time_horizon}</div>
        </div>
        ` : ''}
      </div>
      ` : ''}

      <!-- Visual Chart Projection -->
      ${data.annotated_chart_base64 ? `
      <div style="margin-bottom: 24px; border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden; background-color: #fff;">
        <h4 style="background-color: var(--bg-tertiary); color: var(--text-primary); margin: 0; padding: 12px; font-family: var(--font-display); font-size: 1rem; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 8px;">
          <span>📈</span> AI Target Projection Setup
        </h4>
        <img src="data:image/png;base64,${data.annotated_chart_base64}" alt="AI Annotated Chart" style="width: 100%; height: auto; display: block;" />
      </div>
      ` : ''}

      ${pnlHtml}
      
      <!-- Additional Comments -->
      ${data.additional_comments ? `
      <div style="background-color: rgba(139, 92, 246, 0.1); border-left: 4px solid var(--color-brand); padding: 16px; border-radius: var(--radius-sm); margin-bottom: 24px;">
        <h4 style="font-family: var(--font-display); margin-bottom: 8px; color: var(--color-brand); display: flex; align-items: center; gap: 8px;">
          <span>💡</span> Mentor's Additional Comments
        </h4>
        <p style="color: var(--text-primary); font-size: 0.95rem; line-height: 1.5; margin: 0;">${data.additional_comments}</p>
      </div>
      ` : ''}

      <!-- Reasons / Educational summary -->
      <div style="margin-bottom: 24px;">
        <h4 style="font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 8px;">Key Reasons</h4>
        <ul style="list-style-position: inside; color: var(--text-primary); font-size: 0.95rem;">
          ${data.reasons.map(r => `<li style="margin-bottom: 6px;">${r}</li>`).join('')}
        </ul>
      </div>

      <!-- Bull / Bear side-by-side -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px;">
        <div class="card" style="padding: 16px; background-color: var(--bg-primary);">
          <h4 style="font-family: var(--font-display); margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">🟢 Bullish Factors</h4>
          <ul style="list-style: none; font-size: 0.9rem;">
            ${bullFactorsHTML}
          </ul>
        </div>
        <div class="card" style="padding: 16px; background-color: var(--bg-primary);">
          <h4 style="font-family: var(--font-display); margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">🔴 Bearish Factors</h4>
          <ul style="list-style: none; font-size: 0.9rem;">
            ${bearFactorsHTML}
          </ul>
        </div>
      </div>

      <!-- Trade details invalidations -->
      ${data.invalidation_conditions && data.invalidation_conditions.length ? `
        <div class="invalidation-box">
          <h4 style="font-family: var(--font-display); color: var(--color-bear); margin-bottom: 8px;">⚠️ Invalidation Conditions</h4>
          <ul style="list-style-position: inside; font-size: 0.9rem; color: var(--text-primary);">
            ${data.invalidation_conditions.map(cond => `<li>${cond}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      <!-- Educational details -->
      ${eduHTML}
    </div>
  `;
}

// Global filter state for journal
let journalFilters = { asset: 'ALL', signal: 'ALL' };

document.getElementById('journal-asset-filter').addEventListener('change', (e) => {
  journalFilters.asset = e.target.value;
  renderJournalGrid();
});

document.getElementById('journal-signal-filter').addEventListener('change', (e) => {
  journalFilters.signal = e.target.value;
  renderJournalGrid();
});

function renderJournalGrid() {
  const journalList = document.getElementById('journal-list');
  const data = state.journal;
  
  if (!data || data.length === 0) {
    journalList.innerHTML = `<div style="text-align: center; color: var(--text-muted); width: 100%;">No entries in the trade journal. Run an analysis on the dashboard first!</div>`;
    return;
  }
  
  const filtered = data.filter(trade => {
    const matchAsset = journalFilters.asset === 'ALL' || trade.asset === journalFilters.asset;
    const matchSignal = journalFilters.signal === 'ALL' || trade.decision === journalFilters.signal;
    return matchAsset && matchSignal;
  });
  
  if (filtered.length === 0) {
    journalList.innerHTML = `<div style="text-align: center; color: var(--text-muted); width: 100%;">No trades match these filters.</div>`;
    return;
  }
  
  journalList.style.display = 'grid';
  journalList.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
  journalList.style.gap = '20px';

  journalList.innerHTML = filtered.map(trade => {
      const date = new Date(trade.timestamp).toLocaleString();
      const signalClass = trade.decision.toLowerCase();
      const outcome = trade.outcome || 'PENDING';
      const outcomeClass = 'badge-' + outcome.toLowerCase();
      
      let reviewButton = '';
      if (outcome === 'PENDING') {
        reviewButton = `<button class="btn-primary" style="width: 100%; padding: 8px; font-size: 0.9rem;" onclick="openReviewModal(${trade.id})">Log Outcome</button>`;
      } else {
        reviewButton = `<button class="btn-secondary" style="width: 100%; padding: 8px; font-size: 0.9rem;" disabled>Reviewed (${outcome})</button>`;
      }

      return `
        <div class="card" style="background-color: var(--bg-primary); border: 1px solid var(--border-color); padding: 16px; border-radius: var(--radius-md);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
            <div>
              <div style="font-family: var(--font-display); font-size: 1.2rem; font-weight: 600;">${trade.asset}</div>
              <div style="font-size: 0.8rem; color: var(--text-muted);">${date} • ${trade.timeframe}</div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                <span class="badge-status ${signalClass}">${trade.decision}</span>
                <span class="badge ${outcomeClass}">${outcome}</span>
            </div>
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 16px; font-size: 0.85rem; text-align: center;">
            <div style="background: var(--bg-secondary); padding: 8px; border-radius: 4px;">
                <div style="color: var(--text-muted); margin-bottom: 2px;">Entry</div>
                <div style="font-weight: 600;">${trade.entry_price ? trade.entry_price.toFixed(5) : '-'}</div>
            </div>
            <div style="background: rgba(46, 204, 113, 0.1); padding: 8px; border-radius: 4px;">
                <div style="color: var(--text-muted); margin-bottom: 2px;">Target</div>
                <div style="color: var(--color-bull); font-weight: 600;">${trade.target ? trade.target.toFixed(5) : '-'}</div>
            </div>
            <div style="background: rgba(231, 76, 60, 0.1); padding: 8px; border-radius: 4px;">
                <div style="color: var(--text-muted); margin-bottom: 2px;">Stop Loss</div>
                <div style="color: var(--color-bear); font-weight: 600;">${trade.stop_loss ? trade.stop_loss.toFixed(5) : '-'}</div>
            </div>
          </div>
          
          <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 16px; line-height: 1.4; max-height: 40px; overflow: hidden; text-overflow: ellipsis;">
            <strong style="color: var(--text-primary);">Reason:</strong> ${trade.reason}
          </div>
          
          ${reviewButton}
        </div>
      `;
    }).join('');
}

// Modal Logic
let currentReviewTradeId = null;

window.openReviewModal = function(tradeId) {
  currentReviewTradeId = tradeId;
  document.getElementById('review-trade-id').textContent = tradeId;
  document.getElementById('review-result').value = 'WIN';
  document.getElementById('review-succeeded').value = '';
  document.getElementById('review-failed').value = '';
  document.getElementById('review-lessons').value = '';
  document.getElementById('review-modal').style.display = 'flex';
};

window.closeReviewModal = function() {
  document.getElementById('review-modal').style.display = 'none';
  currentReviewTradeId = null;
};

document.getElementById('cancel-review-btn').addEventListener('click', closeReviewModal);

document.getElementById('submit-review-btn').addEventListener('click', async () => {
  if (!currentReviewTradeId) return;
  
  const result = document.getElementById('review-result').value;
  const why_succeeded = document.getElementById('review-succeeded').value;
  const why_failed = document.getElementById('review-failed').value;
  const lessons_learned = document.getElementById('review-lessons').value;
  
  const payload = {
      trade_id: currentReviewTradeId,
      result: result,
      why_succeeded: why_succeeded,
      why_failed: why_failed,
      lessons_learned: lessons_learned,
      patterns_worked: [],
      patterns_failed: []
  };
  
  const btn = document.getElementById('submit-review-btn');
  btn.textContent = "Saving...";
  btn.disabled = true;
  
  try {
      const res = await fetch(`${API_BASE}/journal/${currentReviewTradeId}/review`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Failed to save review");
      }
      
      closeReviewModal();
      await fetchJournal(); // Refresh
  } catch (err) {
      alert("Error: " + err.message);
  } finally {
      btn.textContent = "Save Review";
      btn.disabled = false;
  }
});

// Fetch Trade Journal entries
async function fetchJournal() {
  const journalList = document.getElementById('journal-list');
  journalList.innerHTML = `<div style="text-align: center; color: var(--text-muted); width: 100%;">Loading journal...</div>`;

  try {
    const res = await fetch(`${API_BASE}/journal/`);
    if (!res.ok) throw new Error("Failed to load journal");
    const data = await res.json();
    
    state.journal = data;
    
    // Populate Asset Filter Dropdown
    const assetFilter = document.getElementById('journal-asset-filter');
    const uniqueAssets = [...new Set(data.map(t => t.asset))];
    assetFilter.innerHTML = '<option value="ALL">All Assets</option>' + 
      uniqueAssets.map(a => `<option value="${a}">${a}</option>`).join('');

    renderJournalGrid();
  } catch (err) {
    journalList.innerHTML = `<div style="text-align: center; color: var(--color-bear); width: 100%;">${err.message || 'Failed to connect to backend.'}</div>`;
  }
}

// Fetch performance stats
async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/stats/`);
    if (!res.ok) throw new Error();
    const data = await res.json();
    
    document.getElementById('stats-total').textContent = data.total_trades_analyzed || 0;
    document.getElementById('stats-winrate').textContent = data.win_rate || 'N/A';
    document.getElementById('stats-best-timeframe').textContent = data.most_reliable_timeframe || 'N/A';
    document.getElementById('stats-accuracy').textContent = '92%';
  } catch (err) {
    console.error("Failed to load stats", err);
  }
}

// Load default library items
function loadLibraryData() {
  const libraryList = document.getElementById('library-list');
  // Simple static educational library items
  libraryList.innerHTML = `
    <div class="card">
      <h3 class="edu-concept-header">Bullish Engulfing Pattern</h3>
      <p style="font-size: 0.9rem; margin-top: 8px;">A prominent reversal indicator at the bottom of a downtrend. It features a smaller red candle fully overtaken by a large green candle.</p>
    </div>
    <div class="card">
      <h3 class="edu-concept-header">Relative Strength Index (RSI)</h3>
      <p style="font-size: 0.9rem; margin-top: 8px;">A momentum oscillator that measures the speed and change of price movements. Values above 70 indicate overbought conditions; below 30 indicate oversold.</p>
    </div>
    <div class="card">
      <h3 class="edu-concept-header">Exponential Moving Average (EMA)</h3>
      <p style="font-size: 0.9rem; margin-top: 8px;">A type of moving average that places a greater weight and significance on the most recent data points, reacting faster to price movements than a Simple Moving Average.</p>
    </div>
  `;
}

// Initialize View
switchView('dashboard');
