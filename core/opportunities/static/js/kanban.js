/**
 * Kanban Board JavaScript for Opportunity Pipeline
 * Uses Sortable.js for drag-and-drop functionality
 */

(function () {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function () {
        initializeKanban();
    });

    function initializeKanban() {
        const columns = document.querySelectorAll('.column-cards');

        if (columns.length === 0) {
            console.warn('No Kanban columns found');
            return;
        }

        // Initialize Sortable for each column
        columns.forEach(column => {
            new Sortable(column, {
                group: 'opportunities',
                animation: 150,
                ghostClass: 'drag-ghost',
                chosenClass: 'drag-chosen',
                dragClass: 'drag-active',
                handle: '.opportunity-card',
                draggable: '.opportunity-card',

                onStart: function (evt) {
                    // Add visual feedback when dragging starts
                    evt.item.classList.add('dragging');
                },

                onEnd: function (evt) {
                    // Remove visual feedback
                    evt.item.classList.remove('dragging');

                    // Check if item moved to a different column
                    const oldStageId = evt.from.dataset.stageId;
                    const newStageId = evt.to.dataset.stageId;

                    if (oldStageId !== newStageId) {
                        const opportunityId = evt.item.dataset.opportunityId;
                        updateOpportunityStage(opportunityId, newStageId, evt.item);
                    }
                }
            });
        });

        console.log('Kanban board initialized with Sortable.js');
    }

    function updateOpportunityStage(opportunityId, newStageId, cardElement) {
        const csrfToken = getCSRFToken();

        if (!csrfToken) {
            console.error('CSRF token not found');
            showNotification('Error: Unable to update stage', 'error');
            return;
        }

        // Show loading state
        cardElement.classList.add('updating');

        fetch(`/opportunities/${opportunityId}/update-stage/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                stage_id: newStageId
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                cardElement.classList.remove('updating');

                if (data.success) {
                    // Update card's stage data attribute
                    cardElement.dataset.stageId = newStageId;

                    // Update probability if returned
                    if (data.new_probability !== undefined) {
                        updateCardProbability(cardElement, data.new_probability);
                    }

                    // Update column counts and values
                    updateColumnStats();

                    // Show success notification
                    showNotification(data.message || 'Stage updated successfully', 'success');

                    console.log('Stage updated:', data);
                } else {
                    // Revert the change
                    console.error('Failed to update stage:', data.message);
                    showNotification(data.message || 'Failed to update stage', 'error');
                    location.reload(); // Reload to revert
                }
            })
            .catch(error => {
                cardElement.classList.remove('updating');
                console.error('Error updating stage:', error);
                showNotification('Network error. Please try again.', 'error');
                location.reload(); // Reload to revert
            });
    }

    function updateCardProbability(cardElement, newProbability) {
        // Convert to percentage (0-100)
        const probabilityPercent = Math.round(newProbability * 100);

        // Update probability bar
        const probabilityBar = cardElement.querySelector('.probability-fill');
        if (probabilityBar) {
            probabilityBar.style.width = probabilityPercent + '%';
        }

        // Update probability text
        const probabilityText = cardElement.querySelector('.card-probability');
        if (probabilityText) {
            const textNode = probabilityText.childNodes[probabilityText.childNodes.length - 1];
            if (textNode && textNode.nodeType === Node.TEXT_NODE) {
                textNode.textContent = probabilityPercent + '%';
            }
        }
    }

    function updateColumnStats() {
        const columns = document.querySelectorAll('.column-cards');

        columns.forEach(column => {
            const stageId = column.dataset.stageId;
            const cards = column.querySelectorAll('.opportunity-card');
            const count = cards.length;

            // Update count badge
            const countBadge = document.querySelector(`[data-stage-id="${stageId}"] .column-count`);
            if (countBadge) {
                countBadge.textContent = count;
            }

            // Calculate total value for this column
            let totalValue = 0;
            cards.forEach(card => {
                const amountText = card.querySelector('.card-amount')?.textContent;
                if (amountText) {
                    // Remove $ and commas, then parse
                    const amount = parseFloat(amountText.replace(/[$,]/g, ''));
                    if (!isNaN(amount)) {
                        totalValue += amount;
                    }
                }
            });

            // Update column value
            const columnValue = document.querySelector(`[data-stage-id="${stageId}"] .column-value`);
            if (columnValue) {
                columnValue.textContent = '$' + formatNumber(totalValue);
            }

            // Show/hide empty state
            const emptyState = column.querySelector('.empty-column');
            if (count === 0 && !emptyState) {
                column.innerHTML = `
                    <div class="empty-column">
                        <svg fill="currentColor" viewBox="0 0 16 16">
                            <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v13.5a.5.5 0 0 1-.777.416L8 13.101l-5.223 2.815A.5.5 0 0 1 2 15.5V2zm2-1a1 1 0 0 0-1 1v12.566l4.723-2.482a.5.5 0 0 1 .554 0L13 14.566V2a1 1 0 0 0-1-1H4z"/>
                        </svg>
                        <div>No opportunities</div>
                    </div>
                `;
            } else if (count > 0 && emptyState) {
                emptyState.remove();
            }
        });

        // Update overall stats
        updateOverallStats();
    }

    function updateOverallStats() {
        const allCards = document.querySelectorAll('.opportunity-card');
        let totalValue = 0;
        let weightedValue = 0;

        allCards.forEach(card => {
            const amountText = card.querySelector('.card-amount')?.textContent;
            const probabilityBar = card.querySelector('.probability-fill');

            if (amountText) {
                const amount = parseFloat(amountText.replace(/[$,]/g, ''));
                if (!isNaN(amount)) {
                    totalValue += amount;

                    // Calculate weighted value
                    if (probabilityBar) {
                        const probability = parseFloat(probabilityBar.style.width) / 100;
                        weightedValue += amount * probability;
                    }
                }
            }
        });

        // Update header stats
        const totalValueElement = document.querySelector('.pipeline-stats .stat-value');
        if (totalValueElement) {
            totalValueElement.textContent = '$' + formatNumber(totalValue);
        }

        const weightedValueElement = document.querySelectorAll('.pipeline-stats .stat-value')[1];
        if (weightedValueElement) {
            weightedValueElement.textContent = '$' + formatNumber(weightedValue);
        }

        const countElement = document.querySelectorAll('.pipeline-stats .stat-value')[2];
        if (countElement) {
            countElement.textContent = allCards.length;
        }
    }

    function getCSRFToken() {
        // Try to get from hidden input
        const tokenInput = document.getElementById('csrf-token');
        if (tokenInput) {
            return tokenInput.value;
        }

        // Try to get from cookie
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function formatNumber(num) {
        return Math.round(num).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `kanban-notification kanban-notification-${type}`;
        notification.textContent = message;

        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            font-size: 14px;
            font-weight: 500;
            animation: slideIn 0.3s ease-out;
        `;

        // Add to page
        document.body.appendChild(notification);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
        
        .opportunity-card.updating {
            opacity: 0.6;
            pointer-events: none;
        }
        
        .drag-ghost {
            opacity: 0.4;
        }
        
        .drag-chosen {
            cursor: grabbing !important;
        }
        
        .drag-active {
            cursor: grabbing !important;
            transform: rotate(5deg);
        }
    `;
    document.head.appendChild(style);

})();
