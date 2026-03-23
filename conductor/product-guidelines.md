# Product Guidelines

## 1. Visual Language & Aesthetics
- **SVG Standards**: All generated SVGs must be compliant with SVG 1.1 or 2.0 standards, ensuring cross-browser compatibility.
- **Responsiveness**: Assets should use relative units (e.g., percentages, `viewBox`) to ensure they scale gracefully across different screen sizes.
- **Color Palette**: Use consistent, accessible color palettes (WCAG AA/AAA compliant) as defined in the global design system.

## 2. Code Quality & Performance
- **Minimalism**: Prioritize clean, human-readable XML. Avoid redundant groups (`<g>`), empty attributes, and overly precise coordinates.
- **Optimization**: All SVGs must undergo an optimization pass (e.g., using SVGO) to minimize file size without compromising visual fidelity.
- **Semantic Structure**: Use descriptive IDs and classes where appropriate to aid in accessibility and potential CSS/JS manipulation.

## 3. User Experience (UX)
- **Immediate Feedback**: The Generate-Audit-Repair loop should provide clear, actionable status updates to the user.
- **Accessibility**: Include `<title>` and `<desc>` tags in generated SVGs to support screen readers.
- **Audit Transparency**: Clearly communicate why an SVG failed an audit (e.g., "overlapping text detected") to facilitate manual or automated repair.

## 4. Development Workflow
- **Validation First**: Every asset must pass a VLM-based visual quality audit before being considered "production-ready."
- **Regression Testing**: Maintain a suite of reference SVGs to ensure optimization passes do not introduce visual artifacts.
