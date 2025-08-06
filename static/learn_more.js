const html = document.documentElement;
const panel = document.getElementById('accessibilityPanel');
const panelToggle = document.getElementById('togglePanel');
const closePanel = document.getElementById('closePanel');
const decreaseBtn = document.getElementById('fontDecrease');
const resetBtn = document.getElementById('fontReset');
const increaseBtn = document.getElementById('fontIncrease');

panelToggle.addEventListener('click', () => {
    panel.classList.toggle('hidden');
});

closePanel.addEventListener('click', () => {
    accessibilityPanel.classList.add('hidden');
  });

document.addEventListener('click', function (event) {
    const isClickInsidePanel = accessibilityPanel.contains(event.target);
    const isClickToggleButton = togglePanel.contains(event.target);

    if (!isClickInsidePanel && !isClickToggleButton) {
      accessibilityPanel.classList.add('hidden');
    }
  });

function setupToggle(buttonId, classTarget, className) {
    const button = document.getElementById(buttonId);
    const thumb = button.querySelector('span');

    button.addEventListener('click', () => {
    const isActive = classTarget.classList.toggle(className);
    button.classList.toggle('bg-blue-600', isActive);
    button.classList.toggle('bg-gray-300', !isActive);
    thumb.classList.toggle('translate-x-6', isActive);
    thumb.classList.toggle('translate-x-1', !isActive);
    });
}

setupToggle('toggleDyslexic', html, 'dyslexic-font');
setupToggle('toggleMonochrome', html, 'monochrome');
// setupToggle('toggleRuler', html, 'reading-ruler');
setupToggle('toggleCursor', html, 'big-cursor');

//ruler
const ruler = document.getElementById('readingRuler');
const rulerToggle = document.getElementById('toggleRuler');
const rulerThumb = rulerToggle.querySelector('span');

let rulerActive = false;

rulerToggle.addEventListener('click', () => {
rulerActive = !rulerActive;
ruler.classList.toggle('hidden', !rulerActive);

rulerToggle.classList.toggle('bg-blue-600', rulerActive);
rulerToggle.classList.toggle('bg-gray-300', !rulerActive);
rulerThumb.classList.toggle('translate-x-6', rulerActive);
rulerThumb.classList.toggle('translate-x-1', !rulerActive);
});

document.addEventListener('mousemove', (e) => {
if (rulerActive) {
    const height = ruler.offsetHeight;
    ruler.style.top = `${e.clientY - height / 2}px`;
}
});
//font size
let currentFontSize = 16;
decreaseBtn.addEventListener('click', () => {
    if (currentFontSize > 12) {
        currentFontSize -= 1;
        updateFontSize();
    }
});
resetBtn.addEventListener('click', () => {
    currentFontSize = 16;
    updateFontSize();
});
increaseBtn.addEventListener('click', () => {
    if (currentFontSize < 24) {
        currentFontSize += 1;
        updateFontSize();
    }
});

function updateFontSize() {
    document.documentElement.style.setProperty('--font-size-base', `${currentFontSize}px`);
    document.body.style.fontSize = `${currentFontSize}px`;
    html.style.fontSize = `${currentFontSize}px`;
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const faqToggles = document.querySelectorAll('.faq-toggle');
    
    faqToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const faqItem = this.parentElement;
            
            // Check if this item is already active
            const isActive = faqItem.classList.contains('active');
            
            // Close all FAQs first
            document.querySelectorAll('.faq-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // If the clicked item wasn't active, open it
            if (!isActive) {
                faqItem.classList.add('active');
            }
        });
    });
});
