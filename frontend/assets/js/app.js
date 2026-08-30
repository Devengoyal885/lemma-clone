/**
 * LEMMA 2.0 & PANDaz PDF SUITE — Complete Frontend Application Engine
 * Pure Vanilla JavaScript, zero hardcoded mocks, complete offline/Lite Mode support.
 */

(function () {
    'use strict';

    // --- APPLICATION STATE ---
    const state = {
        apiBaseUrl: 'http://localhost:8000',
        activeSection: 'view-dashboard',
        activeDocument: null,
        activeTone: 'academic',
        selectedMatch: null,
        history: [],
        workspace: [],
        theme: 'dark',
        batchCancelRequested: false
    };

    // --- DOM ELEMENT REFERENCES ---
    const DOM = {
        // Navigation
        navItems: document.querySelectorAll('.sidebar-nav .nav-item'),
        viewSections: document.querySelectorAll('.view-section'),
        currentPageTitle: document.getElementById('current-page-title'),
        mobileMenuToggle: document.getElementById('mobile-menu-toggle'),
        sidebar: document.getElementById('sidebar-panel'),
        themeToggle: document.getElementById('theme-toggle'),
        systemStatusIndicator: document.getElementById('system-status-indicator'),
        
        // Header
        headerQuickPandaz: document.getElementById('header-quick-pandaz-btn'),
        headerQuickAnalyze: document.getElementById('header-quick-analyze-btn'),
        commandPaletteTrigger: document.getElementById('command-palette-trigger'),
        
        // Dashboard
        dashBtnAnalyze: document.getElementById('dash-btn-analyze'),
        dashBtnPaste: document.getElementById('dash-btn-paste'),
        dashBtnPandaz: document.getElementById('dash-btn-pandaz'),
        dashBtnSample: document.getElementById('dash-btn-sample'),
        dashOverallScore: document.getElementById('dash-overall-score'),
        dashStatDocs: document.getElementById('dash-stat-docs'),
        dashStatMatches: document.getElementById('dash-stat-matches'),
        dashStatWords: document.getElementById('dash-stat-words'),
        dashRecentTbody: document.getElementById('dash-recent-tbody'),
        dashViewAllHistory: document.getElementById('dash-view-all-history'),
        
        // Analyze View
        tabUploadBtn: document.getElementById('tab-upload-btn'),
        tabPasteBtn: document.getElementById('tab-paste-btn'),
        panelUpload: document.getElementById('panel-upload'),
        panelPaste: document.getElementById('panel-paste'),
        fileInput: document.getElementById('file-input'),
        uploadDropzone: document.getElementById('upload-dropzone'),
        btnBrowseFile: document.getElementById('btn-browse-file'),
        uploadProgressWrapper: document.getElementById('upload-progress-wrapper'),
        progressFilename: document.getElementById('progress-filename'),
        progressPercent: document.getElementById('progress-percent'),
        progressBarFill: document.getElementById('progress-bar-fill'),
        pasteTextarea: document.getElementById('paste-textarea'),
        pasteCharCount: document.getElementById('paste-char-count'),
        pasteWordCount: document.getElementById('paste-word-count'),
        pasteSentCount: document.getElementById('paste-sent-count'),
        btnClearPaste: document.getElementById('btn-clear-paste'),
        btnSamplePaste: document.getElementById('btn-sample-paste'),
        btnAnalyzePaste: document.getElementById('btn-analyze-paste'),
        
        // Analysis Results
        analysisResultsWrapper: document.getElementById('analysis-results-wrapper'),
        resPlagVal: document.getElementById('res-plag-val'),
        resPlagSubtitle: document.getElementById('res-plag-subtitle'),
        resOrigVal: document.getElementById('res-orig-val'),
        resCountLexical: document.getElementById('res-count-lexical'),
        resCountHybrid: document.getElementById('res-count-hybrid'),
        resCountSemantic: document.getElementById('res-count-semantic'),
        resCountTotal: document.getElementById('res-count-total'),
        resWords: document.getElementById('res-words'),
        resReadingEase: document.getElementById('res-reading-ease'),
        resGradeLevel: document.getElementById('res-grade-level'),
        resReadingTime: document.getElementById('res-reading-time'),
        resDocTitle: document.getElementById('res-doc-title'),
        btnOpenInPandaz: document.getElementById('btn-open-in-pandaz'),
        btnAskAboutDoc: document.getElementById('btn-ask-about-doc'),
        btnRewriteFlagged: document.getElementById('btn-rewrite-flagged'),
        btnDownloadReportDirect: document.getElementById('btn-download-report-direct'),
        documentTextRendered: document.getElementById('document-text-rendered'),
        matchesCountBadge: document.getElementById('matches-count-badge'),
        matchesListWrapper: document.getElementById('matches-list-wrapper'),
        
        // Ask Lemma Chat
        chatActiveDocPill: document.getElementById('chat-active-doc-pill'),
        chatDocName: document.getElementById('chat-doc-name'),
        chatMessagesBox: document.getElementById('chat-messages-box'),
        chatInputText: document.getElementById('chat-input-text'),
        btnSendChat: document.getElementById('btn-send-chat'),
        
        // Paraphraser
        paraphraseProviderBadge: document.getElementById('paraphrase-provider-badge'),
        paraphraseInput: document.getElementById('paraphrase-input'),
        paraphraseOutput: document.getElementById('paraphrase-output'),
        btnCopyOriginal: document.getElementById('btn-copy-original'),
        btnCopyRewritten: document.getElementById('btn-copy-rewritten'),
        btnReplaceInDoc: document.getElementById('btn-replace-in-doc'),
        btnExecuteParaphrase: document.getElementById('btn-execute-paraphrase'),
        btnBatchRewriteAll: document.getElementById('btn-batch-rewrite-all'),
        batchProgressBox: document.getElementById('batch-progress-box'),
        batchProgressStatus: document.getElementById('batch-progress-status'),
        batchProgressBar: document.getElementById('batch-progress-bar'),
        btnCancelBatch: document.getElementById('btn-cancel-batch'),
        
        // Sources
        sourcesSearchInput: document.getElementById('sources-search-input'),
        btnSearchSources: document.getElementById('btn-search-sources'),
        sourcesGridWrapper: document.getElementById('sources-grid-wrapper'),
        
        // Reports
        btnGenerateReportView: document.getElementById('btn-generate-report-view'),
        repDate: document.getElementById('rep-date'),
        repFilename: document.getElementById('rep-filename'),
        repPlagScore: document.getElementById('rep-plag-score'),
        repOrigScore: document.getElementById('rep-orig-score'),
        repSentences: document.getElementById('rep-sentences'),
        repSummaryText: document.getElementById('rep-summary-text'),
        repSourcesList: document.getElementById('rep-sources-list'),
        
        // History
        historyTableTbody: document.getElementById('history-table-tbody'),
        btnClearHistory: document.getElementById('btn-clear-history'),
        
        // Workspace
        workspaceGridContainer: document.getElementById('workspace-grid-container'),
        btnWorkspaceNewDoc: document.getElementById('btn-workspace-new-doc'),
        
        // Pandaz
        pandazWorkbenchModal: document.getElementById('pandaz-workbench-modal'),
        pandazModalTitle: document.getElementById('pandaz-modal-title'),
        pandazModalBody: document.getElementById('pandaz-modal-body'),
        btnClosePandazModal: document.getElementById('btn-close-pandaz-modal'),
        
        // Settings
        btnRefreshStatus: document.getElementById('btn-refresh-status'),
        settingApiUrl: document.getElementById('setting-api-url'),
        btnSaveApiUrl: document.getElementById('btn-save-api-url'),
        setAiStatus: document.getElementById('set-ai-status'),
        
        // Modals & Command Palette
        matchInspectorModal: document.getElementById('match-inspector-modal'),
        modalMatchTitle: document.getElementById('modal-match-title'),
        modalMatchBadge: document.getElementById('modal-match-badge'),
        modalMatchScore: document.getElementById('modal-match-score'),
        modalQuerySentence: document.getElementById('modal-query-sentence'),
        modalRefSentence: document.getElementById('modal-ref-sentence'),
        modalSourceTitle: document.getElementById('modal-source-title'),
        modalSourceAuthor: document.getElementById('modal-source-author'),
        modalSourcePub: document.getElementById('modal-source-pub'),
        modalBtnRewrite: document.getElementById('modal-btn-rewrite'),
        modalBtnCopy: document.getElementById('modal-btn-copy'),
        modalBtnViewSource: document.getElementById('modal-btn-view-source'),
        btnCloseMatchModal: document.getElementById('btn-close-match-modal'),
        commandPaletteModal: document.getElementById('command-palette-modal'),
        paletteSearchInput: document.getElementById('palette-search-input'),
        paletteResultsList: document.getElementById('palette-results-list'),
        toastContainer: document.getElementById('toast-container')
    };

    // --- SAMPLE DOCUMENT TEXT ---
    const SAMPLE_DOCUMENT_TEXT = `Deep learning is a subset of machine learning that is based on artificial neural networks with representation learning. The adjective deep in deep learning refers to the use of multiple layers in the network. Historically, neural networks were limited in depth due to computational constraints and training difficulties. Today, modern deep learning architectures utilize convolutional neural networks and transformer architectures to process vast datasets.

Climate change represents one of the defining challenges of our generation, requiring immediate and decisive systemic shifts. Global greenhouse gas emissions must be reduced by half before the end of this decade to prevent catastrophic warming. Transitioning from fossil fuels to renewable energy sources like wind and solar power is crucial.

In our proprietary study, we observed that algorithmic latency decreases substantially when vectorized matrices are cached locally in memory. Our experimental benchmark demonstrated a 4.2x increase in throughput across consumer grade hardware. These novel empirical measurements confirm the validity of our local-first computational hypothesis.`;

    // --- INITIALIZATION ---
    async function initApp() {
        // Resolve API base URL
        state.apiBaseUrl = await APIConfigManager.getApiBaseUrl();
        if (DOM.settingApiUrl) {
            DOM.settingApiUrl.value = state.apiBaseUrl;
        }

        // Load persisted state
        loadHistory();
        loadWorkspace();
        initTheme();

        // Setup event listeners
        setupNavigation();
        setupDashboard();
        setupAnalyze();
        setupAskLemma();
        setupParaphraser();
        setupSources();
        setupReports();
        setupHistory();
        setupWorkspace();
        setupPandaz();
        setupSettings();
        setupCommandPalette();
        setupModals();

        // Check backend system health
        checkSystemHealth();
    }

    // --- TOAST NOTIFICATIONS ---
    function showToast(message, type = 'info') {
        if (!DOM.toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type}`;
        
        let icon = 'fa-circle-info';
        if (type === 'success') icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-circle-exclamation';
        if (type === 'warning') icon = 'fa-triangle-exclamation';

        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${escapeHTML(message)}</span>
        `;
        DOM.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // --- SYSTEM HEALTH CHECK ---
    async function checkSystemHealth() {
        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/system/status`);
            if (res.ok) {
                const data = await res.json();
                if (DOM.systemStatusIndicator) {
                    DOM.systemStatusIndicator.innerHTML = `
                        <span class="status-dot online"></span>
                        <span class="status-label">Lemma 2.0 Online</span>
                    `;
                }
                if (DOM.setAiStatus) {
                    const aiOnline = data.subsystems && data.subsystems.ai_assistant && data.subsystems.ai_assistant.includes('ONLINE');
                    DOM.setAiStatus.textContent = aiOnline ? 'ONLINE (Ollama)' : 'LOCAL (Deterministic)';
                    DOM.setAiStatus.className = aiOnline ? 'text-success' : 'text-warning';
                }
                if (DOM.paraphraseProviderBadge) {
                    const aiOnline = data.subsystems && data.subsystems.ai_assistant && data.subsystems.ai_assistant.includes('ONLINE');
                    DOM.paraphraseProviderBadge.innerHTML = aiOnline ? 
                        '<span class="badge badge-success">AI REWRITE ACTIVE</span>' : 
                        '<span class="badge badge-info">OFFLINE REWRITE ACTIVE</span>';
                }
            } else {
                setOfflineIndicator();
            }
        } catch (e) {
            setOfflineIndicator();
        }
    }

    function setOfflineIndicator() {
        if (DOM.systemStatusIndicator) {
            DOM.systemStatusIndicator.innerHTML = `
                <span class="status-dot offline"></span>
                <span class="status-label">Backend Offline</span>
            `;
        }
    }

    // --- NAVIGATION & VIEWS ---
    function setupNavigation() {
        DOM.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetViewId = item.getAttribute('data-target');
                if (targetViewId) {
                    switchView(targetViewId);
                }
            });
        });

        // Mobile menu toggle
        if (DOM.mobileMenuToggle) {
            DOM.mobileMenuToggle.addEventListener('click', () => {
                document.getElementById('app-container-el').classList.toggle('sidebar-open');
            });
        }

        // Header quick buttons
        if (DOM.headerQuickPandaz) {
            DOM.headerQuickPandaz.addEventListener('click', () => switchView('view-pandaz'));
        }
        if (DOM.headerQuickAnalyze) {
            DOM.headerQuickAnalyze.addEventListener('click', () => switchView('view-analyze'));
        }

        // Feature cards navigation on dashboard
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('click', () => {
                const action = card.getAttribute('data-action');
                if (action === 'goto-analyze') switchView('view-analyze');
                if (action === 'goto-asklemma') switchView('view-asklemma');
                if (action === 'goto-paraphrase') switchView('view-paraphrase');
                if (action === 'goto-pandaz') switchView('view-pandaz');
            });
        });
    }

    function switchView(viewId) {
        DOM.viewSections.forEach(section => {
            section.classList.remove('active');
            if (section.id === viewId) {
                section.classList.add('active');
            }
        });

        DOM.navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-target') === viewId) {
                item.classList.add('active');
            }
        });

        state.activeSection = viewId;

        // Update Title & Breadcrumb
        const titleMap = {
            'view-dashboard': 'Dashboard',
            'view-analyze': 'Plagiarism & Originality Analysis',
            'view-asklemma': 'Ask Lemma Assistant',
            'view-paraphrase': 'Paraphraser & Rewriter',
            'view-sources': 'Source Discovery & References',
            'view-reports': 'Lemma Integrity Reports',
            'view-history': 'Analysis History',
            'view-workspace': 'Workspace',
            'view-pandaz': 'Pandaz PDF Tools',
            'view-settings': 'Settings & Status'
        };
        if (DOM.currentPageTitle) {
            DOM.currentPageTitle.textContent = titleMap[viewId] || 'Lemma';
        }

        // Refresh views if needed
        if (viewId === 'view-history') renderHistoryTable();
        if (viewId === 'view-workspace') renderWorkspace();
        if (viewId === 'view-sources') renderSourcesView();
        if (viewId === 'view-reports') renderReportsView();

        // Close mobile sidebar
        document.getElementById('app-container-el').classList.remove('sidebar-open');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // --- DASHBOARD SETUP ---
    function setupDashboard() {
        if (DOM.dashBtnAnalyze) {
            DOM.dashBtnAnalyze.addEventListener('click', () => {
                switchView('view-analyze');
                activateAnalyzeTab('upload');
            });
        }
        if (DOM.dashBtnPaste) {
            DOM.dashBtnPaste.addEventListener('click', () => {
                switchView('view-analyze');
                activateAnalyzeTab('paste');
            });
        }
        if (DOM.dashBtnPandaz) {
            DOM.dashBtnPandaz.addEventListener('click', () => switchView('view-pandaz'));
        }
        if (DOM.dashBtnSample) {
            DOM.dashBtnSample.addEventListener('click', () => {
                switchView('view-analyze');
                activateAnalyzeTab('paste');
                if (DOM.pasteTextarea) {
                    DOM.pasteTextarea.value = SAMPLE_DOCUMENT_TEXT;
                    updatePasteCounters();
                }
                executeTextAnalysis(SAMPLE_DOCUMENT_TEXT, "Sample Research Document");
            });
        }
        if (DOM.dashViewAllHistory) {
            DOM.dashViewAllHistory.addEventListener('click', () => switchView('view-history'));
        }
    }

    function updateDashboardStats() {
        const totalDocs = state.history.length;
        if (DOM.dashStatDocs) DOM.dashStatDocs.textContent = totalDocs;

        let totalMatches = 0;
        let totalWords = 0;
        let totalOrig = 0;

        state.history.forEach(item => {
            const an = item.analysis || {};
            totalMatches += (an.matched_sentences_count || 0);
            totalWords += (item.char_count ? Math.round(item.char_count / 5) : 0);
            totalOrig += (an.originality_score || 100);
        });

        if (DOM.dashStatMatches) DOM.dashStatMatches.textContent = totalMatches;
        if (DOM.dashStatWords) DOM.dashStatWords.textContent = totalWords.toLocaleString();

        const avgOrig = totalDocs > 0 ? Math.round(totalOrig / totalDocs) : 95;
        if (DOM.dashOverallScore) DOM.dashOverallScore.textContent = `${avgOrig}%`;

        // Render recent dashboard rows
        if (DOM.dashRecentTbody) {
            if (state.history.length === 0) {
                DOM.dashRecentTbody.innerHTML = `
                    <tr class="empty-row">
                        <td colspan="6">No recent documents analyzed yet. Click <strong>Analyze Document</strong> or <strong>Try Sample</strong> to begin.</td>
                    </tr>
                `;
            } else {
                DOM.dashRecentTbody.innerHTML = state.history.slice(0, 5).map(item => `
                    <tr>
                        <td><strong>${escapeHTML(item.filename || 'Untitled')}</strong></td>
                        <td>${new Date(item.timestamp).toLocaleDateString()}</td>
                        <td>${item.char_count ? Math.round(item.char_count/5).toLocaleString() : 'N/A'}</td>
                        <td><span class="badge badge-danger">${item.analysis?.plagiarism_score || 0}%</span></td>
                        <td><span class="badge badge-success">${item.analysis?.originality_score || 100}%</span></td>
                        <td>
                            <button class="btn btn-ghost btn-xs btn-open-history" data-id="${item.id}">Open</button>
                            <button class="btn btn-outline btn-xs btn-download-hist-rep" data-id="${item.id}">Report</button>
                        </td>
                    </tr>
                `).join('');

                DOM.dashRecentTbody.querySelectorAll('.btn-open-history').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = btn.getAttribute('data-id');
                        openHistoryItem(id);
                    });
                });
                DOM.dashRecentTbody.querySelectorAll('.btn-download-hist-rep').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = btn.getAttribute('data-id');
                        downloadHistoryReport(id);
                    });
                });
            }
        }
    }

    // --- ANALYZE VIEW SETUP ---
    function setupAnalyze() {
        if (DOM.tabUploadBtn) {
            DOM.tabUploadBtn.addEventListener('click', () => activateAnalyzeTab('upload'));
        }
        if (DOM.tabPasteBtn) {
            DOM.tabPasteBtn.addEventListener('click', () => activateAnalyzeTab('paste'));
        }

        // File upload trigger
        if (DOM.btnBrowseFile) {
            DOM.btnBrowseFile.addEventListener('click', () => DOM.fileInput.click());
        }
        if (DOM.uploadDropzone) {
            DOM.uploadDropzone.addEventListener('click', (e) => {
                if (e.target !== DOM.btnBrowseFile) DOM.fileInput.click();
            });

            // Drag & Drop
            DOM.uploadDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                DOM.uploadDropzone.classList.add('drag-over');
            });
            DOM.uploadDropzone.addEventListener('dragleave', () => {
                DOM.uploadDropzone.classList.remove('drag-over');
            });
            DOM.uploadDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                DOM.uploadDropzone.classList.remove('drag-over');
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    handleFileUpload(e.dataTransfer.files[0]);
                }
            });
        }

        if (DOM.fileInput) {
            DOM.fileInput.addEventListener('change', () => {
                if (DOM.fileInput.files && DOM.fileInput.files.length > 0) {
                    handleFileUpload(DOM.fileInput.files[0]);
                }
            });
        }

        // Paste Text Controls
        if (DOM.pasteTextarea) {
            DOM.pasteTextarea.addEventListener('input', updatePasteCounters);
        }
        if (DOM.btnClearPaste) {
            DOM.btnClearPaste.addEventListener('click', () => {
                DOM.pasteTextarea.value = '';
                updatePasteCounters();
            });
        }
        if (DOM.btnSamplePaste) {
            DOM.btnSamplePaste.addEventListener('click', () => {
                DOM.pasteTextarea.value = SAMPLE_DOCUMENT_TEXT;
                updatePasteCounters();
                showToast("Sample research document loaded!", "info");
            });
        }
        if (DOM.btnAnalyzePaste) {
            DOM.btnAnalyzePaste.addEventListener('click', () => {
                const text = DOM.pasteTextarea.value.trim();
                if (!text) {
                    showToast("Please enter or paste text to analyze.", "warning");
                    return;
                }
                executeTextAnalysis(text, "Pasted Analysis");
            });
        }

        // Results Actions
        if (DOM.btnDownloadReportDirect) {
            DOM.btnDownloadReportDirect.addEventListener('click', downloadCurrentReport);
        }
        if (DOM.btnOpenInPandaz) {
            DOM.btnOpenInPandaz.addEventListener('click', () => {
                switchView('view-pandaz');
                showToast("Switched to Pandaz PDF toolkit.", "info");
            });
        }
        if (DOM.btnAskAboutDoc) {
            DOM.btnAskAboutDoc.addEventListener('click', () => {
                switchView('view-asklemma');
                if (state.activeDocument) {
                    sendChatMessage(`What is my plagiarism score and how can I improve my originality?`);
                }
            });
        }
        if (DOM.btnRewriteFlagged) {
            DOM.btnRewriteFlagged.addEventListener('click', () => {
                switchView('view-paraphrase');
                if (state.activeDocument && state.activeDocument.analysis && state.activeDocument.analysis.matches.length > 0) {
                    const firstMatch = state.activeDocument.analysis.matches[0];
                    const sentText = firstMatch.query_sentence?.text || firstMatch.query_text || '';
                    if (DOM.paraphraseInput) {
                        DOM.paraphraseInput.value = sentText;
                    }
                    showToast("Flagged sentence loaded into Paraphraser!", "info");
                }
            });
        }
    }

    function activateAnalyzeTab(tab) {
        if (tab === 'upload') {
            DOM.tabUploadBtn.classList.add('active');
            DOM.tabPasteBtn.classList.remove('active');
            DOM.panelUpload.style.display = 'block';
            DOM.panelPaste.style.display = 'none';
        } else {
            DOM.tabPasteBtn.classList.add('active');
            DOM.tabUploadBtn.classList.remove('active');
            DOM.panelPaste.style.display = 'block';
            DOM.panelUpload.style.display = 'none';
        }
    }

    function updatePasteCounters() {
        const text = DOM.pasteTextarea.value;
        const chars = text.length;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        const sents = text.trim() ? text.split(/[.!?]+/).filter(Boolean).length : 0;

        if (DOM.pasteCharCount) DOM.pasteCharCount.textContent = `${chars.toLocaleString()} characters`;
        if (DOM.pasteWordCount) DOM.pasteWordCount.textContent = `${words.toLocaleString()} words`;
        if (DOM.pasteSentCount) DOM.pasteSentCount.textContent = `${sents.toLocaleString()} sentences`;
    }

    // --- REAL FILE UPLOAD HANDLER ---
    async function handleFileUpload(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['pdf', 'docx', 'txt'].includes(ext)) {
            showToast(`Unsupported file type (.${ext}). Allowed: PDF, DOCX, TXT.`, "error");
            return;
        }

        // Show upload progress
        if (DOM.uploadProgressWrapper) {
            DOM.uploadProgressWrapper.style.display = 'block';
            DOM.progressFilename.textContent = file.name;
            DOM.progressPercent.textContent = '10%';
            DOM.progressBarFill.style.width = '10%';
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            DOM.progressPercent.textContent = '40%';
            DOM.progressBarFill.style.width = '40%';

            const res = await fetch(`${state.apiBaseUrl}/api/v1/documents/upload`, {
                method: 'POST',
                body: formData
            });

            DOM.progressPercent.textContent = '80%';
            DOM.progressBarFill.style.width = '80%';

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Upload failed with status ${res.status}`);
            }

            const docData = await res.json();
            DOM.progressPercent.textContent = '100%';
            DOM.progressBarFill.style.width = '100%';

            setTimeout(() => {
                if (DOM.uploadProgressWrapper) DOM.uploadProgressWrapper.style.display = 'none';
            }, 500);

            // Populate document state and render results
            renderAnalysisResults(docData);
            saveToHistory(docData);
            showToast(`Analysis completed for "${file.name}"!`, "success");

        } catch (error) {
            if (DOM.uploadProgressWrapper) DOM.uploadProgressWrapper.style.display = 'none';
            showToast(`Upload Error: ${error.message}`, "error");
        }
    }

    // --- REAL DIRECT TEXT ANALYSIS ---
    async function executeTextAnalysis(text, title = "Pasted Analysis") {
        showToast("Analyzing document originality...", "info");
        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/analyze/text`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text, title: title })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `Analysis failed with status ${res.status}`);
            }

            const data = await res.json();
            renderAnalysisResults(data);
            saveToHistory(data);
            showToast("Originality verification completed!", "success");

        } catch (e) {
            showToast(`Analysis Error: ${e.message}`, "error");
        }
    }

    // --- RENDER ANALYSIS RESULTS & HIGHLIGHTING ---
    function renderAnalysisResults(docData) {
        state.activeDocument = docData;

        // Show results panel
        if (DOM.analysisResultsWrapper) {
            DOM.analysisResultsWrapper.style.display = 'block';
            DOM.analysisResultsWrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        const analysis = docData.analysis || {};
        const metrics = docData.metrics || {};
        const plagScore = analysis.plagiarism_score || 0;
        const origScore = analysis.originality_score || (100 - plagScore);

        // Update score badges
        if (DOM.resPlagVal) {
            DOM.resPlagVal.textContent = `${plagScore}%`;
            DOM.resPlagVal.className = `gauge-display-val ${plagScore > 20 ? 'text-danger' : (plagScore > 0 ? 'text-warning' : 'text-success')}`;
        }
        if (DOM.resOrigVal) DOM.resOrigVal.textContent = `${origScore}%`;
        if (DOM.resDocTitle) DOM.resDocTitle.textContent = docData.filename || 'Analyzed Document';

        // Breakdown counts
        if (DOM.resCountLexical) DOM.resCountLexical.textContent = analysis.lexical_matches_count || 0;
        if (DOM.resCountHybrid) DOM.resCountHybrid.textContent = analysis.hybrid_matches_count || 0;
        if (DOM.resCountSemantic) DOM.resCountSemantic.textContent = analysis.semantic_matches_count || 0;
        if (DOM.resCountTotal) DOM.resCountTotal.textContent = docData.sentence_count || analysis.total_sentences || 0;

        // Analytics
        if (DOM.resWords) DOM.resWords.textContent = (metrics.word_count || Math.round((docData.char_count || 0)/5)).toLocaleString();
        if (DOM.resReadingEase) DOM.resReadingEase.textContent = metrics.flesch_reading_ease || 'N/A';
        if (DOM.resGradeLevel) DOM.resGradeLevel.textContent = metrics.flesch_kincaid_grade || 'College';
        if (DOM.resReadingTime) DOM.resReadingTime.textContent = `${metrics.reading_time_minutes || 1}m`;

        // Render Highlighted Text Box
        renderHighlightedDocument(docData);

        // Render Right-hand Matches List
        renderMatchesSidebar(docData);

        // Update Ask Lemma active pill
        if (DOM.chatDocName) DOM.chatDocName.textContent = docData.filename || 'Active Document';
    }

    function renderHighlightedDocument(docData) {
        if (!DOM.documentTextRendered) return;
        const text = docData.text || '';
        const sentences = docData.sentences || [];
        const analysis = docData.analysis || {};
        const matches = analysis.matches || [];

        // Map sentence start_char to match
        const matchesMap = {};
        matches.forEach(m => {
            const startChar = m.query_sentence ? m.query_sentence.start_char : m.start_position;
            if (startChar !== undefined) {
                matchesMap[startChar] = m;
            }
        });

        let htmlParts = [];
        let lastOffset = 0;

        sentences.forEach((s, idx) => {
            const start = s.start_char;
            const end = s.end_char;
            const sentText = s.text;

            // Raw characters between sentences
            if (start > lastOffset) {
                htmlParts.push(escapeHTML(text.substring(lastOffset, start)).replace(/\n/g, '<br>'));
            }

            const match = matchesMap[start];
            if (match) {
                const mType = match.match_type || 'lexical';
                const markClass = `mark-${mType}`;
                htmlParts.push(
                    `<mark class="${markClass} interactive-mark" data-match-id="${match.id}" data-idx="${idx}" title="Click to view match provenance & rewrite">${escapeHTML(sentText)}</mark>`
                );
            } else {
                htmlParts.push(escapeHTML(sentText));
            }
            lastOffset = end;
        });

        if (lastOffset < text.length) {
            htmlParts.push(escapeHTML(text.substring(lastOffset)).replace(/\n/g, '<br>'));
        }

        DOM.documentTextRendered.innerHTML = htmlParts.join('');

        // Attach click listeners to all interactive highlights
        DOM.documentTextRendered.querySelectorAll('.interactive-mark').forEach(markEl => {
            markEl.addEventListener('click', () => {
                const matchId = markEl.getAttribute('data-match-id');
                const match = matches.find(m => m.id === matchId);
                if (match) {
                    openMatchInspector(match);
                }
            });
        });
    }

    function renderMatchesSidebar(docData) {
        if (!DOM.matchesListWrapper) return;
        const matches = docData.analysis?.matches || [];
        if (DOM.matchesCountBadge) DOM.matchesCountBadge.textContent = matches.length;

        if (matches.length === 0) {
            DOM.matchesListWrapper.innerHTML = `
                <div class="empty-matches-notice">
                    <i class="fa-solid fa-circle-check text-success"></i>
                    <p>No plagiarism detected! Your document demonstrates high originality.</p>
                </div>
            `;
            return;
        }

        DOM.matchesListWrapper.innerHTML = matches.map((m, i) => {
            const querySent = m.query_sentence?.text || m.query_text || '';
            const matchedSent = m.matched_sentence || m.matched_text || '';
            const sourceTitle = m.source || m.doc_title || 'Reference Library';
            const sim = Math.round((m.similarity || m.score || 0) * 100);
            const mType = (m.match_type || 'lexical').toUpperCase();
            const badgeClass = mType === 'LEXICAL' ? 'badge-danger' : (mType === 'HYBRID' ? 'badge-warning' : 'badge-purple');

            return `
                <div class="match-sidebar-card" data-match-id="${m.id}">
                    <div class="match-card-header">
                        <span class="match-num">#${i + 1}</span>
                        <span class="badge ${badgeClass}">${mType} • ${sim}%</span>
                    </div>
                    <div class="match-card-source">
                        <i class="fa-solid fa-book"></i> <strong>${escapeHTML(sourceTitle)}</strong>
                    </div>
                    <p class="match-card-snippet">"${escapeHTML(querySent.substring(0, 100))}${querySent.length > 100 ? '...' : ''}"</p>
                    <div class="match-card-actions">
                        <button class="btn btn-ghost btn-xs btn-inspect-match" data-match-id="${m.id}">Inspect</button>
                        <button class="btn btn-outline btn-xs btn-rewrite-match" data-match-id="${m.id}">Rewrite</button>
                    </div>
                </div>
            `;
        }).join('');

        // Attach event listeners
        DOM.matchesListWrapper.querySelectorAll('.btn-inspect-match').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-match-id');
                const match = matches.find(m => m.id === id);
                if (match) openMatchInspector(match);
            });
        });

        DOM.matchesListWrapper.querySelectorAll('.btn-rewrite-match').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-match-id');
                const match = matches.find(m => m.id === id);
                if (match) {
                    const textToRewrite = match.query_sentence?.text || match.query_text || '';
                    switchView('view-paraphrase');
                    if (DOM.paraphraseInput) DOM.paraphraseInput.value = textToRewrite;
                }
            });
        });
    }

    // --- MATCH INSPECTOR MODAL ---
    function openMatchInspector(match) {
        state.selectedMatch = match;
        const sim = Math.round((match.similarity || match.score || 0) * 100);
        const mType = match.match_type || 'lexical';
        const queryText = match.query_sentence?.text || match.query_text || '';
        const matchedText = match.matched_sentence || match.matched_text || '';
        const sourceTitle = match.source || match.doc_title || 'Reference Publication';
        const sourceAuthor = match.source_author || match.doc_author || 'Scholarly Contributors';
        const sourcePub = match.source_publication || match.doc_source || 'Academic Database';
        const sourceUrl = match.source_url || match.doc_url || '#';

        if (DOM.modalMatchTitle) DOM.modalMatchTitle.textContent = `Match Inspection (#${match.id})`;
        if (DOM.modalMatchBadge) DOM.modalMatchBadge.textContent = `${mType.toUpperCase()} MATCH`;
        if (DOM.modalMatchScore) DOM.modalMatchScore.textContent = `${sim}% Similarity`;
        if (DOM.modalQuerySentence) DOM.modalQuerySentence.textContent = queryText;
        if (DOM.modalRefSentence) DOM.modalRefSentence.textContent = matchedText;
        if (DOM.modalSourceTitle) DOM.modalSourceTitle.textContent = sourceTitle;
        if (DOM.modalSourceAuthor) DOM.modalSourceAuthor.textContent = `Author: ${sourceAuthor}`;
        if (DOM.modalSourcePub) DOM.modalSourcePub.textContent = `Publication: ${sourcePub}`;

        if (DOM.modalBtnViewSource) {
            if (sourceUrl && sourceUrl !== '#') {
                DOM.modalBtnViewSource.href = sourceUrl;
                DOM.modalBtnViewSource.style.display = 'inline-flex';
            } else {
                DOM.modalBtnViewSource.style.display = 'none';
            }
        }

        if (DOM.matchInspectorModal) {
            DOM.matchInspectorModal.style.display = 'flex';
        }
    }

    function setupModals() {
        if (DOM.btnCloseMatchModal) {
            DOM.btnCloseMatchModal.addEventListener('click', () => {
                DOM.matchInspectorModal.style.display = 'none';
            });
        }
        if (DOM.modalBtnRewrite) {
            DOM.modalBtnRewrite.addEventListener('click', () => {
                if (state.selectedMatch) {
                    const text = state.selectedMatch.query_sentence?.text || state.selectedMatch.query_text || '';
                    DOM.matchInspectorModal.style.display = 'none';
                    switchView('view-paraphrase');
                    if (DOM.paraphraseInput) DOM.paraphraseInput.value = text;
                }
            });
        }
        if (DOM.modalBtnCopy) {
            DOM.modalBtnCopy.addEventListener('click', () => {
                if (state.selectedMatch) {
                    const text = state.selectedMatch.query_sentence?.text || state.selectedMatch.query_text || '';
                    navigator.clipboard.writeText(text);
                    showToast("Sentence copied to clipboard!", "success");
                }
            });
        }
    }

    // --- ASK LEMMA AI CHAT ---
    function setupAskLemma() {
        if (DOM.btnSendChat) {
            DOM.btnSendChat.addEventListener('click', handleSendChat);
        }
        if (DOM.chatInputText) {
            DOM.chatInputText.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendChat();
                }
            });
        }

        // Chip suggestions
        document.querySelectorAll('.chip-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.getAttribute('data-prompt');
                if (prompt) {
                    sendChatMessage(prompt);
                }
            });
        });
    }

    function handleSendChat() {
        const text = DOM.chatInputText.value.trim();
        if (!text) return;
        DOM.chatInputText.value = '';
        sendChatMessage(text);
    }

    async function sendChatMessage(query) {
        appendChatMessage('user', query);

        // Assistant placeholder
        const assistantMsgEl = appendChatMessage('assistant', 'Thinking...');
        const contentEl = assistantMsgEl.querySelector('.message-content');

        try {
            const contextPayload = state.activeDocument || {};
            const res = await fetch(`${state.apiBaseUrl}/api/v1/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: query,
                    context: contextPayload
                })
            });

            if (!res.ok) throw new Error("Chat request failed");
            const data = await res.json();
            
            // Render markdown formatted response
            contentEl.innerHTML = renderMarkdown(data.response || "No response received.");

        } catch (e) {
            contentEl.innerHTML = `<p class="text-danger">⚠️ Assistant error: ${e.message}. Using offline intelligence mode.</p>`;
        }
    }

    function appendChatMessage(sender, content) {
        if (!DOM.chatMessagesBox) return null;
        const msg = document.createElement('div');
        msg.className = `chat-message ${sender}`;
        
        const avatar = sender === 'user' ? 
            '<div class="message-avatar user-av"><i class="fa-solid fa-user"></i></div>' : 
            '<div class="message-avatar"><i class="fa-solid fa-robot"></i></div>';

        msg.innerHTML = `
            ${avatar}
            <div class="message-content">
                <p>${escapeHTML(content)}</p>
            </div>
        `;
        DOM.chatMessagesBox.appendChild(msg);
        DOM.chatMessagesBox.scrollTop = DOM.chatMessagesBox.scrollHeight;
        return msg;
    }

    function renderMarkdown(md) {
        if (!md) return '';
        let html = md
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        return `<p>${html}</p>`;
    }

    // --- PARAPHRASER & REWRITER ---
    function setupParaphraser() {
        document.querySelectorAll('.tone-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tone-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.activeTone = btn.getAttribute('data-tone') || 'academic';
            });
        });

        if (DOM.btnExecuteParaphrase) {
            DOM.btnExecuteParaphrase.addEventListener('click', executeSingleParaphrase);
        }
        if (DOM.btnCopyOriginal) {
            DOM.btnCopyOriginal.addEventListener('click', () => {
                navigator.clipboard.writeText(DOM.paraphraseInput.value);
                showToast("Original text copied!", "info");
            });
        }
        if (DOM.btnCopyRewritten) {
            DOM.btnCopyRewritten.addEventListener('click', () => {
                navigator.clipboard.writeText(DOM.paraphraseOutput.textContent);
                showToast("Rewritten text copied!", "success");
            });
        }
        if (DOM.btnReplaceInDoc) {
            DOM.btnReplaceInDoc.addEventListener('click', handleReplaceInDoc);
        }
        if (DOM.btnBatchRewriteAll) {
            DOM.btnBatchRewriteAll.addEventListener('click', executeBatchRewriteAll);
        }
        if (DOM.btnCancelBatch) {
            DOM.btnCancelBatch.addEventListener('click', () => {
                state.batchCancelRequested = true;
                showToast("Batch rewrite cancellation requested.", "warning");
            });
        }
    }

    async function executeSingleParaphrase() {
        const text = DOM.paraphraseInput.value.trim();
        if (!text) {
            showToast("Please enter text to paraphrase.", "warning");
            return;
        }

        DOM.paraphraseOutput.innerHTML = `<span class="placeholder-text"><i class="fa-solid fa-spinner fa-spin"></i> Paraphrasing in ${state.activeTone} tone...</span>`;

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/rewrite`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    tone: state.activeTone
                })
            });

            if (!res.ok) throw new Error("Paraphrase request failed");
            const data = await res.json();
            DOM.paraphraseOutput.textContent = data.rewritten_text || "No rewrite produced.";
            showToast("Paraphrase generated!", "success");

        } catch (e) {
            DOM.paraphraseOutput.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
        }
    }

    function handleReplaceInDoc() {
        const rewritten = DOM.paraphraseOutput.textContent.trim();
        const original = DOM.paraphraseInput.value.trim();
        if (!rewritten || !state.activeDocument) {
            showToast("No active document or rewritten text to replace.", "warning");
            return;
        }

        if (state.activeDocument.text.includes(original)) {
            state.activeDocument.text = state.activeDocument.text.replace(original, rewritten);
            showToast("Text replaced in active document! Re-analyzing...", "success");
            executeTextAnalysis(state.activeDocument.text, state.activeDocument.filename);
        } else {
            showToast("Original text snippet not found in current document.", "warning");
        }
    }

    async function executeBatchRewriteAll() {
        if (!state.activeDocument || !state.activeDocument.analysis) {
            showToast("No active document analyzed to rewrite.", "warning");
            return;
        }

        const matches = state.activeDocument.analysis.matches || [];
        if (matches.length === 0) {
            showToast("No flagged sentences to rewrite in this document!", "info");
            return;
        }

        const flaggedSentences = matches.map(m => m.query_sentence?.text || m.query_text).filter(Boolean);
        state.batchCancelRequested = false;

        if (DOM.batchProgressBox) {
            DOM.batchProgressBox.style.display = 'block';
            DOM.batchProgressStatus.textContent = `Rewriting flagged sentences: 0 / ${flaggedSentences.length}`;
            DOM.batchProgressBar.style.width = '0%';
        }

        let updatedDocText = state.activeDocument.text;
        let rewrittenCount = 0;

        for (let i = 0; i < flaggedSentences.length; i++) {
            if (state.batchCancelRequested) {
                showToast("Batch rewriting cancelled.", "warning");
                break;
            }

            const sent = flaggedSentences[i];
            try {
                const res = await fetch(`${state.apiBaseUrl}/api/v1/rewrite`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: sent, tone: state.activeTone })
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.rewritten_text && updatedDocText.includes(sent)) {
                        updatedDocText = updatedDocText.replace(sent, data.rewritten_text);
                        rewrittenCount++;
                    }
                }
            } catch (e) {}

            const pct = Math.round(((i + 1) / flaggedSentences.length) * 100);
            DOM.batchProgressStatus.textContent = `Rewriting flagged sentences: ${i + 1} / ${flaggedSentences.length}`;
            DOM.batchProgressBar.style.width = `${pct}%`;
        }

        setTimeout(() => {
            if (DOM.batchProgressBox) DOM.batchProgressBox.style.display = 'none';
        }, 800);

        showToast(`Batch rewrite finished! Re-analyzing updated document...`, "success");
        executeTextAnalysis(updatedDocText, state.activeDocument.filename);
    }

    // --- SOURCES VIEW ---
    function setupSources() {
        document.querySelectorAll('.sources-filter-bar .filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.sources-filter-bar .filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderSourcesView(btn.getAttribute('data-filter'));
            });
        });

        if (DOM.btnSearchSources) {
            DOM.btnSearchSources.addEventListener('click', handleExternalSourceSearch);
        }
        if (DOM.sourcesSearchInput) {
            DOM.sourcesSearchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') handleExternalSourceSearch();
            });
        }
    }

    function renderSourcesView(filter = 'all') {
        if (!DOM.sourcesGridWrapper) return;
        const currentDocSources = state.activeDocument?.analysis?.sources || [];
        
        let filtered = currentDocSources;
        if (filter !== 'all') {
            filtered = currentDocSources.filter(s => (s.match_type || 'lexical').toLowerCase() === filter.toLowerCase());
        }

        if (filtered.length === 0) {
            DOM.sourcesGridWrapper.innerHTML = `
                <div class="empty-sources-box">
                    <i class="fa-solid fa-book-open"></i>
                    <p>No reference sources matched for this filter. Use the search bar above to discover external scholarly publications from OpenAlex, Crossref, and arXiv.</p>
                </div>
            `;
            return;
        }

        DOM.sourcesGridWrapper.innerHTML = filtered.map(s => `
            <div class="source-card">
                <div class="source-card-header">
                    <span class="source-badge">${(s.match_type || 'Lexical').toUpperCase()}</span>
                    <span class="source-match-count">${s.match_count || 1} match(es)</span>
                </div>
                <h4>${escapeHTML(s.title || 'Untitled Reference')}</h4>
                <div class="source-author"><i class="fa-solid fa-user-pen"></i> ${escapeHTML(s.author || 'Scholarly Contributors')}</div>
                <div class="source-venue"><i class="fa-solid fa-building-columns"></i> ${escapeHTML(s.source || 'Reference Library')}</div>
                ${s.url ? `<a href="${s.url}" target="_blank" class="source-link"><i class="fa-solid fa-arrow-up-right-from-square"></i> View Source Document</a>` : ''}
            </div>
        `).join('');
    }

    async function handleExternalSourceSearch() {
        const query = DOM.sourcesSearchInput.value.trim();
        if (!query) {
            showToast("Enter a topic to search scholarly sources.", "info");
            return;
        }

        DOM.sourcesGridWrapper.innerHTML = `
            <div class="empty-sources-box">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <p>Searching Wikipedia, OpenAlex, Crossref, and arXiv for "${escapeHTML(query)}"...</p>
            </div>
        `;

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/sources/discover`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, limit: 9 })
            });

            if (!res.ok) throw new Error("Search failed");
            const data = await res.json();
            const sources = data.sources || [];

            if (sources.length === 0) {
                DOM.sourcesGridWrapper.innerHTML = `<div class="empty-sources-box"><p>No scholarly sources found for "${escapeHTML(query)}".</p></div>`;
                return;
            }

            DOM.sourcesGridWrapper.innerHTML = sources.map(s => `
                <div class="source-card">
                    <div class="source-card-header">
                        <span class="source-badge">${escapeHTML(s.provider || 'SCHOLARLY')}</span>
                        <span class="source-cat">${escapeHTML(s.category || 'General')}</span>
                    </div>
                    <h4>${escapeHTML(s.title || 'Untitled Reference')}</h4>
                    <div class="source-author"><i class="fa-solid fa-user-pen"></i> ${escapeHTML(s.author || 'Contributors')}</div>
                    <div class="source-venue"><i class="fa-solid fa-building-columns"></i> ${escapeHTML(s.source || 'Public Repository')}</div>
                    <p class="source-snippet">"${escapeHTML((s.text || '').substring(0, 120))}..."</p>
                    ${s.url ? `<a href="${s.url}" target="_blank" class="source-link"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open Publication</a>` : ''}
                </div>
            `).join('');

        } catch (e) {
            showToast(`Search error: ${e.message}`, "error");
        }
    }

    // --- REPORTS VIEW ---
    function setupReports() {
        if (DOM.btnGenerateReportView) {
            DOM.btnGenerateReportView.addEventListener('click', downloadCurrentReport);
        }
    }

    function renderReportsView() {
        const doc = state.activeDocument;
        if (!doc) return;

        const an = doc.analysis || {};
        if (DOM.repDate) DOM.repDate.textContent = new Date().toLocaleDateString();
        if (DOM.repFilename) DOM.repFilename.textContent = doc.filename || 'Document';
        if (DOM.repPlagScore) DOM.repPlagScore.textContent = `${an.plagiarism_score || 0}%`;
        if (DOM.repOrigScore) DOM.repOrigScore.textContent = `${an.originality_score || 100}%`;
        if (DOM.repSentences) DOM.repSentences.textContent = doc.sentence_count || an.total_sentences || 0;

        if (DOM.repSummaryText) {
            const plag = an.plagiarism_score || 0;
            DOM.repSummaryText.textContent = plag > 15 ? 
                `This document was analyzed using Lemma 2.0. ${plag}% of sentences contain matched phraseology with existing reference corpus literature.` : 
                `This document demonstrates high originality (${100 - plag}%) with minimal lexical overlap. Verified by Lemma 2.0.`;
        }

        if (DOM.repSourcesList) {
            const sources = an.sources || [];
            if (sources.length === 0) {
                DOM.repSourcesList.innerHTML = '<p>No external reference sources matched.</p>';
            } else {
                DOM.repSourcesList.innerHTML = sources.map((s, i) => `
                    <div class="rep-source-item">
                        <strong>#${i + 1} ${escapeHTML(s.title || 'Reference')}</strong>
                        <span>By ${escapeHTML(s.author || 'N/A')} (${escapeHTML(s.source || 'Journal')})</span>
                    </div>
                `).join('');
            }
        }
    }

    async function downloadCurrentReport() {
        if (!state.activeDocument) {
            showToast("Please analyze a document before generating a report.", "warning");
            return;
        }

        showToast("Generating official Lemma Integrity PDF Report...", "info");
        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/documents/report/direct`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(state.activeDocument)
            });

            if (!res.ok) throw new Error("Report generation failed");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${(state.activeDocument.filename || 'lemma_doc').replace(/\.[^/.]+$/, '')}_integrity_report.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            showToast("Report downloaded successfully!", "success");

        } catch (e) {
            showToast(`Report Download Error: ${e.message}`, "error");
        }
    }

    // --- HISTORY STORAGE & VIEW ---
    function setupHistory() {
        if (DOM.btnClearHistory) {
            DOM.btnClearHistory.addEventListener('click', () => {
                if (confirm("Are you sure you want to clear all analysis history?")) {
                    state.history = [];
                    localStorage.removeItem('lemma_history');
                    renderHistoryTable();
                    updateDashboardStats();
                    showToast("History cleared.", "info");
                }
            });
        }
    }

    function loadHistory() {
        try {
            const raw = localStorage.getItem('lemma_history');
            if (raw) state.history = JSON.parse(raw);
        } catch (e) {
            state.history = [];
        }
        updateDashboardStats();
    }

    function saveToHistory(docData) {
        const item = {
            id: `hist_${Date.now()}`,
            filename: docData.filename,
            timestamp: new Date().toISOString(),
            char_count: docData.char_count,
            sentence_count: docData.sentence_count,
            sentences: docData.sentences,
            text: docData.text,
            metrics: docData.metrics,
            analysis: docData.analysis
        };
        state.history.unshift(item);
        if (state.history.length > 50) state.history.pop();
        localStorage.setItem('lemma_history', JSON.stringify(state.history));
        updateDashboardStats();
    }

    function renderHistoryTable() {
        if (!DOM.historyTableTbody) return;
        if (state.history.length === 0) {
            DOM.historyTableTbody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="6">No saved history records found.</td>
                </tr>
            `;
            return;
        }

        DOM.historyTableTbody.innerHTML = state.history.map(item => `
            <tr>
                <td><strong>${escapeHTML(item.filename || 'Document')}</strong></td>
                <td>${new Date(item.timestamp).toLocaleString()}</td>
                <td>${item.char_count ? Math.round(item.char_count / 5).toLocaleString() : '0'}</td>
                <td><span class="badge badge-danger">${item.analysis?.plagiarism_score || 0}%</span></td>
                <td><span class="badge badge-success">${item.analysis?.originality_score || 100}%</span></td>
                <td>
                    <button class="btn btn-ghost btn-xs btn-open-hist" data-id="${item.id}">Open</button>
                    <button class="btn btn-outline btn-xs btn-dl-hist" data-id="${item.id}">Report</button>
                    <button class="btn btn-ghost btn-xs text-danger btn-del-hist" data-id="${item.id}"><i class="fa-solid fa-trash"></i></button>
                </td>
            </tr>
        `).join('');

        DOM.historyTableTbody.querySelectorAll('.btn-open-hist').forEach(b => {
            b.addEventListener('click', () => openHistoryItem(b.getAttribute('data-id')));
        });
        DOM.historyTableTbody.querySelectorAll('.btn-dl-hist').forEach(b => {
            b.addEventListener('click', () => downloadHistoryReport(b.getAttribute('data-id')));
        });
        DOM.historyTableTbody.querySelectorAll('.btn-del-hist').forEach(b => {
            b.addEventListener('click', () => {
                const id = b.getAttribute('data-id');
                state.history = state.history.filter(h => h.id !== id);
                localStorage.setItem('lemma_history', JSON.stringify(state.history));
                renderHistoryTable();
                updateDashboardStats();
                showToast("Item removed from history.", "info");
            });
        });
    }

    function openHistoryItem(id) {
        const item = state.history.find(h => h.id === id);
        if (item) {
            switchView('view-analyze');
            renderAnalysisResults(item);
            showToast(`Loaded "${item.filename}" from history!`, "success");
        }
    }

    async function downloadHistoryReport(id) {
        const item = state.history.find(h => h.id === id);
        if (item) {
            state.activeDocument = item;
            downloadCurrentReport();
        }
    }

    // --- WORKSPACE VIEW ---
    function setupWorkspace() {
        if (DOM.btnWorkspaceNewDoc) {
            DOM.btnWorkspaceNewDoc.addEventListener('click', () => {
                const name = prompt("Enter document title:", "New Research Paper");
                if (name) {
                    const newDoc = {
                        id: `ws_${Date.now()}`,
                        name: name,
                        created_at: new Date().toISOString(),
                        text: "Start writing or paste your academic content here...",
                        type: "doc"
                    };
                    state.workspace.unshift(newDoc);
                    localStorage.setItem('lemma_workspace', JSON.stringify(state.workspace));
                    renderWorkspace();
                    showToast(`Created "${name}"!`, "success");
                }
            });
        }
    }

    function loadWorkspace() {
        try {
            const raw = localStorage.getItem('lemma_workspace');
            if (raw) state.workspace = JSON.parse(raw);
            else {
                state.workspace = [
                    { id: 'ws_sample', name: 'Deep Learning & Neural Networks', created_at: new Date().toISOString(), text: SAMPLE_DOCUMENT_TEXT, type: 'doc' }
                ];
            }
        } catch (e) {
            state.workspace = [];
        }
    }

    function renderWorkspace() {
        if (!DOM.workspaceGridContainer) return;
        if (state.workspace.length === 0) {
            DOM.workspaceGridContainer.innerHTML = `<div class="empty-workspace-box"><p>No workspace documents found. Click 'New Document' to start.</p></div>`;
            return;
        }

        DOM.workspaceGridContainer.innerHTML = state.workspace.map(doc => `
            <div class="workspace-card" data-id="${doc.id}">
                <div class="ws-card-header">
                    <i class="fa-solid fa-file-lines text-purple"></i>
                    <span class="ws-date">${new Date(doc.created_at).toLocaleDateString()}</span>
                </div>
                <h4>${escapeHTML(doc.name)}</h4>
                <p class="ws-snippet">"${escapeHTML((doc.text || '').substring(0, 90))}..."</p>
                <div class="ws-actions">
                    <button class="btn btn-primary btn-xs btn-ws-open" data-id="${doc.id}">Open & Analyze</button>
                    <button class="btn btn-ghost btn-xs text-danger btn-ws-del" data-id="${doc.id}"><i class="fa-solid fa-trash"></i></button>
                </div>
            </div>
        `).join('');

        DOM.workspaceGridContainer.querySelectorAll('.btn-ws-open').forEach(b => {
            b.addEventListener('click', () => {
                const id = b.getAttribute('data-id');
                const doc = state.workspace.find(d => d.id === id);
                if (doc) {
                    switchView('view-analyze');
                    activateAnalyzeTab('paste');
                    if (DOM.pasteTextarea) DOM.pasteTextarea.value = doc.text;
                    updatePasteCounters();
                    executeTextAnalysis(doc.text, doc.name);
                }
            });
        });

        DOM.workspaceGridContainer.querySelectorAll('.btn-ws-del').forEach(b => {
            b.addEventListener('click', () => {
                const id = b.getAttribute('data-id');
                state.workspace = state.workspace.filter(d => d.id !== id);
                localStorage.setItem('lemma_workspace', JSON.stringify(state.workspace));
                renderWorkspace();
                showToast("Document deleted.", "info");
            });
        });
    }

    // --- PANDAZ PDF TOOLS SUITE ---
    function setupPandaz() {
        document.querySelectorAll('.btn-pandaz-launch, .pandaz-card').forEach(el => {
            el.addEventListener('click', (e) => {
                const tool = el.getAttribute('data-tool');
                if (tool) openPandazTool(tool);
            });
        });

        if (DOM.btnClosePandazModal) {
            DOM.btnClosePandazModal.addEventListener('click', () => {
                DOM.pandazWorkbenchModal.style.display = 'none';
            });
        }
    }

    function openPandazTool(toolName) {
        DOM.pandazWorkbenchModal.style.display = 'flex';
        const body = DOM.pandazModalBody;
        const title = DOM.pandazModalTitle;

        if (toolName === 'merge') {
            title.textContent = 'Merge PDF Documents';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Select multiple PDF files to merge into a single downloadable PDF.</p>
                    <input type="file" id="pandaz-merge-files" multiple accept=".pdf" class="form-control mb-3">
                    <div id="pandaz-merge-filelist" class="file-list-preview mb-3"></div>
                    <button class="btn btn-primary" id="btn-run-pandaz-merge">
                        <i class="fa-solid fa-object-group"></i> Merge PDFs
                    </button>
                </div>
            `;
            document.getElementById('btn-run-pandaz-merge').addEventListener('click', executePandazMerge);
        }

        else if (toolName === 'split') {
            title.textContent = 'Split PDF Document';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Upload a PDF and specify the page numbers / range to extract.</p>
                    <input type="file" id="pandaz-split-file" accept=".pdf" class="form-control mb-3">
                    <div class="form-group mb-3">
                        <label>Page Range (e.g. 1-3, 5, 8-10):</label>
                        <input type="text" id="pandaz-split-range" class="form-control" value="1-2">
                    </div>
                    <button class="btn btn-primary" id="btn-run-pandaz-split">
                        <i class="fa-solid fa-scissors"></i> Split PDF
                    </button>
                </div>
            `;
            document.getElementById('btn-run-pandaz-split').addEventListener('click', executePandazSplit);
        }

        else if (toolName === 'compress') {
            title.textContent = 'Compress PDF Document';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Upload a PDF to compress streams and reduce total file size.</p>
                    <input type="file" id="pandaz-comp-file" accept=".pdf" class="form-control mb-3">
                    <button class="btn btn-primary" id="btn-run-pandaz-compress">
                        <i class="fa-solid fa-file-zipper"></i> Compress PDF
                    </button>
                    <div id="pandaz-comp-results" class="mt-3" style="display: none;"></div>
                </div>
            `;
            document.getElementById('btn-run-pandaz-compress').addEventListener('click', executePandazCompress);
        }

        else if (toolName === 'csv') {
            title.textContent = 'Extract PDF Tables to CSV';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Extract structured tabular data from PDF pages directly into CSV format.</p>
                    <input type="file" id="pandaz-csv-file" accept=".pdf" class="form-control mb-3">
                    <button class="btn btn-primary" id="btn-run-pandaz-csv">
                        <i class="fa-solid fa-table"></i> Extract & Download CSV
                    </button>
                </div>
            `;
            document.getElementById('btn-run-pandaz-csv').addEventListener('click', executePandazCSV);
        }

        else if (toolName === 'rename') {
            title.textContent = 'Safely Rename PDF';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Provide a new sanitized filename and download the renamed document.</p>
                    <input type="file" id="pandaz-rename-file" accept=".pdf" class="form-control mb-3">
                    <div class="form-group mb-3">
                        <label>New Filename:</label>
                        <input type="text" id="pandaz-rename-val" class="form-control" placeholder="my_academic_paper.pdf">
                    </div>
                    <button class="btn btn-primary" id="btn-run-pandaz-rename">
                        <i class="fa-solid fa-file-pen"></i> Download Renamed PDF
                    </button>
                </div>
            `;
            document.getElementById('btn-run-pandaz-rename').addEventListener('click', executePandazRename);
        }

        else if (toolName === 'sign') {
            title.textContent = 'Edit & Sign PDF';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Upload a PDF, draw your digital signature on the pad below, and stamp it onto the PDF.</p>
                    <input type="file" id="pandaz-sign-file" accept=".pdf" class="form-control mb-3">
                    <div class="sig-canvas-wrapper mb-3">
                        <label>Digital Signature Pad (Draw with mouse / finger):</label>
                        <canvas id="sig-pad-canvas" width="400" height="150" style="border: 1px solid var(--border-color); background: #ffffff; border-radius: 8px; cursor: crosshair; display: block;"></canvas>
                        <button class="btn btn-ghost btn-xs mt-2" id="btn-clear-sig-pad">Clear Signature</button>
                    </div>
                    <button class="btn btn-primary" id="btn-run-pandaz-sign">
                        <i class="fa-solid fa-signature"></i> Stamp & Download PDF
                    </button>
                </div>
            `;
            initSignaturePad();
            document.getElementById('btn-run-pandaz-sign').addEventListener('click', executePandazSign);
        }

        else if (toolName === 'ocr') {
            title.textContent = 'OCR Document & Handwriting to Text';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Upload a scanned PDF or image (PNG/JPG) to extract machine-readable text.</p>
                    <input type="file" id="pandaz-ocr-file" accept=".pdf,.png,.jpg,.jpeg" class="form-control mb-3">
                    <button class="btn btn-primary mb-3" id="btn-run-pandaz-ocr">
                        <i class="fa-solid fa-eye"></i> Run OCR
                    </button>
                    <div id="pandaz-ocr-result-box" style="display: none;">
                        <div class="ocr-meta-pill mb-2">
                            <span>Confidence: <strong id="ocr-conf-val">0%</strong></span>
                            <span>Engine: <strong id="ocr-engine-val">Standard</strong></span>
                        </div>
                        <textarea id="pandaz-ocr-textarea" class="form-control mb-2" rows="6"></textarea>
                        <div class="d-flex gap-2">
                            <button class="btn btn-secondary btn-sm" id="btn-copy-ocr-text">Copy Text</button>
                            <button class="btn btn-outline btn-sm" id="btn-ocr-to-lemma">
                                <i class="fa-solid fa-magnifying-glass-chart"></i> Analyze with Lemma
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('btn-run-pandaz-ocr').addEventListener('click', executePandazOCR);
        }

        else if (toolName === 'summarizer') {
            title.textContent = 'AI PDF Summarizer';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Upload a PDF document to generate an instant executive summary, key points, and keywords.</p>
                    <input type="file" id="pandaz-sum-file" accept=".pdf" class="form-control mb-3">
                    <button class="btn btn-primary mb-3" id="btn-run-pandaz-summarize">
                        <i class="fa-solid fa-brain"></i> Summarize PDF
                    </button>
                    <div id="pandaz-sum-result-box" class="card-box mt-3" style="display: none;">
                        <h4>TL;DR</h4>
                        <p id="sum-tldr-text">...</p>
                        <h4>Key Core Points</h4>
                        <ul id="sum-keypoints-list"></ul>
                        <h4>Keywords</h4>
                        <div id="sum-keywords-tags" class="d-flex gap-2 flex-wrap"></div>
                        <hr class="my-3">
                        <button class="btn btn-primary btn-sm" id="btn-send-sum-to-lemma">
                            <i class="fa-solid fa-magnifying-glass-chart"></i> Analyze Originality in Lemma
                        </button>
                    </div>
                </div>
            `;
            document.getElementById('btn-run-pandaz-summarize').addEventListener('click', executePandazSummarize);
        }

        else if (toolName === 'rotate') {
            title.textContent = 'Rotate & Manage PDF Pages';
            body.innerHTML = `
                <div class="pandaz-tool-view">
                    <p>Rotate PDF orientation or delete specified pages.</p>
                    <input type="file" id="pandaz-rotate-file" accept=".pdf" class="form-control mb-3">
                    <div class="form-group mb-3">
                        <label>Rotate Clockwise by:</label>
                        <select id="pandaz-rotate-degrees" class="form-control">
                            <option value="90">90° Clockwise</option>
                            <option value="180">180° Invert</option>
                            <option value="270">270° Counter-Clockwise</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" id="btn-run-pandaz-rotate">
                        <i class="fa-solid fa-rotate-right"></i> Rotate & Download
                    </button>
                </div>
            `;
            document.getElementById('btn-run-pandaz-rotate').addEventListener('click', executePandazRotate);
        }
    }

    // --- PANDAZ EXECUTION HANDLERS ---
    async function executePandazMerge() {
        const input = document.getElementById('pandaz-merge-files');
        if (!input.files || input.files.length < 2) {
            showToast("Please select at least 2 PDF files to merge.", "warning");
            return;
        }

        showToast("Merging PDF documents...", "info");
        const fd = new FormData();
        for (let i = 0; i < input.files.length; i++) {
            fd.append('files', input.files[i]);
        }

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/merge`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Merge failed on server.");
            const blob = await res.blob();
            downloadBlob(blob, 'pandaz_merged.pdf');
            showToast("PDFs merged successfully!", "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`Merge error: ${e.message}`, "error");
        }
    }

    async function executePandazSplit() {
        const input = document.getElementById('pandaz-split-file');
        const range = document.getElementById('pandaz-split-range').value.trim();
        if (!input.files || input.files.length === 0) {
            showToast("Please select a PDF to split.", "warning");
            return;
        }

        showToast("Splitting PDF pages...", "info");
        const fd = new FormData();
        fd.append('file', input.files[0]);
        fd.append('page_range', range || '1-2');

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/split`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Split failed.");
            const blob = await res.blob();
            downloadBlob(blob, `${input.files[0].name.replace('.pdf', '')}_split.pdf`);
            showToast("PDF split completed!", "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`Split error: ${e.message}`, "error");
        }
    }

    async function executePandazCompress() {
        const input = document.getElementById('pandaz-comp-file');
        if (!input.files || input.files.length === 0) {
            showToast("Select a PDF to compress.", "warning");
            return;
        }

        showToast("Compressing PDF file...", "info");
        const fd = new FormData();
        fd.append('file', input.files[0]);

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/compress`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Compression failed.");
            const reduction = res.headers.get('X-Reduction-Percent') || '0';
            const blob = await res.blob();
            downloadBlob(blob, `${input.files[0].name.replace('.pdf', '')}_compressed.pdf`);
            showToast(`PDF compressed! Reduced by ${reduction}%.`, "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`Compression error: ${e.message}`, "error");
        }
    }

    async function executePandazCSV() {
        const input = document.getElementById('pandaz-csv-file');
        if (!input.files || input.files.length === 0) {
            showToast("Select a PDF with tables.", "warning");
            return;
        }

        showToast("Extracting tables to CSV...", "info");
        const fd = new FormData();
        fd.append('file', input.files[0]);

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/to-csv`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Table extraction failed.");
            const blob = await res.blob();
            downloadBlob(blob, `${input.files[0].name.replace('.pdf', '')}_tables.csv`);
            showToast("CSV exported successfully!", "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`CSV error: ${e.message}`, "error");
        }
    }

    async function executePandazRename() {
        const input = document.getElementById('pandaz-rename-file');
        const newName = document.getElementById('pandaz-rename-val').value.trim();
        if (!input.files || input.files.length === 0 || !newName) {
            showToast("Select a file and enter a new filename.", "warning");
            return;
        }

        const fd = new FormData();
        fd.append('file', input.files[0]);
        fd.append('new_name', newName);

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/rename`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Rename failed.");
            const blob = await res.blob();
            downloadBlob(blob, newName.endsWith('.pdf') ? newName : `${newName}.pdf`);
            showToast("Renamed PDF downloaded!", "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`Rename error: ${e.message}`, "error");
        }
    }

    function initSignaturePad() {
        const canvas = document.getElementById('sig-pad-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let isDrawing = false;

        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';

        function start(e) {
            isDrawing = true;
            ctx.beginPath();
            ctx.moveTo(e.offsetX, e.offsetY);
        }
        function draw(e) {
            if (!isDrawing) return;
            ctx.lineTo(e.offsetX, e.offsetY);
            ctx.stroke();
        }
        function stop() {
            isDrawing = false;
        }

        canvas.addEventListener('mousedown', start);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stop);
        canvas.addEventListener('mouseleave', stop);

        document.getElementById('btn-clear-sig-pad').addEventListener('click', () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        });
    }

    async function executePandazSign() {
        const input = document.getElementById('pandaz-sign-file');
        const canvas = document.getElementById('sig-pad-canvas');
        if (!input.files || input.files.length === 0) {
            showToast("Please upload a PDF to sign.", "warning");
            return;
        }

        const sigBase64 = canvas ? canvas.toDataURL('image/png') : null;
        showToast("Stamping signature on PDF...", "info");
        const fd = new FormData();
        fd.append('file', input.files[0]);
        fd.append('signature_base64', sigBase64 || '');

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/sign`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Sign failed.");
            const blob = await res.blob();
            downloadBlob(blob, `${input.files[0].name.replace('.pdf', '')}_signed.pdf`);
            showToast("Signed PDF downloaded!", "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`Sign error: ${e.message}`, "error");
        }
    }

    async function executePandazOCR() {
        const input = document.getElementById('pandaz-ocr-file');
        if (!input.files || input.files.length === 0) {
            showToast("Upload an image or PDF to OCR.", "warning");
            return;
        }

        showToast("Running Optical Character Recognition...", "info");
        const fd = new FormData();
        fd.append('file', input.files[0]);

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/ocr`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("OCR processing failed.");
            const data = await res.json();

            const box = document.getElementById('pandaz-ocr-result-box');
            const textarea = document.getElementById('pandaz-ocr-textarea');
            box.style.display = 'block';
            textarea.value = data.text || '';
            document.getElementById('ocr-conf-val').textContent = `${data.confidence || 90}%`;
            document.getElementById('ocr-engine-val').textContent = data.engine || 'Standard';

            document.getElementById('btn-copy-ocr-text').onclick = () => {
                navigator.clipboard.writeText(textarea.value);
                showToast("OCR text copied!", "success");
            };

            document.getElementById('btn-ocr-to-lemma').onclick = () => {
                DOM.pandazWorkbenchModal.style.display = 'none';
                switchView('view-analyze');
                activateAnalyzeTab('paste');
                if (DOM.pasteTextarea) DOM.pasteTextarea.value = textarea.value;
                updatePasteCounters();
                executeTextAnalysis(textarea.value, `OCR Import - ${input.files[0].name}`);
            };

        } catch (e) {
            showToast(`OCR Error: ${e.message}`, "error");
        }
    }

    async function executePandazSummarize() {
        const input = document.getElementById('pandaz-sum-file');
        if (!input.files || input.files.length === 0) {
            showToast("Upload a PDF to summarize.", "warning");
            return;
        }

        showToast("Generating PDF executive summary...", "info");
        const fd = new FormData();
        fd.append('file', input.files[0]);

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/summarize`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Summarization failed.");
            const data = await res.json();

            const box = document.getElementById('pandaz-sum-result-box');
            box.style.display = 'block';
            document.getElementById('sum-tldr-text').textContent = data.tldr || 'Summary generated.';
            
            const kpList = document.getElementById('sum-keypoints-list');
            kpList.innerHTML = (data.key_points || []).map(p => `<li>${escapeHTML(p)}</li>`).join('');

            const kwDiv = document.getElementById('sum-keywords-tags');
            kwDiv.innerHTML = (data.keywords || []).map(k => `<span class="badge badge-info">${escapeHTML(k)}</span>`).join('');

            document.getElementById('btn-send-sum-to-lemma').onclick = async () => {
                DOM.pandazWorkbenchModal.style.display = 'none';
                showToast("Importing PDF into Lemma Plagiarism Engine...", "info");
                
                const sendFd = new FormData();
                sendFd.append('file', input.files[0]);
                const lemmaRes = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/to-lemma`, {
                    method: 'POST',
                    body: sendFd
                });
                if (lemmaRes.ok) {
                    const lData = await lemmaRes.json();
                    switchView('view-analyze');
                    renderAnalysisResults(lData);
                    saveToHistory(lData);
                    showToast("PDF imported and analyzed in Lemma!", "success");
                }
            };

        } catch (e) {
            showToast(`Summarizer error: ${e.message}`, "error");
        }
    }

    async function executePandazRotate() {
        const input = document.getElementById('pandaz-rotate-file');
        const degrees = document.getElementById('pandaz-rotate-degrees').value;
        if (!input.files || input.files.length === 0) {
            showToast("Select a PDF to rotate.", "warning");
            return;
        }

        const fd = new FormData();
        fd.append('file', input.files[0]);
        fd.append('degrees', degrees);

        try {
            const res = await fetch(`${state.apiBaseUrl}/api/v1/pandaz/rotate`, {
                method: 'POST',
                body: fd
            });
            if (!res.ok) throw new Error("Rotate failed.");
            const blob = await res.blob();
            downloadBlob(blob, `rotated_${input.files[0].name}`);
            showToast("Rotated PDF downloaded!", "success");
            DOM.pandazWorkbenchModal.style.display = 'none';
        } catch (e) {
            showToast(`Rotate error: ${e.message}`, "error");
        }
    }

    function downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
    }

    // --- COMMAND PALETTE (CTRL + K) ---
    function setupCommandPalette() {
        const commands = [
            { title: 'Analyze Document', icon: 'fa-magnifying-glass-chart', action: () => { switchView('view-analyze'); activateAnalyzeTab('upload'); } },
            { title: 'Paste Text for Analysis', icon: 'fa-paste', action: () => { switchView('view-analyze'); activateAnalyzeTab('paste'); } },
            { title: 'Try Sample Document Analysis', icon: 'fa-flask', action: () => { switchView('view-analyze'); executeTextAnalysis(SAMPLE_DOCUMENT_TEXT, "Sample Research Document"); } },
            { title: 'Ask Lemma AI Assistant', icon: 'fa-robot', action: () => switchView('view-asklemma') },
            { title: 'Paraphraser & Rewriter', icon: 'fa-wand-magic-sparkles', action: () => switchView('view-paraphrase') },
            { title: 'Scholarly Sources & Discovery', icon: 'fa-book-bookmark', action: () => switchView('view-sources') },
            { title: 'Generate Lemma Integrity Report', icon: 'fa-file-invoice', action: () => switchView('view-reports') },
            { title: 'View Analysis History', icon: 'fa-clock-rotate-left', action: () => switchView('view-history') },
            { title: 'Workspace Document Manager', icon: 'fa-folder-tree', action: () => switchView('view-workspace') },
            { title: 'Pandaz: Merge PDFs', icon: 'fa-object-group', action: () => { switchView('view-pandaz'); openPandazTool('merge'); } },
            { title: 'Pandaz: Split PDF', icon: 'fa-scissors', action: () => { switchView('view-pandaz'); openPandazTool('split'); } },
            { title: 'Pandaz: Compress PDF', icon: 'fa-file-zipper', action: () => { switchView('view-pandaz'); openPandazTool('compress'); } },
            { title: 'Pandaz: PDF to CSV', icon: 'fa-table', action: () => { switchView('view-pandaz'); openPandazTool('csv'); } },
            { title: 'Pandaz: Edit & Sign PDF', icon: 'fa-signature', action: () => { switchView('view-pandaz'); openPandazTool('sign'); } },
            { title: 'Pandaz: OCR Text Extractor', icon: 'fa-eye', action: () => { switchView('view-pandaz'); openPandazTool('ocr'); } },
            { title: 'Pandaz: AI PDF Summarizer', icon: 'fa-brain', action: () => { switchView('view-pandaz'); openPandazTool('summarizer'); } },
            { title: 'Settings & System Health', icon: 'fa-sliders', action: () => switchView('view-settings') }
        ];

        function renderPaletteResults(filter = '') {
            const f = filter.toLowerCase();
            const matched = commands.filter(c => c.title.toLowerCase().includes(f));
            DOM.paletteResultsList.innerHTML = matched.map((c, i) => `
                <div class="palette-item ${i === 0 ? 'selected' : ''}" data-idx="${i}">
                    <i class="fa-solid ${c.icon}"></i>
                    <span>${escapeHTML(c.title)}</span>
                </div>
            `).join('');

            DOM.paletteResultsList.querySelectorAll('.palette-item').forEach((item, idx) => {
                item.addEventListener('click', () => {
                    DOM.commandPaletteModal.style.display = 'none';
                    matched[idx].action();
                });
            });
        }

        // Trigger shortcut
        window.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                DOM.commandPaletteModal.style.display = 'flex';
                DOM.paletteSearchInput.value = '';
                DOM.paletteSearchInput.focus();
                renderPaletteResults();
            }
            if (e.key === 'Escape' && DOM.commandPaletteModal.style.display === 'flex') {
                DOM.commandPaletteModal.style.display = 'none';
            }
        });

        if (DOM.commandPaletteTrigger) {
            DOM.commandPaletteTrigger.addEventListener('click', () => {
                DOM.commandPaletteModal.style.display = 'flex';
                DOM.paletteSearchInput.value = '';
                DOM.paletteSearchInput.focus();
                renderPaletteResults();
            });
        }

        if (DOM.paletteSearchInput) {
            DOM.paletteSearchInput.addEventListener('input', () => {
                renderPaletteResults(DOM.paletteSearchInput.value);
            });
        }
    }

    // --- SETTINGS VIEW ---
    function setupSettings() {
        if (DOM.btnRefreshStatus) {
            DOM.btnRefreshStatus.addEventListener('click', () => {
                showToast("Checking subsystem health...", "info");
                checkSystemHealth();
            });
        }
        if (DOM.btnSaveApiUrl) {
            DOM.btnSaveApiUrl.addEventListener('click', () => {
                const url = DOM.settingApiUrl.value.trim();
                APIConfigManager.setDeveloperOverrideUrl(url);
                state.apiBaseUrl = url || 'http://localhost:8000';
                showToast("API URL override saved!", "success");
                checkSystemHealth();
            });
        }

        document.querySelectorAll('.theme-choice-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const t = btn.getAttribute('data-theme');
                applyTheme(t);
            });
        });
    }

    // --- THEME ENGINE ---
    function initTheme() {
        state.theme = localStorage.getItem('lemma-theme') || 'dark';
        applyTheme(state.theme);

        if (DOM.themeToggle) {
            DOM.themeToggle.addEventListener('click', () => {
                const newT = state.theme === 'dark' ? 'light' : 'dark';
                applyTheme(newT);
            });
        }
    }

    function applyTheme(theme) {
        state.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('lemma-theme', theme);

        if (DOM.themeToggle) {
            DOM.themeToggle.innerHTML = theme === 'dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        }
        document.querySelectorAll('.theme-choice-btn').forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-theme') === theme);
        });
    }

    // --- HELPER FUNCTIONS ---
    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Initialize on DOM load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initApp);
    } else {
        initApp();
    }

})();
