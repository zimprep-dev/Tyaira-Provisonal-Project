// Mobile Test Interface JavaScript

const mobileTestInterface = {
    questions: [],
    currentQuestionIndex: 0,
    userAnswers: {},
    startTime: null,
    timerInterval: null,
    timeLimit: 480, // 8 minutes in seconds
    timeRemaining: 480,
    sessionId: null,

    initializeTest() {
        const category = document.querySelector('.mobile-test-container').dataset.category;
        this.loadQuestions(category);
        this.setupEventListeners();
    },

    async loadQuestions(category) {
        // Show loading state
        this.showLoadingState();
        
        try {
            // Try to load from cache first if offline
            if (!navigator.onLine) {
                const cachedData = this.loadFromCache(category);
                if (cachedData) {
                    console.log('Loading questions from cache (offline mode)');
                    this.questions = cachedData.questions;
                    this.sessionId = 'offline-' + Date.now(); // Generate offline session ID
                    this.timeLimit = cachedData.time_limit_seconds || 480;
                    this.timeRemaining = this.timeLimit;
                    
                    document.getElementById('mobileTotalQuestions').textContent = this.questions.length;
                    
                    this.startTimer();
                    this.displayQuestion();
                    this.showOfflineNotice();
                    return;
                } else {
                    this.showOfflineError();
                    return;
                }
            }

            // Online: Fetch from server
            const response = await fetch(`/api/test/start/${category}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // API returns: {session_id, time_limit_seconds, questions}
            if (data.questions && data.questions.length > 0) {
                this.questions = data.questions;
                this.sessionId = data.session_id;
                this.timeLimit = data.time_limit_seconds || 480;
                this.timeRemaining = this.timeLimit;
                
                // Cache questions for offline use
                this.saveToCache(category, data);
                
                document.getElementById('mobileTotalQuestions').textContent = this.questions.length;
                
                this.startTimer();
                this.displayQuestion();
            } else {
                alert('No questions available for this category. Please try another.');
                window.location.href = '/take_test';
            }
        } catch (error) {
            console.error('Error loading questions:', error);
            
            // Check if it's a network error - try cache
            if (!navigator.onLine || error.message.includes('Failed to fetch')) {
                const cachedData = this.loadFromCache(category);
                if (cachedData) {
                    console.log('Network error - falling back to cached questions');
                    this.questions = cachedData.questions;
                    this.sessionId = 'offline-' + Date.now();
                    this.timeLimit = cachedData.time_limit_seconds || 480;
                    this.timeRemaining = this.timeLimit;
                    
                    document.getElementById('mobileTotalQuestions').textContent = this.questions.length;
                    
                    this.startTimer();
                    this.displayQuestion();
                    this.showOfflineNotice();
                } else {
                    this.showOfflineError();
                }
            } else {
                alert('An error occurred while loading the test. Please check your connection and try again.');
                window.location.href = '/take_test';
            }
        }
    },

    saveToCache(category, data) {
        try {
            const cacheKey = `test_questions_${category}`;
            const cacheData = {
                questions: data.questions,
                time_limit_seconds: data.time_limit_seconds,
                cached_at: new Date().toISOString()
            };
            localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            console.log(`Cached ${data.questions.length} questions for category: ${category}`);
        } catch (error) {
            console.error('Error caching questions:', error);
        }
    },

    loadFromCache(category) {
        try {
            const cacheKey = `test_questions_${category}`;
            const cached = localStorage.getItem(cacheKey);
            if (cached) {
                const data = JSON.parse(cached);
                console.log(`Found cached questions for category: ${category}`);
                return data;
            }
        } catch (error) {
            console.error('Error loading from cache:', error);
        }
        return null;
    },

    showOfflineNotice() {
        this.showConnectionWarning('📴 Offline Mode - Using cached questions', 'warning');
    },

    showLoadingState() {
        const questionText = document.getElementById('mobileQuestionText');
        questionText.innerHTML = `
            <div style="text-align: center; padding: 2rem 1rem;">
                <div style="
                    width: 48px;
                    height: 48px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #007bff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 1rem;
                "></div>
                <p style="color: #666;">Loading questions...</p>
            </div>
        `;
    },

    showOfflineError() {
        const questionText = document.getElementById('mobileQuestionText');
        questionText.innerHTML = `
            <div style="text-align: center; padding: 2rem 1rem; color: #dc3545;">
                <i data-feather="wifi-off" style="width: 48px; height: 48px; margin-bottom: 1rem;"></i>
                <h3 style="margin-bottom: 1rem;">No Cached Questions</h3>
                <p style="margin-bottom: 1.5rem; color: #666;">
                    You need to load this test online at least once before it can be used offline.
                </p>
                <p style="margin-bottom: 1.5rem; color: #666; font-size: 0.9rem;">
                    💡 Tip: Load tests while online, and they'll be available offline later!
                </p>
                <button onclick="location.reload()" style="
                    background: #007bff;
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                ">
                    <i data-feather="refresh-cw" style="width: 18px; height: 18px;"></i>
                    Try Again
                </button>
                <button onclick="window.location.href='/dashboard'" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 0.75rem 1.5rem;
                    border-radius: 8px;
                    font-size: 1rem;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.5rem;
                    margin-left: 0.5rem;
                ">
                    <i data-feather="home" style="width: 18px; height: 18px;"></i>
                    Go Home
                </button>
            </div>
        `;
        
        // Replace feather icons
        if (window.feather) feather.replace();
        
        // Hide navigation buttons
        document.getElementById('mobilePrevBtn').style.display = 'none';
        document.getElementById('mobileNextBtn').style.display = 'none';
        document.getElementById('mobileFinishBtn').style.display = 'none';
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

        // Online/Offline detection
        window.addEventListener('offline', () => {
            this.showConnectionWarning('You are now offline. Your answers are saved locally.');
        });
        
        window.addEventListener('online', () => {
            this.showConnectionWarning('Connection restored!', 'success');
        });
    },

    showConnectionWarning(message, type = 'warning') {
        // Create or update connection toast
        let toast = document.getElementById('connectionToast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'connectionToast';
            toast.style.cssText = `
                position: fixed;
                top: 70px;
                left: 50%;
                transform: translateX(-50%);
                background: ${type === 'success' ? '#28a745' : '#ffc107'};
                color: ${type === 'success' ? 'white' : '#333'};
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                z-index: 9999;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                transition: opacity 0.3s;
            `;
            document.body.appendChild(toast);
        }
        
        toast.textContent = message;
        toast.style.background = type === 'success' ? '#28a745' : '#ffc107';
        toast.style.color = type === 'success' ? 'white' : '#333';
        toast.style.opacity = '1';
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
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
        
        // Check if this is an offline session
        if (this.sessionId && this.sessionId.startsWith('offline-')) {
            // Offline mode - save results locally
            this.saveOfflineResults();
            this.showOfflineResults();
            return;
        }
        
        // Check if online before submitting
        if (!navigator.onLine) {
            alert('You are offline. Your test results will be saved locally.');
            this.saveOfflineResults();
            this.showOfflineResults();
            return;
        }
        
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
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // API returns: {score, total, percentage, test_result_id}
            if (result.score !== undefined) {
                this.showResults(result);
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error submitting test:', error);
            
            if (!navigator.onLine || error.message.includes('Failed to fetch')) {
                alert('Network error: Unable to submit test. Please check your internet connection and try again.');
            } else {
                alert('An error occurred while submitting the test. Please try again.');
            }
            
            // Restart timer so user can try again
            this.startTimer();
        }
    },

    saveOfflineResults() {
        const timeTaken = this.timeLimit - this.timeRemaining;
        let score = 0;
        
        this.questions.forEach(question => {
            const userAnswer = this.userAnswers[question.id];
            const correctOption = question.options ? Object.keys(question.options).find(key => {
                const opt = question.options[key];
                return typeof opt === 'object' && opt.is_correct;
            }) : null;
            
            if (userAnswer && userAnswer === correctOption) {
                score++;
            }
        });
        
        const result = {
            score: score,
            total: this.questions.length,
            percentage: (score / this.questions.length) * 100,
            time_taken: timeTaken,
            date: new Date().toISOString(),
            offline: true
        };
        
        // Save to localStorage
        const offlineResults = JSON.parse(localStorage.getItem('offline_test_results') || '[]');
        offlineResults.push(result);
        localStorage.setItem('offline_test_results', JSON.stringify(offlineResults));
        
        this.offlineResult = result;
    },

    showOfflineResults() {
        const result = this.offlineResult;
        document.getElementById('mobileCompletionModal').style.display = 'none';
        
        const percentage = Math.round(result.percentage);
        
        document.getElementById('mobileScorePercentage').textContent = `${percentage}%`;
        document.getElementById('mobileScoreValue').textContent = `${result.score}/${result.total}`;
        
        let message = '';
        if (percentage >= 80) {
            message = '📴 Offline: Excellent! You passed! 🎉';
        } else if (percentage >= 60) {
            message = '📴 Offline: Good effort! Keep practicing.';
        } else {
            message = '📴 Offline: Keep studying and try again!';
        }
        
        document.getElementById('mobileResultMessage').textContent = message;
        
        // Hide review button in offline mode
        const reviewBtn = document.getElementById('mobileReviewBtn');
        reviewBtn.style.display = 'none';
        
        document.getElementById('mobileResultsModal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        if (window.feather) feather.replace();
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
        reviewBtn.style.display = 'inline-flex';
        reviewBtn.onclick = () => {
            window.location.href = `/test_review/${result.test_result_id}`;
        };
        
        document.getElementById('mobileResultsModal').style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Replace feather icons
        if (window.feather) feather.replace();
    }
};
