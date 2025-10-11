const testInterface = {
    questions: [],
    userAnswers: {},
    currentQuestionIndex: 0,
    sessionId: null,
    timerInterval: null,
    startTime: null,

    async initializeTest() {
        const testInterfaceElement = document.querySelector('.test-interface');
        const category = testInterfaceElement.dataset.category || 'all';

        try {
            const response = await fetch(`/api/test/start/${category}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                
                // Check if it's a free tier limit error
                if (errorData.error === 'free_limit_reached') {
                    // Show toast notification
                    if (window.showToast) {
                        showToast(errorData.message, 'error');
                    }
                    
                    // Redirect to dashboard after 3 seconds
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 3000);
                    
                    document.getElementById('questionText').innerHTML = `
                        <div style="text-align: center; padding: 2rem;">
                            <h3 style="color: #dc3545; margin-bottom: 1rem;">Free Tier Limit Reached</h3>
                            <p>${errorData.message}</p>
                            <a href="/subscribe" class="btn btn-primary" style="margin-top: 1rem;">Subscribe Now</a>
                        </div>
                    `;
                    return;
                }
                
                throw new Error('Failed to start test.');
            }
            
            const data = await response.json();

            this.questions = data.questions;
            this.sessionId = data.session_id;
            this.userAnswers = {};
            this.currentQuestionIndex = 0;

            document.getElementById('totalQuestions').textContent = this.questions.length;

            this.renderQuestion();
            this.renderNavigator();
            this.startTimer(data.time_limit_seconds);

        } catch (error) {
            console.error('Error initializing test:', error);
            document.getElementById('questionText').textContent = 'Failed to load test. Please try again.';
        }
    },

    renderQuestion() {
        const question = this.questions[this.currentQuestionIndex];
        if (!question) return;

        document.getElementById('currentQuestion').textContent = this.currentQuestionIndex + 1;
        document.getElementById('headerCategory').textContent = question.category;
        document.getElementById('questionText').innerHTML = question.text;

        // Image
        const questionContentEl = document.querySelector('.question-content-wrapper');
        const imageContainer = document.getElementById('imageContainer');
        const imagePlaceholder = document.getElementById('imagePlaceholder');
        const questionImage = document.getElementById('questionImage');
        const imageControls = document.getElementById('imageControls');

        if (question.image_url && questionImage) {
            if (questionContentEl) questionContentEl.classList.add('has-image');
            imagePlaceholder.style.display = 'none';
            questionImage.src = question.image_url;
            questionImage.alt = `Image for question: ${question.text}`;
            questionImage.style.display = 'block';
            questionImage.style.transform = 'scale(1)'; // Reset zoom
            imageControls.style.display = 'flex';
            document.querySelector('.question-image').style.display = 'block';
        } else {
            if (questionContentEl) questionContentEl.classList.remove('has-image');
            if (imagePlaceholder) imagePlaceholder.style.display = 'flex';
            if (questionImage) questionImage.style.display = 'none';
            if (imageControls) imageControls.style.display = 'none';
            document.querySelector('.question-image').style.display = 'none';
        }

        // Options
        for (const option of ['A', 'B', 'C', 'D']) {
            const optionEl = document.getElementById(`option${option}Text`);
            if (optionEl) {
                const optionContainer = optionEl.closest('.option-item');
                if (question.options && question.options[option]) {
                    optionEl.textContent = question.options[option];
                    if (optionContainer) optionContainer.style.display = '';
                } else {
                    if (optionContainer) optionContainer.style.display = 'none';
                }
            }
        }

        // Reset radio buttons and restore selection
        const selectedAnswer = this.userAnswers[question.id];
        document.querySelectorAll('input[name="answer"]').forEach(radio => {
            radio.checked = (radio.value === selectedAnswer);
        });

        this.updateNavigationButtons();
        this.updateNavigatorHighlight();
    },

    renderNavigator() {
        const grid = document.getElementById('questionGrid');
        grid.innerHTML = '';
        this.questions.forEach((q, index) => {
            const item = document.createElement('div');
            item.className = 'grid-item';
            item.textContent = index + 1;
            item.dataset.index = index;
            item.onclick = () => this.jumpToQuestion(index);
            grid.appendChild(item);
        });
    },

    updateNavigationButtons() {
        document.getElementById('prevBtn').disabled = (this.currentQuestionIndex === 0);
        document.getElementById('nextBtn').style.display = (this.currentQuestionIndex === this.questions.length - 1) ? 'none' : 'inline-block';
        document.getElementById('finishBtn').style.display = (this.currentQuestionIndex === this.questions.length - 1) ? 'inline-block' : 'none';
    },

    updateNavigatorHighlight() {
        document.querySelectorAll('.grid-item').forEach(item => {
            const index = parseInt(item.dataset.index, 10);
            item.classList.remove('current', 'answered');

            if (this.userAnswers[this.questions[index].id]) {
                item.classList.add('answered');
            }
            if (index === this.currentQuestionIndex) {
                item.classList.add('current');
            }
        });
    },

    nextQuestion() {
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
            this.renderQuestion();
        }
    },

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.renderQuestion();
        }
    },

    jumpToQuestion(index) {
        this.currentQuestionIndex = index;
        this.renderQuestion();
    },

    selectOption(option) {
        const questionId = this.questions[this.currentQuestionIndex].id;
        this.userAnswers[questionId] = option;
        document.querySelector(`input[name='answer'][value='${option}']`).checked = true;
        this.updateNavigatorHighlight();
    },

    startTimer(duration) {
        let timeLeft = duration;
        this.startTime = Date.now();
        const timerEl = document.getElementById('timeRemaining');

        this.timerInterval = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

            if (timeLeft <= 0) {
                clearInterval(this.timerInterval);
                this.finishTest();
            }
            timeLeft--;
        }, 1000);
    },

    async submitTest() {
        clearInterval(this.timerInterval);
        const timeTaken = Math.floor((Date.now() - this.startTime) / 1000);

        // Hide completion modal
        document.getElementById('completionModal').style.display = 'none';

        try {
            const response = await fetch('/submit_test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    answers: this.userAnswers,
                    time_taken: timeTaken
                })
            });
            if (!response.ok) {
                throw new Error('Submission failed');
            }
            const result = await response.json();
            this.showResults(result);
        } catch (error) {
            console.error('Error submitting test:', error);
            alert('Failed to submit test results. Please check your connection and try again.');
        }
    },

    finishTest() {
        // This function now just shows the confirmation modal
        const answeredCount = Object.keys(this.userAnswers).length;
        const timeElapsed = Math.floor((Date.now() - this.startTime) / 1000);
        const minutes = Math.floor(timeElapsed / 60);
        const seconds = timeElapsed % 60;

        document.getElementById('answeredCount').textContent = `${answeredCount} / ${this.questions.length}`;
        document.getElementById('timeUsed').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        document.getElementById('completionModal').style.display = 'flex';
    },

    showResults(result) {
        document.getElementById('scoreValue').textContent = `${result.score}/${result.total}`;
        document.getElementById('scorePercentage').textContent = `${result.percentage}%`;

        const reviewBtn = document.getElementById('reviewAnswersBtn');
        if (result.test_result_id) {
            reviewBtn.href = `/test_review/${result.test_result_id}`;
            reviewBtn.style.display = 'inline-flex';
        }

        const messageEl = document.getElementById('resultMessage');
        if (result.percentage >= 80) {
            messageEl.textContent = 'Excellent work, you passed!';
        } else if (result.percentage >= 50) {
            messageEl.textContent = 'Good effort, but more practice is needed.';
        } else {
            messageEl.textContent = 'Keep practicing, you can do it!';
        }

        document.getElementById('resultsModal').style.display = 'flex';
    }
};

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Main test controls
    document.getElementById('nextBtn').addEventListener('click', () => testInterface.nextQuestion());
    document.getElementById('prevBtn').addEventListener('click', () => testInterface.previousQuestion());
    document.getElementById('finishBtn').addEventListener('click', () => testInterface.finishTest());

    // Radio button selection
    document.querySelectorAll('input[name="answer"]').forEach(radio => {
        radio.addEventListener('change', (e) => testInterface.selectOption(e.target.value));
    });

    // Completion Modal controls
    document.getElementById('submitTestBtn').addEventListener('click', () => testInterface.submitTest());
    document.getElementById('continueTestBtn').addEventListener('click', () => {
        document.getElementById('completionModal').style.display = 'none';
    });
});

// Image zoom functions
let currentImageScale = 1;

function zoomTestImage(delta) {
    const img = document.getElementById('questionImage');
    if (!img || img.style.display === 'none') return;
    
    currentImageScale = Math.max(0.5, Math.min(3, currentImageScale + delta));
    img.style.transform = `scale(${currentImageScale})`;
}

function resetTestImageZoom() {
    const img = document.getElementById('questionImage');
    if (!img) return;
    
    currentImageScale = 1;
    img.style.transform = 'scale(1)';
}
