// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && href.length > 1) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Hero animations on load
window.addEventListener('load', () => {
    // Animate hero badges with stagger
    const badges = document.querySelectorAll('.hero-badge');
    badges.forEach((badge, index) => {
        badge.style.opacity = '0';
        badge.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            badge.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            badge.style.opacity = '1';
            badge.style.transform = 'translateY(0)';
        }, 200 * index);
    });

    // Animate hero title lines
    const titleLines = document.querySelectorAll('.hero-title-line');
    titleLines.forEach((line, index) => {
        line.style.opacity = '0';
        line.style.transform = 'translateY(30px)';
        setTimeout(() => {
            line.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
            line.style.opacity = '1';
            line.style.transform = 'translateY(0)';
        }, 600 + (200 * index));
    });

    // Animate subtitle
    const subtitle = document.querySelector('.hero-subtitle');
    if (subtitle) {
        subtitle.style.opacity = '0';
        subtitle.style.transform = 'translateY(20px)';
        setTimeout(() => {
            subtitle.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            subtitle.style.opacity = '1';
            subtitle.style.transform = 'translateY(0)';
        }, 1200);
    }

    // Animate CTA buttons
    const ctaButtons = document.querySelectorAll('.hero-cta .btn');
    ctaButtons.forEach((btn, index) => {
        btn.style.opacity = '0';
        btn.style.transform = 'translateY(20px)';
        setTimeout(() => {
            btn.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            btn.style.opacity = '1';
            btn.style.transform = 'translateY(0)';
        }, 1400 + (100 * index));
    });
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Add animation to sections (except hero which is animated on load)
document.querySelectorAll('section:not(.hero)').forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(20px)';
    section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(section);
});

// Navbar background on scroll
const navbar = document.querySelector('.navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 50) {
        navbar.style.background = 'rgba(10, 10, 11, 0.95)';
        navbar.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.3)';
    } else {
        navbar.style.background = 'rgba(10, 10, 11, 0.8)';
        navbar.style.boxShadow = 'none';
    }

    lastScroll = currentScroll;
});

// Pricing card hover effect
document.querySelectorAll('.pricing-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        if (!this.classList.contains('featured')) {
            this.style.borderColor = '#f97316';
        }
    });

    card.addEventListener('mouseleave', function() {
        if (!this.classList.contains('featured')) {
            this.style.borderColor = '#27272a';
        }
    });
});

// Feature card stagger animation
const featureCards = document.querySelectorAll('.feature-card');
featureCards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
});

// Stats counter animation
const stats = document.querySelectorAll('.stat-value');
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const target = entry.target;
            const finalValue = parseInt(target.textContent);
            const duration = 2000;
            const steps = 60;
            const increment = finalValue / steps;
            let current = 0;

            const counter = setInterval(() => {
                current += increment;
                if (current >= finalValue) {
                    target.textContent = target.textContent.includes('+')
                        ? `${finalValue}+`
                        : finalValue;
                    clearInterval(counter);
                } else {
                    target.textContent = Math.floor(current) + (target.textContent.includes('+') ? '+' : '');
                }
            }, duration / steps);

            statsObserver.unobserve(target);
        }
    });
}, { threshold: 0.5 });

stats.forEach(stat => statsObserver.observe(stat));

// FAQ accordion (optional enhancement)
document.querySelectorAll('.faq-item').forEach(item => {
    const header = item.querySelector('h3');
    const content = item.querySelector('p');

    header.style.cursor = 'pointer';
    header.addEventListener('click', () => {
        // Toggle max-height for smooth animation
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
            header.style.color = 'var(--text-primary)';
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            header.style.color = 'var(--accent-primary)';
        }
    });

    // Initialize p elements
    content.style.overflow = 'hidden';
    content.style.maxHeight = content.scrollHeight + 'px';
    content.style.transition = 'max-height 0.3s ease';
});

// Mobile menu toggle (for future enhancement)
const createMobileMenu = () => {
    const nav = document.querySelector('.nav-content');
    const navLinks = document.querySelector('.nav-links');

    // Only create if it doesn't exist
    if (document.querySelector('.mobile-menu-toggle')) return;

    const toggle = document.createElement('button');
    toggle.className = 'mobile-menu-toggle';
    toggle.innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
    `;

    toggle.style.cssText = `
        display: none;
        background: transparent;
        border: none;
        color: var(--text-primary);
        cursor: pointer;
        padding: 0.5rem;
    `;

    nav.appendChild(toggle);

    // Show on mobile
    if (window.innerWidth <= 768) {
        toggle.style.display = 'block';
        navLinks.style.display = 'none';
    }

    toggle.addEventListener('click', () => {
        const isHidden = navLinks.style.display === 'none';
        navLinks.style.display = isHidden ? 'flex' : 'none';
        navLinks.style.flexDirection = 'column';
        navLinks.style.position = 'absolute';
        navLinks.style.top = '100%';
        navLinks.style.left = '0';
        navLinks.style.right = '0';
        navLinks.style.background = 'var(--bg-secondary)';
        navLinks.style.padding = '1rem';
        navLinks.style.borderTop = '1px solid var(--border-primary)';
    });
};

// Initialize mobile menu on load and resize
window.addEventListener('load', createMobileMenu);
window.addEventListener('resize', () => {
    const navLinks = document.querySelector('.nav-links');
    if (window.innerWidth > 768) {
        navLinks.style.display = 'flex';
        navLinks.style.flexDirection = 'row';
        navLinks.style.position = 'static';
        navLinks.style.padding = '0';
        navLinks.style.borderTop = 'none';
    } else {
        navLinks.style.display = 'none';
    }
});

// Add glow effect to pricing on hover
document.querySelectorAll('.pricing-card.featured').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        card.style.background = `radial-gradient(circle at ${x}px ${y}px, rgba(249, 115, 22, 0.1) 0%, var(--bg-card) 50%)`;
    });

    card.addEventListener('mouseleave', () => {
        card.style.background = 'var(--bg-card)';
    });
});

// Console Easter egg
console.log('%c🦞 AgentClaw API', 'font-size: 24px; font-weight: bold; color: #f97316;');
console.log('%cTransform your real estate business with AI-powered automation', 'font-size: 14px; color: #a1a1aa;');
console.log('%chttps://github.com/Thedurancode/ai-realtor', 'font-size: 12px; color: #71717a;');
