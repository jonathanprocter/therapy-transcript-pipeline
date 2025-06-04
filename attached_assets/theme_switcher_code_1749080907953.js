/**
 * Theme Switcher Implementation for Therapy Transcript Processor
 * 
 * This file contains the JavaScript code for implementing a theme switcher
 * that allows users to toggle between light and dark themes.
 */

// Theme Switcher Class
class ThemeSwitcher {
  constructor() {
    this.themeToggleBtn = null;
    this.currentTheme = 'dark'; // Default theme
    this.initialize();
  }

  /**
   * Initialize the theme switcher
   */
  initialize() {
    // Create theme toggle button if it doesn't exist
    this.createThemeToggleButton();
    
    // Load saved theme preference or detect system preference
    this.loadThemePreference();
    
    // Listen for system preference changes
    this.listenForSystemPreferenceChanges();
  }

  /**
   * Create the theme toggle button and add it to the DOM
   */
  createThemeToggleButton() {
    // Check if button already exists
    const existingButton = document.getElementById('theme-toggle-btn');
    if (existingButton) {
      this.themeToggleBtn = existingButton;
      this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
      return;
    }

    // Create new button
    this.themeToggleBtn = document.createElement('button');
    this.themeToggleBtn.id = 'theme-toggle-btn';
    this.themeToggleBtn.className = 'theme-toggle';
    this.themeToggleBtn.setAttribute('aria-label', 'Switch to light theme');
    this.themeToggleBtn.setAttribute('title', 'Switch theme (Alt+T)');
    
    // Add icon to button
    const icon = document.createElement('span');
    icon.className = 'theme-toggle-icon';
    icon.innerHTML = '☀️'; // Default to sun icon (switch to light theme)
    this.themeToggleBtn.appendChild(icon);
    
    // Add click event listener
    this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
    
    // Add keyboard shortcut (Alt+T)
    document.addEventListener('keydown', (e) => {
      if (e.altKey && e.key === 't') {
        e.preventDefault();
        this.toggleTheme();
      }
    });
    
    // Add button to header
    const header = document.querySelector('header') || document.body;
    const settingsButton = document.querySelector('[data-settings]') || null;
    
    if (settingsButton) {
      // Insert before settings button if it exists
      header.insertBefore(this.themeToggleBtn, settingsButton);
    } else {
      // Otherwise append to header
      header.appendChild(this.themeToggleBtn);
    }
  }

  /**
   * Load theme preference from local storage or detect system preference
   */
  loadThemePreference() {
    // Check for saved preference
    const savedTheme = localStorage.getItem('theme-preference');
    
    if (savedTheme) {
      // Use saved preference
      this.setTheme(savedTheme);
    } else {
      // Detect system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }
  }

  /**
   * Listen for changes to system color scheme preference
   */
  listenForSystemPreferenceChanges() {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only apply system preference if user hasn't set explicit preference
      if (!localStorage.getItem('theme-preference')) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }

  /**
   * Toggle between light and dark themes
   */
  toggleTheme() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
    
    // Save preference
    localStorage.setItem('theme-preference', newTheme);
    
    // Announce theme change for screen readers
    this.announceThemeChange(newTheme);
  }

  /**
   * Set the theme
   * @param {string} theme - 'light' or 'dark'
   */
  setTheme(theme) {
    // Update document attribute
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update current theme
    this.currentTheme = theme;
    
    // Update button icon and aria-label
    const icon = this.themeToggleBtn.querySelector('.theme-toggle-icon');
    if (theme === 'dark') {
      icon.innerHTML = '☀️'; // Sun icon (switch to light theme)
      this.themeToggleBtn.setAttribute('aria-label', 'Switch to light theme');
    } else {
      icon.innerHTML = '🌙'; // Moon icon (switch to dark theme)
      this.themeToggleBtn.setAttribute('aria-label', 'Switch to dark theme');
    }
  }

  /**
   * Announce theme change for screen readers
   * @param {string} theme - The new theme
   */
  announceThemeChange(theme) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.classList.add('sr-only'); // Screen reader only
    announcement.textContent = `Theme changed to ${theme} mode`;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement is read
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 3000);
  }
}

// CSS for the theme toggle button
const addThemeToggleStyles = () => {
  const styleElement = document.createElement('style');
  styleElement.textContent = `
    .theme-toggle {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: transparent;
      border: none;
      cursor: pointer;
      transition: background-color 0.3s, transform 0.2s;
      margin: 0 8px;
      color: var(--text-primary);
    }
    
    .theme-toggle:hover {
      background-color: var(--background-hover);
      transform: scale(1.05);
    }
    
    .theme-toggle:focus {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    
    .theme-toggle-icon {
      font-size: 1.2rem;
    }
    
    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    }
    
    /* Reduced motion preference */
    @media (prefers-reduced-motion: reduce) {
      .theme-toggle, * {
        transition: none !important;
      }
    }
  `;
  
  document.head.appendChild(styleElement);
};

// Initialize theme switcher when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  addThemeToggleStyles();
  window.themeSwitcher = new ThemeSwitcher();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeSwitcher;
}
