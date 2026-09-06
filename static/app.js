// 表达力 Pro - Frontend SPA
const app = {
    state: null,
    user: null,
    cycle: null,
    article: null,
    progress: null,
    selections: {},

    async init() {
        await this.loadUser();
        this.render();
    },

    async loadUser() {
        try {
            const res = await fetch('/api/user');
            const data = await res.json();
            this.user = data.user;
            this.cycle = data.cycle;
            this.state = this.user.state;

            const badge = document.getElementById('method-badge');
            if (badge) {
                if (this.user.current_method) {
                    badge.textContent = this.user.current_method + ' 周期';
                    badge.classList.remove('hidden');
                } else {
                    badge.classList.add('hidden');
                }
            }

            const footer = document.getElementById('footer-nav');
            if (this.cycle && this.state !== 'home') {
                if (footer) footer.classList.remove('hidden');
                const footerDay = document.getElementById('footer-day');
                if (footerDay) footerDay.textContent = this.cycle.current_day;
            } else {
                if (footer) footer.classList.add('hidden');
            }
        } catch (err) {
            console.error('loadUser error:', err.message, err.stack);
        }
    },

    getStateLabel(state) {
        const labels = {
            'home': '首页',
            'select_method': '选择方法',
            'method_learning': '方法学习',
            'article_reading': '文章阅读',
            'drag_analysis': '拖拽分析',
            'qa': '问答练习',
            'retell': '全文复述',
            'free_output': '主动输出',
            'day_complete': '今日完成'
        };
        return labels[state] || state;
    },

    render() {
        const main = document.getElementById('main');
        main.innerHTML = '';

        switch (this.state) {
            case 'home':
                this.renderHome(main);
                break;
            case 'select_method':
                this.renderSelectMethod(main);
                break;
            case 'method_learning':
                this.renderMethodLearning(main);
                break;
            case 'article_reading':
            case 'drag_analysis':
                this.renderArticleAndAnalysis(main);
                break;
            case 'qa':
                this.renderQA(main);
                break;
            case 'retell':
                this.renderRetell(main);
                break;
            case 'free_output':
                this.renderFreeOutput(main);
                break;
            case 'day_complete':
                this.renderDayComplete(main);
                break;
            default:
                this.renderHome(main);
        }
    },

    // -------------------- Home --------------------
    async renderHome(container) {
        const res = await fetch('/api/home');
        const data = await res.json();
        const { streak, weekly, today_checked, week_progress, cycle } = data;

        const hour = new Date().getHours();
        let greeting = '早上好';
        if (hour >= 12 && hour < 18) greeting = '下午好';
        else if (hour >= 18) greeting = '晚上好';

        const today = weekly.find(d => d.is_today);

        container.innerHTML = `
            <div class="fade-in flex flex-col h-full">
                <div class="home-header py-4 px-4 mb-2">
                    <div class="home-greeting">${greeting}，开启今日表达力训练</div>
                    <div class="home-subtitle">坚持打卡，让表达成为习惯</div>
                </div>

                <div class="card py-2 px-3 mb-2">
                    <div class="flex justify-between items-center mb-1">
                        <h3 class="font-bold text-sm text-primary">本周打卡</h3>
                        <span class="text-xs text-muted">${week_progress}/7 天</span>
                    </div>
                    <div class="weekly-calendar my-1">
                        ${weekly.map(day => `
                            <div class="day-cell ${day.checked ? 'checked' : ''} ${day.is_today ? 'today' : ''}">
                                <span class="day-name">${day.day_name}</span>
                                <span class="day-number">${new Date(day.date).getDate()}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <button onclick="app.startCheckin()" class="checkin-btn ${today_checked ? 'checkin-btn-done' : 'checkin-btn-primary'} mb-2" ${today_checked ? 'disabled' : ''}>
                    ${today_checked ? '✓ 今日已打卡' : '开始今日打卡'}
                </button>

                <div class="stats-row mb-2">
                    <div class="stat-card py-2">
                        <div class="stat-value">${streak}</div>
                        <div class="stat-label">连续打卡天数</div>
                    </div>
                    <div class="stat-card py-2">
                        <div class="stat-value">${cycle ? cycle.current_day + '/' + cycle.total_days : '0/4'}</div>
                        <div class="stat-label">当前训练周期</div>
                    </div>
                </div>

                ${cycle ? `
                <div class="card py-2 px-3 mb-2">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="text-xs text-muted">当前进行中的训练</div>
                            <div class="font-bold text-primary text-sm">${cycle.method} 法则 · 第 ${cycle.current_day} 天</div>
                        </div>
                        <button onclick="app.continueTraining()" class="btn-primary text-xs py-1.5 px-3">继续训练</button>
                    </div>
                </div>
                ` : ''}

                <div class="flex-1 min-h-0"></div>
                <button onclick="app.resetAll()" class="w-full text-xs text-black/50 hover:text-primary transition-colors py-2">重置所有进度</button>
            </div>
        `;
    },

    async startCheckin() {
        const res = await fetch('/api/checkin', { method: 'POST' });
        const data = await res.json();
        await this.loadUser();
        this.state = data.state || 'method_learning';
        this.render();
    },

    async continueTraining() {
        // Use the stored user state if valid, otherwise default to article_reading
        const validStates = ['method_learning', 'article_reading', 'drag_analysis', 'qa', 'retell', 'free_output', 'day_complete'];
        this.state = validStates.includes(this.user.state) ? this.user.state : 'article_reading';
        await this.loadUser();
        this.render();
    },

    // -------------------- Select Method --------------------
    renderSelectMethod(container) {
        container.innerHTML = `
            <div class="fade-in text-center py-8">
                <div class="icon-circle bg-gradient-to-br from-primary to-primary-light text-white mx-auto mb-6 shadow-lg">
                    <span class="text-2xl">🎯</span>
                </div>
                <h2 class="text-2xl font-bold mb-3 text-primary">开启你的表达力训练</h2>
                <p class="text-black/60 mb-8">选择一个逻辑框架，完成 4 天为一个周期的刻意练习</p>

                <div class="space-y-4 mb-8">
                    <button onclick="app.selectMethod('STAR')" class="w-full card card-hover text-left p-0 overflow-hidden">
                        <div class="p-5">
                            <div class="flex items-start gap-4">
                                <div class="w-14 h-14 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-2xl shrink-0">📖</div>
                                <div class="flex-1">
                                    <div class="badge badge-green mb-2">叙事型框架</div>
                                    <h3 class="text-xl font-bold mb-1 text-primary">STAR 法则</h3>
                                    <p class="text-sm text-black/60">情境 · 任务 · 行动 · 结果</p>
                                    <p class="text-xs text-black/50 mt-2">适合面试、述职、案例分享</p>
                                </div>
                                <span class="text-2xl text-black/30">→</span>
                            </div>
                        </div>
                        <div class="h-1 bg-gradient-to-r from-primary via-primary-light via-green-400 to-primary-dark"></div>
                    </button>

                    <button onclick="app.selectMethod('PREP')" class="w-full card card-hover text-left p-0 overflow-hidden">
                        <div class="p-5">
                            <div class="flex items-start gap-4">
                                <div class="w-14 h-14 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-2xl shrink-0">💡</div>
                                <div class="flex-1">
                                    <div class="badge badge-accent mb-2">观点型框架</div>
                                    <h3 class="text-xl font-bold mb-1 text-primary">PREP 结构</h3>
                                    <p class="text-sm text-black/60">观点 · 理由 · 例证 · 重申</p>
                                    <p class="text-xs text-black/50 mt-2">适合辩论、演讲、观点表达</p>
                                </div>
                                <span class="text-2xl text-black/30">→</span>
                            </div>
                        </div>
                        <div class="h-1 bg-gradient-to-r from-primary via-green-400 to-primary-dark"></div>
                    </button>
                </div>

                <button onclick="app.resetAll()" class="text-sm text-black/50 hover:text-primary transition-colors">重置所有进度</button>
            </div>
        `;
    },

    async selectMethod(method) {
        const res = await fetch('/api/select-method', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method, total_days: 4 })
        });
        if (res.ok) {
            await this.loadUser();
            this.render();
        }
    },

    async goHome() {
        this.state = 'home';
        this.render();
    },

    async resetAll() {
        if (!confirm('确定要重置所有进度吗？')) return;
        await fetch('/api/reset', { method: 'POST' });
        window.location.reload();
    },

    // -------------------- Method Learning --------------------
    renderMethodLearning(container) {
        const isStar = this.user.current_method === 'STAR';
        const title = isStar ? 'STAR 法则' : 'PREP 结构';
        const subtitle = isStar ? '情境 · 任务 · 行动 · 结果' : '观点 · 理由 · 例证 · 重申';
        const steps = isStar ? [
            { key: 'S', name: '情境', desc: 'Situation：交代背景，时间、地点、人物、环境。', color: 'green' },
            { key: 'T', name: '任务', desc: 'Task：明确目标，你面临的具体挑战。', color: 'green-light' },
            { key: 'A', name: '行动', desc: 'Action：关键动作，你做了什么、为什么做。', color: 'green' },
            { key: 'R', name: '结果', desc: 'Result：量化成果，最好有数字。', color: 'green-dark' }
        ] : [
            { key: 'P', name: '观点', desc: 'Point：先亮明立场，让人第一时间知道你的看法。', color: 'green' },
            { key: 'R', name: '理由', desc: 'Reason：给出 2-3 条支撑理由，建立逻辑骨架。', color: 'green' },
            { key: 'E', name: '例证', desc: 'Example：用案例、数据或故事让理由更具体。', color: 'green-light' },
            { key: 'P', name: '重申', desc: 'Point：回扣观点，强化记忆点。', color: 'green-dark' }
        ];

        const colorMap = {
            green: 'bg-primary/10 text-primary',
            'green-light': 'bg-primary/5 text-primary-light',
            'green-dark': 'bg-primary/20 text-primary-dark'
        };

        container.innerHTML = `
            <div class="fade-in flex flex-col h-full">
                <div class="text-center mb-3">
                    <div class="badge badge-accent mb-1 text-xs">第 1 步：方法学习</div>
                    <h2 class="text-xl font-bold text-primary mb-1">${title}</h2>
                    <p class="text-xs text-black/60">${subtitle}</p>
                </div>

                <div class="grid grid-cols-2 gap-2 mb-3">
                    ${steps.map((step, idx) => `
                        <div class="card p-2 mb-0">
                            <div class="flex items-center gap-2 mb-1">
                                <div class="w-7 h-7 rounded-lg ${colorMap[step.color]} flex items-center justify-center text-sm font-bold shrink-0">${step.key}</div>
                                <h3 class="font-bold text-sm text-primary">${step.name}</h3>
                            </div>
                            <p class="text-xs text-black/60 leading-snug">${step.desc}</p>
                        </div>
                    `).join('')}
                </div>

                <div class="card py-2 px-3 mb-3 bg-gradient-to-br from-primary/5 to-primary/10 border-primary/10">
                    <h4 class="font-bold text-xs text-primary mb-1">💡 话术模板</h4>
                    <p class="text-xs text-black/70 leading-snug bg-white/70 p-2 rounded-lg">
                        ${isStar
                            ? '当时情况是……，我负责……，于是采取……，最终实现了……。'
                            : '我的观点是……，理由有三：第一……第二……第三……，因此……。'}
                    </p>
                </div>

                <div class="flex-1 min-h-0"></div>
                <button onclick="app.finishMethodLearning()" class="btn-primary w-full">我已掌握，开始实战</button>
            </div>
        `;
    },

    async finishMethodLearning() {
        const res = await fetch('/api/method/learned', { method: 'POST' });
        if (res.ok) {
            await this.loadUser();
            this.render();
        }
    },

    // -------------------- Article Reading + Highlight Analysis --------------------
    async renderArticleAndAnalysis(container) {
        const res = await fetch('/api/article');
        const data = await res.json();
        this.article = data.article;
        this.progress = data.progress;
        this.cycle = data.cycle;
        this.selections = {};

        const isStar = this.cycle.method === 'STAR';
        const sections = isStar
            ? [
                { key: 'S', label: 'S - 情境', desc: 'Situation', color: 'green', descText: '故事发生的背景' },
                { key: 'T', label: 'T - 任务', desc: 'Task', color: 'green-light', descText: '面临的核心挑战' },
                { key: 'A', label: 'A - 行动', desc: 'Action', color: 'green', descText: '采取的关键动作' },
                { key: 'R', label: 'R - 结果', desc: 'Result', color: 'green-dark', descText: '最终达成的成果' }
            ]
            : [
                { key: 'P', label: 'P - 观点', desc: 'Point', color: 'green', descText: '作者的核心立场' },
                { key: 'R', label: 'R - 理由', desc: 'Reason', color: 'green', descText: '支撑观点的逻辑' },
                { key: 'E', label: 'E - 例证', desc: 'Example', color: 'green-light', descText: '具体案例或数据' },
                { key: 'P2', label: 'P - 重申', desc: 'Point', color: 'green-dark', descText: '回扣并强化观点' }
            ];

        const colorClasses = {
            green: 'bg-primary/50',
            'green-light': 'bg-primary/30',
            'green-dark': 'bg-primary/70'
        };

        const chipClasses = {
            green: 'bg-primary/5 text-primary border-primary/20',
            'green-light': 'bg-primary/5 text-primary border-primary/20',
            'green-dark': 'bg-primary/5 text-primary border-primary/20'
        };

        container.innerHTML = `
            <div class="fade-in">
                <div class="card">
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <div class="badge badge-accent mb-2">第 ${this.cycle.current_day} 天 · 内容实战</div>
                            <h2 class="text-xl font-bold text-primary leading-tight">${this.article.title}</h2>
                        </div>
                        <button onclick="app.swapArticle()" class="btn-outline shrink-0 ml-3">换一篇</button>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-black/50 mb-4">
                        <span class="badge badge-green">${this.cycle.method}</span>
                        <span>约 ${this.article.content.length} 字</span>
                    </div>
                    <div id="article-text" class="article-content">
                        ${this.article.content}
                    </div>
                </div>

                <div class="card">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3 class="font-bold text-lg text-primary">结构分析</h3>
                            <p class="text-sm text-black/60">选中上方文字，选择对应的 ${this.cycle.method} 部分</p>
                        </div>
                        <button onclick="app.resetHighlights()" class="btn-outline text-xs">清除标记</button>
                    </div>

                    <div class="space-y-3">
                        ${sections.map(section => `
                            <div class="analysis-section" id="section-${section.key}" data-slot="${section.key}">
                                <div class="analysis-section-header">
                                    <div class="analysis-section-letter ${colorClasses[section.color]}">${section.key[0]}</div>
                                    <div>
                                        <div class="analysis-section-title">${section.label}</div>
                                        <div class="analysis-section-desc">${section.descText}</div>
                                    </div>
                                </div>
                                <div class="analysis-section-content" id="content-${section.key}">
                                    <span class="text-black/50 text-sm">尚未标记相关内容</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <button id="submit-analysis" onclick="app.submitAnalysis()" class="btn-primary w-full" disabled>完成分析，进入问答</button>
            </div>
        `;

        // Setup selection listener
        const articleText = document.getElementById('article-text');
        if (articleText) {
            articleText.addEventListener('mouseup', (e) => this.handleTextSelection(e));
            articleText.addEventListener('touchend', (e) => this.handleTextSelection(e));
        }

        // Hide toolbar when clicking outside
        document.addEventListener('mousedown', (e) => {
            const toolbar = document.getElementById('highlight-toolbar');
            if (toolbar && !toolbar.contains(e.target)) {
                toolbar.remove();
                this.clearSelection();
            }
        });
    },

    handleTextSelection(e) {
        // Remove existing toolbar
        const existing = document.getElementById('highlight-toolbar');
        if (existing) existing.remove();

        const selection = window.getSelection();
        const text = selection.toString().trim();

        if (!text || text.length < 2) return;

        // Prevent toolbar from showing when clicking toolbar buttons
        if (e.target.closest('#highlight-toolbar')) return;

        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        this.showHighlightToolbar(rect, text);
    },

    showHighlightToolbar(rect, text) {
        const isStar = this.cycle.method === 'STAR';
        const options = isStar
            ? [
                { key: 'S', label: 'S', name: '情境', color: 'green' },
                { key: 'T', label: 'T', name: '任务', color: 'green-light' },
                { key: 'A', label: 'A', name: '行动', color: 'green' },
                { key: 'R', label: 'R', name: '结果', color: 'green-dark' }
            ]
            : [
                { key: 'P', label: 'P', name: '观点', color: 'green' },
                { key: 'R', label: 'R', name: '理由', color: 'green' },
                { key: 'E', label: 'E', name: '例证', color: 'green-light' },
                { key: 'P2', label: 'P', name: '重申', color: 'green-dark' }
            ];

        const toolbar = document.createElement('div');
        toolbar.id = 'highlight-toolbar';
        toolbar.className = 'highlight-toolbar';
        toolbar.innerHTML = options.map(opt => `
            <button class="toolbar-btn" onclick="app.assignHighlight('${opt.key}', '${text.replace(/'/g, "\\'")}')" title="标记为${opt.name}">
                ${opt.label}
            </button>
        `).join('');

        const main = document.getElementById('main');
        const mainRect = main.getBoundingClientRect();

        toolbar.style.left = `${Math.max(10, Math.min(rect.left - mainRect.left + rect.width / 2 - toolbar.offsetWidth / 2, mainRect.width - 150))}px`;
        toolbar.style.top = `${rect.top - mainRect.top - 55}px`;

        main.appendChild(toolbar);

        // Recenter after append
        const toolbarRect = toolbar.getBoundingClientRect();
        toolbar.style.left = `${rect.left - mainRect.left + rect.width / 2 - toolbarRect.width / 2}px`;
    },

    assignHighlight(slot, text) {
        if (!this.selections[slot]) {
            this.selections[slot] = [];
        }
        this.selections[slot].push(text);

        // Wrap selected text in article with highlight class
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            const span = document.createElement('span');
            span.className = `hl-${slot}`;
            try {
                range.surroundContents(span);
            } catch (e) {
                // If selection spans multiple elements, just add to list without wrapping
            }
        }

        this.updateAnalysisSections();
        this.clearSelection();

        const toolbar = document.getElementById('highlight-toolbar');
        if (toolbar) toolbar.remove();

        this.checkAnalysisComplete();
    },

    removeHighlight(slot, index) {
        this.selections[slot].splice(index, 1);
        if (this.selections[slot].length === 0) {
            delete this.selections[slot];
        }
        this.updateAnalysisSections();
        this.checkAnalysisComplete();
    },

    updateAnalysisSections() {
        const isStar = this.cycle.method === 'STAR';
        const sections = isStar
            ? [
                { key: 'S', color: 'green' },
                { key: 'T', color: 'green-light' },
                { key: 'A', color: 'green' },
                { key: 'R', color: 'green-dark' }
            ]
            : [
                { key: 'P', color: 'green' },
                { key: 'R', color: 'green' },
                { key: 'E', color: 'green-light' },
                { key: 'P2', color: 'green-dark' }
            ];

        const chipClasses = {
            green: 'bg-primary/5 text-primary border-primary/20',
            'green-light': 'bg-primary/5 text-primary border-primary/20',
            'green-dark': 'bg-primary/5 text-primary border-primary/20'
        };

        sections.forEach(section => {
            const contentEl = document.getElementById(`content-${section.key}`);
            const items = this.selections[section.key] || [];

            if (items.length === 0) {
                contentEl.innerHTML = '<span class="text-black/50 text-sm">尚未标记相关内容</span>';
                contentEl.classList.remove('has-content');
            } else {
                contentEl.innerHTML = items.map((item, idx) => `
                    <span class="analysis-chip ${chipClasses[section.color]} border">
                        ${item}
                        <span class="remove-chip" onclick="app.removeHighlight('${section.key}', ${idx})">×</span>
                    </span>
                `).join('');
                contentEl.classList.add('has-content');
            }
        });
    },

    resetHighlights() {
        this.selections = {};
        const articleText = document.getElementById('article-text');
        if (articleText) {
            // Remove highlight spans but keep text
            const spans = articleText.querySelectorAll('span[class^="hl-"]');
            spans.forEach(span => {
                const parent = span.parentNode;
                parent.insertBefore(document.createTextNode(span.textContent), span);
                parent.removeChild(span);
            });
        }
        this.updateAnalysisSections();
        this.checkAnalysisComplete();
    },

    clearSelection() {
        window.getSelection().removeAllRanges();
    },

    checkAnalysisComplete() {
        const filled = Object.keys(this.selections).length;
        const btn = document.getElementById('submit-analysis');
        if (filled >= 2) {
            btn.disabled = false;
        } else {
            btn.disabled = true;
        }
    },

    async submitAnalysis() {
        const res = await fetch('/api/drag/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mappings: this.selections })
        });

        if (res.ok) {
            await this.loadUser();
            this.render();
        }
    },

    async swapArticle() {
        const res = await fetch('/api/article/swap', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            this.article = data.article;
            this.renderArticleAndAnalysis(document.getElementById('main'));
        } else {
            alert('没有更多备选文章了');
        }
    },

    // -------------------- Q&A --------------------
    renderQA(container) {
        const isStar = this.cycle.method === 'STAR';
        const question = isStar
            ? `请用 STAR 法则简述：本文主人公面临的核心任务是什么？他采取了哪些关键行动？`
            : `请用 PREP 结构概括：作者的核心观点是什么？他用了什么理由支撑？`;

        container.innerHTML = `
            <div class="fade-in flex flex-col h-full">
                <div class="step-indicator mb-3">
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot active"></div>
                    <div class="step-dot"></div>
                    <div class="step-dot"></div>
                </div>

                <div class="card text-center py-3 px-4 mb-3">
                    <div class="badge badge-accent mb-2 text-xs">问答练习</div>
                    <h2 class="text-lg font-bold mb-2 text-primary leading-relaxed">${question}</h2>
                    <p class="text-xs text-black/60">屏幕不显示原文，请基于记忆口头作答</p>
                </div>

                <div class="card recording-card text-center py-3 px-4 mb-3">
                    <div id="qa-timer" class="timer text-4xl mb-2">00:00</div>
                    <button id="qa-record-btn" onclick="app.toggleRecording('qa')" class="recording-btn w-16 h-16 mx-auto mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                    </button>
                    <p id="qa-record-hint" class="text-xs text-black/60">点击开始录音</p>
                </div>

                <div class="card py-3 px-4 mb-3 flex-1 flex flex-col">
                    <label class="block text-xs font-medium text-black/70 mb-2">或直接输入文字：</label>
                    <textarea id="qa-transcript" class="textarea flex-1" placeholder="在这里输入你的回答..."></textarea>
                </div>

                <div id="qa-feedback" class="hidden feedback-bubble mb-3"></div>

                <button id="qa-next" onclick="app.submitQA()" class="btn-primary w-full">下一步</button>
            </div>
        `;
    },

    recording: {
        active: false,
        module: null,
        startTime: null,
        timerInterval: null
    },

    toggleRecording(module) {
        if (this.recording.active && this.recording.module === module) {
            this.stopRecording(module);
        } else {
            this.startRecording(module);
        }
    },

    startRecording(module) {
        this.recording.active = true;
        this.recording.module = module;
        this.recording.startTime = Date.now();

        const btn = document.getElementById(`${module}-record-btn`);
        const hint = document.getElementById(`${module}-record-hint`);
        if (btn) btn.classList.add('recording');
        if (hint) hint.textContent = '录音中... 再次点击结束';

        this.recording.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recording.startTime) / 1000);
            const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
            const ss = String(elapsed % 60).padStart(2, '0');
            const timerEl = document.getElementById(`${module}-timer`);
            if (timerEl) timerEl.textContent = `${mm}:${ss}`;
        }, 1000);
    },

    stopRecording(module) {
        this.recording.active = false;
        clearInterval(this.recording.timerInterval);

        const btn = document.getElementById(`${module}-record-btn`);
        const hint = document.getElementById(`${module}-record-hint`);
        if (btn) btn.classList.remove('recording');
        if (hint) hint.textContent = '录音已保存';

        const textarea = document.getElementById(`${module}-transcript`);
        if (textarea && !textarea.value.trim()) {
            textarea.value = this.generateMockTranscript(module);
        }
    },

    generateMockTranscript(module) {
        if (!this.article) return '';
        const sentences = this.article.content.split(/[。！？]/).filter(s => s.trim());
        if (module === 'qa') {
            return sentences.slice(0, 2).join('。') + '。';
        } else if (module === 'retell') {
            return this.article.content.substring(0, 120) + '...';
        }
        return '这是我的即兴表达内容...';
    },

    async submitQA() {
        const transcript = document.getElementById('qa-transcript').value.trim();
        if (!transcript) {
            alert('请先输入或录制回答内容');
            return;
        }

        const res = await fetch('/api/qa/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript })
        });

        const data = await res.json();
        const feedbackEl = document.getElementById('qa-feedback');
        if (feedbackEl) {
            feedbackEl.textContent = data.feedback;
            feedbackEl.classList.remove('hidden');
        }

        const nextBtn = document.getElementById('qa-next');
        if (nextBtn) {
            nextBtn.textContent = '进入复述环节';
            nextBtn.onclick = async () => {
                await this.loadUser();
                this.render();
            };
        }
    },

    // -------------------- Retell --------------------
    renderRetell(container) {
        container.innerHTML = `
            <div class="fade-in flex flex-col h-full">
                <div class="step-indicator mb-3">
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot active"></div>
                    <div class="step-dot"></div>
                </div>

                <div class="card text-center py-3 px-4 mb-3">
                    <div class="badge badge-accent mb-2 text-xs">全文复述</div>
                    <h2 class="text-lg font-bold mb-1 text-primary">复述今日文章</h2>
                    <p class="text-xs text-black/60">屏幕隐藏原文，可用关键词辅助记忆</p>
                </div>

                <div class="card text-center py-3 px-4 mb-3">
                    <button onclick="app.showKeywords()" class="btn-secondary w-full text-sm py-2 px-4 mb-2">点击显示关键词</button>
                    <div id="keywords-area" class="hidden text-xs text-primary bg-primary/5 p-2 rounded-xl font-medium"></div>
                </div>

                <div class="card recording-card text-center py-3 px-4 mb-3">
                    <div id="retell-timer" class="timer text-4xl mb-2">00:00</div>
                    <button id="retell-record-btn" onclick="app.toggleRecording('retell')" class="recording-btn w-16 h-16 mx-auto mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                    </button>
                    <p id="retell-record-hint" class="text-xs text-black/60">点击开始复述</p>
                </div>

                <div class="card py-3 px-4 mb-3 flex-1 flex flex-col">
                    <label class="block text-xs font-medium text-black/70 mb-2">或直接输入文字：</label>
                    <textarea id="retell-transcript" class="textarea flex-1" placeholder="在这里输入你的复述..."></textarea>
                </div>

                <div id="retell-feedback" class="hidden mb-3"></div>

                <button id="retell-next" onclick="app.submitRetell()" class="btn-primary w-full">完成复述</button>
            </div>
        `;
    },

    showKeywords() {
        if (!this.article) return;
        const keywords = this.article.keywords.split('，').join(' · ');
        const el = document.getElementById('keywords-area');
        if (el) {
            el.textContent = keywords;
            el.classList.remove('hidden');
        }
    },

    async submitRetell() {
        const transcript = document.getElementById('retell-transcript').value.trim();
        if (!transcript) {
            alert('请先输入或录制复述内容');
            return;
        }

        const res = await fetch('/api/retell/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript })
        });

        const data = await res.json();
        const fb = data.result;
        const fbEl = document.getElementById('retell-feedback');
        if (!fbEl) return;

        if (fb.suggestion && fb.polish) {
            fbEl.innerHTML = `
                <div class="feedback-bubble mb-3">【建议】${fb.suggestion}</div>
                <div class="card bg-black/5">
                    <h4 class="font-bold mb-2 text-primary">【润色】</h4>
                    <p class="text-sm leading-relaxed text-black/70">${fb.polish}</p>
                    <p class="text-sm font-medium mt-3" style="color: var(--accent)">${fb.comfort}</p>
                </div>
            `;
        } else {
            fbEl.innerHTML = `<div class="feedback-bubble">【建议】${fb.suggestion || fb}</div>`;
        }
        fbEl.classList.remove('hidden');

        const nextBtn = document.getElementById('retell-next');
        if (nextBtn) {
            nextBtn.textContent = '进入主动输出';
            nextBtn.onclick = async () => {
                await this.loadUser();
                this.render();
            };
        }
    },

    // -------------------- Free Output --------------------
    renderFreeOutput(container) {
        const topics = [
            { t: '分享一次你主导团队协作的经历', icon: '🤝' },
            { t: '描述一件让你改变看法的事', icon: '💭' },
            { t: '说说你最近学到的一项新技能', icon: '📚' },
            { t: '介绍一个你敬佩的人', icon: '⭐' },
            { t: '谈谈你对远程办公的看法', icon: '🏠' }
        ];

        container.innerHTML = `
            <div class="fade-in">
                <div class="step-indicator">
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot active"></div>
                </div>

                <div class="card text-center">
                    <div class="badge badge-accent mb-3">主动输出</div>
                    <h2 class="text-xl font-bold mb-2 text-primary">即兴表达</h2>
                    <p class="text-sm text-black/60">选择一个主题，自由表达 1-2 分钟</p>
                </div>

                <div class="card">
                    <h3 class="font-bold mb-3 text-primary">推荐主题</h3>
                    <div class="space-y-2">
                        ${topics.map((item) => `
                            <button onclick="app.selectTopic('${item.t.replace(/'/g, "\\'")}')" class="topic-btn" data-topic="${item.t.replace(/"/g, '&quot;')}">
                                <div class="flex items-center gap-3">
                                    <span class="text-xl">${item.icon}</span>
                                    <div class="flex-1">
                                        <div class="text-sm font-medium text-black/80">${item.t}</div>
                                        <div class="text-xs text-black/50 mt-1">建议用 ${this.cycle.method} 框架</div>
                                    </div>
                                </div>
                            </button>
                        `).join('')}
                    </div>
                    <input type="hidden" id="free-topic" value="">
                </div>

                <div class="card recording-card text-center">
                    <div id="free-timer" class="timer mb-4">00:00</div>
                    <button id="free-record-btn" onclick="app.toggleRecording('free')" class="recording-btn mx-auto mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                    </button>
                    <p id="free-record-hint" class="text-sm text-black/60">点击开始录音</p>
                </div>

                <div class="card">
                    <label class="block text-sm font-medium text-black/70 mb-2">或直接输入文字：</label>
                    <textarea id="free-transcript" rows="4" class="textarea" placeholder="在这里输入你的即兴表达..."></textarea>
                </div>

                <div id="free-feedback" class="hidden"></div>

                <button id="free-finish" onclick="app.submitFree()" class="btn-primary w-full">完成今日训练</button>
            </div>
        `;
    },

    selectTopic(topic) {
        document.getElementById('free-topic').value = topic;
        document.querySelectorAll('.topic-btn').forEach(btn => {
            if (btn.dataset.topic === topic) {
                btn.classList.add('selected');
            } else {
                btn.classList.remove('selected');
            }
        });
    },

    async submitFree() {
        const transcript = document.getElementById('free-transcript').value.trim();
        const topic = document.getElementById('free-topic').value || '自由主题';

        if (!transcript) {
            alert('请先输入或录制表达内容');
            return;
        }

        const res = await fetch('/api/free/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript, topic })
        });

        const data = await res.json();
        const fb = data.result;
        const fbEl = document.getElementById('free-feedback');
        if (!fbEl) return;

        fbEl.innerHTML = `
            <div class="feedback-bubble mb-3">【建议】${fb.suggestion}</div>
            <div class="card bg-black/5">
                <h4 class="font-bold mb-3 text-primary">详细报告</h4>
                <div class="space-y-2 text-sm mb-4">
                    <div class="flex justify-between items-center py-2 border-b border-black/5"><span class="text-black/60">主题相关</span><span class="font-medium text-primary">${fb.metrics_display.relevance_feedback}</span></div>
                    <div class="flex justify-between items-center py-2 border-b border-black/5"><span class="text-black/60">结构框架</span><span class="font-medium text-primary">${fb.metrics_display.structure_feedback}</span></div>
                    <div class="flex justify-between items-center py-2 border-b border-black/5"><span class="text-black/60">观点密度</span><span class="font-medium text-primary">${fb.metrics_display.density_feedback}</span></div>
                    <div class="flex justify-between items-center py-2"><span class="text-black/60">语言习惯</span><span class="font-medium text-primary">${fb.metrics_display.habit_feedback}</span></div>
                </div>
                <div class="p-3 bg-white rounded-lg text-sm text-black/70 leading-relaxed">
                    <strong class="text-primary">润色版：</strong>${fb.rewrite}
                </div>
                <p class="text-sm font-medium mt-3" style="color: var(--accent)">${fb.comfort_message}</p>
            </div>
        `;
        fbEl.classList.remove('hidden');

        const finishBtn = document.getElementById('free-finish');
        if (finishBtn) {
            finishBtn.textContent = '查看今日总结';
            finishBtn.onclick = () => {
                this.state = 'day_complete';
                this.render();
            };
        }
    },

    // -------------------- Day Complete --------------------
    renderDayComplete(container) {
        const totalDays = this.cycle ? this.cycle.total_days : 4;
        const currentDay = this.cycle ? this.cycle.current_day : 1;
        const isLastDay = currentDay >= totalDays;
        const progress = Math.round((currentDay / totalDays) * 100);

        container.innerHTML = `
            <div class="fade-in text-center py-8">
                <div class="w-20 h-20 bg-gradient-to-br from-accent to-accent-light rounded-full mx-auto mb-6 flex items-center justify-center text-white text-3xl shadow-lg">🎉</div>
                <h2 class="text-2xl font-bold mb-3 text-primary">${isLastDay ? '周期完成！' : '今日训练完成！'}</h2>
                <p class="text-black/60 mb-8 px-4">
                    ${isLastDay
                        ? '你已经完成了当前方法的全部训练，可以解锁新方法。'
                        : `今天是第 ${currentDay}/${totalDays} 天，明天继续加油！`}
                </p>

                <div class="card mb-6 text-left">
                    <h3 class="font-bold mb-3 text-primary">周期进度</h3>
                    <div class="progress-bar mb-3">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div class="flex justify-between text-sm text-black/60">
                        <span>第 ${currentDay} 天</span>
                        <span>${progress}%</span>
                    </div>
                </div>

                <div class="card mb-6 text-left">
                    <h3 class="font-bold mb-3 text-primary">今日打卡</h3>
                    <div class="grid grid-cols-5 gap-2 text-center text-xs">
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">方法<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">分析<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">问答<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">复述<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">输出<br>✓</div>
                    </div>
                </div>

                <button onclick="app.nextDay()" class="btn-primary w-full">
                    ${isLastDay ? '解锁新方法' : '进入下一天'}
                </button>
            </div>
        `;
    },

    async nextDay() {
        const res = await fetch('/api/day/complete', { method: 'POST' });
        const data = await res.json();
        await this.loadUser();
        this.render();
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
