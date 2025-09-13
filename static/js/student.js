// Student Assessment JavaScript
class StudentAssessment {
    constructor() {
        this.currentQuestion = null;
        this.questionNumber = 1;
        this.isWaitingForNext = false;
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Start session form
        const startForm = document.getElementById('start-session-form');
        if (startForm) {
            startForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startSession();
            });
        }
        
        // Answer submission form
        const answerForm = document.getElementById('answer-form');
        if (answerForm) {
            answerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                if (!this.isWaitingForNext) {
                    this.submitAnswer();
                }
            });
        }
        
        // Next question button
        const nextBtn = document.getElementById('next-question-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.getNextQuestion();
            });
        }
        
        // Enter key handling for answer input
        const answerInput = document.getElementById('student-answer');
        if (answerInput) {
            answerInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.isWaitingForNext) {
                    e.preventDefault();
                    this.submitAnswer();
                }
            });
        }
        
        // Math keyboard buttons
        this.initializeMathKeyboard();
    }
    
    initializeMathKeyboard() {
        // Add event listeners to all math symbol buttons
        const mathButtons = document.querySelectorAll('.math-btn');
        mathButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const symbol = e.currentTarget.dataset.symbol;
                this.insertSymbol(symbol);
            });
        });
    }
    
    insertSymbol(symbol) {
        const answerInput = document.getElementById('student-answer');
        if (answerInput) {
            const cursorPos = answerInput.selectionStart;
            const textBefore = answerInput.value.substring(0, cursorPos);
            const textAfter = answerInput.value.substring(answerInput.selectionEnd);
            
            answerInput.value = textBefore + symbol + textAfter;
            answerInput.focus();
            
            // Set cursor position after inserted symbol
            const newPos = cursorPos + symbol.length;
            answerInput.setSelectionRange(newPos, newPos);
        }
    }
    
    async startSession() {
        const name = document.getElementById('student-name').value.trim();
        const grade = document.getElementById('student-grade').value;
        
        if (!name || !grade) {
            this.showAlert('لطفا تمام فیلدها را پر کنید', 'danger');
            return;
        }
        
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/start_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, grade })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideForm();
                this.showQuestionSection();
                // ✅ یک تأخیر کوتاه اضافه شده تا نمایش صفحه تضمین شود
                setTimeout(() => {
                    this.getNextQuestion(); 
                }, 100); 
            } else {
                this.showAlert(data.error || 'خطا در شروع جلسه', 'danger');
            }
        } catch (error) {
            console.error('Error starting session:', error);
            this.showAlert('خطا در ارتباط با سرور', 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    async getNextQuestion() {
        this.showLoading(true);
        this.hideFeedback();
        
        try {
            const response = await fetch('/api/get_question');
            const data = await response.json();
            
            if (data.success) {
                if (data.completed) {
                    this.showResults(data.score, data.total);
                } else {
                    this.displayQuestion(data.question);
                }
            } else {
                this.showAlert(data.error || 'خطا در دریافت سوال', 'danger');
            }
        } catch (error) {
            console.error('Error getting question:', error);
            this.showAlert('خطا در ارتباط با سرور', 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayQuestion(question) {
        this.currentQuestion = question;
        this.isWaitingForNext = false;
        
        // Update question display
        document.getElementById('question-number').textContent = this.questionNumber;
        document.getElementById('prerequisite-name').textContent = question.prerequisite;
        document.getElementById('question-text').innerHTML = question.text;
        
        // Clear previous answer
        document.getElementById('student-answer').value = '';
        document.getElementById('student-answer').focus();
        
        // Enable form
        this.setFormEnabled(true);
        
        // Re-render MathJax for mathematical expressions
        if (window.MathJax) {
            MathJax.typesetPromise([document.getElementById('question-text')]);
        }
    }
    
    async submitAnswer() {
        const answer = document.getElementById('student-answer').value.trim();
        
        if (!answer) {
            this.showAlert('لطفا پاسخ خود را وارد کنید', 'warning');
            return;
        }
        
        this.setFormEnabled(false);
        this.showLoading(true);
        
        try {
            const response = await fetch('/api/submit_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ answer })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showFeedback(data.correct, data.correct_answer, answer, data.dont_know);
                this.questionNumber++;
                this.isWaitingForNext = true;
            } else {
                this.showAlert(data.error || 'خطا در ثبت پاسخ', 'danger');
                this.setFormEnabled(true);
            }
        } catch (error) {
            console.error('Error submitting answer:', error);
            this.showAlert('خطا در ارتباط با سرور', 'danger');
            this.setFormEnabled(true);
        } finally {
            this.showLoading(false);
        }
    }
    
    showFeedback(isCorrect, correctAnswer, userAnswer, isDontKnow = false) {
        const feedbackSection = document.getElementById('feedback-section');
        const feedbackContent = document.getElementById('feedback-content');
        
        let feedbackHtml = '';
        
        if (isDontKnow) {
            feedbackHtml = `
                <div class="text-warning">
                    <i class="fas fa-question-circle fa-3x mb-3"></i>
                    <h4>نگران نباشید! نداشتن اطلاع نشانه صداقت است</h4>
                    <p class="mb-2">شما گفتید: <strong class="text-warning">بلد نیستم</strong></p>
                    <p class="mb-0">پاسخ صحیح: <strong class="text-success">${correctAnswer}</strong></p>
                    <small class="text-muted mt-2 d-block">این سوال در تحلیل نهایی تأثیر منفی نخواهد داشت</small>
                </div>
            `;
        } else if (isCorrect) {
            feedbackHtml = `
                <div class="text-success">
                    <i class="fas fa-check-circle fa-3x mb-3"></i>
                    <h4>آفرین! پاسخ شما صحیح است</h4>
                    <p class="mb-0">پاسخ صحیح: <strong>${correctAnswer}</strong></p>
                </div>
            `;
        } else {
            feedbackHtml = `
                <div class="text-danger">
                    <i class="fas fa-times-circle fa-3x mb-3"></i>
                    <h4>متأسفانه پاسخ شما اشتباه است</h4>
                    <p class="mb-2">پاسخ شما: <strong class="text-danger">${userAnswer}</strong></p>
                    <p class="mb-0">پاسخ صحیح: <strong class="text-success">${correctAnswer}</strong></p>
                </div>
            `;
        }
        
        feedbackContent.innerHTML = feedbackHtml;
        feedbackSection.style.display = 'block';
        feedbackSection.classList.add('feedback-animation');
        
        // Re-render MathJax for mathematical expressions
        if (window.MathJax) {
            MathJax.typesetPromise([feedbackContent]);
        }
    }
    
    hideFeedback() {
        const feedbackSection = document.getElementById('feedback-section');
        feedbackSection.style.display = 'none';
        feedbackSection.classList.remove('feedback-animation');
    }
    
    showResults(score, total) {
        // Hide question section
        document.getElementById('question-section').style.display = 'none';
        this.hideFeedback();
        
        // Show results
        const resultsSection = document.getElementById('results-section');
        const percentage = total > 0 ? Math.round((score / total) * 100) : 0;
        
        document.getElementById('final-score').innerHTML = `
            <h2 class="mb-3">نمره نهایی شما: ${percentage}%</h2>
            <p class="text-muted">شما ${score} سوال از ${total} سوال را درست پاسخ دادید</p>
        `;
        
        document.getElementById('correct-answers').textContent = score;
        document.getElementById('total-questions').textContent = total;
        
        resultsSection.style.display = 'block';
    }
    
    hideForm() {
        document.getElementById('student-form').style.display = 'none';
    }
    
    showQuestionSection() {
        document.getElementById('question-section').style.display = 'block';
    }
    
    setFormEnabled(enabled) {
        const submitBtn = document.querySelector('#answer-form button[type="submit"]');
        const answerInput = document.getElementById('student-answer');
        
        submitBtn.disabled = !enabled;
        answerInput.disabled = !enabled;
        
        if (enabled) {
            submitBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>ارسال پاسخ';
        } else {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>در حال ارسال...';
        }
    }
    
    showLoading(show) {
        const loading = document.getElementById('loading');
        loading.style.display = show ? 'block' : 'none';
    }
    
    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Portal Functions
function showStudentForm() {
    document.getElementById('student-form').style.display = 'block';
    document.getElementById('student-form').scrollIntoView({ behavior: 'smooth' });
}

function hideStudentForm() {
    document.getElementById('student-form').style.display = 'none';
}

// Math Keyboard Functions
function toggleMathKeyboard() {
    const panel = document.getElementById('math-keyboard-panel');
    const button = document.getElementById('keyboard-toggle');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        button.innerHTML = '<i class="fas fa-keyboard"></i> مخفی کردن کیبورد';
    } else {
        panel.style.display = 'none';
        button.innerHTML = '<i class="fas fa-keyboard"></i> نمایش کیبورد';
    }
}

function clearAnswer() {
    const answerInput = document.getElementById('student-answer');
    if (answerInput) {
        answerInput.value = '';
        answerInput.focus();
    }
}

function dontKnowAnswer() {
    const answerInput = document.getElementById('student-answer');
    if (answerInput) {
        answerInput.value = 'بلد نیستم';
        answerInput.focus();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new StudentAssessment();
});
