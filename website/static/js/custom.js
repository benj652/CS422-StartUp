document.addEventListener('DOMContentLoaded', function() {
    // Target the Get Started button ID from .html file
    const getStartedBtn = document.getElementById('get-started-btn');

    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', function() {
        
            trackAction('get_started_click');
        });
    }
});

/**
 * Sends a POST request to the Flask backend to log an action
 * @param {string} actionType - The 'atype' string saved in the DB
 */
function trackAction(actionType) {
    fetch("/track-action", { 
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