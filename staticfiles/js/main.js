/**
 * Learning Platform - Main JavaScript
 * ====================================
 * Features:
 * - Back to top button
 * - Smooth scrolling
 * - Search form handling
 * - Quiz timer functionality
 * - Reading progress indicator
 * - Scroll animations (fade-in, slide-in)
 * - Navbar active link highlighting
 */

(function () {
    'use strict';

    /* ----------------------------------------------------------
       DOM Ready
       ---------------------------------------------------------- */
    document.addEventListener('DOMContentLoaded', function () {
        initBackToTop();
        initReadingProgress();
        initScrollAnimations();
        initSearchForm();
        initQuizTimer();
        initQuizOptions();
        initNavbarHighlight();
        initSmoothScroll();
    });

    /* ----------------------------------------------------------
       1. Back to Top Button
       ---------------------------------------------------------- */
    function initBackToTop() {
        var btn = document.getElementById('backToTop');
        if (!btn) return;

        var scrollThreshold = 300;

        window.addEventListener('scroll', function () {
            if (window.scrollY > scrollThreshold) {
                btn.classList.add('visible');
                btn.style.display = 'flex';
            } else {
                btn.classList.remove('visible');
                setTimeout(function () {
                    if (!btn.classList.contains('visible')) {
                        btn.style.display = 'none';
                    }
                }, 300);
            }
        }, { passive: true });

        btn.addEventListener('click', function () {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    /* ----------------------------------------------------------
       2. Reading Progress Indicator
       ---------------------------------------------------------- */
    function initReadingProgress() {
        var progressBar = document.getElementById('readingProgress');
        if (!progressBar) return;

        window.addEventListener('scroll', function () {
            var scrollTop = window.scrollY;
            var docHeight = document.documentElement.scrollHeight - window.innerHeight;
            var progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            progressBar.style.width = Math.min(progress, 100) + '%';
        }, { passive: true });
    }

    /* ----------------------------------------------------------
       3. Scroll Animations (Intersection Observer)
       ---------------------------------------------------------- */
    function initScrollAnimations() {
        var animatedElements = document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .scale-in');

        if (!animatedElements.length) return;

        if ('IntersectionObserver' in window) {
            var observer = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            animatedElements.forEach(function (el) {
                observer.observe(el);
            });
        } else {
            // Fallback: show all elements immediately
            animatedElements.forEach(function (el) {
                el.classList.add('visible');
            });
        }
    }

    /* ----------------------------------------------------------
       4. Search Form Handling
       ---------------------------------------------------------- */
    function initSearchForm() {
        var searchForms = document.querySelectorAll('form[action*="search"]');

        searchForms.forEach(function (form) {
            form.addEventListener('submit', function (e) {
                var input = form.querySelector('input[name="q"]');
                if (input) {
                    var query = input.value.trim();
                    if (query.length < 2) {
                        e.preventDefault();
                        input.classList.add('is-invalid');
                        input.focus();
                        setTimeout(function () {
                            input.classList.remove('is-invalid');
                        }, 2000);
                        return;
                    }
                    input.value = query;
                }
            });

            // Clear invalid state on input
            var input = form.querySelector('input[name="q"]');
            if (input) {
                input.addEventListener('input', function () {
                    input.classList.remove('is-invalid');
                });
            }
        });
    }

    /* ----------------------------------------------------------
       5. Quiz Timer Functionality
       ---------------------------------------------------------- */
    function initQuizTimer() {
        var timerEl = document.getElementById('quizTimer');
        var timerDisplay = document.getElementById('quizTimerDisplay');
        if (!timerEl || !timerDisplay) return;

        var totalSeconds = parseInt(timerEl.getAttribute('data-duration'), 10) * 60;
        if (isNaN(totalSeconds) || totalSeconds <= 0) return;

        var remainingSeconds = totalSeconds;
        var timerInterval = null;
        var quizForm = document.getElementById('quizForm');

        function updateTimerDisplay() {
            var hours = Math.floor(remainingSeconds / 3600);
            var minutes = Math.floor((remainingSeconds % 3600) / 60);
            var seconds = remainingSeconds % 60;

            var display = '';
            if (hours > 0) {
                display = hours + ':' + padZero(minutes) + ':' + padZero(seconds);
            } else {
                display = padZero(minutes) + ':' + padZero(seconds);
            }
            timerDisplay.textContent = display;

            // Warning state when under 2 minutes
            if (remainingSeconds <= 120) {
                timerEl.classList.add('warning');
            } else {
                timerEl.classList.remove('warning');
            }
        }

        function padZero(num) {
            return num < 10 ? '0' + num : num.toString();
        }

        function submitQuiz() {
            if (quizForm) {
                // Add a hidden input to indicate time expired
                var hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'time_expired';
                hiddenInput.value = 'true';
                quizForm.appendChild(hiddenInput);
                quizForm.submit();
            }
        }

        updateTimerDisplay();

        timerInterval = setInterval(function () {
            remainingSeconds--;
            updateTimerDisplay();

            if (remainingSeconds <= 0) {
                clearInterval(timerInterval);
                submitQuiz();
            }
        }, 1000);

        // Submit quiz manually clears the timer
        if (quizForm) {
            quizForm.addEventListener('submit', function () {
                clearInterval(timerInterval);
            });
        }

        // Pause timer when tab is hidden (save time)
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                // Timer keeps running but we could pause here if desired
            }
        });
    }

    /* ----------------------------------------------------------
       6. Quiz Options (MCQ Selection)
       ---------------------------------------------------------- */
    function initQuizOptions() {
        var quizOptions = document.querySelectorAll('.quiz-option');
        if (!quizOptions.length) return;

        quizOptions.forEach(function (option) {
            option.addEventListener('click', function () {
                var questionGroup = option.closest('.quiz-question');
                if (!questionGroup) return;

                // Remove selected state from siblings
                var siblings = questionGroup.querySelectorAll('.quiz-option');
                siblings.forEach(function (sib) {
                    sib.classList.remove('selected');
                });

                // Add selected state
                option.classList.add('selected');

                // Check the radio button
                var radio = option.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        });
    }

    /* ----------------------------------------------------------
       7. Navbar Active Link Highlighting
       ---------------------------------------------------------- */
    function initNavbarHighlight() {
        var currentPath = window.location.pathname;
        var navLinks = document.querySelectorAll('.navbar .nav-link');

        navLinks.forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href) return;

            // Exact match or starts with for section links
            if (currentPath === href) {
                link.classList.add('active');
            } else if (href !== '/' && currentPath.startsWith(href)) {
                link.classList.add('active');
            }
        });
    }

    /* ----------------------------------------------------------
       8. Smooth Scrolling for Anchor Links
       ---------------------------------------------------------- */
    function initSmoothScroll() {
        document.addEventListener('click', function (e) {
            var link = e.target.closest('a[href^="#"]');
            if (!link) return;

            var targetId = link.getAttribute('href');
            if (targetId === '#' || targetId === '') return;

            var target = document.querySelector(targetId);
            if (!target) return;

            e.preventDefault();

            var navbarHeight = document.querySelector('.navbar')
                ? document.querySelector('.navbar').offsetHeight
                : 0;

            var targetPosition = target.getBoundingClientRect().top + window.scrollY - navbarHeight - 20;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });

            // Update URL hash without jumping
            if (history.pushState) {
                history.pushState(null, null, targetId);
            }
        });
    }

})();
