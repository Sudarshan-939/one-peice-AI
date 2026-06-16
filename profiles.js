document.addEventListener('DOMContentLoaded', () => {

    /**
     * Helper to render nice UI cards based on the source data
     */
    function renderUICard(data, sourceId) {
        if (!data) return '<p>No data available</p>';
        try {
            if (sourceId === 'output-github') {
                const user = data.data ? data.data : data;
                if (!user) return '<p>No user data</p>';
                return `
                    <div class="profile-card">
                        <div class="profile-header">
                            <img src="${user.avatar_url}" class="profile-avatar" alt="Avatar">
                            <div class="profile-title">
                                <h4>${user.name || user.username}</h4>
                                <p><a href="${user.profile_url}" target="_blank" style="color:var(--accent-color)">@${user.username}</a></p>
                            </div>
                        </div>
                        <p style="font-size: 0.8rem; margin: 0;">${user.bio || 'No bio'}</p>
                        <div class="profile-stats">
                            <div class="stat-badge"><strong>${user.public_repos}</strong> Repos</div>
                            <div class="stat-badge"><strong>${user.followers}</strong> Followers</div>
                            <div class="stat-badge"><strong>${user.following}</strong> Following</div>
                        </div>
                    </div>
                `;
            } else if (sourceId === 'output-getcp') {
                const user = data.data && data.data.result ? data.data.result[0] : (data.result ? data.result[0] : null);
                if (!user) return '<p>No user data</p>';
                return `
                    <div class="profile-card">
                        <div class="profile-header">
                            <img src="${user.avatar}" class="profile-avatar" alt="Avatar">
                            <div class="profile-title">
                                <h4>${user.firstName || ''} ${user.lastName || ''}</h4>
                                <p style="color:var(--accent-color)">${user.handle}</p>
                            </div>
                        </div>
                        <div class="profile-stats">
                            <div class="stat-badge">Rating: <strong>${user.rating || 'Unrated'}</strong></div>
                            <div class="stat-badge">Rank: <strong>${user.rank || 'N/A'}</strong></div>
                            <div class="stat-badge">Max Rating: <strong>${user.maxRating || 'N/A'}</strong></div>
                        </div>
                    </div>
                `;
            } else if (sourceId === 'output-linkedin') {
                const profile = data.data ? data.data.profile : null;
                const posts = data.data ? data.data.recent_posts : [];
                if (!profile) return `<p>Requires valid email and password</p>`;

                let postsHtml = posts.slice(0, 3).map(p => `
                    <div class="data-item">
                        <strong style="color:var(--text-primary)">${p.author ? p.author.name : 'Post'}</strong>
                        <p style="margin: 4px 0;">${(p.text || '').substring(0, 100)}...</p>
                        <small style="color:var(--text-secondary)">⭐ ${p.numLikes || 0} | 💬 ${p.numComments || 0}</small>
                    </div>
                `).join('');

                return `
                    <div class="profile-card">
                        <div class="profile-header">
                            <div class="profile-title">
                                <h4>${profile.firstName} ${profile.lastName}</h4>
                                <p>${profile.headline || ''}</p>
                            </div>
                        </div>
                        <div class="profile-stats">
                            <div class="stat-badge"><strong>${data.data.recent_posts ? data.data.recent_posts.length : 0}</strong> Recent Posts</div>
                        </div>
                        <div class="data-list">
                            ${postsHtml}
                        </div>
                    </div>
                `;
            } else if (sourceId === 'output-leetcode') {
                const user = data.data ? data.data : null;
                if (!user) return '<p>No user data</p>';
                return `
                    <div class="profile-card">
                        <div class="profile-header">
                            <img src="${user.profile.userAvatar}" class="profile-avatar" alt="Avatar">
                            <div class="profile-title">
                                <h4>${user.profile.realName}</h4>
                                <p style="color:var(--accent-color)">${user.username}</p>
                            </div>
                        </div>
                        <div class="profile-stats">
                            <div class="stat-badge">Ranking: <strong>${user.profile.ranking}</strong></div>
                            <div class="stat-badge">Reputation: <strong>${user.profile.reputation}</strong></div>
                            <div class="stat-badge">Country: <strong>${user.profile.countryName || 'Unknown'}</strong></div>
                        </div>
                    </div>
                `;
            } else if (sourceId === 'output-hackerrank') {
                const user = data.extracted_data;
                if (!user) return '<p>No user data</p>';
                return `
                    <div class="profile-card">
                        <div class="profile-header">
                            <div class="profile-title">
                                <h4>${user.profile_name}</h4>
                                <p style="color:var(--accent-color)">@${user.username}</p>
                            </div>
                        </div>
                        <a href="${user.url}" target="_blank" class="stat-badge" style="display:inline-block; margin-top:10px; text-decoration:none;">View Profile</a>
                    </div>
                `;
            } else if (sourceId === 'output-cpscore') {
                const user = data;
                if (!user) return '<p>No data</p>';
                return `
                    <div class="profile-card">
                        <div class="profile-header">
                            <div class="profile-title">
                                <h4>${user.username}</h4>
                                <p>Aggregated Competitive Score</p>
                            </div>
                        </div>
                        <div class="profile-stats" style="margin-top: 15px;">
                            <div class="stat-badge" style="background-color:var(--accent-color); color:white; border:none; padding:8px 12px; font-size:1rem;">Total: <strong>${user.total_score}</strong></div>
                        </div>
                        <div class="data-list">
                            <div class="data-item">Codeforces: <strong>${user.breakdown.codeforces_rating}</strong></div>
                            <div class="data-item">LeetCode: <strong>${user.breakdown.leetcode_rating}</strong></div>
                            <div class="data-item">CodeChef: <strong>${user.breakdown.codechef_rating}</strong></div>
                        </div>
                    </div>
                `;
            }
        } catch (e) {
            return `<p>Cannot render UI: ${e.message}</p>`;
        }
        return '<p>UI rendering not configured for this source yet.</p>';
    }

    /**
     * Syntax-highlight JSON string with colored spans
     */
    function syntaxHighlightJSON(json) {
        if (typeof json !== 'string') {
            json = JSON.stringify(json, null, 2);
        }
        // Escape HTML entities
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        // Apply syntax highlighting via regex
        return json.replace(
            /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
            function (match) {
                let cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/null/.test(match)) {
                    cls = 'json-null';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            }
        );
    }

    /**
     * Helper to wrap output in Toggle Tabs
     */
    function wrapResultsWithToggle(outputEl, jsonData, sourceId) {
        // Remove styling from the main output area so children can control scrolling
        outputEl.style.padding = '0';
        outputEl.style.border = 'none';
        outputEl.style.background = 'transparent';
        outputEl.style.overflow = 'visible';

        const highlightedJson = syntaxHighlightJSON(jsonData);
        const uiHtml = renderUICard(jsonData, sourceId);

        // Save in cache for the AI builder to use
        window.scrapedCache = window.scrapedCache || {};
        window.scrapedCache[sourceId] = jsonData;

        outputEl.innerHTML = `
            <div class="output-container">
                <div class="view-toggle">
                    <button type="button" class="toggle-btn active" onclick="this.parentElement.nextElementSibling.classList.remove('hidden'); this.parentElement.nextElementSibling.nextElementSibling.classList.add('hidden'); this.classList.add('active'); this.nextElementSibling.classList.remove('active');">JSON</button>
                    <button type="button" class="toggle-btn" onclick="this.parentElement.nextElementSibling.classList.add('hidden'); this.parentElement.nextElementSibling.nextElementSibling.classList.remove('hidden'); this.classList.add('active'); this.previousElementSibling.classList.remove('active');">Card UI</button>
                </div>
                <div class="json-view">
                    <pre class="json-pre"><code>${highlightedJson}</code></pre>
                </div>
                <div class="ui-view hidden" style="height: 200px; display:flex; flex-direction:column;">
                    <div style="flex:1; overflow-y:auto;">
                        ${uiHtml}
                    </div>
                    <button class="btn primary-btn" style="margin-top: 10px; width: 100%; border:1px solid var(--accent-color); background:rgba(99, 102, 241, 0.1);" onclick="window.openResumeModal('${sourceId}')">
                        <i class="fas fa-magic"></i> Build Resume with AI
                    </button>
                </div>
            </div>
        `;
    }


    /**
     * Helper function to handle form submission, loading state, and API fetch
     * @param {string} formId The ID of the form element
     * @param {string} inputId The ID of the input element
     * @param {string} outputId The ID of the output element where results go
     * @param {string} apiEndpoint The URL of the API endpoint to hit
     */
    function setupScraper(formId, inputId, outputId, apiEndpoint) {
        const form = document.getElementById(formId);
        const input = document.getElementById(inputId);
        const output = document.getElementById(outputId);

        if (!form || !input || !output) return;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const query = input.value.trim();
            if (!query) return;

            // Set loading state
            output.innerHTML = '<div class="output-loading"><i class="fas fa-circle-notch"></i></div>';
            const btn = form.querySelector('button');
            const originalBtnText = btn.innerText;
            btn.disabled = true;
            btn.innerText = 'Fetching...';

            try {
                // Here is where you integrate with your actual endpoints. 
                // For demonstration, we attempt a GET request with the query parameter.

                // e.g., http://localhost:5000/api/github?username=ys770
                const url = new URL(apiEndpoint, window.location.origin);
                url.searchParams.append('query', query);

                // If this is Linkedin, try to append the email and pass credentials
                const emailInput = document.getElementById(`email-${formId.replace('form-', '')}`);
                const passwordInput = document.getElementById(`password-${formId.replace('form-', '')}`);

                if (emailInput && emailInput.value) {
                    url.searchParams.append('email', emailInput.value.trim());
                }
                if (passwordInput && passwordInput.value) {
                    url.searchParams.append('password', passwordInput.value.trim());
                }

                // Assuming cross-origin might be needed if APIs run on different ports
                // Replace this block with your actual fetch logic
                const response = await fetch(url, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!response.ok) {
                    throw new Error(`HTTP Error: ${response.status}`);
                }

                const data = await response.json();

                // Format successful output
                wrapResultsWithToggle(output, data, outputId);

            } catch (error) {
                console.error(`Error fetching from ${apiEndpoint}:`, error);

                // Format error output
                output.innerHTML = `<pre style="color: var(--error-color);"><code>Failed to fetch data.\n\nSimulated output for testing:\n{\n  "status": "error",\n  "message": "Actual API endpoint ${apiEndpoint} not reachable yet. Please update the JS to point to your real backend services!."\n}</code></pre>`;
            } finally {
                // Reset button state
                btn.disabled = false;
                btn.innerText = originalBtnText;
            }
        });
    }

    // Initialize all 6 tools with their prospective endpoints.
    // Replace these URLs with the actual urls where your scrapers are running.

    // 1. LinkedIn Profile Scraper
    setupScraper('form-linkedin', 'input-linkedin', 'output-linkedin', 'http://localhost:5000/api/linkedin');

    // 2. GitHub Profile
    setupScraper('form-github', 'input-github', 'output-github', 'http://localhost:5000/api/github');

    // 3. LeetCode Data
    setupScraper('form-leetcode', 'input-leetcode', 'output-leetcode', 'http://localhost:5000/api/leetcode');

    // 4. GetCP (Codeforces)
    setupScraper('form-getcp', 'input-getcp', 'output-getcp', 'http://localhost:5000/api/getcp');

    // 5. Competitive Programming Score API
    setupScraper('form-cpscore', 'input-cpscore', 'output-cpscore', 'http://localhost:5000/api/cpscore');

    // 6. HackerRank WebScraping Selenium
    setupScraper('form-hackerrank', 'input-hackerrank', 'output-hackerrank', 'http://localhost:5000/api/hackerrank');

    // Setup Resume Modal Logic
    setupResumeModal();
});

function setupResumeModal() {
    // Inject Modal HTML into the DOM
    const modalHtml = `
    <div id="ai-resume-modal" class="modal-overlay hidden">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-magic"></i> AI Resume Builder</h2>
                <button class="icon-btn" onclick="window.closeResumeModal()"><i class="fas fa-times"></i></button>
            </div>
            
            <div class="modal-body" id="modal-body-container">
            
                <div id="resume-step-1">
                    <h3 style="margin-bottom:10px; font-size:1.1rem; color:var(--text-color);">High ATS Score Templates (Word DOCX)</h3>
                    <div class="template-grid">
                        <div class="template-card active" data-value="Two-Column Resume.docx" onclick="window.selectTemplate(this)">
                            <div class="wireframe tech-wf">
                                <div class="w-cols"><div class="w-left"></div><div class="w-right"><div class="w-line"></div><div class="w-line" style="width: 50%"></div></div></div>
                            </div>
                            <span>Two-Column Resume</span>
                        </div>
                        <div class="template-card" data-value="Modern Resume.docx" onclick="window.selectTemplate(this)">
                            <div class="wireframe biz-wf">
                                <div class="w-title"></div>
                                <div class="w-line"></div>
                                <div class="w-line" style="height: 1px; width: 80%"></div>
                            </div>
                            <span>Modern Resume</span>
                        </div>
                        <div class="template-card" data-value="Harvard Resume.docx" onclick="window.selectTemplate(this)">
                            <div class="wireframe mod-wf">
                                <div class="w-header"></div>
                                <div class="w-cols"><div class="w-left"></div><div class="w-right"></div></div>
                            </div>
                            <span>Harvard Resume</span>
                        </div>
                        <div class="template-card" data-value="Chronological Resume.docx" onclick="window.selectTemplate(this)">
                            <div class="wireframe time-wf">
                                <div class="w-dot"></div><div class="w-block"></div>
                                <div class="w-dot" style="top: 30px"></div><div class="w-block"></div>
                            </div>
                            <span>Chronological</span>
                        </div>
                        <div class="template-card" data-value="Creative Resume.docx" onclick="window.selectTemplate(this)">
                            <div class="wireframe crt-wf">
                                <div class="w-header"></div>
                                <div class="w-cols"><div class="w-left"></div><div class="w-right"></div></div>
                            </div>
                            <span>Creative Resume</span>
                        </div>
                    </div>

                    <h3 style="margin-top:20px; margin-bottom:10px; font-size:1.1rem; color:var(--text-color);">Modern Web Templates (HTML/PDF)</h3>
                    <div class="template-grid">
                        <div class="template-card" data-value="Dev Portfolio" onclick="window.selectTemplate(this)">
                            <div class="wireframe dev-wf">
                                <div class="w-header"></div>
                                <div class="w-cols"><div class="w-left"></div><div class="w-right"></div></div>
                            </div>
                            <span>Dev Portfolio</span>
                        </div>
                        <div class="template-card" data-value="minimal-resume" onclick="window.selectTemplate(this)">
                            <div class="wireframe min-wf">
                                <div class="w-title"></div>
                                <div class="w-line"></div>
                                <div class="w-line" style="width: 80%"></div>
                                <div style="height: 10px"></div>
                                <div class="w-line" style="width: 60%"></div>
                            </div>
                            <span>Minimalist</span>
                        </div>
                        <div class="template-card" data-value="Simple Resume Two-column" onclick="window.selectTemplate(this)">
                            <div class="wireframe two-col-wf">
                                <div class="w-header"></div>
                                <div class="w-cols"><div class="w-sidebar"></div><div class="w-main"></div></div>
                            </div>
                            <span>Two-Column HTML</span>
                        </div>
                        <div class="template-card" data-value="Markdown Clean CSS printable" onclick="window.selectTemplate(this)">
                            <div class="wireframe print-wf">
                                <div class="w-title"></div>
                                <div class="w-divider"></div>
                                <div class="w-text-block"></div>
                                <div class="w-text-block" style="height:30%"></div>
                            </div>
                            <span>Printable B&W</span>
                        </div>
                    </div>

                    <button class="btn primary-btn btn-full" style="margin-top:15px;" onclick="window.goToResumeStep2()">
                        Next: Add Missing Details &nbsp; <i class="fas fa-arrow-right"></i>
                    </button>
                    <input type="hidden" id="resume-template-select" value="Two-Column Resume.docx">
                </div>

                <div id="resume-step-2" class="hidden">
                    <button class="btn secondary-btn" style="margin-bottom:15px;" onclick="window.goToResumeStep1()"><i class="fas fa-arrow-left"></i> Back to Templates</button>
                    
                    <h3 style="margin-bottom:15px; color:var(--text-color);">Fill Missing Details</h3>
                    <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:15px;">Add any details that weren't publicly available on your profile.</p>

                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" id="manual-email" placeholder="john@example.com" style="width:100%; padding:8px; border-radius:4px; border:1px solid #ccc;">
                    </div>
                    <div class="form-group" style="display:flex; gap:10px;">
                        <div style="flex:1;">
                            <label>Phone Number</label>
                            <input type="text" id="manual-phone" placeholder="+1 234 567 8900" style="width:100%; padding:8px; border-radius:4px; border:1px solid #ccc;">
                        </div>
                        <div style="flex:1;">
                            <label>Location</label>
                            <input type="text" id="manual-location" placeholder="City, Country" style="width:100%; padding:8px; border-radius:4px; border:1px solid #ccc;">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Custom Summary Overwrite (Optional)</label>
                        <textarea id="manual-summary" rows="3" placeholder="A brief professional summary..." style="width:100%; padding:8px; border-radius:4px; border:1px solid #ccc;"></textarea>
                    </div>

                    <div id="repo-selection-container" class="form-group hidden" style="margin-top: 20px;">
                        <!-- Dynamically populated repo checkboxes go here -->
                    </div>
                    
                    <button id="generate-resume-btn" class="btn primary-btn btn-full" style="margin-top:20px;" onclick="window.generateResume()">
                        <i class="fas fa-magic"></i> Generate AI Resume
                    </button>
                </div>

                <div id="resume-loading" class="hidden" style="margin-top:20px; text-align:center;">
                    <i class="fas fa-circle-notch fa-spin fa-2x" style="color:var(--accent-color);"></i>
                    <p style="margin-top:10px; color:var(--text-secondary);">Designing resume with AI... (this may take up to 30 seconds)</p>
                </div>
                
                <div id="resume-result" class="hidden" style="margin-top:20px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h4 style="margin:0; color:var(--text-color);">Preview</h4>
                        <div style="display:flex; gap: 10px;">
                            <button id="download-pdf-btn" class="btn secondary-btn" style="background-color: var(--accent-color); color: white; border-color: var(--accent-color); display: none;" onclick="window.downloadPDF()"><i class="fas fa-file-pdf"></i> Download PDF</button>
                            <a id="download-resume-btn" class="btn secondary-btn" download="ai_resume.html" style="display:none;"><i class="fas fa-file-code"></i> Download HTML</a>
                        </div>
                    </div>
                    <iframe id="resume-preview-iframe" class="hidden" style="width:100%; height:400px; background:white; border:1px solid #ddd; border-radius:4px;"></iframe>
                    <p id="docx-download-msg" class="hidden" style="color:var(--text-secondary); text-align:center; padding: 20px;">Your DOCX Resume is downloading automatically!</p>
                </div>
            </div>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Global Handlers
    window.currentResumeSourceId = null;

    window.selectTemplate = (cardElement) => {
        // Remove active class from all
        document.querySelectorAll('.template-card').forEach(c => c.classList.remove('active'));
        // Add to clicked
        cardElement.classList.add('active');
        // Update hidden input
        document.getElementById('resume-template-select').value = cardElement.getAttribute('data-value');
    };

    window.goToResumeStep1 = () => {
        document.getElementById('resume-step-1').classList.remove('hidden');
        document.getElementById('resume-step-2').classList.add('hidden');
    };

    window.goToResumeStep2 = () => {
        document.getElementById('resume-step-1').classList.add('hidden');
        document.getElementById('resume-step-2').classList.remove('hidden');
    };

    window.openResumeModal = (sourceId) => {
        window.currentResumeSourceId = sourceId;
        const sourceData = window.scrapedCache[sourceId];

        document.getElementById('ai-resume-modal').classList.remove('hidden');
        document.getElementById('resume-step-1').classList.remove('hidden');
        document.getElementById('resume-step-2').classList.add('hidden');
        document.getElementById('resume-result').classList.add('hidden');
        document.getElementById('resume-loading').classList.add('hidden');

        // Reset manual inputs
        document.getElementById('manual-email').value = '';
        document.getElementById('manual-phone').value = '';
        document.getElementById('manual-location').value = '';
        document.getElementById('manual-summary').value = '';

        // Dynamically populate Repositories if they exist in the payload
        const repoContainer = document.getElementById('repo-selection-container');
        repoContainer.innerHTML = '';

        if (sourceData && sourceData.data && sourceData.data.top_repositories_with_readme && sourceData.data.top_repositories_with_readme.length > 0) {
            repoContainer.classList.remove('hidden');
            let html = '<label style="margin-bottom:10px; display:block;"><i class="fas fa-code-branch"></i> Select Repositories to Include</label><div class="repo-list">';
            sourceData.data.top_repositories_with_readme.forEach((repo, idx) => {
                html += `
                    <div class="repo-item">
                        <input type="checkbox" id="repo-${idx}" value="${repo.name}" checked>
                        <label for="repo-${idx}">
                            <strong>${repo.name}</strong> 
                            <span style="font-size:0.8rem; color:var(--text-secondary)">
                                <i class="fas fa-star" style="color:gold"></i> ${repo.stars || 0} &middot; ${repo.language || 'Code'}
                            </span>
                        </label>
                    </div>`;
            });
            html += '</div>';
            repoContainer.innerHTML = html;
        } else {
            repoContainer.classList.add('hidden');
        }
    };

    window.closeResumeModal = () => {
        document.getElementById('ai-resume-modal').classList.add('hidden');
    };

    window.downloadPDF = async () => {
        const iframe = document.getElementById('resume-preview-iframe');
        if (!iframe || !iframe.contentDocument || !iframe.contentDocument.documentElement) {
            alert("Resume is not loaded yet.");
            return;
        }

        const htmlStr = "<!DOCTYPE html>\n" + iframe.contentDocument.documentElement.outerHTML;
        const btn = document.getElementById('download-pdf-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;

        try {
            const res = await fetch('http://localhost:5000/api/generate_pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ html_content: htmlStr })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server error generating PDF');

            // Convert base64 PDF string directly back into a downloadable binary Blob
            const binaryString = window.atob(data.pdf_base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const blob = new Blob([bytes], { type: 'application/pdf' });
            const blobUrl = URL.createObjectURL(blob);

            // Trigger silent auto-download
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = 'ai_resume.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(blobUrl);

        } catch (e) {
            alert('Failed to generate PDF: ' + e.message);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };

    window.generateResume = async () => {
        const sourceData = window.scrapedCache[window.currentResumeSourceId];
        if (!sourceData) {
            alert('Error: Missing profile data in memory. Please rescrape the profile first.');
            return;
        }

        // Deep clone so we do not overwrite the master cache in memory
        let finalData = JSON.parse(JSON.stringify(sourceData));

        // Append missing manual overrides
        finalData.data = finalData.data || {};
        finalData.data.manual_overrides = {
            email: document.getElementById('manual-email').value,
            phone: document.getElementById('manual-phone').value,
            location: document.getElementById('manual-location').value,
            summary: document.getElementById('manual-summary').value
        };

        // Filter Repositories if the user unchecked any
        const repoContainer = document.getElementById('repo-selection-container');
        if (!repoContainer.classList.contains('hidden') && finalData.data && finalData.data.top_repositories_with_readme) {
            const selectedRepos = Array.from(repoContainer.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
            finalData.data.top_repositories_with_readme = finalData.data.top_repositories_with_readme.filter(r => selectedRepos.includes(r.name));
        }

        const templateStyle = document.getElementById('resume-template-select').value;
        const btn = document.getElementById('generate-resume-btn');
        const loading = document.getElementById('resume-loading');
        const result = document.getElementById('resume-result');
        const iframe = document.getElementById('resume-preview-iframe');
        const downloadBtn = document.getElementById('download-resume-btn');
        const pdfBtn = document.getElementById('download-pdf-btn');
        const docxMsg = document.getElementById('docx-download-msg');

        document.getElementById('resume-step-2').classList.add('hidden');
        loading.classList.remove('hidden');
        result.classList.add('hidden');

        const isDocx = templateStyle.endsWith('.docx');
        const endpoint = isDocx ? 'http://localhost:5000/api/generate_docx' : 'http://localhost:5000/api/generate_resume';

        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile_data: finalData,
                    template_style: templateStyle,
                    model: 'bemudu'
                })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server error generating resume');

            if (isDocx) {
                // Download binary DOCX
                const binaryString = window.atob(data.docx_base64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
                const blobUrl = URL.createObjectURL(blob);

                const a = document.createElement('a');
                a.href = blobUrl;
                a.download = templateStyle.replace('.docx', '') + '_Generated.docx';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(blobUrl);

                iframe.classList.add('hidden');
                pdfBtn.style.display = 'none';
                downloadBtn.style.display = 'none';
                docxMsg.classList.remove('hidden');
            } else {
                // Download HTML
                const htmlContent = data.html;
                const blob = new Blob([htmlContent], { type: 'text/html' });
                const blobUrl = URL.createObjectURL(blob);

                iframe.src = blobUrl;
                downloadBtn.href = blobUrl;

                iframe.classList.remove('hidden');
                pdfBtn.style.display = 'block';
                downloadBtn.style.display = 'block';
                docxMsg.classList.add('hidden');
            }

            loading.classList.add('hidden');
            result.classList.remove('hidden');

        } catch (e) {
            alert('Failed to generate resume: ' + e.message);
            loading.classList.add('hidden');
            document.getElementById('resume-step-2').classList.remove('hidden');
        }
    };
}
