/**
 * Lead Kanban Board JavaScript
 * Uses Sortable.js for drag-and-drop lead status management
 */

(function () {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function () {
        initializeLeadKanban();
    });

    function initializeLeadKanban() {
        const columns = document.querySelectorAll('.column-cards');

        if (columns.length === 0) {
            console.warn('No Kanban columns found');
            return;
        }

        // Initialize Sortable for each column
        columns.forEach(column => {
            new Sortable(column, {
                group: 'leads',
                animation: 150,
                ghostClass: 'drag-ghost',
                chosenClass: 'drag-chosen',
                dragClass: 'drag-active',
                handle: '.lead-card',
                draggable: '.lead-card',

                onStart: function (evt) {
                    evt.item.classList.add('dragging');
                },

                onEnd: function (evt) {
                    evt.item.classList.remove('dragging');

                    const oldStatusId = evt.from.dataset.statusId;
                    const newStatusId = evt.to.dataset.statusId;

                    if (oldStatusId !== newStatusId) {
                        const leadId = evt.item.dataset.leadId;
                        updateLeadStatus(leadId, newStatusId, evt.item);
                    }
                }
            });
        });

        console.log('Lead Kanban board initialized with Sortable.js');
    }

    function updateLeadStatus(leadId, newStatusId, cardElement) {
        const csrfToken = getCSRFToken();

        if (!csrfToken) {
            console.error('CSRF token not found');
            showNotification('Error: Unable to update status', 'error');
            return;
        }

        // Show loading state
        cardElement.classList.add('updating');

        fetch(`/leads/${leadId}/update-status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                status_id: newStatusId
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
                    cardElement.dataset.statusId = newStatusId;

                    // Update score if returned
                    if (data.new_score !== undefined) {
                        updateCardScore(cardElement, data.new_score);
                    }

                    // Update column stats
                    updateColumnStats();

                    // Show success notification
                    showNotification(data.message || 'Status updated successfully', 'success');

                    console.log('Status updated:', data);
                } else {
                    console.error('Failed to update status:', data.message);
                    showNotification(data.message || 'Failed to update status', 'error');
                    location.reload();
                }
            })
            .catch(error => {
                cardElement.classList.remove('updating');
                console.error('Error updating status:', error);
                showNotification('Network error. Please try again.', 'error');
                location.reload();
            });
    }

    function updateCardScore(cardElement, newScore) {
        const scoreElement = cardElement.querySelector('.card-score');
        if (scoreElement) {
            // Remove existing score classes
            scoreElement.classList.remove('score-high', 'score-medium', 'score-low');

            // Add new score class
            if (newScore >= 75) {
                scoreElement.classList.add('score-high');
            } else if (newScore >= 50) {
                scoreElement.classList.add('score-medium');
            } else {
                scoreElement.classList.add('score-low');
            }

            // Update score text (find the text node)
            const textNodes = Array.from(scoreElement.childNodes).filter(
                node => node.nodeType === Node.TEXT_NODE
            );
            if (textNodes.length > 0) {
                textNodes[textNodes.length - 1].textContent = ' ' + newScore;
            }
        }
    }

    function updateColumnStats() {
        const columns = document.querySelectorAll('.column-cards');

        columns.forEach(column => {
            const statusId = column.dataset.statusId;
            const cards = column.querySelectorAll('.lead-card');
            const count = cards.length;

            // Update count badge
            const countBadge = document.querySelector(`[data-status-id="${statusId}"] .column-count`);
            if (countBadge) {
                countBadge.textContent = count;
            }

            // Show/hide empty state
            const emptyState = column.querySelector('.empty-column');
            if (count === 0 && !emptyState) {
                column.innerHTML = `
                    <div class="empty-column">
                        <svg fill="currentColor" viewBox="0 0 16 16">
                            <path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v13.5a.5.5 0 0 1-.777.416L8 13.101l-5.223 2.815A.5.5 0 0 1 2 15.5V2zm2-1a1 1 0 0 0-1 1v12.566l4.723-2.482a.5.5 0 0 1 .554 0L13 14.566V2a1 1 0 0 0-1-1H4z"/>
                        </svg>
                        <div>No leads</div>
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
        const allCards = document.querySelectorAll('.lead-card');
        const totalCount = allCards.length;

        // Update total leads stat
        const totalCountElements = document.querySelectorAll('.pipeline-stats .stat-value');
        if (totalCountElements.length > 0) {
            totalCountElements[0].textContent = totalCount;
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
        
        .lead-card.updating {
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
