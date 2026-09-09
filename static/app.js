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
        // Always land on the home page when the app first loads;
        // users can continue training from there.
        this.state = 'home';
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

        // Keep footer in sync with current cycle state
        this.updateFooter();

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
                            <div class="font-bold text-primary text-sm">${cycle.method} 法则 · 第 ${cycle.current_day} 篇</div>
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
            { key: 'S', name: '情境', en: 'Situation', desc: '先交代背景：时间、地点、人物、环境。让对方快速理解这件事发生的前提。', tip: '例如：去年 Q3，我们团队负责一款新产品的上线。' },
            { key: 'T', name: '任务', en: 'Task', desc: '明确你面临的具体目标或挑战。让听众知道你要解决什么问题。', tip: '例如：我的任务是在两周内把用户激活率提升 20%。' },
            { key: 'A', name: '行动', en: 'Action', desc: '讲述你采取的关键动作，以及为什么这样选择。突出你的思考过程。', tip: '例如：我重新梳理了 onboarding 流程，并做了三轮 A/B 测试。' },
            { key: 'R', name: '结果', en: 'Result', desc: '用数据和事实收尾。最好能量化成果，让表达有说服力。', tip: '例如：最终激活率提升了 27%，超出预期。' }
        ] : [
            { key: 'P', name: '观点', en: 'Point', desc: '先亮明立场，让人第一时间知道你的核心看法。', tip: '例如：我认为远程办公会常态化。' },
            { key: 'R', name: '理由', en: 'Reason', desc: '给出 2-3 条支撑理由，建立清晰的逻辑骨架。', tip: '例如：第一，人才不再受地域限制；第二，企业成本更低。' },
            { key: 'E', name: '例证', en: 'Example', desc: '用案例、数据或故事让理由更具体、可信。', tip: '例如：某互联网公司在全面远程后，招聘效率提升了 40%。' },
            { key: 'P', name: '重申', en: 'Point', desc: '回扣观点，强化记忆点，让听众带走一个清晰结论。', tip: '例如：因此，企业应该主动拥抱远程办公。' }
        ];

        container.innerHTML = `
            <div class="fade-in flex flex-col h-full">
                <div class="text-center mb-3">
                    <div class="badge badge-accent mb-1 text-xs">第 1 步：方法学习</div>
                    <h2 class="text-xl font-bold text-primary mb-1">${title}</h2>
                    <p class="text-xs text-black/60">${subtitle}</p>
                </div>

                <div class="flex-1 overflow-y-auto pr-1 mb-3 space-y-2">
                    ${steps.map((step, idx) => `
                        <div class="card p-3">
                            <div class="flex items-center gap-3 mb-2">
                                <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center text-lg font-bold shrink-0">${step.key}</div>
                                <div>
                                    <h3 class="font-bold text-base text-primary">${step.name}</h3>
                                    <p class="text-xs text-black/40">${step.en}</p>
                                </div>
                            </div>
                            <p class="text-sm text-black/70 leading-relaxed mb-2">${step.desc}</p>
                            <p class="text-xs text-primary/80 bg-primary/5 p-2 rounded-lg">${step.tip}</p>
                        </div>
                    `).join('')}
                </div>

                <button onclick="app.finishMethodLearning()" class="btn-primary w-full shrink-0">我已掌握，开始实战</button>
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
                            <div class="badge badge-accent mb-2">第 ${this.cycle.current_day} 篇 · 内容实战</div>
                            <h2 class="text-xl font-bold text-primary leading-tight">${this.article.title}</h2>
                        </div>
                        <button onclick="app.swapArticle()" class="btn-outline shrink-0 ml-3">换一篇</button>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-black/50 mb-2">
                        <span class="badge badge-green">${this.cycle.method}</span>
                        <span>${this.article.content.length} 字</span>
                    </div>
                    <p class="text-xs text-black/40 mb-2">对文章文字划线，选择对应的部分</p>
                    <div id="article-text" class="article-content select-text">
                        ${this.article.content}
                    </div>
                </div>

                <div class="card">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3 class="font-bold text-lg text-primary">结构分析</h3>
                            <p class="text-sm text-black/60">对文章文字划线，选择对应的 ${this.cycle.method} 部分</p>
                        </div>
                        <button onclick="app.resetHighlights()" class="btn-outline text-xs reset-highlights-btn">清除<br>标记</button>
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
        // Prevent toolbar from showing when clicking toolbar buttons
        if (e && e.target && e.target.closest('#highlight-toolbar')) return;

        // Delay to let mobile selection settle
        setTimeout(() => {
            const selection = window.getSelection();
            const text = selection.toString().trim();

            if (!text || text.length < 2) return;

            // Only allow selection inside article-text
            const anchor = selection.anchorNode;
            if (!anchor) return;
            const articleText = document.getElementById('article-text');
            if (!articleText || !articleText.contains(anchor)) return;

            // Remove existing toolbar
            const existing = document.getElementById('highlight-toolbar');
            if (existing) existing.remove();

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return;

            this.showHighlightToolbar(rect, text);
        }, e && e.type === 'touchend' ? 120 : 50);
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

        const data = await res.json();

        if (data.success) {
            await this.loadUser();
            this.render();
        } else {
            this.showDragCorrections(data.slots || {}, data.message);
        }
    },

    showDragCorrections(slots, message) {
        // Separate correct (>=90%) and incorrect slots
        const incorrectSlots = {};
        const correctSlots = [];
        Object.entries(slots).forEach(([slot, info]) => {
            if (info && info.correct) {
                correctSlots.push(slot);
            } else {
                incorrectSlots[slot] = info ? info.correct_text : '';
            }
        });

        // Clear only incorrect highlights; keep correct user highlights
        this.resetHighlightsForSlots(Object.keys(incorrectSlots));

        // Highlight the correct text spans inside the article using plain-text positions
        this.highlightCorrectSpans(incorrectSlots);

        // For incorrect slots, show the correct text as a chip without "参考：" prefix
        Object.entries(incorrectSlots).forEach(([slot, text]) => {
            if (!text) return;
            const contentEl = document.getElementById(`content-${slot}`);
            if (!contentEl) return;
            contentEl.innerHTML = `
                <span class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
                    ${text}
                </span>
            `;
        });

        // Show correction banner
        let banner = document.getElementById('drag-correction-banner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'drag-correction-banner';
            banner.className = 'card drag-correction-banner mb-3';
            const analysisCard = document.querySelector('.analysis-section')?.closest('.card');
            if (analysisCard && analysisCard.parentNode) {
                analysisCard.parentNode.insertBefore(banner, analysisCard);
            }
        }
        banner.innerHTML = `
            <p class="text-sm font-medium">${message}</p>
            <p class="text-xs text-black/60 mt-1">橙色标注为正确结构，对照后可继续练习</p>
        `;

        // Change submit button to allow proceeding after review
        const btn = document.getElementById('submit-analysis');
        if (btn) {
            btn.disabled = false;
            btn.textContent = '我已对照，继续练习';
            btn.onclick = async () => {
                await fetch('/api/drag/force-complete', { method: 'POST' });
                await this.loadUser();
                this.render();
            };
        }
    },

    resetHighlightsForSlots(slotsToReset) {
        const articleText = document.getElementById('article-text');
        if (!articleText || slotsToReset.length === 0) return;
        const classes = slotsToReset.map(s => `hl-${s}`);
        const spans = articleText.querySelectorAll(classes.map(c => `span.${c}`).join(', '));
        spans.forEach(span => {
            const parent = span.parentNode;
            parent.replaceChild(document.createTextNode(span.textContent), span);
            parent.normalize();
        });
    },

    normalizeText(text) {
        return text.replace(/\s+/g, ' ').trim();
    },

    highlightCorrectSpans(correctTexts) {
        const articleText = document.getElementById('article-text');
        if (!articleText || !correctTexts) return;

        const plainText = articleText.textContent;
        const normalizedPlain = this.normalizeText(plainText);
        const spans = [];

        Object.entries(correctTexts).forEach(([slot, text]) => {
            if (!text || text.length < 2) return;
            const normalizedTarget = this.normalizeText(text);
            if (!normalizedTarget) return;

            // Try to find the target in the normalized plain text
            let idx = normalizedPlain.indexOf(normalizedTarget);
            if (idx === -1) {
                // Fallback: try shorter leading substring
                const half = Math.floor(normalizedTarget.length / 2);
                const shortTarget = normalizedTarget.slice(0, Math.max(half, 8));
                idx = normalizedPlain.indexOf(shortTarget);
            }
            if (idx === -1) return;

            // Map normalized position back to raw text position by counting non-whitespace chars
            let rawStart = 0;
            let normCount = 0;
            for (let i = 0; i < plainText.length && normCount < idx; i++) {
                if (/\S/.test(plainText[i])) {
                    normCount++;
                }
                rawStart++;
            }

            let rawEnd = rawStart;
            let targetNormCount = 0;
            const targetLen = normalizedTarget.length;
            for (let i = rawStart; i < plainText.length && targetNormCount < targetLen; i++) {
                if (/\S/.test(plainText[i])) {
                    targetNormCount++;
                }
                rawEnd++;
            }

            spans.push({ start: rawStart, end: rawEnd, slot });
        });

        if (spans.length === 0) return;

        // Sort by start position; prefer longer spans when overlaps occur
        spans.sort((a, b) => a.start - b.start || b.end - a.end);
        const merged = [];
        for (const span of spans) {
            if (merged.length === 0 || span.start >= merged[merged.length - 1].end) {
                merged.push(span);
            } else if (span.end > merged[merged.length - 1].end) {
                merged[merged.length - 1].end = span.end;
                merged[merged.length - 1].slot = span.slot; // last one wins in overlap
            }
        }

        // Rebuild HTML by wrapping text ranges
        let html = '';
        let lastEnd = 0;
        for (const span of merged) {
            html += this.escapeHtml(plainText.slice(lastEnd, span.start));
            html += `<span class="hl-correct hl-correct-${span.slot.toLowerCase()}">${this.escapeHtml(plainText.slice(span.start, span.end))}</span>`;
            lastEnd = span.end;
        }
        html += this.escapeHtml(plainText.slice(lastEnd));
        articleText.innerHTML = html;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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
                    <p class="text-xs text-black/60">请基于记忆口头作答</p>
                </div>

                <div class="card recording-card py-3 px-4 mb-3">
                    <div class="flex flex-col items-center justify-center gap-2 mb-2">
                        <div id="qa-timer" class="timer text-4xl">00:00</div>
                        <button id="qa-record-btn" onclick="app.toggleRecording('qa')" class="recording-btn w-16 h-16">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        </button>
                    </div>
                    <div class="flex items-center justify-center gap-3">
                        <p id="qa-record-hint" class="text-xs text-black/60">点击开始录音</p>
                        <button onclick="app.restartRecording('qa')" class="text-xs text-primary underline">重新录音</button>
                    </div>
                </div>

                <div class="card py-3 px-4 mb-3 flex-1 flex flex-col">
                    <label class="block text-xs font-medium text-black/70 mb-2">输入文字（语音将自动识别为文字）：</label>
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
        timerInterval: null,
        recognition: null,
        finalTranscript: '',
        interimTranscript: '',
        hasSpeech: false,
        totalElapsed: 0
    },

    toggleRecording(module) {
        if (this.recording.active && this.recording.module === module) {
            this.stopRecording(module);
        } else {
            if (this.recording.active) {
                this.stopRecording(this.recording.module);
            }
            this.startRecording(module);
        }
    },

    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return null;
        const recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onresult = (event) => {
            let interim = '';
            let final = '';
            let heardSomething = false;
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (transcript.trim()) heardSomething = true;
                if (event.results[i].isFinal) {
                    final += transcript;
                } else {
                    interim += transcript;
                }
            }
            if (heardSomething) this.recording.hasSpeech = true;
            this.recording.finalTranscript += final;
            this.recording.interimTranscript = interim;
            const textarea = document.getElementById(`${this.recording.module}-transcript`);
            if (textarea) {
                textarea.value = this.recording.finalTranscript + this.recording.interimTranscript;
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            if (event.error === 'not-allowed') {
                alert('请允许使用麦克风权限，或选择直接输入文字。');
                this.stopRecording(this.recording.module);
            }
        };

        recognition.onend = () => {
            if (this.recording.active && this.recording.recognition) {
                try { this.recording.recognition.start(); } catch(e) {}
            }
        };

        return recognition;
    },

    startRecording(module) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert('当前浏览器不支持语音识别，请直接输入文字练习。');
            return;
        }

        this.recording.active = true;
        this.recording.module = module;
        this.recording.startTime = Date.now();
        this.recording.interimTranscript = '';
        this.recording.hasSpeech = false;

        // Continue from existing transcript (manual input or previous recording)
        const textarea = document.getElementById(`${module}-transcript`);
        this.recording.finalTranscript = textarea ? (textarea.value || '') : '';

        const recognition = this.initSpeechRecognition();
        this.recording.recognition = recognition;
        try {
            recognition.start();
        } catch(e) {
            console.error('Failed to start recognition', e);
            this.recording.active = false;
            return;
        }

        const btn = document.getElementById(`${module}-record-btn`);
        const hint = document.getElementById(`${module}-record-hint`);
        if (btn) btn.classList.add('recording');
        if (hint) hint.textContent = '录音中... 再次点击结束';

        this.recording.timerInterval = setInterval(() => {
            const sessionElapsed = Math.floor((Date.now() - this.recording.startTime) / 1000);
            const total = this.recording.totalElapsed + sessionElapsed;
            const mm = String(Math.floor(total / 60)).padStart(2, '0');
            const ss = String(total % 60).padStart(2, '0');
            const timerEl = document.getElementById(`${module}-timer`);
            if (timerEl) timerEl.textContent = `${mm}:${ss}`;
        }, 1000);
    },

    stopRecording(module) {
        this.recording.active = false;
        clearInterval(this.recording.timerInterval);

        // Save elapsed time of this session so the next start continues the timer
        const sessionElapsed = Math.floor((Date.now() - this.recording.startTime) / 1000);
        this.recording.totalElapsed += sessionElapsed;

        // Finalize any interim transcript into the textarea
        this.recording.finalTranscript += this.recording.interimTranscript;
        this.recording.interimTranscript = '';
        const textarea = document.getElementById(`${module}-transcript`);
        if (textarea) textarea.value = this.recording.finalTranscript;

        if (this.recording.recognition) {
            try { this.recording.recognition.stop(); } catch(e) {}
            this.recording.recognition = null;
        }

        // Warn if no speech was recognized in this session
        if (!this.recording.hasSpeech) {
            alert('未识别出文字');
        }

        const btn = document.getElementById(`${module}-record-btn`);
        const hint = document.getElementById(`${module}-record-hint`);
        if (btn) btn.classList.remove('recording');
        if (hint) hint.textContent = '录音已暂停，再次点击继续录音';
    },

    restartRecording(module) {
        if (!confirm('是否重新录音？之前的录音内容将被清空。')) return;
        const textarea = document.getElementById(`${module}-transcript`);
        if (textarea) textarea.value = '';
        this.recording.finalTranscript = '';
        this.recording.totalElapsed = 0;
        if (this.recording.active) {
            this.stopRecording(module);
        }
        // Reset timer display immediately
        const timerEl = document.getElementById(`${module}-timer`);
        if (timerEl) timerEl.textContent = '00:00';
        setTimeout(() => this.startRecording(module), 300);
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

                <div class="card recording-card py-3 px-4 mb-3">
                    <div class="flex flex-col items-center justify-center gap-2 mb-2">
                        <div id="retell-timer" class="timer text-4xl">00:00</div>
                        <button id="retell-record-btn" onclick="app.toggleRecording('retell')" class="recording-btn w-16 h-16">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        </button>
                    </div>
                    <div class="flex items-center justify-center gap-3">
                        <p id="retell-record-hint" class="text-xs text-black/60">点击开始复述</p>
                        <button onclick="app.restartRecording('retell')" class="text-xs text-primary underline">重新录音</button>
                    </div>
                </div>

                <div class="card py-3 px-4 mb-3 flex-1 flex flex-col">
                    <label class="block text-xs font-medium text-black/70 mb-2">输入文字（语音将自动识别为文字）：</label>
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
                <div class="feedback-bubble mb-3">${fb.suggestion}</div>
                <div class="card retell-polish-card">
                    <h4 class="font-bold mb-2 text-primary">润色参考</h4>
                    <p class="text-sm leading-relaxed text-black/70 retell-polish-text">${fb.polish}</p>
                    <p class="text-sm font-medium mt-3" style="color: var(--accent)">${fb.comfort}</p>
                </div>
            `;
        } else {
            fbEl.innerHTML = `<div class="feedback-bubble">${fb.suggestion || fb}</div>`;
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
    topicPool: [
        '分享一次你主导团队协作的经历',
        '描述一件让你改变看法的事',
        '说说你最近学到的一项新技能',
        '介绍一个你敬佩的人',
        '谈谈你对远程办公的看法',
        '讲述一次失败及你从中学到的东西',
        '如果给你一个月假期，你会做什么',
        '描述一次你化解冲突的经历',
        '介绍一本对你影响很大的书',
        '谈谈你对人工智能的看法',
        '分享一次你主动争取机会的经历',
        '描述你理想的工作状态',
        '说说你保持专注的方法',
        '介绍一个你喜欢的城市',
        '谈谈你遇到过最大的挑战'
    ],

    getUsedTopics() {
        try {
            return JSON.parse(localStorage.getItem('expressionPro_usedTopics') || '[]');
        } catch (e) {
            return [];
        }
    },

    markTopicUsed(topic) {
        const used = this.getUsedTopics();
        if (!used.includes(topic)) {
            used.push(topic);
            // Keep last 30 to avoid running out
            if (used.length > 30) used.shift();
            localStorage.setItem('expressionPro_usedTopics', JSON.stringify(used));
        }
    },

    getRandomTopics(count = 5) {
        const used = this.getUsedTopics();
        const available = this.topicPool.filter(t => !used.includes(t));
        const pool = available.length >= count ? available : this.topicPool;
        const shuffled = [...pool].sort(() => Math.random() - 0.5);
        return shuffled.slice(0, count);
    },

    formatMetricLabel(label) {
        // Split 4-character metric labels into two 2-character lines
        if (label && label.length === 4) {
            return `${label.slice(0, 2)}<br>${label.slice(2, 4)}`;
        }
        return label;
    },

    renderFreeOutput(container) {
        const topics = this.getRandomTopics();
        const method = this.cycle ? this.cycle.method : 'STAR';

        container.innerHTML = `
            <div class="fade-in flex flex-col h-full">
                <div class="step-indicator mb-3">
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot completed"></div>
                    <div class="step-dot active"></div>
                </div>

                <div class="card text-center py-3 px-4 mb-3">
                    <div class="badge badge-accent mb-2 text-xs">主动输出</div>
                    <h2 class="text-lg font-bold mb-1 text-primary">即兴表达</h2>
                    <p class="text-xs text-black/60">输入话题，自由表达 1-2 分钟</p>
                </div>

                <div class="card py-3 px-4 mb-3">
                    <label class="block text-xs font-medium text-black/70 mb-2">今天想练习什么话题？</label>
                    <div class="relative">
                        <input type="text" id="free-topic-input" class="textarea py-3 pr-20" placeholder="输入你想说的话题..." value="">
                        <button onclick="app.toggleTopicSuggestions()" class="absolute right-3 bottom-3 text-xs text-primary underline">没想法？</button>
                    </div>
                    <div id="topic-suggestions" class="hidden mt-3 pt-3 border-t border-primary/10">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-xs font-medium text-black/70">推荐话题</span>
                            <button onclick="app.refreshTopicSuggestions()" class="text-xs text-primary underline">换一换</button>
                        </div>
                        <div class="space-y-2" id="topic-list">
                            ${topics.map(t => `
                                <button onclick="app.useSuggestedTopic('${t.replace(/'/g, "\\'")}')" class="topic-btn text-left text-sm py-2 px-3 rounded-xl border border-primary/10 bg-white hover:bg-primary/5 transition-colors w-full">
                                    ${t}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="card recording-card py-3 px-4 mb-3">
                    <div class="flex flex-col items-center justify-center gap-2 mb-2">
                        <div id="free-timer" class="timer text-4xl">00:00</div>
                        <button id="free-record-btn" onclick="app.toggleRecording('free')" class="recording-btn w-16 h-16">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        </button>
                    </div>
                    <div class="flex items-center justify-center gap-3">
                        <p id="free-record-hint" class="text-xs text-black/60">点击开始录音</p>
                        <button onclick="app.restartRecording('free')" class="text-xs text-primary underline">重新录音</button>
                    </div>
                    <p class="text-center text-xs text-black/40 mt-2">建议用 ${method} 框架组织表达</p>
                </div>

                <div class="card py-3 px-4 mb-3 flex-1 flex flex-col">
                    <label class="block text-xs font-medium text-black/70 mb-2">输入文字（语音将自动识别为文字）：</label>
                    <textarea id="free-transcript" class="textarea flex-1" placeholder="在这里输入你的即兴表达..."></textarea>
                </div>

                <div id="free-feedback" class="hidden mb-3"></div>

                <button id="free-finish" onclick="app.submitFree()" class="btn-primary w-full">完成今日训练</button>
            </div>
        `;
    },

    toggleTopicSuggestions() {
        const panel = document.getElementById('topic-suggestions');
        if (panel) {
            panel.classList.toggle('hidden');
            if (!panel.classList.contains('hidden')) {
                this.refreshTopicSuggestions();
            }
        }
    },

    refreshTopicSuggestions() {
        const list = document.getElementById('topic-list');
        if (!list) return;
        const topics = this.getRandomTopics();
        list.innerHTML = topics.map(t => `
            <button onclick="app.useSuggestedTopic('${t.replace(/'/g, "\\'")}')" class="topic-btn text-left text-sm py-2 px-3 rounded-xl border border-primary/10 bg-white hover:bg-primary/5 transition-colors w-full">
                ${t}
            </button>
        `).join('');
    },

    useSuggestedTopic(topic) {
        const input = document.getElementById('free-topic-input');
        if (input) input.value = topic;
        const panel = document.getElementById('topic-suggestions');
        if (panel) panel.classList.add('hidden');
        // Mark as used so it won't appear in future "换一换"
        this.markTopicUsed(topic);
    },

    async submitFree() {
        const transcript = document.getElementById('free-transcript').value.trim();
        const topicInput = document.getElementById('free-topic-input');
        const topic = (topicInput ? topicInput.value : '') || '自由主题';

        if (!transcript) {
            alert('请先输入或录制表达内容');
            return;
        }

        // Mark topic as used so suggestions won't repeat it
        if (topic !== '自由主题') {
            this.markTopicUsed(topic);
        }

        const res = await fetch('/api/free/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript, topic })
        });

        const data = await res.json();
        const fb = data.result;
        if (data.cycle) {
            this.cycle = data.cycle;
        }
        const fbEl = document.getElementById('free-feedback');
        if (!fbEl) return;

        fbEl.innerHTML = `
            <div class="feedback-bubble mb-3">${fb.suggestion}</div>
            <div class="card free-report-card">
                <h4 class="font-bold mb-3 text-primary">详细报告</h4>
                <div class="space-y-2 text-sm mb-4">
                    <div class="flex justify-between items-center py-2 border-b border-black/5">
                        <span class="metric-label text-black/60">${this.formatMetricLabel('主题相关')}</span>
                        <span class="font-medium text-primary text-right flex-1 ml-2">${fb.metrics_display.relevance_feedback}</span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-black/5">
                        <span class="metric-label text-black/60">${this.formatMetricLabel('结构框架')}</span>
                        <span class="font-medium text-primary text-right flex-1 ml-2">${fb.metrics_display.structure_feedback}</span>
                    </div>
                    <div class="flex justify-between items-center py-2 border-b border-black/5">
                        <span class="metric-label text-black/60">${this.formatMetricLabel('观点密度')}</span>
                        <span class="font-medium text-primary text-right flex-1 ml-2">${fb.metrics_display.density_feedback}</span>
                    </div>
                    <div class="flex justify-between items-center py-2">
                        <span class="metric-label text-black/60">${this.formatMetricLabel('语言习惯')}</span>
                        <span class="font-medium text-primary text-right flex-1 ml-2">${fb.metrics_display.habit_feedback}</span>
                    </div>
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
    updateFooter() {
        const footer = document.getElementById('footer-nav');
        const footerDay = document.getElementById('footer-day');
        if (this.cycle && this.state !== 'home') {
            footer?.classList.remove('hidden');
            // Show current article number in sequence (1-based)
            const currentArticle = (this.cycle.completed_articles_count || 0) + 1;
            if (footerDay) footerDay.textContent = currentArticle;
        } else {
            footer?.classList.add('hidden');
        }
    },

    renderDayComplete(container) {
        const totalDays = this.cycle ? this.cycle.total_days : 4;
        const currentDay = this.cycle ? this.cycle.current_day : 1;
        const isLastDay = currentDay >= totalDays;
        // Use the actual count of completed articles for display
        const completedCount = this.cycle ? (this.cycle.completed_articles_count || 0) : 0;
        const progress = Math.min(100, Math.round((completedCount / totalDays) * 100));

        container.innerHTML = `
            <div class="fade-in text-center py-8">
                <div class="w-20 h-20 bg-gradient-to-br from-accent to-accent-light rounded-full mx-auto mb-6 flex items-center justify-center text-white text-3xl shadow-lg">🎉</div>
                <h2 class="text-2xl font-bold mb-3 text-primary">${isLastDay ? '周期完成！' : '本篇训练完成！'}</h2>
                <p class="text-black/60 mb-8 px-4">
                    ${isLastDay
                        ? '你已经完成了当前方法的全部训练，可以解锁新方法，也可以再巩固一篇。'
                        : `已完成 ${completedCount}/${totalDays} 篇，继续加油！`}
                </p>

                <div class="card mb-6 text-left">
                    <h3 class="font-bold mb-3 text-primary">周期进度</h3>
                    <div class="progress-bar mb-3">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div class="flex justify-between text-sm text-black/60">
                        <span>已完成 ${completedCount}/${totalDays} 篇</span>
                        <span>${progress}%</span>
                    </div>
                </div>

                <div class="card mb-6 text-left">
                    <h3 class="font-bold mb-3 text-primary">本篇打卡</h3>
                    <div class="grid grid-cols-5 gap-2 text-center text-xs">
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">方法<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">分析<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">问答<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">复述<br>✓</div>
                        <div class="p-2 rounded-lg bg-primary/5 text-primary font-medium">输出<br>✓</div>
                    </div>
                </div>

                <div class="space-y-3">
                    ${isLastDay ? `
                        <button onclick="app.unlockNewMethod()" class="btn-primary w-full">解锁新方法</button>
                        <button onclick="app.retrySameMethod()" class="btn-secondary w-full">再学一篇本方法</button>
                    ` : `
                        <button onclick="app.nextDay()" class="btn-primary w-full">完成</button>
                        <button onclick="app.retryDay()" class="btn-secondary w-full">再练一篇</button>
                    `}
                </div>
            </div>
        `;
    },

    async nextDay() {
        const res = await fetch('/api/day/complete', { method: 'POST' });
        const data = await res.json();
        await this.loadUser();
        this.render();
    },

    async retryDay() {
        // Stay on current day, reset today's progress and start a new article
        const res = await fetch('/api/day/retry', { method: 'POST' });
        if (res.ok) {
            await this.loadUser();
            this.render();
        }
    },

    async unlockNewMethod() {
        const res = await fetch('/api/day/complete', { method: 'POST' });
        if (res.ok) {
            await this.loadUser();
            this.state = 'select_method';
            this.render();
        }
    },

    async retrySameMethod() {
        const res = await fetch('/api/day/retry-method', { method: 'POST' });
        if (res.ok) {
            await this.loadUser();
            this.render();
        }
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
