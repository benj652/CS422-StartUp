document.addEventListener('DOMContentLoaded', function() {
    const roadmapBtn = document.getElementById('roadmap-button');

    if (roadmapBtn) {
        roadmapBtn.addEventListener('click', function() {
            // Track that the user opened the modal
            trackAction('roadmap_modal_open');
        });
    }
});

/**
 * Sends a POST request to the Flask backend to log an action
 * @param {string} actionType - The 'atype' string saved in the DB
 */
function trackAction(actionType) {
    fetch("/track-action", { // Ensure this matches your route in landing_views
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ atype: actionType })
    })
    .then(response => response.json())
    .then(data => console.log('Action tracked:', actionType))
    .catch((error) => console.error('Error tracking action:', error));
}