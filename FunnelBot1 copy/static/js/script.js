document.addEventListener('DOMContentLoaded', () => {
    const transcriptInput = document.getElementById('transcriptInput');
    const salesRepNamesInput = document.getElementById('salesRepNames');
    const analyzeButton = document.getElementById('analyzeButton');
    
    const resultsArea = document.getElementById('resultsArea');
    const analysisOutputPre = document.getElementById('analysisOutput');
    
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorOutputDiv = document.getElementById('errorOutput');
    const errorOutputP = document.querySelector('#errorOutput p');

    // Educational carousel functionality
    let currentSlide = 0;
    const carouselItems = document.querySelectorAll('.carousel-item');
    const totalSlides = carouselItems.length;
    let carouselInterval;
    
    function showSlide(index, direction = 'next') {
        if (totalSlides === 0) return;
        const previousSlide = currentSlide;
        currentSlide = (index + totalSlides) % totalSlides; // Ensure index is within bounds

        carouselItems.forEach(item => {
            item.classList.remove('active', 'slide-in-left', 'slide-in-right', 'slide-out-left', 'slide-out-right');
        });

        if (direction === 'next') {
            carouselItems[previousSlide].classList.add('slide-out-left');
            carouselItems[currentSlide].classList.add('active', 'slide-in-right');
        } else {
            carouselItems[previousSlide].classList.add('slide-out-right');
            carouselItems[currentSlide].classList.add('active', 'slide-in-left');
        }
    }
    
    function nextSlide() {
        showSlide(currentSlide + 1, 'next');
    }
    
    function startCarousel() {
        if (totalSlides > 0) {
            carouselItems[0].classList.add('active'); // Show first slide without animation initially
        }    
        if (carouselInterval) clearInterval(carouselInterval); // Clear existing interval
        carouselInterval = setInterval(nextSlide, 7000); // Change slide every 7 seconds
    }
    
    function stopCarousel() {
        clearInterval(carouselInterval);
    }

    analyzeButton.addEventListener('click', async () => {
        const transcript = transcriptInput.value.trim();
        const salesRepNames = salesRepNamesInput.value.trim();
        const merchantNames = "Customer";
        
        if (!salesRepNames) {
            showError('Please enter the Sales Rep(s) name(s).');
            salesRepNamesInput.focus();
            return;
        }
        if (!transcript) {
            showError('Please paste a transcript before analyzing.');
            transcriptInput.focus();
            return;
        }

        hideError();
        resultsArea.style.display = 'none';
        analysisOutputPre.textContent = '';
        loadingIndicator.style.display = 'flex'; // Use flex for centering
        analyzeButton.disabled = true; // Disable button
        
        startCarousel();
        loadingIndicator.scrollIntoView({ behavior: 'smooth' });

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transcript: transcript,
                    sales_rep_names: salesRepNames,
                    merchant_names: merchantNames
                }),
            });

            // Stop loading indicators regardless of response status
            stopCarousel();
            loadingIndicator.style.display = 'none';
            // analyzeButton.disabled = false; // Re-enable button (moved to finally block)

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data && data.error ? data.error : `Server error: ${response.status}`;
                showError(errorMessage);
                // Button re-enabled in finally block
                return;
            }

            if (data.error) {
                showError(data.error);
            } else if (data.is_error) {
                // Specific backend errors like NEED_SPEAKER_ROLES
                showError(data.analysis_text); 
            } else if (data.analysis_text) {
                // Log the raw text before attempting to format it
                console.log('Raw analysis text:\n', data.analysis_text);
                
                // Store raw text in a global variable or similar scope if needed elsewhere
                window.rawAnalysisText = data.analysis_text; // Keep for potential debug button
                
                let formattedHtml = '';
                try {
                    // Attempt to create formatted HTML
                    formattedHtml = enhanceTextFormatting(data.analysis_text);
                } catch (formatError) {
                    console.error("Error during text formatting:", formatError);
                    // Optionally show a specific formatting error message, or just fall back to raw text
                }

                // Use formatted HTML if successful, otherwise show raw text as fallback
                if (formattedHtml && formattedHtml.trim() !== '') {
                    analysisOutputPre.innerHTML = formattedHtml;
                } else {
                    // Fallback: Show raw text if formatting failed or returned empty
                    console.warn("Formatting failed or returned empty. Displaying raw text.");
                    analysisOutputPre.innerHTML = `<p style="color: orange; font-style: italic;">Could not format analysis. Displaying raw text:</p><pre style="white-space: pre-wrap; font-family: monospace; padding: 15px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; overflow-x: auto;">${data.analysis_text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`;
                }

                // Add a debug button that might be useful for troubleshooting
                const debugButton = document.createElement('button');
                debugButton.textContent = 'Toggle Raw/Formatted View';
                debugButton.style.marginTop = '20px';
                debugButton.style.padding = '8px 12px';
                debugButton.style.fontSize = '0.8em';
                debugButton.style.backgroundColor = '#f0f0f0';
                debugButton.style.border = '1px solid #ccc';
                debugButton.style.borderRadius = '4px';
                debugButton.style.cursor = 'pointer';
                
                debugButton.addEventListener('click', function() {
                    if (this.dataset.showingRaw === 'true') {
                        analysisOutputPre.innerHTML = formattedHtml;
                        this.textContent = 'Show Raw Text';
                        this.dataset.showingRaw = 'false';
                    } else {
                        // Show the raw text with line breaks preserved
                        analysisOutputPre.innerHTML = `<pre style="white-space: pre-wrap; font-family: monospace; padding: 15px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; overflow-x: auto;">${window.rawAnalysisText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`;
                        this.textContent = 'Show Formatted View';
                        this.dataset.showingRaw = 'true';
                    }
                });
                
                // Add the debug button to the bottom of the results
                analysisOutputPre.appendChild(debugButton);

                // ALWAYS show the results area if we got analysis_text
                resultsArea.style.display = 'block'; 
                resultsArea.scrollIntoView({ behavior: 'smooth' });

            } else {
                // This case means response was OK, but no error and no analysis_text
                showError('Received an empty analysis from the server.');
            }

        } catch (error) {
            // Error handling remains the same
            stopCarousel();
            loadingIndicator.style.display = 'none';
            console.error('Error during analysis:', error);
            showError('An unexpected client-side error occurred. Please check the console or try again.');
        } finally {
            // Ensure the button is always re-enabled after fetch completes or fails
            analyzeButton.disabled = false; 
        }
    });

    // Enhanced function to format the plain text output into structured HTML
    function enhanceTextFormatting(text) {
        let html = '';

        // Split text into lines for easier processing
        const lines = text.trim().split('\n');
        let currentSection = null; // To track which section we are in (breakdown, summaries, lists, tips)
        let currentListType = null; // To track if we are inside a specific list (e.g., Thinking questions)

        // Add debugging
        console.log("Starting text formatting. Lines to process:", lines.length);
        
        lines.forEach(line => {
            line = line.trim();
            if (!line) return; // Skip empty lines

            // --- Check for Section Titles FIRST ---
            // This ensures we close the previous section *before* processing the new title line.
            if (line.startsWith('Category breakdown:')) {
                if (currentListType === 'funnel-details' && currentSection === 'summaries') html += `</ul></div>`; // Close last funnel
                else if (currentListType && currentSection === 'lists') html += `</ul>`; // Close last aggregate list
                if (currentSection === 'lists') html += `</div>`; // Close lists section
                if (currentSection === 'summaries') html += `</div>`; // Close summaries section
                if (currentSection === 'tips') html += `</div>`; // Close tips section
                // Now start the new section
                html += `<div class="category-breakdown"><h3 class="section-title">Category breakdown:</h3><ul>`;
                currentSection = 'breakdown';
                currentListType = null;
            }
            else if (line.startsWith('Funnel summaries:')) {
                if (currentSection === 'breakdown') html += `</ul></div>`; // Close breakdown list
                else if (currentListType && currentSection === 'lists') html += `</ul>`; // Close last aggregate list
                if (currentSection === 'lists') html += `</div>`; // Close lists section
                if (currentSection === 'tips') html += `</div>`; // Close tips section
                // Now start the new section
                html += `<div class="funnel-summaries"><h3 class="section-title">Funnel summaries:</h3>`;
                currentSection = 'summaries';
                currentListType = null; // Reset list type for the new section
            }
            else if (line.startsWith('Aggregate lists (tagged):')) {
                if (currentListType === 'funnel-details' && currentSection === 'summaries') html += `</ul></div>`; // Close last funnel
                if (currentSection === 'summaries') html += `</div>`; // Close summaries section
                else if (currentSection === 'breakdown') html += `</ul></div>`; // Close breakdown list
                else if (currentSection === 'tips') html += `</div>`; // Close tips section
                // Now start the new section
                html += `<div class="aggregate-lists"><h3 class="section-title">Aggregate lists (tagged):</h3>`;
                currentSection = 'lists';
                currentListType = null; // Reset list type for the new section
            }
             else if (line.startsWith('Coaching tips:')) {
                if (currentListType === 'funnel-details' && currentSection === 'summaries') html += `</ul></div>`; // Close last funnel
                else if (currentListType && currentSection === 'lists') html += `</ul>`; // Close last aggregate list
                if (currentSection === 'lists') html += `</div>`; // Close lists section
                if (currentSection === 'summaries') html += `</div>`; // Close summaries section
                else if (currentSection === 'breakdown') html += `</ul></div>`; // Close breakdown list
                 // Now start the new section
                html += `<div class="coaching-tips-section"><h3 class="section-title">Coaching tips:</h3>`;
                currentSection = 'tips';
                currentListType = null;
            }
            // --- Score Header (processed after potential section closing) ---
            else if (line.startsWith('Final Score:')) {
                // Close any potentially open section before the score header
                if (currentListType === 'funnel-details' && currentSection === 'summaries') html += `</ul></div>`;
                else if (currentListType && currentSection === 'lists') html += `</ul>`;
                if (currentSection === 'breakdown') html += `</ul></div>`;
                if (currentSection === 'summaries') html += `</div>`;
                if (currentSection === 'lists') html += `</div>`;
                if (currentSection === 'tips') html += `</div>`;

                const match = line.match(/Final Score:\s*(\d+\/\d+)\s*\(([^)]+)\)/);
                if (match) {
                    html += `<div class="score-header">Final Score: <span class="score-value">${match[1]}</span> (<span class="interpretation">${match[2]}</span>)</div>`;
                    currentSection = null; // Reset section after score
                    currentListType = null;
                } else {
                    html += `<p>${line}</p>`; // Fallback
                }
            } 
            // --- Content within Sections (if not a title or score header) ---
            else {
                // If no section has been identified yet (e.g., lines before 'Final Score'), skip.
                if (!currentSection) return;

                switch (currentSection) {
                    case 'breakdown':
                        const breakdownMatch = line.match(/•\s*([^–]+)\s*–\s*(.*)/);
                        if (breakdownMatch) {
                            html += `<li>${breakdownMatch[1].trim()}: <span class="category-score">${breakdownMatch[2].trim()}</span></li>`;
                        }
                        break;

                    case 'summaries':
                        console.log("Processing line in 'summaries' section:", line);
                        const funnelHeaderMatch = line.match(/(###\s*F\d+)(\s*\(.*\))?/);
                        if (funnelHeaderMatch) {
                            console.log("Found funnel header:", line);
                            // Close PREVIOUS funnel's list/div if open
                            if (currentListType === 'funnel-details') {
                                html += `</ul></div>`;
                            }
                            // Start the new funnel div and list
                            html += `<div class="funnel-summary"><div class="funnel-title">${funnelHeaderMatch[1]}${funnelHeaderMatch[2] ? `<span>${funnelHeaderMatch[2]}</span>` : ''}</div><ul class="detail-list">`;
                            currentListType = 'funnel-details';
                        } 
                        // Handle lines that start with '-' which are the funnel details
                        else if (line.startsWith('-')) {
                            console.log("Found detail line:", line);
                            // Always ensure we're in a detail list when we see a '-' line in summaries section
                            if (currentListType !== 'funnel-details') {
                                console.warn("Found a detail line but not in funnel-details context. Creating list anyway.");
                                html += `<ul class="detail-list">`;
                                currentListType = 'funnel-details';
                            }
                            
                            // Try to match the common pattern like "- Type: Content"
                            const detailMatch = line.match(/-\s*([^:]+):\s*(.*)/);
                            if (detailMatch) {
                                html += `<li><strong>${detailMatch[1].trim()}:</strong> ${formatQuote(detailMatch[2])}</li>`;
                            } else {
                                // Handle other formats of detail lines
                                html += `<li>${formatQuote(line.substring(1).trim())}</li>`;
                            }
                        }
                        // Handle other content in the summaries section that's not a header or detail
                        else if (currentListType === 'funnel-details' && !line.startsWith('Aggregate lists')) {
                            // If we're in a funnel and the line doesn't start a new section, treat it as part of the current funnel
                            console.log("Processing other line in funnel:", line);
                            if (line.trim().length > 0) {
                                html += `<li class="misc-item">${line}</li>`;
                            }
                        }
                        // Don't close the funnel detail list until we hit a new section explicitly
                        break;

                    case 'lists':
                        // Handle list titles and items in the Aggregate Lists section
                        const trimmedLine = line.trim(); // Trim the line once

                        // Check if this line looks like a list title (ends with colon)
                        if (trimmedLine.endsWith(':') && 
                            !trimmedLine.startsWith('•') && 
                            !trimmedLine.startsWith('-') && 
                            !trimmedLine.startsWith('*')) {
                            
                            // If we're currently in a list, close it
                            if (currentListType) {
                                html += `</ul>`;
                            }
                            
                            // Get the title text (without the colon)
                            const titleText = trimmedLine.substring(0, trimmedLine.lastIndexOf(':')).trim();
                            
                            // Check if this is the Missed Opportunities section
                            const isMissedOpps = titleText.toLowerCase().includes('missed');
                            const listClass = isMissedOpps ? 'missed-opportunities' : '';
                            
                            // Add the title and start a new list
                            html += `<p class="list-title-paragraph" style="margin-top: 15px;"><strong>${titleText}:</strong></p>`;
                            html += `<ul class="detail-list ${listClass}">`;
                            
                            // Remember what list we're in
                            currentListType = titleText.toLowerCase();
                        }
                        // Check if this line is a list item (starts with bullet: •, -, or *) and currentListType is set
                        else if ((trimmedLine.startsWith('•') || 
                                 trimmedLine.startsWith('-') || 
                                 trimmedLine.startsWith('*')) && currentListType) {
                            
                            // Get the text after the bullet
                            let itemText = trimmedLine;
                            if (itemText.startsWith('•')) itemText = itemText.substring(1).trim();
                            else if (itemText.startsWith('-')) itemText = itemText.substring(1).trim();
                            else if (itemText.startsWith('*')) itemText = itemText.substring(1).trim();
                            
                            // Add the list item if it's not empty
                            if (itemText) {
                                html += `<li>${formatQuote(itemText)}</li>`;
                            }
                        }
                        // Handle cases where a line might belong to a list but doesn't start with a bullet (e.g., wrapped text)
                        // This is a basic heuristic and might need refinement based on actual output variations.
                        else if (currentListType && trimmedLine.length > 0 && !trimmedLine.endsWith(':')) {
                            // Append to the last list item if it exists and seems like a continuation
                            if (html.endsWith('</li>')) {
                                // Remove closing tag, append text, add tag back
                                html = html.slice(0, -5) + ` ${formatQuote(trimmedLine)}</li>`;
                            } else {
                                // Otherwise, treat as a new (potentially malformed) list item
                                html += `<li>${formatQuote(trimmedLine)}</li>`;
                            }
                        }
                        break;

                    case 'tips':
                        // Treat each paragraph as a tip
                        html += `<p>${formatTipParagraph(line)}</p>`;
                        break;

                    default:
                        // Avoid adding potentially stray lines if section is unknown
                        break;
                }
            }
        });

        // Close any open sections/lists at the very end
        if (currentListType === 'funnel-details' && currentSection === 'summaries') {
             html += `</ul></div>`; // Close last funnel
        } else if (currentListType && currentSection === 'lists') {
            html += `</ul>`; // Close last list in aggregates
        }
        // Close the overall section div if needed
        if (currentSection === 'breakdown') html += `</ul></div>`; // Needs closing ul and div
        if (currentSection === 'summaries') html += `</div>`; // Div only, ul closed above or not needed
        if (currentSection === 'lists') html += `</div>`; // Div only, ul closed above
        if (currentSection === 'tips') html += `</div>`;

        return html;
    }
    
    // Helper to format quotes within list items or funnel details
    function formatQuote(text) {
        // Simple approach: escape HTML and wrap in quotes if not already quoted
        text = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        if (text.startsWith('"') && text.endsWith('"')) {
            return text;
        } else {
            return `"${text}"`;
        }
    }
    
    // Helper to format coaching tip paragraphs, adding <code> tags for quotes
    function formatTipParagraph(text) {
        // Find potential quotes (simple heuristic: text within double quotes)
        // Escape HTML first to avoid breaking tags
        text = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
        // Replace quoted text with <code> tags
        text = text.replace(/"([^"]+)"/g, (match, p1) => `<code>${p1}</code>`);
        // Replace markdown-style bold (**text**) with <strong> tags
        text = text.replace(/\*\*([^\*\*]+)\*\*/g, (match, p1) => `<strong>${p1}</strong>`);
        return text;
    }

    function showError(message) {
        errorOutputP.innerHTML = message; // Use innerHTML if message might contain HTML
        errorOutputDiv.style.display = 'block';
        resultsArea.style.display = 'none';
        errorOutputDiv.scrollIntoView({ behavior: 'smooth' });
    }

    function hideError() {
        errorOutputDiv.style.display = 'none';
        errorOutputP.innerHTML = '';
    }
    
    // Initialize first slide of carousel if items exist
    if (carouselItems.length > 0) {
        carouselItems[0].classList.add('active');
    }

    // Delete the entire ensureAggregateListsSection function - we don't need it anymore
    function ensureAggregateListsSection(rawText) {
        // This function is no longer needed as we're removing the section
        return; // Do nothing
    }
}); 