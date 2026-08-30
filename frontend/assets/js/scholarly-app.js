/**
 * LEMMA 2.0 — SCHOLARLY INSTRUMENT ENGINE
 * Full-stack interactive client for document intelligence, plagiarism detection,
 * multi-tone paraphrasing, RAG chat assistant, history, workspace, and Pandaz PDF suite.
 */

(function () {
  'use strict';

  // --- API BASE PATH CONFIGURATION ---
  const API_BASE = window.location.origin.includes('8000')
    ? ''
    : (window.LEMMA_CONFIG?.API_BASE_URL || '');

  // --- GLOBAL APPLICATION STATE ---
  const state = {
    theme: localStorage.getItem('lemma-theme') || 'dark',
    activeView: 'view-dashboard',
    currentDoc: {
      id: null,
      filename: 'Sample Academic Paper.txt',
      title: 'Neural Representation Learning & Research Integrity',
      text: `Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning. The adjective deep in deep learning refers to the use of multiple layers in the network. Historically, neural networks were limited in depth due to computational constraints and training difficulties. Today, modern deep learning architectures utilize convolutional neural networks and transformer architectures to process vast datasets. In this paper, we introduce an empirical evaluation of lexical and semantic document similarity metrics to assist researchers in maintaining manuscript originality.`,
      char_count: 538,
      sentence_count: 5,
      sentences: [],
      metrics: {
        word_count: 76,
        char_count: 538,
        sentence_count: 5,
        avg_sentence_length: 15.2,
        lexical_diversity: 0.72,
        flesch_reading_ease: 42.5,
        flesch_kincaid_grade: '12.4',
        readability_level: 'Fairly Difficult (College)',
        reading_time_minutes: 0.4
      },
      analysis: {
        plagiarism_score: 40.0,
        originality_score: 60.0,
        lexical_score: 50.0,
        semantic_score: 30.0,
        hybrid_score: 40.0,
        total_sentences: 5,
        matched_sentences_count: 2,
        matches: [
          {
            query_sentence: {
              text: "Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning.",
              start_char: 0,
              end_char: 120
            },
            matched_sentence: {
              text: "Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning.",
              doc_id: "ref_deep_learning",
              doc_title: "Deep Learning: Principles and Foundations",
              doc_author: "Dr. Sarah Jenkins",
              doc_source: "Journal of Artificial Intelligence Research, 2024",
              doc_url: "https://doi.org/10.1016/j.jair.2024.01.004"
            },
            match_type: "lexical",
            similarity: 0.98,
            score: 0.98,
            highlights: [{ start_char: 0, end_char: 120, text: "Deep learning is a subset of machine learning..." }]
          },
          {
            query_sentence: {
              text: "The adjective deep in deep learning refers to the use of multiple layers in the network.",
              start_char: 121,
              end_char: 209
            },
            matched_sentence: {
              text: "The term deep denotes the presence of numerous successive layers through which data is transformed.",
              doc_id: "ref_neural_nets",
              doc_title: "Foundations of Modern Deep Neural Architectures",
              doc_author: "Prof. Elena Rostova",
              doc_source: "MIT Press AI Series, 2023",
              doc_url: "https://mitpress.mit.edu/foundations-deep-learning"
            },
            match_type: "semantic",
            similarity: 0.74,
            score: 0.74,
            highlights: [{ start_char: 121, end_char: 209, text: "The adjective deep..." }]
          }
        ]
      }
    },
    selectedSentenceIndex: 0,
    activeTone: 'academic',
    history: [],
    projects: [],
    activeProject: 'default',
    chatMessages: [
      {
        role: 'assistant',
        text: "👋 Welcome to **Ask Lemma**! I am your document-aware research assistant. I have full context of your manuscript, plagiarism scores, matched sources, and readability metrics. What would you like to examine?"
      }
    ],
    pandaz: {
      activeTool: 'merge',
      uploadedFiles: [],
      result: null
    }
  };

  // --- INITIALIZATION ---
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initCommandPalette();
    initAnalyzeView();
    initParaphraserView();
    initAskLemmaView();
    initSourcesView();
    initReportsView();
    initHistoryView();
    initWorkspaceView();
    initPandazView();
    fetchSystemStatus();
    loadRemoteHistory();
    loadRemoteProjects();

    // Render default state on load
    renderManuscript();
    renderDashboardOverview();
  });

  // --- THEME SYSTEM (INK / PAPER) ---
  function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
    toggleBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        state.theme = state.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', state.theme);
        localStorage.setItem('lemma-theme', state.theme);
        updateThemeIcons();
      });
    });
    updateThemeIcons();
  }

  function updateThemeIcons() {
    const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
    toggleBtns.forEach(btn => {
      btn.innerHTML = state.theme === 'dark'
        ? '<i class="fa-solid fa-sun"></i>'
        : '<i class="fa-solid fa-moon"></i>';
      btn.title = state.theme === 'dark' ? 'Switch to Paper (Light) Theme' : 'Switch to Ink (Dark) Theme';
    });
  }

  // --- NAVIGATION & VIEW ROUTING ---
  function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item-btn[data-target]');
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        const targetView = item.getAttribute('data-target');
        switchView(targetView);
      });
    });

    // Handle hash links
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '');
      if (hash) {
        const matchingBtn = document.querySelector(`.nav-item-btn[data-target="view-${hash}"]`);
        if (matchingBtn) {
          switchView(`view-${hash}`);
        }
      }
    });

    // Quick Launch Buttons
    document.querySelectorAll('[data-goto]').forEach(el => {
      el.addEventListener('click', () => {
        const target = el.getAttribute('data-goto');
        switchView(target);
      });
    });
  }

  function switchView(viewId) {
    state.activeView = viewId;
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    const targetSection = document.getElementById(viewId);
    if (targetSection) targetSection.classList.add('active');

    document.querySelectorAll('.nav-item-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`.nav-item-btn[data-target="${viewId}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    // Update Breadcrumb
    const bc = document.getElementById('breadcrumb-active-label');
    if (bc && activeBtn) {
      const label = activeBtn.querySelector('span') ? activeBtn.querySelector('span').textContent : viewId;
      bc.textContent = label;
    }

    // Refresh specific view contents
    if (viewId === 'view-analyze') renderManuscript();
    if (viewId === 'view-dashboard') renderDashboardOverview();
    if (viewId === 'view-sources') renderSourcesList();
    if (viewId === 'view-reports') renderReportsView();
    if (viewId === 'view-history') renderHistoryTable();
    if (viewId === 'view-workspace') renderWorkspaceView();
  }

  // --- SYSTEM STATUS & RESILIENCE ---
  async function fetchSystemStatus() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/system/status`);
      if (res.ok) {
        const data = await res.json();
        const indicator = document.getElementById('system-status-text');
        if (indicator) {
          indicator.textContent = data.mode || 'Lite Mode (Local Ready)';
        }
      }
    } catch (e) {
      console.warn('Using offline status indicator');
    }
  }

  // --- 1. DASHBOARD VIEW ---
  function renderDashboardOverview() {
    const doc = state.currentDoc;
    const plagScoreEl = document.getElementById('dash-plag-score');
    const origScoreEl = document.getElementById('dash-orig-score');
    const wordsEl = document.getElementById('dash-words-count');
    const gradeEl = document.getElementById('dash-grade-level');
    const docNameEl = document.getElementById('dash-doc-name');

    if (plagScoreEl) plagScoreEl.textContent = `${doc.analysis.plagiarism_score || 0}%`;
    if (origScoreEl) origScoreEl.textContent = `${doc.analysis.originality_score || 100}%`;
    if (wordsEl) wordsEl.textContent = (doc.metrics.word_count || 0).toLocaleString();
    if (gradeEl) gradeEl.textContent = doc.metrics.flesch_kincaid_grade || 'Grade 12';
    if (docNameEl) docNameEl.textContent = doc.filename || 'Untitled Document';
  }

  // --- 2. MANUSCRIPT DESK & ANALYZE VIEW ---
  function initAnalyzeView() {
    // Paste Text Modal triggers
    const pasteBtn = document.getElementById('btn-paste-text-modal');
    const pasteSubmit = document.getElementById('btn-submit-pasted-text');
    const pasteArea = document.getElementById('paste-text-input');
    const fileUploadInput = document.getElementById('manuscript-file-upload');

    if (pasteSubmit && pasteArea) {
      pasteSubmit.addEventListener('click', async () => {
        const text = pasteArea.value.trim();
        if (!text) return alert('Please enter manuscript text to analyze.');
        await analyzeDirectText(text, 'Pasted Manuscript');
        document.getElementById('paste-text-modal').classList.remove('open');
      });
    }

    if (fileUploadInput) {
      fileUploadInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) await uploadAndAnalyzeFile(file);
      });
    }

    // Drag and Drop on Analyze View
    const dropZone = document.getElementById('analyze-dropzone');
    if (dropZone) {
      dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
      dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
          await uploadAndAnalyzeFile(e.dataTransfer.files[0]);
        }
      });
    }
  }

  async function analyzeDirectText(text, title = 'Manuscript') {
    showLoadingOverlay('Analyzing manuscript structure and originality...');
    try {
      const res = await fetch(`${API_BASE}/api/v1/analyze/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, title })
      });
      if (!res.ok) throw new Error('Analysis failed');
      const data = await res.json();
      updateDocumentState(data);
      await saveToHistory(data);
      switchView('view-analyze');
    } catch (err) {
      alert(`Analysis error: ${err.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  async function uploadAndAnalyzeFile(file) {
    showLoadingOverlay(`Uploading & analyzing ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/api/v1/documents/upload`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error('Document extraction & analysis failed');
      const data = await res.json();
      updateDocumentState(data);
      await saveToHistory(data);
      switchView('view-analyze');
    } catch (err) {
      alert(`Upload error: ${err.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  function updateDocumentState(data) {
    state.currentDoc.filename = data.filename || 'Manuscript';
    state.currentDoc.title = data.filename || 'Manuscript';
    state.currentDoc.text = data.text || '';
    state.currentDoc.char_count = data.char_count || data.text.length;
    state.currentDoc.sentence_count = data.sentence_count || (data.sentences ? data.sentences.length : 0);
    state.currentDoc.sentences = data.sentences || [];
    state.currentDoc.metrics = data.metrics || {};
    state.currentDoc.analysis = data.analysis || {};
    state.selectedSentenceIndex = 0;
    renderManuscript();
    renderDashboardOverview();
  }

  function renderManuscript() {
    const container = document.getElementById('manuscript-text-pane');
    if (!container) return;

    const doc = state.currentDoc;
    const matches = doc.analysis.matches || [];

    // Title & Doc details
    const titleEl = document.getElementById('manuscript-header-title');
    const wordPill = document.getElementById('manuscript-word-pill');
    const plagPill = document.getElementById('manuscript-plag-pill');
    if (titleEl) titleEl.textContent = doc.filename || 'Manuscript';
    if (wordPill) wordPill.textContent = `${doc.metrics.word_count || 0} Words`;
    if (plagPill) {
      const pScore = doc.analysis.plagiarism_score || 0;
      plagPill.textContent = `${pScore}% Flagged`;
      plagPill.className = pScore > 15 ? 'score-badge danger' : 'score-badge clean';
    }

    // If sentences list is empty, split by sentences
    let sentences = doc.sentences;
    if (!sentences || !sentences.length) {
      const rawSents = doc.text.match(/[^.!?]+[.!?]+/g) || [doc.text];
      let offset = 0;
      sentences = rawSents.map(s => {
        const start = doc.text.indexOf(s, offset);
        const end = start + s.length;
        offset = end;
        return { text: s.trim(), start_char: start, end_char: end };
      });
      doc.sentences = sentences;
    }

    container.innerHTML = '';

    sentences.forEach((sent, idx) => {
      // Check if sentence matches any flagged match
      const matched = matches.find(m => {
        const qText = m.query_sentence ? m.query_sentence.text : (m.query_text || '');
        return qText.trim() === sent.text.trim() ||
               (m.query_sentence && m.query_sentence.start_char === sent.start_char);
      });

      const span = document.createElement('span');
      span.className = 'manuscript-sentence';
      span.textContent = sent.text + ' ';
      span.dataset.index = idx;
      span.dataset.start = sent.start_char;
      span.dataset.end = sent.end_char;

      if (matched) {
        const mType = (matched.match_type || 'lexical').toLowerCase();
        span.classList.add(`flagged-${mType}`);
      }

      if (idx === state.selectedSentenceIndex) {
        span.classList.add('selected-sentence');
      }

      span.addEventListener('click', () => {
        selectSentence(idx, matched);
      });

      container.appendChild(span);
    });

    // Render Inspector Dock for the initially selected sentence
    const initialMatch = matches.find(m => {
      const qText = m.query_sentence ? m.query_sentence.text : (m.query_text || '');
      return sentences[state.selectedSentenceIndex] && qText.trim() === sentences[state.selectedSentenceIndex].text.trim();
    });
    renderInspectorDock(state.selectedSentenceIndex, initialMatch);
  }

  function selectSentence(index, matchData) {
    state.selectedSentenceIndex = index;
    document.querySelectorAll('.manuscript-sentence').forEach(el => {
      el.classList.toggle('selected-sentence', parseInt(el.dataset.index) === index);
    });
    renderInspectorDock(index, matchData);
  }

  function renderInspectorDock(index, matchData) {
    const dock = document.getElementById('inspector-dock-content');
    if (!dock) return;

    const sentence = state.currentDoc.sentences[index];
    if (!sentence) {
      dock.innerHTML = '<p class="text-muted">Select any sentence in the manuscript to inspect its character coordinates and source matches.</p>';
      return;
    }

    const startChar = sentence.start_char || 0;
    const endChar = sentence.end_char || sentence.text.length;
    const len = endChar - startChar;

    let matchHtml = '';
    if (matchData) {
      const src = matchData.matched_sentence || {};
      const sim = Math.round((matchData.similarity || matchData.score || 0.8) * 100);
      const mType = (matchData.match_type || 'lexical').toUpperCase();
      const docTitle = src.doc_title || 'Academic Reference Library';
      const docAuthor = src.doc_author || 'Scholar / Academic Author';
      const docSource = src.doc_source || 'Scholarly Journal';
      const docUrl = src.doc_url || '';

      matchHtml = `
        <div class="inspector-card">
          <div class="inspector-header">
            <span class="inspector-title"><i class="fa-solid fa-triangle-exclamation" style="color:var(--accent-flag)"></i> Matched Source</span>
            <span class="score-badge danger">${sim}% ${mType}</span>
          </div>
          <div class="match-comparison-box">
            <div>
              <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); margin-bottom:4px;">MANUSCRIPT SENTENCE</div>
              <div class="sentence-snippet target">${escapeHtml(sentence.text)}</div>
            </div>
            <div>
              <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); margin-bottom:4px;">MATCHED REFERENCE</div>
              <div class="sentence-snippet source">${escapeHtml(src.text || sentence.text)}</div>
              <div class="source-meta">
                <strong>${escapeHtml(docTitle)}</strong> by ${escapeHtml(docAuthor)}<br>
                <span>${escapeHtml(docSource)}</span>
                ${docUrl ? `<br><a href="${docUrl}" target="_blank" style="color:var(--accent-scholarly); text-decoration:underline;">View Publication <i class="fa-solid fa-arrow-up-right-from-square"></i></a>` : ''}
              </div>
            </div>
          </div>
          <div style="display:flex; gap:0.5rem; margin-top:1rem;">
            <button class="btn btn-primary btn-sm" id="btn-quick-rewrite" style="flex:1;">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Paraphrase
            </button>
            <button class="btn btn-secondary btn-sm" id="btn-copy-match" title="Copy Sentence">
              <i class="fa-regular fa-copy"></i>
            </button>
          </div>
        </div>
      `;
    } else {
      matchHtml = `
        <div class="inspector-card">
          <div class="inspector-header">
            <span class="inspector-title"><i class="fa-solid fa-circle-check" style="color:var(--accent-clean)"></i> Originality Status</span>
            <span class="score-badge clean">100% Clean</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:0.75rem;">
            This sentence contains zero direct lexical or semantic overlaps with the reference database.
          </p>
          <div class="sentence-snippet" style="border-left-color:var(--accent-clean)">
            ${escapeHtml(sentence.text)}
          </div>
        </div>
      `;
    }

    const coordinateHtml = `
      <div class="inspector-card">
        <div class="inspector-header">
          <span class="inspector-title"><i class="fa-solid fa-ruler-combined"></i> Coordinate Inspector</span>
          <span class="nav-badge">SENTENCE #${index + 1}</span>
        </div>
        <table class="coordinate-table">
          <tr><td>Start Character:</td><td><code>${startChar}</code></td></tr>
          <tr><td>End Character:</td><td><code>${endChar}</code></td></tr>
          <tr><td>Character Length:</td><td><code>${len} chars</code></td></tr>
          <tr><td>Word Count:</td><td><code>${sentence.text.trim().split(/\s+/).length} words</code></td></tr>
        </table>
      </div>
    `;

    dock.innerHTML = matchHtml + coordinateHtml;

    // Attach actions
    const rewriteBtn = document.getElementById('btn-quick-rewrite');
    if (rewriteBtn) {
      rewriteBtn.addEventListener('click', () => {
        loadSentenceIntoParaphraser(sentence.text);
      });
    }

    const copyBtn = document.getElementById('btn-copy-match');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(sentence.text);
        copyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
        setTimeout(() => copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i>', 1500);
      });
    }
  }

  // --- 3. PARAPHRASER WORKBENCH ---
  function initParaphraserView() {
    const toneButtons = document.querySelectorAll('.tone-btn');
    toneButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        toneButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeTone = btn.dataset.tone;
      });
    });

    const rewriteBtn = document.getElementById('btn-execute-rewrite');
    const replaceBtn = document.getElementById('btn-replace-in-manuscript');
    const copyOutputBtn = document.getElementById('btn-copy-paraphrase');
    const rewriteAllBtn = document.getElementById('btn-rewrite-all-flagged');
    const reanalyzeBtn = document.getElementById('btn-reanalyze-manuscript');

    if (rewriteBtn) {
      rewriteBtn.addEventListener('click', async () => {
        const inputArea = document.getElementById('paraphrase-input-text');
        const text = inputArea.value.trim();
        if (!text) return alert('Please enter or select text to rewrite.');

        showLoadingOverlay(`Paraphrasing in ${state.activeTone} tone...`);
        try {
          const res = await fetch(`${API_BASE}/api/v1/rewrite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, tone: state.activeTone })
          });
          if (!res.ok) throw new Error('Paraphrase request failed');
          const data = await res.json();
          const outputArea = document.getElementById('paraphrase-output-text');
          outputArea.value = data.rewritten_text || '';
          updateParaphraseStats(text, data.rewritten_text || '');
        } catch (e) {
          alert(`Paraphrasing error: ${e.message}`);
        } finally {
          hideLoadingOverlay();
        }
      });
    }

    if (replaceBtn) {
      replaceBtn.addEventListener('click', () => {
        const inputArea = document.getElementById('paraphrase-input-text');
        const outputArea = document.getElementById('paraphrase-output-text');
        const original = inputArea.value.trim();
        const rewritten = outputArea.value.trim();
        if (!original || !rewritten) return alert('No rewritten text to replace.');

        state.currentDoc.text = state.currentDoc.text.replace(original, rewritten);
        inputArea.value = rewritten;
        outputArea.value = '';
        renderManuscript();
        alert('Sentence successfully updated in active manuscript!');
      });
    }

    if (copyOutputBtn) {
      copyOutputBtn.addEventListener('click', () => {
        const outputArea = document.getElementById('paraphrase-output-text');
        if (outputArea.value) {
          navigator.clipboard.writeText(outputArea.value);
          copyOutputBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
          setTimeout(() => copyOutputBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy Output', 1500);
        }
      });
    }

    // Batch Rewrite All Flagged Sentences
    if (rewriteAllBtn) {
      rewriteAllBtn.addEventListener('click', async () => {
        const matches = state.currentDoc.analysis.matches || [];
        if (!matches.length) return alert('No flagged sentences to rewrite.');

        const sentencesToRewrite = matches.map(m => m.query_sentence ? m.query_sentence.text : (m.query_text || ''));
        showLoadingOverlay(`Batch paraphrasing ${sentencesToRewrite.length} flagged sentences...`);

        try {
          const res = await fetch(`${API_BASE}/api/v1/rewrite/batch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sentences: sentencesToRewrite, tone: state.activeTone })
          });
          if (!res.ok) throw new Error('Batch rewrite failed');
          const data = await res.json();
          
          // Replace each sentence in current document
          data.results.forEach(item => {
            if (item.original && item.rewritten) {
              state.currentDoc.text = state.currentDoc.text.replace(item.original, item.rewritten);
            }
          });

          // Automatically trigger re-analysis to show real score improvement!
          await reanalyzeCurrentManuscript();
          switchView('view-analyze');
        } catch (e) {
          alert(`Batch rewrite error: ${e.message}`);
        } finally {
          hideLoadingOverlay();
        }
      });
    }

    if (reanalyzeBtn) {
      reanalyzeBtn.addEventListener('click', async () => {
        await reanalyzeCurrentManuscript();
      });
    }
  }

  function loadSentenceIntoParaphraser(sentenceText) {
    const inputArea = document.getElementById('paraphrase-input-text');
    const outputArea = document.getElementById('paraphrase-output-text');
    if (inputArea) inputArea.value = sentenceText;
    if (outputArea) outputArea.value = '';
    updateParaphraseStats(sentenceText, '');
    switchView('view-paraphrase');
  }

  function updateParaphraseStats(orig, rew) {
    const origWords = orig.trim() ? orig.trim().split(/\s+/).length : 0;
    const rewWords = rew.trim() ? rew.trim().split(/\s+/).length : 0;
    const diffStat = document.getElementById('paraphrase-diff-stat');
    if (diffStat) {
      const delta = rewWords - origWords;
      diffStat.textContent = rew ? `Original: ${origWords} words → Rewritten: ${rewWords} words (${delta >= 0 ? '+' : ''}${delta})` : `Word Count: ${origWords}`;
    }
  }

  async function reanalyzeCurrentManuscript() {
    showLoadingOverlay('Re-analyzing updated manuscript to verify originality improvement...');
    const oldScore = state.currentDoc.analysis.plagiarism_score || 0;
    try {
      const res = await fetch(`${API_BASE}/api/v1/analyze/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: state.currentDoc.text, title: state.currentDoc.filename })
      });
      if (!res.ok) throw new Error('Re-analysis failed');
      const data = await res.json();
      updateDocumentState(data);
      await saveToHistory(data);
      const newScore = data.analysis.plagiarism_score || 0;
      alert(`🎉 Re-Analysis Complete!\nPlagiarism Score changed from ${oldScore}% → ${newScore}%!`);
    } catch (e) {
      alert(`Re-analysis error: ${e.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  // --- 4. ASK LEMMA CHAT (RAG ASSISTANT) ---
  function initAskLemmaView() {
    const sendBtn = document.getElementById('btn-send-chat');
    const inputEl = document.getElementById('chat-user-input');
    const prompts = document.querySelectorAll('.chat-suggestion-pill');

    if (sendBtn && inputEl) {
      sendBtn.addEventListener('click', () => sendChatMessage());
      inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendChatMessage();
        }
      });
    }

    prompts.forEach(p => {
      p.addEventListener('click', () => {
        if (inputEl) {
          inputEl.value = p.textContent.trim().replace(/^['"]|['"]$/g, '');
          sendChatMessage();
        }
      });
    });

    renderChatMessages();
  }

  async function sendChatMessage() {
    const inputEl = document.getElementById('chat-user-input');
    const msg = inputEl.value.trim();
    if (!msg) return;

    inputEl.value = '';
    state.chatMessages.push({ role: 'user', text: msg });
    renderChatMessages();

    // Create placeholder assistant message
    const placeholderMsg = { role: 'assistant', text: 'Thinking...' };
    state.chatMessages.push(placeholderMsg);
    renderChatMessages();

    try {
      const payload = {
        message: msg,
        context: {
          text: state.currentDoc.text,
          filename: state.currentDoc.filename,
          metrics: state.currentDoc.metrics,
          analysis: state.currentDoc.analysis,
          matches: state.currentDoc.analysis.matches || [],
          sources: (state.currentDoc.analysis.matches || []).map(m => m.matched_sentence || {})
        }
      };

      const res = await fetch(`${API_BASE}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Chat assistant response failed');
      const data = await res.json();
      placeholderMsg.text = data.response || 'I have analyzed your request.';
    } catch (e) {
      placeholderMsg.text = `⚠️ Error: ${e.message}`;
    } finally {
      renderChatMessages();
    }
  }

  function renderChatMessages() {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    container.innerHTML = '';
    state.chatMessages.forEach(m => {
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${m.role}`;
      bubble.innerHTML = formatMarkdown(m.text);
      container.appendChild(bubble);
    });

    container.scrollTop = container.scrollHeight;
  }

  // --- 5. SOURCES DISCOVERY VIEW ---
  function initSourcesView() {
    const searchBtn = document.getElementById('btn-search-sources');
    const searchInput = document.getElementById('sources-search-query');
    const filterTabs = document.querySelectorAll('.source-filter-tab');

    if (searchBtn && searchInput) {
      searchBtn.addEventListener('click', () => {
        fetchExternalSources(searchInput.value.trim());
      });
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') fetchExternalSources(searchInput.value.trim());
      });
    }

    filterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        filterTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        renderSourcesList(tab.dataset.filter);
      });
    });
  }

  function renderSourcesList(filter = 'all') {
    const container = document.getElementById('sources-list-container');
    if (!container) return;

    const matches = state.currentDoc.analysis.matches || [];
    let filtered = matches;
    if (filter !== 'all') {
      filtered = matches.filter(m => (m.match_type || 'lexical').toLowerCase() === filter);
    }

    if (!filtered.length) {
      container.innerHTML = `<div class="inspector-card"><p class="text-muted">No ${filter === 'all' ? '' : filter} sources flagged for this document.</p></div>`;
      return;
    }

    container.innerHTML = filtered.map((m, idx) => {
      const src = m.matched_sentence || {};
      const sim = Math.round((m.similarity || m.score || 0.8) * 100);
      const mType = (m.match_type || 'lexical').toUpperCase();
      return `
        <div class="inspector-card" style="margin-bottom:1rem;">
          <div class="inspector-header">
            <span class="inspector-title"><i class="fa-solid fa-book-bookmark"></i> ${escapeHtml(src.doc_title || 'Reference Document')}</span>
            <span class="score-badge danger">${sim}% ${mType}</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:0.5rem;">
            Author: <strong>${escapeHtml(src.doc_author || 'N/A')}</strong> | Source: <em>${escapeHtml(src.doc_source || 'Academic Library')}</em>
          </p>
          <div class="sentence-snippet source">${escapeHtml(src.text || '')}</div>
          ${src.doc_url ? `<div style="margin-top:0.5rem;"><a href="${src.doc_url}" target="_blank" style="font-size:0.8rem; color:var(--accent-scholarly);">Open Publication Source <i class="fa-solid fa-arrow-up-right-from-square"></i></a></div>` : ''}
        </div>
      `;
    }).join('');
  }

  async function fetchExternalSources(query) {
    if (!query) return;
    showLoadingOverlay(`Searching OpenAlex, Crossref, arXiv, and Wikipedia for "${query}"...`);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/discover?query=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Search failed');
      const data = await res.json();
      const container = document.getElementById('sources-list-container');
      if (!data || !data.length) {
        container.innerHTML = '<div class="inspector-card"><p class="text-muted">No external sources found for query.</p></div>';
        return;
      }
      container.innerHTML = data.map(item => `
        <div class="inspector-card" style="margin-bottom:1rem;">
          <div class="inspector-header">
            <span class="inspector-title"><i class="fa-solid fa-globe"></i> ${escapeHtml(item.title)}</span>
            <span class="nav-badge">${item.provider || 'Academic API'}</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:0.5rem;">
            Author: <strong>${escapeHtml(item.author || 'Scholarly Authors')}</strong> | Source: <em>${escapeHtml(item.source || 'Open Access')}</em>
          </p>
          <div class="sentence-snippet">${escapeHtml(item.text || '')}</div>
          ${item.url ? `<div style="margin-top:0.5rem;"><a href="${item.url}" target="_blank" style="font-size:0.8rem; color:var(--accent-scholarly);">Access Resource <i class="fa-solid fa-arrow-up-right-from-square"></i></a></div>` : ''}
        </div>
      `).join('');
    } catch (e) {
      alert(`Source discovery error: ${e.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  // --- 6. REPORTS VIEW ---
  function initReportsView() {
    const downloadPdfBtn = document.getElementById('btn-download-pdf-report');
    if (downloadPdfBtn) {
      downloadPdfBtn.addEventListener('click', async () => {
        await downloadIntegrityPdfReport();
      });
    }
  }

  function renderReportsView() {
    const doc = state.currentDoc;
    const docTitle = document.getElementById('report-doc-title');
    const plagScore = document.getElementById('report-plag-score');
    const origScore = document.getElementById('report-orig-score');
    const lexicalScore = document.getElementById('report-lexical-score');
    const semanticScore = document.getElementById('report-semantic-score');

    if (docTitle) docTitle.textContent = doc.filename || 'Manuscript';
    if (plagScore) plagScore.textContent = `${doc.analysis.plagiarism_score || 0}%`;
    if (origScore) origScore.textContent = `${doc.analysis.originality_score || 100}%`;
    if (lexicalScore) lexicalScore.textContent = `${doc.analysis.lexical_score || 0}%`;
    if (semanticScore) semanticScore.textContent = `${doc.analysis.semantic_score || 0}%`;
  }

  async function downloadIntegrityPdfReport() {
    showLoadingOverlay('Generating Lemma Integrity PDF Report...');
    try {
      const payload = {
        filename: `${state.currentDoc.filename.replace(/\.[^/.]+$/, '')}_Integrity_Report.pdf`,
        text: state.currentDoc.text,
        char_count: state.currentDoc.char_count,
        sentence_count: state.currentDoc.sentence_count,
        sentences: state.currentDoc.sentences,
        metrics: state.currentDoc.metrics,
        analysis: state.currentDoc.analysis
      };

      const res = await fetch(`${API_BASE}/api/v1/documents/report/direct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Report generation failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = payload.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Report download error: ${e.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  // --- 7. HISTORY VIEW & PERSISTENCE ---
  function initHistoryView() {
    const clearBtn = document.getElementById('btn-clear-history');
    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        if (confirm('Clear all local analysis history?')) {
          state.history = [];
          renderHistoryTable();
        }
      });
    }
  }

  async function loadRemoteHistory() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/history`);
      if (res.ok) {
        const data = await res.json();
        state.history = data.history || [];
      }
    } catch (e) {
      console.warn('Could not load history from server, using local memory');
    }
  }

  async function saveToHistory(docData) {
    try {
      const payload = {
        id: docData.id || `hist_${Date.now()}`,
        filename: docData.filename || 'Manuscript',
        title: docData.filename || 'Manuscript',
        char_count: docData.char_count || docData.text.length,
        sentence_count: docData.sentence_count || (docData.sentences ? docData.sentences.length : 0),
        text: docData.text,
        metrics: docData.metrics,
        analysis: docData.analysis,
        sentences: docData.sentences,
        project_id: state.activeProject
      };
      await fetch(`${API_BASE}/api/v1/history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      await loadRemoteHistory();
    } catch (e) {
      console.warn('History save error:', e);
    }
  }

  function renderHistoryTable() {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;

    if (!state.history.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted" style="text-align:center; padding:2rem;">No historical analyses found. Upload or paste a manuscript to begin.</td></tr>';
      return;
    }

    tbody.innerHTML = state.history.map(item => {
      const plag = item.analysis ? (item.analysis.plagiarism_score || 0) : 0;
      const orig = item.analysis ? (item.analysis.originality_score || 100) : 100;
      return `
        <tr>
          <td><strong>${escapeHtml(item.filename || 'Document')}</strong></td>
          <td><span class="score-badge ${plag > 15 ? 'danger' : 'clean'}">${plag}%</span></td>
          <td><span class="score-badge clean">${orig}%</span></td>
          <td><code>${(item.char_count || 0).toLocaleString()} chars</code></td>
          <td style="font-size:0.8rem; color:var(--text-muted);">${item.created_at || 'Recently'}</td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="window.LemmaApp.loadHistoryItem('${item.id}')">
              <i class="fa-solid fa-folder-open"></i> Open
            </button>
            <button class="btn btn-outline btn-sm" onclick="window.LemmaApp.deleteHistoryItem('${item.id}')" style="color:var(--accent-flag);">
              <i class="fa-regular fa-trash-can"></i>
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }

  // --- 8. WORKSPACE PROJECTS ---
  function initWorkspaceView() {
    const newProjBtn = document.getElementById('btn-create-project');
    if (newProjBtn) {
      newProjBtn.addEventListener('click', async () => {
        const name = prompt('Enter new workspace project name:');
        if (name && name.trim()) {
          await createProject(name.trim());
        }
      });
    }
  }

  async function loadRemoteProjects() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/projects`);
      if (res.ok) {
        const data = await res.json();
        state.projects = data.projects || [];
      }
    } catch (e) {
      state.projects = [{ id: 'default', name: 'General Research', description: 'Default workspace' }];
    }
  }

  async function createProject(name) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: 'User-created workspace project' })
      });
      if (res.ok) {
        await loadRemoteProjects();
        renderWorkspaceView();
      }
    } catch (e) {
      alert(`Project creation error: ${e.message}`);
    }
  }

  function renderWorkspaceView() {
    const container = document.getElementById('workspace-projects-grid');
    if (!container) return;

    container.innerHTML = state.projects.map(p => `
      <div class="pandaz-card" style="cursor:pointer;" onclick="window.LemmaApp.selectProject('${p.id}')">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:1.5rem;">📁</span>
          <span class="nav-badge">${p.id === state.activeProject ? 'ACTIVE PROJECT' : 'PROJECT'}</span>
        </div>
        <div class="pandaz-card-title">${escapeHtml(p.name)}</div>
        <div class="pandaz-card-desc">${escapeHtml(p.description || 'Workspace container for documents and chats.')}</div>
        <div style="margin-top:auto; font-size:0.75rem; color:var(--text-muted);">
          Created: ${p.created_at || 'Recently'}
        </div>
      </div>
    `).join('');
  }

  // --- 9. PANDAZ PDF SUITE (9 TOOLS + ANALYZE HANDOFF) ---
  function initPandazView() {
    const toolCards = document.querySelectorAll('.pandaz-tool-card');
    toolCards.forEach(card => {
      card.addEventListener('click', () => {
        const toolName = card.dataset.tool;
        openPandazTool(toolName);
      });
    });

    const executeBtn = document.getElementById('btn-execute-pandaz-tool');
    const sendToLemmaBtn = document.getElementById('btn-pandaz-to-lemma');

    if (executeBtn) {
      executeBtn.addEventListener('click', () => executeActivePandazTool());
    }

    if (sendToLemmaBtn) {
      sendToLemmaBtn.addEventListener('click', () => handoffPandazToLemma());
    }

    // Signature Canvas setup
    initSignCanvas();
  }

  function openPandazTool(toolName) {
    state.pandaz.activeTool = toolName;
    state.pandaz.result = null;

    const modal = document.getElementById('pandaz-tool-modal');
    const titleEl = document.getElementById('pandaz-modal-tool-title');
    const descEl = document.getElementById('pandaz-modal-tool-desc');
    const toolOptionsContainer = document.getElementById('pandaz-tool-options');
    const resultBox = document.getElementById('pandaz-result-box');

    if (resultBox) resultBox.style.display = 'none';

    const toolMeta = {
      merge: { title: 'Merge Multiple PDFs', desc: 'Combine 2 or more PDF files into a single unified publication.' },
      split: { title: 'Split PDF by Page Range', desc: 'Extract specific pages (e.g. 1-3, 5, 8-10) into a new document.' },
      compress: { title: 'Compress PDF Stream', desc: 'Optimize binary streams and eliminate duplicate fonts & objects.' },
      'to-csv': { title: 'PDF → CSV Table Extraction', desc: 'Parse tabular datasets directly into clean comma-separated values.' },
      rename: { title: 'Safe PDF Rename', desc: 'Format and sanitize file metadata and filenames.' },
      sign: { title: 'Sign & Annotate PDF', desc: 'Draw a digital signature or place annotation headers on document pages.' },
      ocr: { title: 'Optical Character Recognition (OCR)', desc: 'Extract searchable digital text from scanned paper PDFs.' },
      summarize: { title: 'AI PDF Executive Summarizer', desc: 'Generate a structured TL;DR, core insights, and keyword taxonomy.' },
      rotate: { title: 'Rotate PDF Pages', desc: 'Rotate document pages by 90°, 180°, or 270° clockwise.' }
    };

    const meta = toolMeta[toolName] || { title: 'Pandaz Tool', desc: 'PDF manipulation utility' };
    if (titleEl) titleEl.textContent = meta.title;
    if (descEl) descEl.textContent = meta.desc;

    // Render tool-specific options
    renderPandazOptions(toolName, toolOptionsContainer);

    if (modal) modal.classList.add('open');
  }

  function renderPandazOptions(toolName, container) {
    if (!container) return;
    if (toolName === 'split') {
      container.innerHTML = `
        <label style="font-size:0.85rem; font-weight:600;">Page Range:</label>
        <input type="text" id="pandaz-split-range" class="chat-input" value="1-3" placeholder="e.g. 1-3, 5">
      `;
    } else if (toolName === 'rename') {
      container.innerHTML = `
        <label style="font-size:0.85rem; font-weight:600;">New Document Name:</label>
        <input type="text" id="pandaz-rename-input" class="chat-input" placeholder="e.g. Final_Thesis_2026.pdf">
      `;
    } else if (toolName === 'sign') {
      container.innerHTML = `
        <label style="font-size:0.85rem; font-weight:600;">Draw Signature:</label>
        <canvas id="pandaz-sig-canvas" width="400" height="120" style="background:#fff; border:1px solid var(--border-medium); border-radius:4px; cursor:crosshair; width:100%;"></canvas>
        <button class="btn btn-outline btn-sm" id="btn-clear-canvas" style="margin-top:4px;">Clear Signature</button>
      `;
      setTimeout(initSignCanvas, 50);
    } else if (toolName === 'rotate') {
      container.innerHTML = `
        <label style="font-size:0.85rem; font-weight:600;">Rotation Angle:</label>
        <select id="pandaz-rotate-angle" class="chat-input">
          <option value="90">90 Degrees Clockwise</option>
          <option value="180">180 Degrees Flip</option>
          <option value="270">270 Degrees Counter-Clockwise</option>
        </select>
      `;
    } else {
      container.innerHTML = '';
    }
  }

  let sigPadDrawing = false;
  function initSignCanvas() {
    const canvas = document.getElementById('pandaz-sig-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;

    canvas.onmousedown = (e) => {
      sigPadDrawing = true;
      ctx.beginPath();
      ctx.moveTo(e.offsetX, e.offsetY);
    };
    canvas.onmousemove = (e) => {
      if (sigPadDrawing) {
        ctx.lineTo(e.offsetX, e.offsetY);
        ctx.stroke();
      }
    };
    canvas.onmouseup = () => sigPadDrawing = false;
    canvas.onmouseleave = () => sigPadDrawing = false;

    const clearBtn = document.getElementById('btn-clear-canvas');
    if (clearBtn) {
      clearBtn.onclick = (e) => {
        e.preventDefault();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      };
    }
  }

  async function executeActivePandazTool() {
    const fileInput = document.getElementById('pandaz-file-input');
    const files = fileInput.files;
    const tool = state.pandaz.activeTool;

    if (!files.length) return alert('Please select a PDF file.');

    showLoadingOverlay(`Executing Pandaz ${tool.toUpperCase()}...`);
    const formData = new FormData();

    if (tool === 'merge') {
      if (files.length < 2) {
        hideLoadingOverlay();
        return alert('Please select at least 2 PDF files to merge.');
      }
      for (let i = 0; i < files.length; i++) formData.append('files', files[i]);
    } else {
      formData.append('file', files[0]);
    }

    if (tool === 'split') {
      const range = document.getElementById('pandaz-split-range').value;
      formData.append('page_range', range);
    } else if (tool === 'rename') {
      const name = document.getElementById('pandaz-rename-input').value;
      formData.append('new_name', name);
    } else if (tool === 'rotate') {
      const deg = document.getElementById('pandaz-rotate-angle').value;
      formData.append('degrees', deg);
    } else if (tool === 'sign') {
      const canvas = document.getElementById('pandaz-sig-canvas');
      if (canvas) {
        formData.append('signature_base64', canvas.toDataURL());
      }
    }

    try {
      const endpoint = `${API_BASE}/api/v1/pandaz/${tool}`;
      const res = await fetch(endpoint, { method: 'POST', body: formData });
      if (!res.ok) throw new Error(`Tool execution failed (HTTP ${res.status})`);

      const resultBox = document.getElementById('pandaz-result-box');
      const resultText = document.getElementById('pandaz-result-text');
      const downloadBtn = document.getElementById('btn-download-pandaz-output');

      if (tool === 'ocr' || tool === 'summarize') {
        const json = await res.json();
        state.pandaz.result = json;
        if (resultText) resultText.textContent = typeof json === 'object' ? JSON.stringify(json, null, 2) : json;
        if (downloadBtn) downloadBtn.style.display = 'none';
      } else {
        const blob = await res.blob();
        state.pandaz.resultBlob = blob;
        if (resultText) {
          const sizeKb = Math.round(blob.size / 1024);
          resultText.textContent = `Operation successful! Output generated (${sizeKb} KB).`;
        }
        if (downloadBtn) {
          downloadBtn.style.display = 'inline-flex';
          downloadBtn.onclick = () => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `pandaz_${tool}_output.pdf`;
            a.click();
          };
        }
      }

      if (resultBox) resultBox.style.display = 'block';
    } catch (e) {
      alert(`Pandaz Error: ${e.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  // One-Click Pandaz -> Lemma Analysis Handoff
  async function handoffPandazToLemma() {
    const fileInput = document.getElementById('pandaz-file-input');
    if (!fileInput.files.length) return alert('No PDF to analyze.');

    showLoadingOverlay('Transferring Pandaz output into Lemma Originality Engine...');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
      const res = await fetch(`${API_BASE}/api/v1/pandaz/to-lemma`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error('Handoff analysis failed');
      const data = await res.json();
      updateDocumentState(data);
      await saveToHistory(data);
      document.getElementById('pandaz-tool-modal').classList.remove('open');
      switchView('view-analyze');
    } catch (e) {
      alert(`Handoff error: ${e.message}`);
    } finally {
      hideLoadingOverlay();
    }
  }

  // --- 10. COMMAND PALETTE (CTRL+K) ---
  function initCommandPalette() {
    const modal = document.getElementById('command-palette-backdrop');
    const input = document.getElementById('command-palette-input');
    const list = document.getElementById('command-palette-results');

    // Global Key Listener
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openCommandPalette();
      }
      if (e.key === 'Escape' && modal && modal.classList.contains('open')) {
        closeCommandPalette();
      }
    });

    const openBtns = document.querySelectorAll('.search-command-btn');
    openBtns.forEach(b => b.addEventListener('click', openCommandPalette));

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeCommandPalette();
      });
    }

    if (input) {
      input.addEventListener('input', () => filterCommandPalette(input.value.trim()));
    }
  }

  function openCommandPalette() {
    const modal = document.getElementById('command-palette-backdrop');
    const input = document.getElementById('command-palette-input');
    if (modal) modal.classList.add('open');
    if (input) {
      input.value = '';
      input.focus();
      filterCommandPalette('');
    }
  }

  function closeCommandPalette() {
    const modal = document.getElementById('command-palette-backdrop');
    if (modal) modal.classList.remove('open');
  }

  async function filterCommandPalette(query) {
    const list = document.getElementById('command-palette-results');
    if (!list) return;

    const baseCommands = [
      { label: 'Go to Dashboard', icon: 'fa-gauge-high', action: () => switchView('view-dashboard') },
      { label: 'Open Manuscript Desk (Analyze)', icon: 'fa-magnifying-glass-chart', action: () => switchView('view-analyze') },
      { label: 'Open AI Paraphraser Workbench', icon: 'fa-wand-magic-sparkles', action: () => switchView('view-paraphrase') },
      { label: 'Ask Lemma Assistant (RAG)', icon: 'fa-robot', action: () => switchView('view-asklemma') },
      { label: 'Scholarly Sources Discovery', icon: 'fa-book-bookmark', action: () => switchView('view-sources') },
      { label: 'Download Integrity PDF Report', icon: 'fa-file-arrow-down', action: () => downloadIntegrityPdfReport() },
      { label: 'Pandaz PDF Tools Suite', icon: 'fa-file-pdf', action: () => switchView('view-pandaz') },
      { label: 'Toggle Light / Dark Theme', icon: 'fa-circle-half-stroke', action: () => document.querySelector('.theme-toggle-btn').click() }
    ];

    let filtered = baseCommands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()));

    // Also perform real cross-entity search if query length >= 2
    if (query.length >= 2) {
      try {
        const res = await fetch(`${API_BASE}/api/v1/search?q=${encodeURIComponent(query)}`);
        if (res.ok) {
          const sData = await res.json();
          (sData.results.documents || []).forEach(d => {
            filtered.push({
              label: `Document: ${d.title}`,
              icon: 'fa-file-lines',
              action: () => window.LemmaApp.loadHistoryItem(d.id)
            });
          });
        }
      } catch (e) {}
    }

    list.innerHTML = filtered.map((cmd, idx) => `
      <li class="command-item" data-idx="${idx}">
        <i class="fa-solid ${cmd.icon}"></i>
        <span>${escapeHtml(cmd.label)}</span>
      </li>
    `).join('');

    list.querySelectorAll('.command-item').forEach((item, idx) => {
      item.addEventListener('click', () => {
        closeCommandPalette();
        filtered[idx].action();
      });
    });
  }

  // --- UTILITY HELPERS ---
  function showLoadingOverlay(msg = 'Processing...') {
    let overlay = document.getElementById('lemma-loading-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'lemma-loading-overlay';
      overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(12, 14, 18, 0.7); backdrop-filter: blur(4px);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        z-index: 9999; color: #fff; font-family: var(--font-sans);
      `;
      overlay.innerHTML = `
        <div style="font-size:2rem; margin-bottom:1rem; animation:spin 1s infinite linear;"><i class="fa-solid fa-spinner"></i></div>
        <div id="lemma-loading-msg" style="font-weight:600; font-size:1.05rem;">Processing...</div>
      `;
      document.body.appendChild(overlay);
    }
    document.getElementById('lemma-loading-msg').textContent = msg;
    overlay.style.display = 'flex';
  }

  function hideLoadingOverlay() {
    const overlay = document.getElementById('lemma-loading-overlay');
    if (overlay) overlay.style.display = 'none';
  }

  function escapeHtml(str) {
    return (str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatMarkdown(text) {
    if (!text) return '';
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
  }

  // --- GLOBAL EXPOSED CONTROLLER ---
  window.LemmaApp = {
    state,
    switchView,
    loadHistoryItem: async (id) => {
      showLoadingOverlay('Loading analysis record...');
      try {
        const res = await fetch(`${API_BASE}/api/v1/history/${id}`);
        if (res.ok) {
          const data = await res.json();
          updateDocumentState(data.record);
          switchView('view-analyze');
        }
      } catch (e) {
        alert('Could not load record');
      } finally {
        hideLoadingOverlay();
      }
    },
    deleteHistoryItem: async (id) => {
      if (confirm('Delete this analysis record?')) {
        await fetch(`${API_BASE}/api/v1/history/${id}`, { method: 'DELETE' });
        await loadRemoteHistory();
        renderHistoryTable();
      }
    },
    selectProject: (id) => {
      state.activeProject = id;
      renderWorkspaceView();
      alert(`Switched active workspace to project: ${id}`);
    }
  };

})();
