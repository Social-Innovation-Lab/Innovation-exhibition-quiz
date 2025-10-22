// Interactive Quiz Carousel Navigation
(function() {
  const form = document.getElementById('quizForm');
  if (!form) return;

  let currentQuestion = 0;
  const totalQuestions = 10;
  let answeredCount = 0;
  const answers = new Set();
  
  // 80-second timer
  let timeRemaining = 80;
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
    const progress = ((currentQuestion + 1) / totalQuestions) * 100;
    document.getElementById('progressFill').style.width = progress + '%';
    
    // Update dots
    for (let i = 0; i <= currentQuestion; i++) {
      const questionCards = document.querySelectorAll('.question-card');
      const qIndex = i;
      const hasAnswer = questionCards[qIndex] && questionCards[qIndex].querySelector('input[type="radio"]:checked');
      if (hasAnswer) {
        document.getElementById('dot' + i).classList.add('answered');
      }
    }
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
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    prevBtn.disabled = currentQuestion === 0;
    
    if (currentQuestion === totalQuestions - 1) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'block';
      submitBtn.disabled = answeredCount < totalQuestions;
    } else {
      nextBtn.style.display = 'flex';
      submitBtn.style.display = 'none';
    }
  }

  function showEncouragement(questionIndex) {
    const encourageEl = document.getElementById('encourage' + (questionIndex + 1));
    if (encourageEl) {
      const randomMsg = encouragements[Math.floor(Math.random() * encouragements.length)];
      encourageEl.textContent = randomMsg;
    }
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
        // Auto-submit the form
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
          submitBtn.click();
        } else {
          form.submit();
        }
      }
    }, 1000);
  }

  // Navigation buttons
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentQuestion > 0) {
        showQuestion(currentQuestion - 1);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      const currentCard = document.querySelector('.question-card.active');
      const currentInput = currentCard ? currentCard.querySelector('input[type="radio"]:checked') : null;
      
      if (!currentInput) {
        // Highlight question to show it needs an answer
        if (currentCard) {
          currentCard.style.animation = 'shake 0.5s';
          setTimeout(() => currentCard.style.animation = '', 500);
        }
        return;
      }
      
      if (currentQuestion < totalQuestions - 1) {
        showQuestion(currentQuestion + 1);
      }
    });
  }

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
        showEncouragement(questionIndex);
        
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

  // Touch swipe navigation
  let touchStartX = 0;
  let touchEndX = 0;
  const carouselWrapper = document.querySelector('.carousel-wrapper');
  
  if (carouselWrapper) {
    carouselWrapper.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    carouselWrapper.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipe();
    }, { passive: true });
  }

  function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
      if (diff > 0 && currentQuestion < totalQuestions - 1) {
        // Swipe left - next question (allow even without answer)
        showQuestion(currentQuestion + 1);
      } else if (diff < 0 && currentQuestion > 0) {
        // Swipe right - previous question
        showQuestion(currentQuestion - 1);
      }
    }
  }

  // Initialize
  updateProgress();
  updateNavButtons();
  startTimer();

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
