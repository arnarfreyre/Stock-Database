// render-utils.js - Shared rendering utilities for all pages

/**
 * Creates a card element based on item data and type
 * @param {Object} item - The data for the card
 * @param {string} type - Type of card ('chapter', 'formula', 'solver', 'problem-set')
 * @returns {HTMLElement} The created card element
 */
function createCard(item, type) {
    const isAvailable = item.status === 'available' || item.path !== null;
    
    // Create card element (link or div based on availability)
    const card = document.createElement(isAvailable && item.path ? 'a' : 'div');
    
    // Set class based on type
    const cardClass = type === 'solver' ? 'solver-card' : 
                      type === 'formula' ? 'chapter-card' : 
                      type === 'problem-set' ? 'problem-set-card' : 
                      'chapter-card';
    card.className = cardClass;
    
    // Set href if available
    if (isAvailable && item.path) {
        card.href = item.path;
    }
    
    // Style unavailable cards
    if (!isAvailable) {
        card.style.opacity = '0.7';
        card.style.cursor = 'not-allowed';
    }
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = item.title;
    card.appendChild(title);
    
    // Add description
    const description = document.createElement('p');
    description.textContent = item.description;
    card.appendChild(description);
    
    // Add PDF button for chapters if PDF is available
    if (type === 'chapter' && item.pdfFile) {
        const pdfButton = document.createElement('button');
        pdfButton.className = 'btn-primary';
        pdfButton.textContent = 'Open PDF';
        pdfButton.style.marginTop = '10px';
        pdfButton.style.marginBottom = '10px';
        pdfButton.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            const pdfPath = 'Chapters/' + item.pdfFile;
            // Open in same window for navigation consistency
            window.location.href = pdfPath;
        };
        card.appendChild(pdfButton);
    }
    
    // Add status badge
    const statusSpan = document.createElement('span');
    const statusClass = type === 'solver' ? 'solver-status' : 'chapter-status';
    const statusText = isAvailable ? 'Available' : 'Coming Soon';
    const statusModifier = isAvailable ? 'status-available' : 'status-coming-soon';
    statusSpan.className = `${statusClass} ${statusModifier}`;
    statusSpan.textContent = statusText;
    card.appendChild(statusSpan);
    
    return card;
}

/**
 * Renders cards into a container
 * @param {string} containerId - ID of the container element
 * @param {Array} items - Array of items to render
 * @param {string} type - Type of cards to render
 */
function renderCards(containerId, items, type) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID '${containerId}' not found`);
        return;
    }
    
    // Clear existing content
    container.innerHTML = '';
    
    // Create and append cards
    items.forEach(item => {
        const card = createCard(item, type);
        container.appendChild(card);
    });
    
    // Add animations
    addCardAnimations(container);
}

/**
 * Adds fade-in animations to cards
 * @param {HTMLElement} container - Container with cards
 */
function addCardAnimations(container) {
    const cards = container.querySelectorAll('.chapter-card, .solver-card, .problem-set-card');
    cards.forEach((card, index) => {
        // Initial state
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.5s ease';
        
        // Force browser to recognize the initial state
        card.offsetHeight;
        
        // Animate in with delay
        setTimeout(() => {
            const isAvailable = !card.style.cursor || card.style.cursor !== 'not-allowed';
            card.style.opacity = isAvailable ? '1' : '0.7';
            card.style.transform = 'translateY(0)';
        }, 50 + index * 100);
    });
}

/**
 * Creates a problem set card with buttons (special case for problem-sets.html)
 * @param {Object} ps - Problem set data
 * @returns {HTMLElement} The created card element
 */
function createProblemSetCard(ps) {
    const available = ps.pdfFile !== null;
    const hasSolution = ps.solutionFile !== null;
    
    const card = document.createElement('div');
    card.className = 'problem-set-card';
    if (!available) {
        card.style.opacity = '0.7';
        card.style.cursor = 'not-allowed';
    }
    
    // Title
    const title = document.createElement('h3');
    title.textContent = ps.title;
    card.appendChild(title);
    
    // Description
    const description = document.createElement('p');
    description.textContent = ps.description;
    card.appendChild(description);
    
    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'problem-set-actions';
    actions.onclick = function(e) {
        e.stopPropagation();
    };
    
    // Open PDF button
    const pdfButton = document.createElement('button');
    pdfButton.className = available ? 'btn-primary' : 'btn-primary btn-disabled';
    pdfButton.textContent = 'Open PDF';
    pdfButton.disabled = !available;
    if (available) {
        pdfButton.onclick = function() {
            const pdfPath = 'Problem sets/' + ps.pdfFile;
            // Open in same window for navigation consistency
            window.location.href = pdfPath;
        };
    }
    actions.appendChild(pdfButton);
    
    // Solutions button
    const solutionsButton = document.createElement('button');
    solutionsButton.className = hasSolution ? 'btn-secondary' : 'btn-secondary btn-disabled';
    solutionsButton.textContent = 'View Solutions';
    solutionsButton.disabled = !hasSolution;
    if (hasSolution) {
        solutionsButton.onclick = function() {
            const solutionPath = 'Solutions/' + ps.solutionFile;
            if (ps.solutionFile.endsWith('.html')) {
                window.location.href = solutionPath;
            } else {
                if (window.openPdfViewer) {
                    window.openPdfViewer(solutionPath, ps.title + ' - Solutions');
                } else {
                    window.location.href = solutionPath;
                }
            }
        };
    }
    actions.appendChild(solutionsButton);
    
    card.appendChild(actions);
    
    // Make entire card clickable to open PDF (if available)
    if (available) {
        card.style.cursor = 'pointer';
        card.onclick = function(e) {
            if (e.target.tagName !== 'BUTTON') {
                const pdfPath = 'Problem sets/' + ps.pdfFile;
                // Open in same window for navigation consistency
                window.location.href = pdfPath;
            }
        };
    }
    
    return card;
}

/**
 * Renders problem set cards (special case)
 * @param {string} containerId - ID of the container element
 * @param {Array} problemSets - Array of problem sets to render
 */
function renderProblemSets(containerId, problemSets) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID '${containerId}' not found`);
        return;
    }
    
    container.innerHTML = '';
    
    problemSets.forEach(ps => {
        const card = createProblemSetCard(ps);
        container.appendChild(card);
    });
    
    addCardAnimations(container);
    
    // Failsafe: Ensure all cards are visible after animation should be complete
    setTimeout(() => {
        const cards = container.querySelectorAll('.problem-set-card');
        cards.forEach(card => {
            if (card.style.opacity === '0' || card.style.opacity === '') {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    }, 2000);
}

// Export for browser use
if (typeof window !== 'undefined') {
    window.renderUtils = {
        createCard,
        renderCards,
        addCardAnimations,
        createProblemSetCard,
        renderProblemSets
    };
}