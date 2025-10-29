// Interactive Quiz Carousel Navigation
(function() {
  const form = document.getElementById('quizForm');
  if (!form) return;

  let currentQuestion = 0;
  const totalQuestions = 10;
  let answeredCount = 0;
  const answers = new Set();
  
  // 150-second timer
  let timeRemaining = 150;
  let timerInterval = null;

  const encouragements = [
    "Great choice! 🎯",
    "You're on fire! 🔥",
    "Excellent! ⭐",
    "Nice one! 👏",
    "Keep it up! 💪",
    "Fantastic! 🌟",
    "Way to go! 🚀",
    "Brilliant! 💡",
    "Perfect! ✨",
    "Amazing! 🎉"
  ];

  function updateProgress() {
    document.getElementById('currentQ').textContent = currentQuestion + 1;
    
    // Count total answered questions
    let totalAnswered = 0;
    const questionCards = document.querySelectorAll('.question-card');
    
    for (let i = 0; i < totalQuestions; i++) {
      const hasAnswer = questionCards[i] && questionCards[i].querySelector('input[type="radio"]:checked');
      if (hasAnswer) {
        totalAnswered++;
        document.getElementById('dot' + i).classList.add('answered');
      } else {
        document.getElementById('dot' + i).classList.remove('answered');
      }
    }
    
    // Progress bar calculation to reach stamps correctly
    // With space-between layout, stamps are at: 0%, 11.11%, 22.22%, ..., 100%
    // Answer 1 → 0%, Answer 2 → 11.11%, ..., Answer 10 → 100%
    const progress = totalAnswered > 0 ? ((totalAnswered - 1) / (totalQuestions - 1)) * 100 : 0;
    document.getElementById('progressFill').style.width = progress + '%';
  }

  function showQuestion(index) {
    const cards = document.querySelectorAll('.question-card');
    cards.forEach((card, i) => {
      card.classList.remove('active', 'prev');
      if (i === index) {
        card.classList.add('active');
      } else if (i < index) {
        card.classList.add('prev');
      }
    });
    
    currentQuestion = index;
    updateProgress();
    updateNavButtons();
    window.scrollTo({top: 0, behavior: 'smooth'});
  }

  function updateNavButtons() {
    const submitBtn = document.getElementById('submitBtn');
    
    if (currentQuestion === totalQuestions - 1) {
      submitBtn.style.display = 'block';
      // Enable submit if all 10 questions answered
      const shouldDisable = answeredCount < totalQuestions;
      submitBtn.disabled = shouldDisable;
      
      // Force enable on mobile/tablet after 2 seconds on last question
      if (shouldDisable) {
        setTimeout(() => {
          const currentAnswered = document.querySelectorAll('input[type="radio"]:checked').length;
          if (currentAnswered >= totalQuestions) {
            submitBtn.disabled = false;
          }
        }, 2000);
      }
      
      console.log('Submit button state:', { answeredCount, totalQuestions, disabled: submitBtn.disabled });
    } else {
      submitBtn.style.display = 'none';
    }
  }
  
  function showCountdown() {
    const overlay = document.getElementById('countdownOverlay');
    const numberEl = document.getElementById('countdownNumber');
    
    let count = 3;
    numberEl.textContent = count;
    overlay.classList.remove('hidden');
    
    const countdownInterval = setInterval(() => {
      count--;
      if (count > 0) {
        numberEl.textContent = count;
        // Re-trigger animation by removing and adding class
        numberEl.style.animation = 'none';
        setTimeout(() => {
          numberEl.style.animation = 'countPulse 1s ease-in-out';
        }, 10);
      } else {
        clearInterval(countdownInterval);
        overlay.classList.add('hidden');
        // Start timer after countdown finishes
        startTimer();
      }
    }, 1000);
  }
  
  function startTimer() {
    const timerCountEl = document.getElementById('timerCount');
    const timerBadge = document.getElementById('timerBadge');
    
    timerInterval = setInterval(() => {
      timeRemaining--;
      timerCountEl.textContent = timeRemaining;
      
      // Add warning state when 30 seconds left
      if (timeRemaining === 30) {
        timerBadge.classList.add('warning');
      }
      
      // Add danger state when 10 seconds left
      if (timeRemaining === 10) {
        timerBadge.classList.remove('warning');
        timerBadge.classList.add('danger');
      }
      
      // Auto-submit when time runs out
      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        timerCountEl.textContent = '0';
        // Force submit the form (bypasses disabled button)
        submitted = true;
        form.submit();
      }
    }, 1000);
  }

  // Navigation is now handled only by swipe gestures and auto-advance

  // Monitor radio selections with instant feedback
  document.querySelectorAll('input[type="radio"]').forEach(input => {
    input.addEventListener('change', function() {
      const questionCard = this.closest('.question-card');
      if (!questionCard) return;
      
      const questionIndex = parseInt(questionCard.dataset.question) - 1;
      
      // Mark as answered
      if (!answers.has(questionIndex)) {
        answers.add(questionIndex);
        answeredCount++;
        
        // Auto-advance after 800ms
        setTimeout(() => {
          if (currentQuestion < totalQuestions - 1) {
            showQuestion(currentQuestion + 1);
          }
        }, 800);
      }
      
      updateNavButtons();
      updateProgress();
    });
  });

  // Add shake animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-10px); }
      75% { transform: translateX(10px); }
    }
  `;
  document.head.appendChild(style);

  // Touch swipe navigation (horizontal only, not vertical scroll)
  let touchStartX = 0;
  let touchEndX = 0;
  let touchStartY = 0;
  let touchEndY = 0;
  let isSwiping = false;
  const carouselWrapper = document.querySelector('.carousel-wrapper');
  
  if (carouselWrapper) {
    carouselWrapper.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].clientX;
      touchStartY = e.changedTouches[0].clientY;
      isSwiping = false;
    }, { passive: true });

    carouselWrapper.addEventListener('touchmove', (e) => {
      if (!isSwiping) {
        const touchX = e.changedTouches[0].clientX;
        const touchY = e.changedTouches[0].clientY;
        const diffX = Math.abs(touchStartX - touchX);
        const diffY = Math.abs(touchStartY - touchY);
        
        // Determine if this is a horizontal swipe early
        if (diffX > 10 || diffY > 10) {
          isSwiping = diffX > diffY;
        }
      }
    }, { passive: true });

    carouselWrapper.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].clientX;
      touchEndY = e.changedTouches[0].clientY;
      handleSwipe();
    }, { passive: true });
  }

  function handleSwipe() {
    const swipeThreshold = 30; // Reduced threshold for easier swiping
    const diffX = touchStartX - touchEndX;
    const diffY = Math.abs(touchStartY - touchEndY);
    
    // Only trigger horizontal swipe if:
    // 1. Horizontal movement exceeds threshold
    // 2. Horizontal movement is dominant (at least 1.5x vertical movement)
    if (Math.abs(diffX) > swipeThreshold && Math.abs(diffX) > diffY * 1.5) {
      if (diffX > 0 && currentQuestion < totalQuestions - 1) {
        // Swipe left - next question
        showQuestion(currentQuestion + 1);
      } else if (diffX < 0 && currentQuestion > 0) {
        // Swipe right - previous question
        showQuestion(currentQuestion - 1);
      }
    }
    
    isSwiping = false;
  }

  // Initialize
  updateProgress();
  updateNavButtons();
  showCountdown();

  // Kiosk mode: prevent accidental back/refresh
  let submitted = false;
  form.addEventListener('submit', () => { 
    submitted = true;
    clearInterval(timerInterval); // Stop timer on submit
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
      submitBtn.disabled = true; 
      submitBtn.innerHTML = '<span>Submitting... ⏳</span>';
    }
  });
  
  window.addEventListener('beforeunload', function(e) {
    if (!submitted) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  // Prevent pinch zoom
  document.addEventListener('gesturestart', e => e.preventDefault());
})();
