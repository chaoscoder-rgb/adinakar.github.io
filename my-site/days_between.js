// Days Between Utility Module
(function() {
    const showDaysBetweenLink = document.getElementById('showDaysBetweenLink');
    const daysBetweenDetails = document.getElementById('daysBetweenDetails');
    const closeDaysBetweenLink = document.getElementById('closeDaysBetweenLink');
    const daysBetweenForm = document.getElementById('daysBetweenForm');
    const daysBetweenResult = document.getElementById('daysBetweenResult');
    const daysBetweenResetBtn = document.getElementById('daysBetweenResetBtn');
    if (showDaysBetweenLink && daysBetweenDetails && closeDaysBetweenLink && daysBetweenForm && daysBetweenResult && daysBetweenResetBtn) {
        showDaysBetweenLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (daysBetweenDetails.style.display === 'none') {
                daysBetweenDetails.style.display = 'block';
                this.style.display = 'none';
            }
            document.getElementById('showMortgageLink').style.display = 'inline';
            document.getElementById('mortgageCalculatorDetails').style.display = 'none';
        });
        closeDaysBetweenLink.addEventListener('click', function(e) {
            e.preventDefault();
            daysBetweenDetails.style.display = 'none';
            showDaysBetweenLink.style.display = 'inline';
        });
        daysBetweenForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var start = document.getElementById('startDate').value;
            var end = document.getElementById('endDate').value;
            if (start && end) {
                var startDate = new Date(start);
                var endDate = new Date(end);
                var diffTime = endDate - startDate;
                var diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));
                daysBetweenResult.textContent = 'Days between: ' + diffDays;
            } else {
                daysBetweenResult.textContent = '';
            }
        });
        daysBetweenResetBtn.addEventListener('click', function() {
            daysBetweenResult.textContent = '';
        });
    }
})();
