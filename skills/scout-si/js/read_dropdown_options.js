/**
 * read_dropdown_options.js
 *
 * What it does:
 *   Reads all available options from the currently open PrimeNG dropdown panel
 *   and returns them as a numbered list. Use this before selecting a value to
 *   confirm the exact option text, since options vary per question.
 *
 * Called from:
 *   scout-si SKILL.md — Phase 4 Step 4.2: run after opening a dropdown (e.g.
 *   "Years of Experience", availability, or similar application form fields)
 *   to see what choices are available before making a selection.
 *
 * Why always read before selecting:
 *   SI Systems uses PrimeNG dropdowns whose options vary by question context.
 *   Reading first prevents selecting an incorrect value due to index shifts or
 *   unexpected option wording.
 *
 * Returns (as the last evaluated expression):
 *   Multi-line string, one option per line:
 *     "0: Less than 1 year"
 *     "1: 1-2 years"
 *     "2: 3-5 years"
 *     etc.
 */

// Target the currently visible PrimeNG dropdown panel.
// The :not([style*="display: none"]) filter excludes hidden panels that may
// exist in the DOM from previously opened (now closed) dropdowns.
const dropdownPanel = document.querySelector('.p-dropdown-panel:not([style*="display: none"])');

// Map each option element to a "index: label" string for easy reading.
Array.from(dropdownPanel.querySelectorAll('.p-dropdown-item'))
  .map((optionElement, optionIndex) => `${optionIndex}: ${optionElement.textContent.trim()}`)
  .join('\n');
