// Main JavaScript for Personality Quiz Daily Landing Page

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all interactive elements
    initScrollAnimations();
    initButtonInteractions();
    initQuizPreview();
    initSmoothScrolling();
    initParallaxEffects();
});

// Scroll animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe elements for animation
    const animatedElements = document.querySelectorAll('.feature-card, .step, .hero-stats');
    animatedElements.forEach(el => {
        observer.observe(el);
    });
}

// Button interactions
function initButtonInteractions() {
    // Navigation is handled by anchor hrefs; no popups or simulated loading
}

// Quiz preview interactions
function initQuizPreview() {
    const quizCard = document.querySelector('.quiz-card');
    const options = document.querySelectorAll('.option');
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');

    if (!quizCard) return;

    let currentQuestion = 1;
    const totalQuestions = 10;

    // Add hover effects to quiz card
    quizCard.addEventListener('mouseenter', function() {
        this.style.transform = 'rotateY(0deg) rotateX(0deg) scale(1.05)';
    });

    quizCard.addEventListener('mouseleave', function() {
        this.style.transform = 'rotateY(-5deg) rotateX(5deg) scale(1)';
    });

    // Option selection simulation
    options.forEach((option, index) => {
        option.addEventListener('click', function() {
            // Remove previous selection
            options.forEach(opt => opt.classList.remove('selected'));
            
            // Add selection to clicked option
            this.classList.add('selected');
            
            // Simulate progress
            setTimeout(() => {
                currentQuestion++;
                if (currentQuestion <= totalQuestions) {
                    updateProgress();
                    simulateNextQuestion();
                } else {
                    // Quiz completed
                    showQuizComplete();
                }
            }, 1000);
        });
    });

    function updateProgress() {
        const progress = (currentQuestion / totalQuestions) * 100;
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        if (progressText) {
            progressText.textContent = `Question ${currentQuestion} of ${totalQuestions}`;
        }
    }

    function simulateNextQuestion() {
        // Reset options
        options.forEach(opt => {
            opt.classList.remove('selected');
            opt.style.transform = 'translateX(0)';
        });

        // Simulate new question (in real app, this would fetch from server)
        const questions = [
            "What motivates you most in life?",
            "How do you handle stress?",
            "What's your ideal weekend?",
            "How do you make decisions?",
            "What energizes you most?"
        ];

        const questionText = document.querySelector('.quiz-question p');
        if (questionText && currentQuestion <= questions.length) {
            questionText.textContent = questions[currentQuestion - 1];
        }
    }

    function showQuizComplete() {
        const quizQuestion = document.querySelector('.quiz-question');
        if (quizQuestion) {
            quizQuestion.innerHTML = '<p style="color: #10b981; font-weight: 600;">🎉 Quiz Complete! Great job!</p>';
        }
        
        if (progressFill) {
            progressFill.style.width = '100%';
        }
        if (progressText) {
            progressText.textContent = 'Quiz Complete!';
        }
    }
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Parallax effects for hero background
function initParallaxEffects() {
    const orbs = document.querySelectorAll('.gradient-orb');
    
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        
        orbs.forEach((orb, index) => {
            const speed = (index + 1) * 0.1;
            orb.style.transform = `translateY(${rate * speed}px) rotate(${scrolled * 0.1}deg)`;
        });
    });
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .feature-card, .step {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.6s ease;
    }
    
    .feature-card.animate-in, .step.animate-in {
        opacity: 1;
        transform: translateY(0);
    }
    
    .option.selected {
        background: var(--primary-color);
        color: white;
        transform: translateX(10px);
    }
    
    .option {
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .option:hover {
        transform: translateX(5px);
    }
    
    .btn:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
    
    .btn:disabled:hover {
        transform: none;
    }
`;
document.head.appendChild(style);
