# Theme Switching Mechanism Design

## Overview

The theme switching mechanism for the Therapy Transcript Processor dashboard will allow users to toggle between dark and light themes based on their preferences. This feature enhances accessibility, accommodates different working environments, and provides a personalized user experience.

## Design Principles

The theme switching implementation will follow these core principles:

1. **Seamless Transition**: Theme changes should occur smoothly without page reloads or disrupting the user's workflow.

2. **Persistent Preference**: The user's theme choice should be remembered across sessions using local storage.

3. **System Preference Respect**: By default, the application should respect the user's system preference for light or dark mode.

4. **Accessibility**: The theme switcher itself must be accessible via keyboard and screen readers.

5. **Visual Clarity**: Both themes must maintain sufficient contrast ratios and visual hierarchy.

## User Interface Components

### Theme Toggle Button

The theme toggle will be implemented as a button in the application header, positioned consistently across all pages. The button will:

1. Use universally recognized icons: a sun icon for light mode and a moon icon for dark mode.
2. Display the icon of the theme that will be activated when clicked (not the current theme).
3. Include appropriate aria-labels for screen reader users.
4. Provide a subtle animation during theme transition to indicate the change.

### Design Specifications

**Button Placement**:
- Position: In the header, aligned with other utility controls
- Size: 40px × 40px (touch-friendly)
- Spacing: 8px margin from adjacent elements

**Visual Indicators**:
- Light Theme Icon: Sun symbol (☀️)
- Dark Theme Icon: Moon symbol (🌙)
- Active State: Subtle glow effect
- Hover State: Slight background color change and scale transform

**Accessibility Features**:
- ARIA Label: "Switch to [theme] theme" (dynamically updated)
- Keyboard Focus: Visible focus ring that meets WCAG standards
- Role: button
- Keyboard Shortcut: Alt+T (with on-screen tooltip)

## Technical Implementation Strategy

### CSS Variables System

The theme system will use CSS custom properties (variables) defined at the :root level. This approach allows for easy theme switching without requiring multiple stylesheets.

```css
:root {
  /* Base theme variables */
  --primary-color: #4a6cf7;
  --secondary-color: #6c757d;
  --success-color: #28a745;
  --warning-color: #ffc107;
  --danger-color: #dc3545;
  --info-color: #17a2b8;
  
  /* Light theme defaults */
  --background-color: #f8f9fa;
  --surface-color: #ffffff;
  --text-primary: #212529;
  --text-secondary: #6c757d;
  --border-color: #dee2e6;
  --shadow-color: rgba(0, 0, 0, 0.1);
  
  /* Component-specific variables */
  --card-background: var(--surface-color);
  --header-background: var(--surface-color);
  --table-header-background: #f1f3f5;
  --table-row-hover: #f8f9fa;
}

[data-theme="dark"] {
  --background-color: #121212;
  --surface-color: #1e1e1e;
  --text-primary: #f8f9fa;
  --text-secondary: #adb5bd;
  --border-color: #343a40;
  --shadow-color: rgba(0, 0, 0, 0.3);
  
  /* Component-specific variables */
  --card-background: #2d2d2d;
  --header-background: #252525;
  --table-header-background: #2d2d2d;
  --table-row-hover: #3d3d3d;
}
```

### Theme Detection and Application

The application will use JavaScript to:

1. Check for user's stored preference in local storage
2. If no stored preference exists, detect system preference using `prefers-color-scheme` media query
3. Apply the appropriate theme by adding a `data-theme` attribute to the document element
4. Update the theme toggle button to reflect the current theme
5. Store the user's selection when they manually change themes

### Transition Effects

To ensure smooth visual transitions between themes:

1. Add CSS transitions for color and background-color properties:
```css
* {
  transition: color 0.3s ease, background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}
```

2. Exclude certain properties from transitions to prevent layout shifts:
```css
* {
  transition: color 0.3s ease, background-color 0.3s ease;
  /* Explicitly prevent transitions on layout properties */
  transition-property: color, background-color, border-color, box-shadow;
}
```

## Theme-Specific Design Considerations

### Light Theme

The light theme will feature:
- Clean white backgrounds for content areas
- Subtle shadows for elevation and depth
- Dark text on light backgrounds for optimal readability
- Vibrant accent colors for interactive elements
- Light gray backgrounds for secondary content areas

### Dark Theme

The dark theme will feature:
- Deep gray backgrounds instead of pure black to reduce eye strain
- Reduced contrast for large background areas while maintaining text legibility
- Slightly muted accent colors compared to light theme to prevent visual fatigue
- Subtle glow effects for interactive elements
- Darker elevation levels for cards and modals

## Component-Specific Theming

### Statistics Cards

Both themes will maintain the distinct color coding for different metrics, but the dark theme will use slightly less saturated colors to prevent visual fatigue. Card backgrounds will have sufficient contrast with the page background to create visual separation.

### Tables

Table styling will adapt to each theme:
- Light theme: White background with light gray header, subtle borders
- Dark theme: Dark surface with slightly lighter header, reduced-opacity borders

### System Status Indicators

Status indicators will maintain their semantic colors (green for operational, amber for warnings, red for errors) across both themes, but with appropriate adjustments to ensure visibility against different backgrounds.

### Charts and Data Visualizations

Charts will use theme-appropriate colors with sufficient contrast. Axis lines, labels, and legends will automatically adapt to the current theme's text color.

## Accessibility Considerations

1. **Contrast Ratios**: Both themes will maintain WCAG AA compliance for text contrast (4.5:1 for normal text, 3:1 for large text).

2. **Focus Indicators**: Visible focus indicators will be maintained across both themes, with appropriate contrast against the background.

3. **Color Independence**: Information will not be conveyed by color alone; additional visual cues like icons or patterns will supplement color coding.

4. **Reduced Motion**: Users with the `prefers-reduced-motion` setting enabled will see instant theme changes instead of transitions.

## User Preference Management

The application will store the user's theme preference in local storage using a simple key-value pair:

```javascript
// When user toggles theme
localStorage.setItem('theme-preference', 'light'); // or 'dark'

// On application load
const savedTheme = localStorage.getItem('theme-preference');
```

If the user has not explicitly set a preference, the application will respect their system preference:

```javascript
if (!savedTheme) {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
}
```

The application will also listen for changes to the system preference:

```javascript
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (!localStorage.getItem('theme-preference')) {
    document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
  }
});
```

This comprehensive theme switching design provides a solid foundation for implementing a flexible, accessible, and user-friendly theme system for the Therapy Transcript Processor dashboard.
