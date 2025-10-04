// Mobile Test Interface JavaScript

const mobileTestInterface = {
    questions: [],
    currentQuestionIndex: 0,
    userAnswers: {},
    startTime: null,
    timerInterval: null,
    timeLimit: 480, // 8 minutes in seconds
    timeRemaining: 480,

    initializeTest() {
        const category = document.querySelector('.mobile-test-container').dataset.category;
        this.loadQuestions(category);
        this.setupEventListeners();
    },

    async loadQuestions(category) {
        try {
            const response = await fetch(`/api/test/start/${category}`);
            const data = await response.json();
            
            // API returns: {session_id, time_limit_seconds, questions}
            if (data.questions && data.questions.length > 0) {
                this.questions = data.questions;
                this.sessionId = data.session_id;
                this.timeLimit = data.time_limit_seconds || 480;
                this.timeRemaining = this.timeLimit;
                
                document.getElementById('mobileTotalQuestions').textContent = this.questions.length;
                
                this.startTimer();
                this.displayQuestion();
            } else {
                alert('No questions available for this category. Please try another.');
                window.location.href = '/take_test';
            }
        } catch (error) {
            console.error('Error loading questions:', error);
            alert('An error occurred. Please try again.');
            window.location.href = '/take_test';
        }
    },

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('mobilePrevBtn').addEventListener('click', () => this.previousQuestion());
        document.getElementById('mobileNextBtn').addEventListener('click', () => this.nextQuestion());
        document.getElementById('mobileFinishBtn').addEventListener('click', () => this.showCompletionModal());
        
        // Answer selection
        document.querySelectorAll('input[name="mobileAnswer"]').forEach(input => {
            input.addEventListener('change', (e) => this.selectAnswer(e.target.value));
        });

        // Completion modal actions
        document.getElementById('mobileContinueTestBtn').addEventListener('click', () => {
            document.getElementById('mobileCompletionModal').style.display = 'none';
            document.body.style.overflow = 'auto';
        });
        
        document.getElementById('mobileSubmitTestBtn').addEventListener('click', () => this.submitTest());

        // Prevent accidental page refresh
        window.addEventListener('beforeunload', (e) => {
            if (this.questions.length > 0) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    },

    displayQuestion() {
        const question = this.questions[this.currentQuestionIndex];
        
        // Update question counter
        document.getElementById('mobileCurrentQuestion').textContent = this.currentQuestionIndex + 1;
        
        // Update progress bar
        const progress = ((this.currentQuestionIndex + 1) / this.questions.length) * 100;
        document.getElementById('mobileProgressFill').style.width = `${progress}%`;
        
        // Display question text
        document.getElementById('mobileQuestionText').textContent = question.text;
        
        // Display image if exists
        const imageSection = document.getElementById('mobileImageSection');
        const questionImage = document.getElementById('mobileQuestionImage');
        
        if (question.image_url) {
            questionImage.src = question.image_url;
            imageSection.style.display = 'block';
        } else {
            imageSection.style.display = 'none';
        }
        
        // Display options - API returns options as {A: "text", B: "text", C: "text"}
        const optionLetters = ['A', 'B', 'C', 'D'];
        optionLetters.forEach(letter => {
            const optionElement = document.querySelector(`.mobile-option[data-option="${letter}"]`);
            const textElement = document.getElementById(`mobileOption${letter}Text`);
            
            if (question.options[letter]) {
                textElement.textContent = question.options[letter];
                optionElement.style.display = 'block';
            } else {
                optionElement.style.display = 'none';
            }
        });
        
        // Restore previous answer if exists
        const previousAnswer = this.userAnswers[question.id];
        if (previousAnswer) {
            document.getElementById(`mobileOption${previousAnswer}`).checked = true;
        } else {
            document.querySelectorAll('input[name="mobileAnswer"]').forEach(input => {
                input.checked = false;
            });
        }
        
        // Update navigation buttons
        this.updateNavigationButtons();
    },

    updateNavigationButtons() {
        const prevBtn = document.getElementById('mobilePrevBtn');
        const nextBtn = document.getElementById('mobileNextBtn');
        const finishBtn = document.getElementById('mobileFinishBtn');
        
        // Previous button
        prevBtn.disabled = this.currentQuestionIndex === 0;
        
        // Next/Finish button
        if (this.currentQuestionIndex === this.questions.length - 1) {
            nextBtn.style.display = 'none';
            finishBtn.style.display = 'flex';
        } else {
            nextBtn.style.display = 'flex';
            finishBtn.style.display = 'none';
        }
    },

    selectAnswer(answer) {
        const currentQuestion = this.questions[this.currentQuestionIndex];
        this.userAnswers[currentQuestion.id] = answer;
    },

    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.displayQuestion();
        }
    },

    nextQuestion() {
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
            this.displayQuestion();
        }
    },

    startTimer() {
        this.startTime = Date.now();
        
        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            
            const minutes = Math.floor(this.timeRemaining / 60);
            const seconds = this.timeRemaining % 60;
            const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            document.getElementById('mobileTimeRemaining').textContent = timeString;
            
            // Change color when time is running out
            const timerElement = document.querySelector('.mobile-timer');
            if (this.timeRemaining <= 60) {
                timerElement.style.color = '#dc3545';
            } else if (this.timeRemaining <= 120) {
                timerElement.style.color = '#ffc107';
            }
            
            if (this.timeRemaining <= 0) {
                clearInterval(this.timerInterval);
                this.submitTest();
            }
        }, 1000);
    },

    showCompletionModal() {
        const answeredCount = Object.keys(this.userAnswers).length;
        const timeTaken = this.timeLimit - this.timeRemaining;
        const minutes = Math.floor(timeTaken / 60);
        const seconds = timeTaken % 60;
        
        document.getElementById('mobileAnsweredCount').textContent = answeredCount;
        document.getElementById('mobileTimeUsed').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        document.getElementById('mobileCompletionModal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
    },

    async submitTest() {
        clearInterval(this.timerInterval);
        
        const timeTaken = this.timeLimit - this.timeRemaining;
        const answers = {};
        
        // Convert to dictionary format: {question_id: user_answer}
        this.questions.forEach(question => {
            const userAnswer = this.userAnswers[question.id] || null;
            answers[question.id] = userAnswer;
        });
        
        const testData = {
            session_id: this.sessionId,
            answers: answers,
            time_taken: timeTaken
        };
        
        try {
            const response = await fetch('/submit_test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(testData)
            });
            
            const result = await response.json();
            
            // API returns: {score, total, percentage, test_result_id}
            if (result.score !== undefined) {
                this.showResults(result);
            } else {
                alert('Failed to submit test. Please try again.');
            }
        } catch (error) {
            console.error('Error submitting test:', error);
            alert('An error occurred while submitting the test.');
        }
    },

    showResults(result) {
        // Hide completion modal if open
        document.getElementById('mobileCompletionModal').style.display = 'none';
        
        const percentage = Math.round(result.percentage);
        
        document.getElementById('mobileScorePercentage').textContent = `${percentage}%`;
        document.getElementById('mobileScoreValue').textContent = `${result.score}/${result.total}`;
        
        let message = '';
        if (percentage >= 80) {
            message = 'Excellent! You passed! 🎉';
        } else if (percentage >= 60) {
            message = 'Good effort! Keep practicing.';
        } else {
            message = 'Keep studying and try again!';
        }
        
        document.getElementById('mobileResultMessage').textContent = message;
        
        // Set up review button
        const reviewBtn = document.getElementById('mobileReviewBtn');
        reviewBtn.onclick = () => {
            window.location.href = `/test_review/${result.test_result_id}`;
        };
        
        document.getElementById('mobileResultsModal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Replace feather icons
        if (window.feather) feather.replace();
    }
};
