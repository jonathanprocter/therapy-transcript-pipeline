document.addEventListener('DOMContentLoaded', function () {
    const filterForm = document.getElementById('filterForm');
    const keywordSearchInput = document.getElementById('keywordSearchInput');
    const filterClient = document.getElementById('filterClient');
    const filterStartDate = document.getElementById('filterStartDate');
    const filterEndDate = document.getElementById('filterEndDate');
    const filterStatus = document.getElementById('filterStatus');
    const filterThemes = document.getElementById('filterThemes');
    const filterMinSentiment = document.getElementById('filterMinSentiment');
    const filterMaxSentiment = document.getElementById('filterMaxSentiment');
    
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    const paginationContainer = document.getElementById('paginationContainer');

    const initialResultsMessage = `
        <div class="alert alert-info" role="alert">
            Use the filters and search bar to find transcripts. Results will appear here.
        </div>`;

    function showLoadingIndicator() {
        searchResultsContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Searching transcripts...</p>
            </div>`;
        if (applyFiltersBtn) applyFiltersBtn.disabled = true;
    }

    function hideLoadingIndicator() {
        if (applyFiltersBtn) applyFiltersBtn.disabled = false;
        // Results will overwrite the loading indicator
    }

    function renderResults(transcripts) {
        if (!transcripts || transcripts.length === 0) {
            searchResultsContainer.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    No transcripts found matching your criteria.
                </div>`;
            return;
        }

        let tableHtml = `
            <table class="table table-hover align-middle">
                <thead class="table-light">
                    <tr>
                        <th>Client</th>
                        <th>Filename</th>
                        <th>Session Date</th>
                        <th>Status</th>
                        <th>Key Themes</th>
                        <th>Sentiment</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        transcripts.forEach(transcript => {
            const sessionDate = transcript.session_date 
                ? new Date(transcript.session_date).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) 
                : 'N/A';
            
            let statusBadgeClass = 'bg-secondary';
            if (transcript.processing_status === 'completed') statusBadgeClass = 'bg-success';
            else if (transcript.processing_status === 'failed') statusBadgeClass = 'bg-danger';
            else if (transcript.processing_status === 'pending') statusBadgeClass = 'bg-warning text-dark';

            const themesHtml = transcript.key_themes && transcript.key_themes.length > 0
                ? transcript.key_themes.map(theme => `<span class="badge bg-light text-dark me-1 mb-1">${theme}</span>`).join('')
                : '<small class="text-muted">None</small>';

            const sentimentScore = typeof transcript.sentiment_score === 'number' 
                ? transcript.sentiment_score.toFixed(2) 
                : '<small class="text-muted">N/A</small>';
            
            // Basic link construction, assuming client_details_url_base is not available
            // In a real Flask app, you might pass a URL template or use a JS routing library.
            const clientDetailUrl = `/client/${transcript.client_id}`; 

            tableHtml += `
                <tr>
                    <td><a href="${clientDetailUrl}">${transcript.client_name || 'N/A'}</a></td>
                    <td>${transcript.original_filename || 'N/A'}</td>
                    <td>${sessionDate}</td>
                    <td><span class="badge ${statusBadgeClass}">${transcript.processing_status || 'Unknown'}</span></td>
                    <td><div class="theme-badges">${themesHtml}</div></td>
                    <td>${sentimentScore}</td>
                    <td>
                        <a href="/api/transcript/${transcript.id}/analysis" class="btn btn-sm btn-outline-primary view-analysis-btn-api" 
                           title="View Raw Analysis (API)" target="_blank">
                           <i class="fas fa-code"></i>
                        </a>
                         <!-- If a modal display for analysis is preferred on this page too: -->
                         <!-- <button type="button" class="btn btn-sm btn-outline-info view-analysis-modal-trigger" 
                                 data-transcript-id="${transcript.id}" 
                                 data-transcript-filename="${transcript.original_filename}"
                                 title="View Analysis Detail">
                             <i class="fas fa-eye"></i>
                         </button> -->
                    </td>
                </tr>
            `;
        });

        tableHtml += `</tbody></table>`;
        searchResultsContainer.innerHTML = tableHtml;
    }

    function renderPagination(pagination, hasResults) {
        paginationContainer.innerHTML = ''; // Clear previous pagination

        if (!hasResults || !pagination || pagination.total_pages <= 1) {
            return;
        }

        let paginationHtml = '<ul class="pagination justify-content-center">';

        // Previous button
        paginationHtml += `
            <li class="page-item ${pagination.page === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${pagination.page - 1}" aria-label="Previous">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;

        // Page number links (simplified example: show a few pages around current)
        const maxPagesToShow = 5;
        let startPage = Math.max(1, pagination.page - Math.floor(maxPagesToShow / 2));
        let endPage = Math.min(pagination.total_pages, startPage + maxPagesToShow - 1);

        if (endPage - startPage + 1 < maxPagesToShow) {
            startPage = Math.max(1, endPage - maxPagesToShow + 1);
        }
        
        if (startPage > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
            if (startPage > 2) {
                 paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${i === pagination.page ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        if (endPage < pagination.total_pages) {
            if (endPage < pagination.total_pages - 1) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.total_pages}">${pagination.total_pages}</a></li>`;
        }


        // Next button
        paginationHtml += `
            <li class="page-item ${pagination.page === pagination.total_pages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${pagination.page + 1}" aria-label="Next">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;

        paginationHtml += '</ul>';
        paginationContainer.innerHTML = paginationHtml;

        // Add event listeners to new pagination links
        paginationContainer.querySelectorAll('.page-link[data-page]').forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const pageNum = parseInt(this.dataset.page, 10);
                if (pageNum && pageNum !== pagination.page) {
                    performSearch(pageNum);
                }
            });
        });
    }

    async function performSearch(page = 1) {
        showLoadingIndicator();

        const params = { page: page, per_page: 10 }; // Default per_page, could be configurable

        if (keywordSearchInput.value.trim()) params.q = keywordSearchInput.value.trim();
        if (filterClient.value) params.client_id = filterClient.value;
        if (filterStartDate.value) params.start_date = filterStartDate.value;
        if (filterEndDate.value) params.end_date = filterEndDate.value;
        if (filterStatus.value) params.status = filterStatus.value;
        if (filterThemes.value.trim()) params.themes = filterThemes.value.trim();
        if (filterMinSentiment.value) params.min_sentiment = filterMinSentiment.value;
        if (filterMaxSentiment.value) params.max_sentiment = filterMaxSentiment.value;
        
        const queryString = new URLSearchParams(params).toString();

        try {
            const response = await fetch(`/api/transcripts/search?${queryString}`);
            if (!response.ok) {
                // Try to parse error from standardized response
                try {
                    const errorJson = await response.json();
                    if (errorJson && errorJson.error && errorJson.error.message) {
                        throw new Error(errorJson.error.message);
                    }
                } catch (parseError) {
                    // Fallback if error response is not JSON or not in expected format
                    throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
                }
            }

            const jsonResponse = await response.json();

            if (jsonResponse.success && jsonResponse.data) {
                renderResults(jsonResponse.data.transcripts);
                renderPagination(jsonResponse.data.pagination, jsonResponse.data.transcripts && jsonResponse.data.transcripts.length > 0);
                if (!jsonResponse.data.transcripts || jsonResponse.data.transcripts.length === 0) {
                     searchResultsContainer.innerHTML = `
                        <div class="alert alert-warning" role="alert">
                            No transcripts found matching your criteria.
                        </div>`;
                }
            } else if (jsonResponse.success && !jsonResponse.data) { // Success but no data (e.g. empty search)
                 searchResultsContainer.innerHTML = `
                        <div class="alert alert-warning" role="alert">
                            No transcripts found matching your criteria.
                        </div>`;
                 renderPagination(null, false); // Clear pagination
            }
            else { // API reported success: false
                const errorMessage = jsonResponse.error && jsonResponse.error.message 
                                     ? jsonResponse.error.message 
                                     : 'An unknown error occurred.';
                searchResultsContainer.innerHTML = `<div class="alert alert-danger" role="alert">Error: ${errorMessage}</div>`;
                renderPagination(null, false); // Clear pagination
            }
        } catch (error) {
            console.error('Search API call failed:', error);
            searchResultsContainer.innerHTML = `<div class="alert alert-danger" role="alert">Failed to fetch search results: ${error.message}</div>`;
            renderPagination(null, false); // Clear pagination
        } finally {
            hideLoadingIndicator();
        }
    }

    if (filterForm) {
        filterForm.addEventListener('submit', function (e) {
            e.preventDefault();
            performSearch(1); // Search from page 1 when filters are applied
        });
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function () {
            if (filterForm) filterForm.reset();
            searchResultsContainer.innerHTML = initialResultsMessage; // Reset to initial message
            paginationContainer.innerHTML = ''; // Clear pagination
            // Optionally, perform a search with no filters to show all/recent items:
            // performSearch(1); 
        });
    }
    
    // Initial state message
    searchResultsContainer.innerHTML = initialResultsMessage;
});

// Note: For a production app, consider more robust error handling, user feedback,
// and potentially debouncing for the keyword search if it were to trigger on input change.
// The "View Raw Analysis (API)" link is a placeholder; a modal similar to client_details.html
// could be implemented for a richer experience.
