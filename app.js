document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('plan-form');
  const button = document.getElementById('submit-button');
  if (form && button) {
    form.addEventListener('submit', () => {
      button.disabled = true;
      button.textContent = 'Generating…';
    });
  }
});
