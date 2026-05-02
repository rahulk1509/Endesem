/* AI Exam Corrector - Results Page JavaScript */

function downloadResults() {
    // Generate a text report
    const results = {
        algorithm: document.querySelector('.algorithm-used strong').textContent,
        filename: document.querySelector('.file-name strong').textContent,
        score: document.querySelector('.score-value').textContent,
        maxScore: document.querySelector('.score-max').textContent,
        percentage: document.querySelector('.percentage-text').textContent,
        timestamp: new Date().toLocaleString()
    };
    
    let reportContent = `AI EXAM CORRECTOR - GRADING REPORT\n`;
    reportContent += `${'='.repeat(50)}\n\n`;
    reportContent += `Generated: ${results.timestamp}\n`;
    reportContent += `Algorithm: ${results.algorithm}\n`;
    reportContent += `File: ${results.filename}\n`;
    reportContent += `Total Score: ${results.score}${results.maxScore}\n`;
    reportContent += `Percentage: ${results.percentage}\n\n`;
    
    // Extract question details
    const questionCards = document.querySelectorAll('.question-card');
    questionCards.forEach((card, index) => {
        const header = card.querySelector('.question-header h4').textContent;
        const score = card.querySelector('.question-score').textContent;
        const feedback = card.querySelector('.feedback-box p:last-child');
        
        reportContent += `${header}\n`;
        reportContent += `Score: ${score}\n`;
        if (feedback) {
            reportContent += `Feedback: ${feedback.textContent}\n`;
        }
        reportContent += `\n`;
    });
    
    // Create download link
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(reportContent));
    element.setAttribute('download', `grading_report_${Date.now()}.txt`);
    element.style.display = 'none';
    
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

// Smooth scroll to questions
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});
