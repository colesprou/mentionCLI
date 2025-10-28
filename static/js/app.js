// Kalshi Mention Market Research Tool - Frontend JavaScript
console.log('JavaScript file loaded!');

class KalshiResearchApp {
    constructor() {
        this.currentMarkets = [];
        this.currentAnalysis = null;
        this.currentEvents = [];
        this.selectedEventIndex = undefined;
        this.init();
    }

    init() {
        console.log('Kalshi Research App initialized');
        this.setupEventListeners();
        this.initCommandInput();
    }

    initCommandInput() {
        // Wait for DOM to be ready
        setTimeout(() => {
            const commandInput = document.getElementById('commandInput');
            console.log('Command input element:', commandInput);
            
            if (commandInput) {
                commandInput.addEventListener('keypress', (e) => {
                    console.log('Key pressed:', e.key);
                    if (e.key === 'Enter') {
                        const command = commandInput.value.trim();
                        console.log('Executing command:', command);
                        this.handleCommand(command);
                        commandInput.value = '';
                    }
                });
                
                // Focus on input when page loads
                commandInput.focus();
                console.log('Command input initialized and focused');
            } else {
                console.error('Command input element not found!');
            }
        }, 100);
    }

    handleCommand(command) {
        console.log('handleCommand called with:', command);
        if (!command) {
            console.log('Empty command, returning');
            return;
        }
        
        const terminalOutput = document.getElementById('terminalOutput');
        console.log('Terminal output element:', terminalOutput);
        
        if (!terminalOutput) {
            console.error('Terminal output element not found!');
            return;
        }
        
        // Add command to output
        terminalOutput.innerHTML += `
            <div class="output-line">
                <span class="command">${command}</span>
            </div>
        `;
        
        // Parse and execute command
        const parts = command.split(' ');
        const cmd = parts[0].toLowerCase();
        const arg = parts[1];
        
        console.log('Parsed command:', { cmd, arg, parts });
        
        switch (cmd) {
            case 'markets':
                const limit = arg ? parseInt(arg) : null;
                console.log('Loading markets with limit:', limit);
                this.loadMarkets(limit);
                break;
                
            case 'research':
                const eventIndex = arg ? parseInt(arg) : null;
                console.log('Research command with event index:', eventIndex);
                if (eventIndex && eventIndex > 0 && eventIndex <= this.currentEvents.length) {
                    researchEvent(eventIndex, this.currentEvents[eventIndex - 1].event_ticker);
                } else {
                    this.addOutput('Error: Invalid event number. Use: research [1-' + this.currentEvents.length + ']', 'error');
                }
                break;
                
            case 'mention':
            case 'rules':
                if (cmd === 'mention' && parts[1] === 'rules') {
                    this.showMentionRules();
                } else {
                    this.showMentionRules();
                }
                break;
                
            case 'help':
                console.log('Showing help');
                this.showHelp();
                break;
                
            case 'clear':
                console.log('Clearing terminal');
                terminalOutput.innerHTML = '';
                break;
                
            case 'test':
                console.log('Test command executed');
                this.addOutput('Test command working! Terminal input is functional.', 'success');
                break;
                
            default:
                console.log('Unknown command:', cmd);
                this.addOutput(`Unknown command: ${cmd}. Type 'help' for available commands.`, 'error');
        }
        
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    addOutput(text, type = 'output') {
        const terminalOutput = document.getElementById('terminalOutput');
        terminalOutput.innerHTML += `
            <div class="output-line">
                <span class="${type}">${text}</span>
            </div>
        `;
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    showHelp() {
        this.addOutput('Available Commands:');
        this.addOutput('  markets [N]     - Show top N markets by volume');
        this.addOutput('  research [i]    - Research event i (if earnings call)');
        this.addOutput('  mention rules   - Show Kalshi mention rules');
        this.addOutput('  test            - Test if terminal input works');
        this.addOutput('  help            - Show this help');
        this.addOutput('  clear           - Clear terminal output');
    }

    setupEventListeners() {
        // Add any global event listeners here
    }

    async loadMarkets(limit = null) {
        this.updateStatus('Loading markets...');
        
        try {
            const url = limit ? `/api/markets/${limit}` : '/api/markets';
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayMarkets(data.data);
                this.updateStatus('Markets loaded');
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Failed to load markets: ' + error.message);
        }
    }

    displayMarkets(markets) {
        const terminalOutput = document.getElementById('terminalOutput');
        
        if (!markets || markets.length === 0) {
            terminalOutput.innerHTML += `
                <div class="output-line">
                    <span class="command">markets</span>
                </div>
                <div class="output-line">
                    <span class="output warning">No markets found</span>
                </div>
            `;
            return;
        }

        // Store events for research command
        this.currentEvents = markets;

        let html = `
            <div class="output-line">
                <span class="command">markets ${markets.length}</span>
            </div>
            <div class="output-line">
                <span class="output success">Found ${markets.length} high-volume mention markets</span>
            </div>
        `;

        markets.forEach((event, index) => {
            html += this.renderEventGroup(event, index + 1);
        });

        terminalOutput.innerHTML += html;
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }

    renderEventGroup(event, index) {
        const betWords = event.bet_words || [];
        const marketCount = event.market_count || 0;
        const totalVolume = event.total_volume || 0;
        
        const betWordsList = betWords.slice(0, 8).join(', ');
        const moreWords = betWords.length > 8 ? `... and ${betWords.length - 8} more` : '';

        return `
            <div class="output-line">
                <span class="output">Event ${index}: ${event.title}</span>
            </div>
            <div class="output-line">
                <span class="output">  Markets: ${marketCount} | Volume: $${totalVolume.toLocaleString()} | Terms: ${betWords.length}</span>
            </div>
            <div class="output-line">
                <span class="output">  Bet Words: ${betWordsList}${moreWords ? ', ' + moreWords : ''}</span>
            </div>
            <div class="output-line">
                <span class="output">  Research: <button class="btn btn-sm btn-outline-success" onclick="researchEvent(${index}, '${event.event_ticker}')">research ${index}</button></span>
            </div>
            <div class="output-line">
                <span class="output"></span>
            </div>
        `;
    }

    showResearchForm() {
        const modal = new bootstrap.Modal(document.getElementById('researchModal'));
        modal.show();
        this.loadEventsForResearch();
    }

    async loadEventsForResearch() {
        try {
            const response = await fetch('/api/markets/10');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentEvents = data.data;
                this.displayEventsForResearch(data.data);
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Failed to load events: ' + error.message);
        }
    }

    displayEventsForResearch(events) {
        const eventList = document.getElementById('eventList');
        let html = '';
        
        events.forEach((event, index) => {
            const isEarnings = this.isEarningsEvent(event);
            html += `
                <div class="event-item" onclick="selectEvent(${index})">
                    <div class="event-title">${index + 1}. ${event.title}</div>
                    <div class="event-meta">
                        ${event.market_count} markets | $${event.total_volume.toLocaleString()} volume | ${event.bet_words.length} terms
                        ${isEarnings ? ' <span class="earnings-badge">Earnings Call</span>' : ''}
                    </div>
                </div>
            `;
        });
        
        eventList.innerHTML = html;
    }

    isEarningsEvent(event) {
        const title = event.title.toLowerCase();
        return title.includes('earnings') || title.includes('q1') || title.includes('q2') || 
               title.includes('q3') || title.includes('q4') || title.includes('quarter');
    }

    showBatchForm() {
        const modal = new bootstrap.Modal(document.getElementById('batchModal'));
        modal.show();
    }

    async runEarningsAnalysis() {
        const ticker = document.getElementById('ticker').value.trim().toUpperCase();
        const terms = document.getElementById('terms').value.split(',').map(t => t.trim()).filter(t => t);
        const quarters = parseInt(document.getElementById('quarters').value);

        if (!ticker || terms.length === 0) {
            this.showError('Please provide both ticker and terms');
            return;
        }

        this.updateStatus('Analyzing earnings calls...');
        
        try {
            const response = await fetch('/api/earnings/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticker: ticker,
                    terms: terms,
                    quarters_back: quarters
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayEarningsResults(data.data);
                this.updateStatus('Analysis complete');
                bootstrap.Modal.getInstance(document.getElementById('earningsModal')).hide();
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Failed to analyze earnings: ' + error.message);
        }
    }

    async runBatchAnalysis() {
        const termsText = document.getElementById('batchTerms').value.trim();
        const quarters = parseInt(document.getElementById('batchQuarters').value);

        let companyTerms;
        try {
            companyTerms = JSON.parse(termsText);
        } catch (error) {
            this.showError('Invalid JSON format for company terms');
            return;
        }

        this.updateStatus('Running batch analysis...');
        
        try {
            const response = await fetch('/api/earnings/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_terms: companyTerms,
                    quarters_back: quarters
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayBatchResults(data.data);
                this.updateStatus('Batch analysis complete');
                bootstrap.Modal.getInstance(document.getElementById('batchModal')).hide();
            } else {
                this.showError(data.message);
            }
        } catch (error) {
            this.showError('Failed to run batch analysis: ' + error.message);
        }
    }

    displayEarningsResults(data) {
        const terminalBody = document.getElementById('terminalBody');
        
        if (data.error) {
            terminalBody.innerHTML = `
                <div class="terminal-output">
                    <div class="command">earnings analysis</div>
                    <div class="output error">${data.error}</div>
                </div>
            `;
            return;
        }

        let html = `
            <div class="terminal-output">
                <div class="command">earnings analysis</div>
                <div class="output success">Analysis complete for ${data.ticker}</div>
            </div>
            <div class="earnings-results">
                <div class="earnings-header">
                    <div class="earnings-ticker">${data.ticker}</div>
                    <div class="earnings-stats">
                        ${data.quarters_analyzed} quarters analyzed | ${data.total_words_analyzed.toLocaleString()} words
                    </div>
                </div>
                <div class="term-results">
        `;

        Object.entries(data.term_results).forEach(([term, result]) => {
            html += this.renderTermResult(term, result);
        });

        html += `
                </div>
            </div>
        `;

        terminalBody.innerHTML = html;
    }

    displayBatchResults(data) {
        const terminalBody = document.getElementById('terminalBody');
        
        let html = `
            <div class="terminal-output">
                <div class="command">batch analysis</div>
                <div class="output success">Batch analysis complete for ${Object.keys(data).length} companies</div>
            </div>
        `;

        Object.entries(data).forEach(([ticker, companyData]) => {
            if (companyData.error) {
                html += `
                    <div class="earnings-results">
                        <div class="earnings-header">
                            <div class="earnings-ticker">${ticker}</div>
                            <div class="earnings-stats error">${companyData.error}</div>
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div class="earnings-results">
                        <div class="earnings-header">
                            <div class="earnings-ticker">${ticker}</div>
                            <div class="earnings-stats">
                                ${companyData.quarters_analyzed} quarters | ${companyData.total_words_analyzed.toLocaleString()} words
                            </div>
                        </div>
                        <div class="term-results">
                `;

                Object.entries(companyData.term_results).forEach(([term, result]) => {
                    html += this.renderTermResult(term, result);
                });

                html += `
                        </div>
                    </div>
                `;
            }
        });

        terminalBody.innerHTML = html;
    }

    renderTermResult(term, result) {
        const probability = (result.empirical_probability * 100).toFixed(4);
        const frequency = (result.mention_frequency * 100).toFixed(1);

        return `
            <div class="term-result">
                <div class="term-name">${term}</div>
                <div class="term-metrics">
                    <div class="metric">
                        <div class="metric-value">${result.total_mentions}</div>
                        <div class="metric-label">Total Mentions</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${probability}%</div>
                        <div class="metric-label">Empirical Probability</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${frequency}%</div>
                        <div class="metric-label">Mention Frequency</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${result.quarters_with_mentions}/${result.total_quarters_analyzed}</div>
                        <div class="metric-label">Quarters w/ Mentions</div>
                    </div>
                </div>
                <div class="quarter-breakdown">
                    <h6>Quarterly Breakdown:</h6>
                    ${Object.entries(result.mentions_by_quarter).map(([quarter, data]) => `
                        <div class="quarter-item">
                            <div class="quarter-name">${quarter}</div>
                            <div class="quarter-count">${data.count} mentions</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    async showMentionRules() {
        const modal = new bootstrap.Modal(document.getElementById('rulesModal'));
        modal.show();

        try {
            const response = await fetch('/api/mention-rules');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayMentionRules(data.data);
            } else {
                this.showError('Failed to load mention rules');
            }
        } catch (error) {
            this.showError('Failed to load mention rules: ' + error.message);
        }
    }

    displayMentionRules(rules) {
        const rulesContent = document.getElementById('rulesContent');
        
        let html = `
            <div class="rules-section">
                <h6>Matching Rules</h6>
                <ul>
                    <li><strong>Case Sensitivity:</strong> ${rules.case_sensitivity}</li>
                    <li><strong>Plural Forms:</strong> ${rules.plural_forms}</li>
                    <li><strong>Compound Words:</strong> ${rules.compound_words}</li>
                    <li><strong>Ordinal Forms:</strong> ${rules.ordinal_forms}</li>
                    <li><strong>Homonyms:</strong> ${rules.homonyms}</li>
                </ul>
                
                <h6>Exclusions</h6>
                <ul>
        `;

        rules.exclusions.forEach(exclusion => {
            html += `<li>${exclusion}</li>`;
        });

        html += `
                </ul>
                
                <h6>Additional Rules</h6>
                <ul>
                    <li><strong>Context Matching:</strong> ${rules.context_matching}</li>
                    <li><strong>Language Restriction:</strong> ${rules.language_restriction}</li>
                </ul>
            </div>
        `;

        rulesContent.innerHTML = html;
    }

    updateStatus(message) {
        const statusIndicator = document.getElementById('statusIndicator');
        statusIndicator.textContent = message;
        
        if (message.includes('Loading') || message.includes('Analyzing')) {
            statusIndicator.style.backgroundColor = '#ffd700';
            statusIndicator.style.color = '#1a1a1a';
        } else if (message.includes('Error') || message.includes('Failed')) {
            statusIndicator.style.backgroundColor = '#ff6b6b';
            statusIndicator.style.color = '#1a1a1a';
        } else {
            statusIndicator.style.backgroundColor = '#00ff88';
            statusIndicator.style.color = '#1a1a1a';
        }
    }

    showError(message) {
        const terminalBody = document.getElementById('terminalBody');
        terminalBody.innerHTML = `
            <div class="terminal-output">
                <div class="command">error</div>
                <div class="output error">${message}</div>
            </div>
        `;
        this.updateStatus('Error');
    }
}

// Global functions for HTML onclick handlers
let app;

document.addEventListener('DOMContentLoaded', function() {
    app = new KalshiResearchApp();
});

function loadMarkets(limit = null) {
    app.loadMarkets(limit);
}

function showEarningsForm() {
    app.showEarningsForm();
}

function showBatchForm() {
    app.showBatchForm();
}

function runEarningsAnalysis() {
    app.runEarningsAnalysis();
}

function runBatchAnalysis() {
    app.runBatchAnalysis();
}

function showMentionRules() {
    app.showMentionRules();
}

function executeQuickCommand(command) {
    const commandInput = document.getElementById('commandInput');
    if (commandInput) {
        commandInput.value = command;
        app.handleCommand(command);
        commandInput.value = '';
    }
}

function researchEvent(eventIndex, eventTicker) {
    // Add to terminal output
    const terminalOutput = document.getElementById('terminalOutput');
    terminalOutput.innerHTML += `
        <div class="output-line">
            <span class="command">research ${eventIndex}</span>
        </div>
    `;
    
    // Show research modal
    app.showResearchForm();
    
    // Pre-select the event and go to step 2
    setTimeout(() => {
        selectEvent(eventIndex - 1);
        // Auto-advance to step 2 after selection
        setTimeout(() => {
            nextResearchStep();
        }, 200);
    }, 100);
}

function selectEvent(eventIndex) {
    // Remove previous selection
    document.querySelectorAll('.event-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Select current event
    const eventItems = document.querySelectorAll('.event-item');
    if (eventItems[eventIndex]) {
        eventItems[eventIndex].classList.add('selected');
        app.selectedEventIndex = eventIndex;
    }
}

function nextResearchStep() {
    if (app.selectedEventIndex === undefined) {
        alert('Please select an event first');
        return;
    }
    
    const event = app.currentEvents[app.selectedEventIndex];
    const eventDetails = document.getElementById('eventDetails');
    
    eventDetails.innerHTML = `
        <div class="selected-event">
            <h6>Selected Event: ${event.title}</h6>
            <p><strong>Bet Words:</strong> ${event.bet_words.join(', ')}</p>
            <p><strong>Markets:</strong> ${event.market_count} | <strong>Volume:</strong> $${event.total_volume.toLocaleString()}</p>
            ${app.isEarningsEvent(event) ? '<p class="text-success"><strong>✓ This is an earnings call - will analyze bet words</strong></p>' : '<p class="text-warning"><strong>⚠ Not an earnings call - limited analysis available</strong></p>'}
        </div>
    `;
    
    // Show step 2 with quarters selection
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
    document.getElementById('researchNextBtn').style.display = 'none';
    document.getElementById('researchAnalyzeBtn').style.display = 'inline-block';
    
    // Focus on quarters selection
    setTimeout(() => {
        document.getElementById('quarters').focus();
    }, 100);
}

async function runResearchAnalysis() {
    const event = app.currentEvents[app.selectedEventIndex];
    const quarters = document.getElementById('quarters').value;
    
    console.log('Running research analysis:', { event: event.title, quarters: quarters });
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('researchModal'));
    modal.hide();
    
    // Add to terminal output
    const terminalOutput = document.getElementById('terminalOutput');
    terminalOutput.innerHTML += `
        <div class="output-line">
            <span class="command">research ${app.selectedEventIndex + 1}</span>
        </div>
        <div class="output-line">
            <span class="output">Analyzing event: ${event.title}</span>
        </div>
        <div class="output-line">
            <span class="output">Looking back ${quarters} quarters...</span>
        </div>
    `;
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
    
    if (app.isEarningsEvent(event)) {
        // Run earnings analysis
        try {
            const companyTicker = extractCompanyTicker(event.event_ticker);
            
            if (!companyTicker) {
                terminalOutput.innerHTML += `
                    <div class="output-line">
                        <span class="output error">Could not determine company ticker from event</span>
                    </div>
                `;
                return;
            }
            
            terminalOutput.innerHTML += `
                <div class="output-line">
                    <span class="output">Company: ${companyTicker} | Terms: ${event.bet_words.join(', ')}</span>
                </div>
            `;
            
            const response = await fetch('/api/earnings/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ticker: companyTicker,
                    terms: event.bet_words,
                    quarters_back: parseInt(quarters)
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                app.displayEarningsResultsInTerminal(data.data);
            } else {
                terminalOutput.innerHTML += `
                    <div class="output-line">
                        <span class="output error">Analysis failed: ${data.message}</span>
                    </div>
                `;
            }
        } catch (error) {
            terminalOutput.innerHTML += `
                <div class="output-line">
                    <span class="output error">Error: ${error.message}</span>
                </div>
            `;
        }
    } else {
        terminalOutput.innerHTML += `
            <div class="output-line">
                <span class="output warning">This is not an earnings call - limited analysis available</span>
            </div>
        `;
    }
    
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

async function analyzeEventBet(eventTicker, betWord) {
    """Analyze a specific bet word from an event"""
    app.updateStatus('Analyzing bet word...');
    
    try {
        // Get the company ticker from the event (assuming it's an earnings call)
        // For now, we'll try to extract it from the event title
        const companyTicker = extractCompanyTicker(eventTicker);
        
        if (!companyTicker) {
            app.showError('Could not determine company ticker from event');
            return;
        }
        
        // Run earnings analysis for this specific bet word
        const response = await fetch('/api/earnings/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticker: companyTicker,
                terms: [betWord],
                quarters_back: 8
            })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            app.displayEarningsResults(data.data);
            app.updateStatus('Analysis complete');
        } else {
            app.showError(data.message);
        }
    } catch (error) {
        app.showError('Failed to analyze bet word: ' + error.message);
    }
}

async function analyzeAllEventBets(eventTicker) {
    """Analyze all bet words from an event"""
    app.updateStatus('Loading event bet words...');
    
    try {
        // Get all bet words for this event
        const response = await fetch(`/api/events/${eventTicker}/bet-words`);
        const data = await response.json();
        
        if (data.status !== 'success') {
            app.showError(data.message);
            return;
        }
        
        const eventData = data.data;
        const companyTicker = extractCompanyTicker(eventTicker);
        
        if (!companyTicker) {
            app.showError('Could not determine company ticker from event');
            return;
        }
        
        app.updateStatus('Analyzing all bet words...');
        
        // Run earnings analysis for all bet words
        const analysisResponse = await fetch('/api/earnings/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ticker: companyTicker,
                terms: eventData.bet_words,
                quarters_back: 8
            })
        });

        const analysisData = await analysisResponse.json();
        
        if (analysisData.status === 'success') {
            app.displayEarningsResults(analysisData.data);
            app.updateStatus('Analysis complete');
        } else {
            app.showError(analysisData.message);
        }
    } catch (error) {
        app.showError('Failed to analyze event bets: ' + error.message);
    }
}

function extractCompanyTicker(eventTicker) {
    """Extract company ticker from event ticker"""
    // This is a simple heuristic - in practice, you might need more sophisticated logic
    // For earnings calls, the ticker is usually at the beginning of the event ticker
    
    // Common patterns for earnings call events
    const earningsPatterns = [
        /^([A-Z]{1,5})/,  // Standard ticker at start
        /([A-Z]{1,5})EARNINGS/,  // Ticker + EARNINGS
        /([A-Z]{1,5})Q[1-4]/,  // Ticker + Quarter
    ];
    
    for (const pattern of earningsPatterns) {
        const match = eventTicker.match(pattern);
        if (match) {
            return match[1];
        }
    }
    
    // Fallback: try to extract any 1-5 letter uppercase sequence at the start
    const fallbackMatch = eventTicker.match(/^([A-Z]{1,5})/);
    return fallbackMatch ? fallbackMatch[1] : null;
}

// Add the displayEarningsResultsInTerminal function
function displayEarningsResultsInTerminal(results) {
    const terminalOutput = document.getElementById('terminalOutput');
    
    let html = `
        <div class="output-line">
            <span class="output success">Analysis complete for ${results.company}</span>
        </div>
        <div class="output-line">
            <span class="output">Total Mentions: ${results.total_mentions} | Empirical Probability: ${(results.empirical_probability * 100).toFixed(1)}% | Quarters: ${results.quarters_analyzed}</span>
        </div>
        <div class="output-line">
            <span class="output"></span>
        </div>
        <div class="output-line">
            <span class="output">Term Analysis:</span>
        </div>
    `;

    results.term_analysis.forEach(term => {
        html += `
            <div class="output-line">
                <span class="output">  ${term.term}: ${term.mention_count} mentions (${(term.hit_rate * 100).toFixed(1)}% hit rate)</span>
            </div>
        `;
    });

    html += `
        <div class="output-line">
            <span class="output"></span>
        </div>
        <div class="output-line">
            <span class="output">Quarterly Breakdown:</span>
        </div>
    `;

    results.quarterly_breakdown.forEach(quarter => {
        html += `
            <div class="output-line">
                <span class="output">  ${quarter.quarter}: ${quarter.mention_count} mentions (${(quarter.hit_rate * 100).toFixed(1)}% hit rate)</span>
            </div>
        `;
    });

    if (results.sample_contexts && results.sample_contexts.length > 0) {
        html += `
            <div class="output-line">
                <span class="output"></span>
            </div>
            <div class="output-line">
                <span class="output">Sample Contexts:</span>
            </div>
        `;

        results.sample_contexts.slice(0, 3).forEach(context => {
            html += `
                <div class="output-line">
                    <span class="output">  ${context.term}: "${context.context}"</span>
                </div>
            `;
        });
    }

    terminalOutput.innerHTML += html;
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing app...');
    window.app = new KalshiResearchApp();
    console.log('App initialized:', window.app);
    
    // Fallback: Direct event listener
    setTimeout(() => {
        const commandInput = document.getElementById('commandInput');
        if (commandInput) {
            console.log('Adding fallback event listener');
            commandInput.addEventListener('keydown', (e) => {
                console.log('Keydown event:', e.key);
                if (e.key === 'Enter') {
                    const command = commandInput.value.trim();
                    console.log('Fallback executing command:', command);
                    if (window.app) {
                        window.app.handleCommand(command);
                    }
                    commandInput.value = '';
                }
            });
        }
    }, 500);
});
